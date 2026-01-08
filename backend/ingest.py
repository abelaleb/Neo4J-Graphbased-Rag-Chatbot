import os
import re
from lxml import etree
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# Configuration
XML_DIR = os.path.join("data", "ai.stackexchange.com") 
BATCH_SIZE = 5000  # Increased for Cloud Latency

# Neo4j Connection
URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")
driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

def clear_database():
    """Wipes the database and sets constraints."""
    print("⚠️  Clearing database...")
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        # Unique constraints are crucial for speed later
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (q:Question) REQUIRE q.id IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (a:Answer) REQUIRE a.id IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (t:Tag) REQUIRE t.name IS UNIQUE")
    print("✅ Database cleared.")

def parse_tags(tag_string):
    if not tag_string: return []
    return re.findall(r'<([^>]+)>', tag_string)

def ingest_users():
    xml_path = os.path.join(XML_DIR, "Users.xml")
    if not os.path.exists(xml_path): return

    print("📥 Ingesting Users (Fast Mode)...")
    # Using CREATE is much faster than MERGE for empty DB
    query = """
    UNWIND $batch AS row
    CREATE (u:User {id: toInteger(row.Id)})
    SET u.name = row.DisplayName, u.reputation = toInteger(row.Reputation)
    """
    
    batch = []
    count = 0
    context = etree.iterparse(xml_path, events=('end',), tag='row')
    
    with driver.session() as session:
        for _, elem in context:
            batch.append(dict(elem.attrib))
            count += 1
            if len(batch) >= BATCH_SIZE:
                session.run(query, batch=batch)
                batch = []
                print(f"   Processed {count} users...", end='\r')
            
            elem.clear()
            while elem.getprevious() is not None: del elem.getparent()[0] # Aggressive memory clearing

        if batch: session.run(query, batch=batch)
    print(f"\n✅ Finished {count} Users.")

def ingest_tags():
    xml_path = os.path.join(XML_DIR, "Tags.xml")
    if not os.path.exists(xml_path): return

    print("📥 Ingesting Tags (Fast Mode)...")
    query = """
    UNWIND $batch AS row
    CREATE (t:Tag {name: row.TagName})
    SET t.count = toInteger(row.Count)
    """
    
    batch = []
    count = 0
    context = etree.iterparse(xml_path, events=('end',), tag='row')
    
    with driver.session() as session:
        for _, elem in context:
            batch.append(dict(elem.attrib))
            count += 1
            if len(batch) >= BATCH_SIZE:
                session.run(query, batch=batch)
                batch = []
                print(f"   Processed {count} tags...", end='\r')
            
            elem.clear()
            while elem.getprevious() is not None: del elem.getparent()[0]

        if batch: session.run(query, batch=batch)
    print(f"\n✅ Finished {count} Tags.")

def ingest_posts():
    xml_path = os.path.join(XML_DIR, "Posts.xml")
    if not os.path.exists(xml_path): return

    print("📥 Ingesting Posts (Fast Mode)...")
    
    # We use MATCH for Users/Tags to ensure connections, but CREATE for the Post itself
    q_query = """
    UNWIND $batch AS row
    CREATE (q:Question {id: toInteger(row.Id)})
    SET q.title = row.Title, q.body = row.Body, q.score = toInteger(row.Score)

    WITH q, row
    MATCH (u:User {id: toInteger(row.OwnerUserId)})
    CREATE (u)-[:ASKED]->(q)

    WITH q, row
    UNWIND row.tags_list AS tag_name
    MATCH (t:Tag {name: tag_name})
    CREATE (q)-[:TAGGED]->(t)
    """

    a_query = """
    UNWIND $batch AS row
    CREATE (a:Answer {id: toInteger(row.Id)})
    SET a.body = row.Body, a.score = toInteger(row.Score), a.is_accepted = (row.Id = row.AcceptedAnswerId)

    WITH a, row
    MATCH (q:Question {id: toInteger(row.ParentId)})
    CREATE (a)-[:ANSWERS]->(q)

    WITH a, row
    MATCH (u:User {id: toInteger(row.OwnerUserId)})
    CREATE (u)-[:PROVIDED]->(a)
    """

    q_batch, a_batch = [], []
    count = 0
    
    context = etree.iterparse(xml_path, events=('end',), tag='row')
    
    with driver.session() as session:
        for _, elem in context:
            post_type = elem.get("PostTypeId")
            row_data = dict(elem.attrib)
            
            if post_type == "1": # Question
                row_data['tags_list'] = parse_tags(row_data.get('Tags', ''))
                q_batch.append(row_data)
                if len(q_batch) >= BATCH_SIZE:
                    session.run(q_query, batch=q_batch)
                    q_batch = []
            
            elif post_type == "2": # Answer
                a_batch.append(row_data)
                if len(a_batch) >= BATCH_SIZE:
                    session.run(a_query, batch=a_batch)
                    a_batch = []
            
            count += 1
            if count % 1000 == 0: print(f"   Processed {count} posts...", end='\r')
            
            elem.clear()
            while elem.getprevious() is not None: del elem.getparent()[0]

        if q_batch: session.run(q_query, batch=q_batch)
        if a_batch: session.run(a_query, batch=a_batch)
        
    print(f"\n✅ Finished {count} Posts.")

if __name__ == "__main__":
    clear_database()
    ingest_users()
    ingest_tags()
    ingest_posts()
    # ingest_votes() SKIPPED for speed
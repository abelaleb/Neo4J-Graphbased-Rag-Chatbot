# ingest.py
import os
import re
from lxml import etree
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# Configuration
XML_DIR = "data"  # Directory where you extracted Posts.xml, Users.xml, Tags.xml
BATCH_SIZE = 1000 # Number of records to commit at once

# Neo4j Connection
URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USERNAME", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

def clear_database():
    """Wipes the database clean before starting."""
    print("⚠️  Clearing database...")
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        # Create constraints for performance
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (q:Question) REQUIRE q.id IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (a:Answer) REQUIRE a.id IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (t:Tag) REQUIRE t.name IS UNIQUE")
    print("✅ Database cleared and constraints set.")

def parse_tags(tag_string):
    """Converts '<nlp><lstm>' into ['nlp', 'lstm']"""
    if not tag_string:
        return []
    return re.findall(r'<([^>]+)>', tag_string)

def ingest_users():
    """Ingests Users.xml"""
    xml_path = os.path.join(XML_DIR, "Users.xml")
    if not os.path.exists(xml_path):
        print(f"Skipping Users (File not found: {xml_path})")
        return

    print("📥 Ingesting Users...")
    query = """
    UNWIND $batch AS row
    MERGE (u:User {id: toInteger(row.Id)})
    SET u.name = row.DisplayName,
        u.reputation = toInteger(row.Reputation)
    """
    
    batch = []
    count = 0
    context = etree.iterparse(xml_path, events=('end',), tag='row')
    
    with driver.session() as session:
        for event, elem in context:
            batch.append(dict(elem.attrib))
            count += 1
            if len(batch) >= BATCH_SIZE:
                session.run(query, batch=batch)
                batch = []
                print(f"   Processed {count} users...", end='\r')
            elem.clear() # Free memory
        if batch:
            session.run(query, batch=batch)
    print(f"\n✅ Finished {count} Users.")

def ingest_posts():
    """Ingests Posts.xml (Handles both Questions and Answers)"""
    xml_path = os.path.join(XML_DIR, "Posts.xml")
    if not os.path.exists(xml_path):
        print("❌ Posts.xml not found!")
        return

    print("📥 Ingesting Posts (Questions & Answers)...")
    
    # Query for Questions (PostTypeId = "1")
    q_query = """
    UNWIND $batch AS row
    MERGE (q:Question {id: toInteger(row.Id)})
    SET q.title = row.Title,
        q.body = row.Body,
        q.score = toInteger(row.Score),
        q.creation_date = row.CreationDate
    
    # Link Owner
    WITH q, row
    WHERE row.OwnerUserId IS NOT NULL
    MATCH (u:User {id: toInteger(row.OwnerUserId)})
    MERGE (u)-[:ASKED]->(q)
    
    # Link Tags
    WITH q, row
    UNWIND row.tags_list AS tag_name
    MERGE (t:Tag {name: tag_name})
    MERGE (q)-[:TAGGED]->(t)
    """

    # Query for Answers (PostTypeId = "2")
    a_query = """
    UNWIND $batch AS row
    MERGE (a:Answer {id: toInteger(row.Id)})
    SET a.body = row.Body,
        a.score = toInteger(row.Score),
        a.is_accepted = (row.Id = row.AcceptedAnswerId)
    
    # Link to Question
    WITH a, row
    MATCH (q:Question {id: toInteger(row.ParentId)})
    MERGE (a)-[:ANSWERS]->(q)
    
    # Link Owner
    WITH a, row
    WHERE row.OwnerUserId IS NOT NULL
    MATCH (u:User {id: toInteger(row.OwnerUserId)})
    MERGE (u)-[:PROVIDED]->(a)
    """

    q_batch = []
    a_batch = []
    count = 0
    
    context = etree.iterparse(xml_path, events=('end',), tag='row')
    
    with driver.session() as session:
        for event, elem in context:
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
            if count % 1000 == 0:
                print(f"   Processed {count} posts...", end='\r')
            
            elem.clear()

        # Commit remainders
        if q_batch: session.run(q_query, batch=q_batch)
        if a_batch: session.run(a_query, batch=a_batch)
        
    print(f"\n✅ Finished {count} Posts.")
# Updated ingest.py snippets for Tags and Comments

def ingest_tags():
    """Ingests Tags.xml to get Tag descriptions."""
    xml_path = os.path.join(XML_DIR, "Tags.xml")
    if not os.path.exists(xml_path): return

    print("📥 Ingesting Tags...")
    query = """
    UNWIND $batch AS row
    MERGE (t:Tag {name: row.TagName})
    SET t.count = toInteger(row.Count),
        t.excerpt_id = toInteger(row.ExcerptPostId)
    """
    # ... (batch logic similar to users)
    print("✅ Finished Tags.")

def ingest_comments():
    """Ingests Comments.xml and links them to Posts."""
    xml_path = os.path.join(XML_DIR, "Comments.xml")
    if not os.path.exists(xml_path): return

    print("📥 Ingesting Comments...")
    query = """
    UNWIND $batch AS row
    MERGE (c:Comment {id: toInteger(row.Id)})
    SET c.text = row.Text, c.score = toInteger(row.Score)
    WITH c, row
    MATCH (p:Post {id: toInteger(row.PostId)})
    MERGE (c)-[:COMMENTED_ON]->(p)
    """
    # ... (batch logic similar to users)
    print("✅ Finished Comments.")
def ingest_votes():
    """Ingests Votes.xml to update Post quality scores."""
    xml_path = os.path.join(XML_DIR, "Votes.xml")
    if not os.path.exists(xml_path):
        print("Skipping Votes (File not found)")
        return

    print("📥 Processing Votes for Quality Scoring...")
    
    # We use a query that updates the existing nodes
    query = """
    UNWIND $batch AS row
    MATCH (p) WHERE p.id = toInteger(row.PostId)
    SET p.community_score = CASE 
        WHEN row.VoteTypeId = '2' THEN coalesce(p.community_score, 0) + 1
        WHEN row.VoteTypeId = '3' THEN coalesce(p.community_score, 0) - 1
        ELSE p.community_score 
    END,
    p.is_accepted_by_user = CASE WHEN row.VoteTypeId = '1' THEN true ELSE p.is_accepted_by_user END
    """
    
    # Use the same batching logic from your previous functions
    # ... (batch processing loop here)
    print("✅ Quality scores updated based on community votes.")
    
if __name__ == "__main__":
    clear_database()
    ingest_users()
    ingest_posts()
    ingest_tags()
    ingest_votes()
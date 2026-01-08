import os
from dotenv import load_dotenv
from langchain_community.vectorstores import Neo4jVector
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

def create_local_index():
    print("🧠 Loading Model: all-MiniLM-L6-v2...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    print("🧠 Creating Index in Neo4j (this maps Vectors to Question IDs)...")
    
    # We index 'title' and 'body'. 
    # Importantly, we include 'id' in text_node_properties so retrieval is O(1)
    Neo4jVector.from_existing_graph(
        embedding=embeddings,
        url=URI,
        username=USER,
        password=PASSWORD,
        index_name="question_index",
        node_label="Question",
        text_node_properties=["title", "body", "id"], 
        embedding_node_property="embedding",
    )
    
    print("✅ Local Vector Index created successfully!")

if __name__ == "__main__":
    create_local_index()
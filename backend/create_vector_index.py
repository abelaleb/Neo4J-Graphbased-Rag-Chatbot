import os
from dotenv import load_dotenv
from langchain_community.graphs import Neo4jGraph
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Neo4jVector

load_dotenv()

# Setup Environment
url = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")
openai_api_key = os.getenv("OPENAI_API_KEY")

def create_index():
    print("🧠 Initializing Vector Indexing...")

    # We use OpenAI Embeddings to convert text to vectors
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

    # This command connects to Neo4j, looks for 'Question' nodes,
    # takes their 'title' and 'body', embeds them, and creates an index named "question_index"
    Neo4jVector.from_existing_graph(
        embedding=embeddings,
        url=url,
        username=username,
        password=password,
        index_name="question_index",
        node_label="Question",
        text_node_properties=["title", "body"], # What fields to read
        embedding_node_property="embedding",    # Where to store the vector
    )
    
    print("✅ Vector Index 'question_index' created successfully!")

if __name__ == "__main__":
    create_index()
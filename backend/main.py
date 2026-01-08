import os
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

# Gemini
from langchain_google_genai import ChatGoogleGenerativeAI

# Local Embeddings & Neo4j
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Neo4jVector
from langchain_neo4j import Neo4jGraph

load_dotenv()

app = FastAPI(title="AI StackExchange GraphRAG (Local Embeddings)")

# --- 1. SETUP RESOURCES ---

# A. Connect to Graph
graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD")
)

# B. Load Local Embeddings (Same model used in indexing)
print("Loading local embedding model (all-MiniLM-L6-v2)...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# C. Connect to Vector Store
vector_index = Neo4jVector.from_existing_index(
    embedding=embeddings,
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD"),
    index_name="question_index"
)

# D. Setup Gemini (LLM)
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-lite-preview-02-05",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0
)

class QueryRequest(BaseModel):
    text: str

@app.get("/health")
def health_check():
    return {"status": "ok", "embedding_model": "all-MiniLM-L6-v2"}

@app.post("/chat")
def chat_endpoint(request: QueryRequest):
    user_query = request.text
    print(f"🔎 Processing: {user_query}")

    # --- STEP 1: SEMANTIC SEARCH (Vector) ---
    # Find the most similar Question node
    try:
        results = vector_index.similarity_search_with_score(user_query, k=1)
    except Exception as e:
        return {"error": str(e)}

    if not results:
        return {"response": "I couldn't find a similar question in the database."}

    # Extract the Question ID from the vector result
    # Neo4jVector puts properties into 'metadata'
    best_doc, score = results[0]
    similar_question_id = best_doc.metadata.get("id")
    similar_question_title = best_doc.metadata.get("title", "Unknown Title")

    print(f"   Matched Question ID: {similar_question_id} (Score: {score:.4f})")

    # --- STEP 2: CONTEXTUAL RETRIEVAL (Graph) ---
    # We use the ID to instantly find the Best Answer
    cypher_query = """
    MATCH (q:Question {id: $q_id})
    
    // Find answers linked to this question
    OPTIONAL MATCH (a:Answer)-[:ANSWERS]->(q)
    
    // Also find the Expert User who answered (optional context)
    OPTIONAL MATCH (u:User)-[:PROVIDED]->(a)
    
    // Return the best answer based on Accepted status or Score
    RETURN q.title AS Question,
           a.body AS Answer,
           a.score AS Score,
           a.is_accepted AS IsAccepted,
           u.reputation AS ExpertReputation
    ORDER BY a.is_accepted DESC, a.score DESC
    LIMIT 1
    """

    try:
        # Pass the ID as an integer
        graph_result = graph.query(cypher_query, params={"q_id": int(similar_question_id)})
    except Exception as e:
        print(f"❌ Graph Query Error: {e}")
        graph_result = []

    # --- STEP 3: SYNTHESIS (LLM) ---
    if not graph_result or not graph_result[0]['Answer']:
        # Fallback: If no answers exist for that question, use the question body itself
        context_text = f"Similiar Question Found: {best_doc.page_content}"
    else:
        record = graph_result[0]
        context_text = (
            f"**Source Question:** {record['Question']}\n"
            f"**Verified Answer** (Score: {record['Score']}, Accepted: {record['IsAccepted']}):\n"
            f"{record['Answer']}\n"
            f"**Expert Reputation:** {record['ExpertReputation']}"
        )

    system_prompt = (
        "You are an AI Assistant for Artificial Intelligence questions. "
        "Answer the user's question based strictly on the provided StackExchange context. "
        "If the context contains code, format it nicely. "
        "Always explicitly cite the 'Source Question' title in your response."
    )

    final_prompt = f"{system_prompt}\n\nUser Input: {user_query}\n\nContext:\n{context_text}"

    response = llm.invoke(final_prompt)

    return {
        "response": response.content,
        "source_question_id": similar_question_id,
        "source_title": similar_question_title,
        "context_type": "Graph Verified"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
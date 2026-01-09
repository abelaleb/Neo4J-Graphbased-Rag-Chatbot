## NBA Neo4j Graph-Based RAG Chatbot – Backend

FastAPI backend for an NBA chatbot built on top of a Neo4j graph database and Google Generative AI (via LangChain). The service exposes a chat endpoint that answers questions about NBA players and teams by translating natural language queries into Cypher, executing them against Neo4j, and composing a natural-language response. It also provides a simple calculator tool and a small evaluation harness.

---

## Features
- FastAPI REST API with CORS support
- Neo4j graph backend for NBA players and teams
- LangChain ReAct agent using Google Generative AI (`ChatGoogleGenerativeAI`)
- Cypher QA chain tool for graph querying
- Simple calculator tool for arithmetic
- Health check endpoint for infrastructure monitoring
- Dataset loader that ingests NBA data from the `balldontlie` API into Neo4j
- Evaluation script with a small “golden set” of questions, logging accuracy and latency

---

## Project Structure
- `main.py` – FastAPI app, LangChain agent and HTTP endpoints
- `populate_db.py` – Script to populate the Neo4j database with NBA teams and players
- `evaluate.py` – Script to evaluate the chatbot on a fixed set of questions
- `evaluation_results.csv` – Output file produced by `evaluate.py`
- `requirements.txt` – Python dependencies

---

## Prerequisites
- Python 3.10+
- A running Neo4j instance (local or remote)
- Google Generative AI API key (for `google-genai` / `langchain-google-genai`)
- (Optional) `balldontlie` API key for higher rate limits when loading data

---

## Installation

From the `backend` directory:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
pip install -r requirements.txt
```

---

## Configuration

Create a `.env` file in the `backend` directory (or otherwise export these variables) with at least:

```env
# Neo4j connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password

# Google Generative AI
GOOGLE_API_KEY=your_google_genai_api_key

# CORS – set to your frontend origin in production
FRONTEND_URL=http://localhost:3000

# Optional: balldontlie API key
BALLDONTLIE_API_KEY=your_balldontlie_key
```

Make sure the Neo4j instance is reachable using the URI and credentials provided.

---

## Populate Neo4j with NBA Data

With the virtual environment activated and `.env` configured:

```bash
python populate_db.py
```

This will:
- Create constraints and indexes in Neo4j
- Fetch NBA teams and players from the `balldontlie` API
- Create `Player` and `Team` nodes and `PLAYS_FOR` relationships

> Note: The script includes pagination and basic rate limiting. For full-scale ingestion, you may want to remove/demo-specific limits in the code.

---

## Run the API Server

From the `backend` directory (with the virtual environment activated):

```bash
uvicorn main:app --reload --port 8000
```

By default this starts the server at `http://localhost:8000`.

---

## API Endpoints

### Health Check
- `GET /health`
- Response example (when Neo4j is healthy):

```json
{
	"status": "healthy",
	"neo4j": "connected"
}
```

If Neo4j is unavailable the endpoint returns `503` with `status: degraded`.

### Chat / Query Endpoint

There are two equivalent chat endpoints:
- `POST /api/generate-query`
- `POST /chat`

**Request body**

```json
{
	"question": "What team does LeBron James play for?"
}
```

**Successful response (shape)**

```json
{
	"input": "...",
	"output": "Natural language answer from the agent",
	"intermediate_steps": [
		{
			"action": {
				"tool": "graph_database_query_tool",
				"tool_input": "...",
				"log": "..."
			},
			"observation": "..."
		}
	]
}
```

The agent internally decides whether to use the graph query tool or the calculator based on the question.

---

## Running the Evaluation Script

1. Start the API server (see “Run the API Server”).
2. In another terminal (same virtual environment), run:

```bash
python evaluate.py
```

The script:
- Sends a small set of predefined test questions to `POST /api/generate-query`
- Checks for expected keywords in the responses
- Logs per-question latency and correctness
- Writes aggregated results to `evaluation_results.csv`

---

## Notes & Troubleshooting
- If `/health` returns `503` or the app logs `Failed to connect to Neo4j`, verify `NEO4J_URI`, `NEO4J_USERNAME`, and `NEO4J_PASSWORD`.
- If you see authentication errors from Google Generative AI, confirm that `GOOGLE_API_KEY` is set and valid.
- When populating the database, network issues or low rate limits on `balldontlie` can cause incomplete data; re-run `populate_db.py` once the issue is resolved.

---

## Development
- Adjust logging levels in `main.py` or `evaluate.py` via `logging.basicConfig` as needed.
- You can add new tools or modify the prompt in `main.py` (`AGENT_PROMPT_TEMPLATE`) to change agent behavior.
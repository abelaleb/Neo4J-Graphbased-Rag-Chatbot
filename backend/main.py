import os
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# LangChain Imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph
from langchain_core.tools import Tool, tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate

# 1. Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 2. Load Environment Variables
load_dotenv()

# 3. Initialize FastAPI App
app = FastAPI(title="NBA Chatbot Agent")

# 4. Production CORS Configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "*")
origins = [FRONTEND_URL]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models for Validation ---
class QueryRequest(BaseModel):
    question: str

# 5. Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

# 6. Robust Neo4j Connection Handling
def get_neo4j_graph():
    """Attempts to connect to Neo4j with retries or graceful failure."""
    try:
        graph = Neo4jGraph(
            url=os.getenv("NEO4J_URI"),
            username=os.getenv("NEO4J_USERNAME"),
            password=os.getenv("NEO4J_PASSWORD")
        )
        graph.refresh_schema()
        logger.info("Successfully connected to Neo4j and refreshed schema.")
        return graph
    except Exception as e:
        logger.critical(f"Failed to connect to Neo4j: {e}")
        return None

graph = get_neo4j_graph()

# 7. Agent Tools Setup
@tool
def calculator(expression: str) -> str:
    """A simple calculator. Use this to evaluate mathematical expressions."""
    try:
        return str(eval(expression))
    except Exception as e:
        return f"Error evaluating expression: {e}"

# Conditional Tool Loading
tools = [calculator]

if graph:
    try:
        graph_qa_chain = GraphCypherQAChain.from_llm(
            llm=llm,
            graph=graph,
            verbose=True,
            allow_dangerous_requests=True,
            return_intermediate_steps=True
        )

        tool_description = (
            "This tool queries a basketball graph database for factual information. "
            "The schema contains two main node types: 'Player' and 'Team'. "
            "1. 'Player' nodes have properties: 'name', 'position', 'height', 'weight', 'jersey_number'. "
            "2. 'Team' nodes have properties: 'name', 'abbreviation', 'city', 'conference'. "
            "RELATIONSHIPS: (:Player)-[:PLAYS_FOR]->(:Team). "
            "Use this tool to find player stats, team rosters, or what team a player belongs to. "
            "Example queries: 'What is the height of LeBron James?', 'Which team does Curry play for?'"
        )

        tools.append(Tool(
            name="graph_database_query_tool",
            func=graph_qa_chain.invoke,
            description=tool_description,
        ))
    except Exception as e:
        logger.error(f"Error initializing GraphCypherQAChain: {e}")
else:
    logger.warning("Neo4j is unavailable. Graph tool will be disabled.")

# 8. Agent Prompt & Executor
AGENT_PROMPT_TEMPLATE = """
You are an expert sports analyst and a master planner. Your primary goal is to answer a user's complex question by breaking it down into a series of smaller, factual sub-questions.

**Tools Available:**
You have access to the following tools:
{tools}

Use the following format:
Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

**Operational Procedure:**
1. Carefully analyze the user's original question to understand what information is needed.
2. Formulate the first simple, factual sub-question and use the 'graph_database_query_tool' to find the answer.
3. Observe the result. **If the tool returns that the information is not available or the result is empty, you MUST stop.** Acknowledge that you cannot answer the question with the available data.
4. Synthesize the gathered facts into a final, comprehensive answer.

Begin!

Question: {input}
Thought:{agent_scratchpad}
"""

agent_prompt = PromptTemplate.from_template(AGENT_PROMPT_TEMPLATE)
agent = create_react_agent(llm, tools, agent_prompt)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    return_intermediate_steps=True,
    max_iterations=7,
    max_execution_time=90.0
)

# 9. Endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers."""
    is_healthy = graph is not None
    status = {
        "status": "healthy" if is_healthy else "degraded",
        "neo4j": "connected" if is_healthy else "disconnected"
    }
    # Return 503 Service Unavailable if critical DB is down, otherwise 200
    if not is_healthy:
        raise HTTPException(status_code=503, detail=status)
    return status

@app.post("/api/generate-query")
async def generate_query(request: QueryRequest):
    """
    Main Chat Endpoint.
    Accepts: {"question": "..."}
    Returns: JSON with answer and intermediate steps.
    """
    question = request.question
    
    if not question:
        raise HTTPException(status_code=400, detail="Field 'question' cannot be empty")

    try:
        logger.info(f"Processing query: {question}")
        
        # Invoke the agent (Note: AgentExecutor is synchronous, so we run it directly. 
        # For high concurrency, you might wrap this in run_in_executor, but this is fine for now)
        response = agent_executor.invoke({"input": question})

        # Format the intermediate steps
        serializable_steps = []
        if "intermediate_steps" in response:
            for action, observation in response["intermediate_steps"]:
                serializable_steps.append({
                    "action": {
                        "tool": action.tool,
                        "tool_input": action.tool_input,
                        "log": action.log.strip(),
                    },
                    "observation": str(observation), # Ensure observation is string
                })

        final_response = {
            "input": response.get("input"),
            "output": response.get("output"),
            "intermediate_steps": serializable_steps,
        }
        
        return final_response

    except Exception as e:
        logger.error(f"Agent execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error processing request")


@app.post("/chat")
async def chat_endpoint(request: QueryRequest):
    """Alias endpoint so frontend can POST /chat with the same payload as /api/generate-query."""
    return await generate_query(request)

# 10. Execution
if __name__ == '__main__':
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    # Run using uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
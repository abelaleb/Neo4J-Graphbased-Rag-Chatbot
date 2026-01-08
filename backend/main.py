# app.py (Corrected Agentic Workflow)
# app.py
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph
from langchain_core.tools import Tool, tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0)

# Initialize the Neo4j graph
try:
    graph = Neo4jGraph(
        url=os.getenv("NEO4J_URI"),
        username=os.getenv("NEO4J_USERNAME"),
        password=os.getenv("NEO4J_PASSWORD")
    )
    graph.refresh_schema()
except Exception as e:
    print(f"Error connecting to Neo4j: {e}")
    graph = None

 # Agent and Tools Setup
@tool
def calculator(expression: str) -> str:
    """A simple calculator. Use this to evaluate mathematical expressions."""
    try:
        # Using eval() is simple for this example.
        return str(eval(expression))
    except Exception as e:
        return f"Error evaluating expression: {e}"

# Initialize the GraphCypherQAChain
graph_qa_chain = GraphCypherQAChain.from_llm(
    llm=llm,
    graph=graph,
    verbose=True,
    allow_dangerous_requests=True,
    return_intermediate_steps=True # Ensure the tool itself returns the Cypher query
)

# Initialize the tool description
tool_description = (
    "This tool queries a basketball graph database for factual information. "
    "Use it for specific questions about players, teams, and coaches. "
    "The database schema includes PLAYER nodes with properties like 'name', 'age', 'number', 'height', and 'weight'. "
    "The input should be a single, clear question. "
    "For example: 'How old is LeBron James?' or 'Who are the teammates of Luka Doncic?'"
)

# Initialize the tools list
tools = [
    Tool(
        name="graph_database_query_tool",
        func=graph_qa_chain.invoke,
        description=tool_description,
    ),
    calculator # <-- Add the new tool here
]

# Initialize the agent prompt template
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
1.  Carefully analyze the user's original question to understand what information is needed.
2.  Formulate the first simple, factual sub-question and use the 'graph_database_query_tool' to find the answer.
3.  Observe the result. **If the tool returns that the information is not available or the result is empty, you MUST stop.** Acknowledge that you cannot answer the question with the available data and formulate a final answer stating that.
4.  Synthesize the gathered facts into a final, comprehensive answer.

Begin!

Question: {input}
Thought:{agent_scratchpad}
"""

# Initialize the agent prompt
agent_prompt = PromptTemplate.from_template(AGENT_PROMPT_TEMPLATE)

# Create the agent using the ReAct framework
agent = create_react_agent(llm, tools, agent_prompt)


# Initialize the agent executor
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    return_intermediate_steps=True,
    max_iterations=7,
    max_execution_time=90.0
)


# Flask API for a basketball chatbot using LangChain, Neo4j, and Gemini AI.
# POST /api/generate-query: Accepts {"question": "..."} and returns agent's answer and reasoning steps.
# Features:
# - Queries Neo4j basketball database (players, teams, coaches)
# - Uses LangChain agent (ReAct) for step-by-step reasoning
# - Supports database queries and calculator tool
# Env vars: NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD 

@app.route('/api/generate-query', methods=['POST'])
def generate_query():
    data = request.get_json()
    question = data.get('question')
    if not question:
        return jsonify({"error": "Question not provided"}), 400
    try:
        # Get the full response from the agent
        response = agent_executor.invoke({"input": question})

        # Format the intermediate steps
        serializable_steps = []
        if "intermediate_steps" in response:
            for action, observation in response["intermediate_steps"]:
                serializable_steps.append(
                    {
                        "action": {
                            "tool": action.tool,
                            "tool_input": action.tool_input,
                            "log": action.log.strip(), # The agent's "thought"
                        },
                        "observation": observation,
                    }
                )

        # Create the final, serializable response object
        final_response = {
            "input": response.get("input"),
            "output": response.get("output"),
            "intermediate_steps": serializable_steps,
        }
        
        return jsonify(final_response)

    except Exception as e:
        print(f"Error during agent executor invocation: {e}")
        return jsonify({"error": "Failed to process request. See server logs."}), 500
    
if __name__ == '__main__':
    app.run(debug=True, port=5000)
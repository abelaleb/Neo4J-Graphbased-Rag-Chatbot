# Neo4j Agentic Chatbot UI

This project is the frontend user interface for the **Neo4j Agentic Chatbot API**. It provides a clean, modern, and responsive chat interface for interacting with the AI agent.

This application was originally cloned from the excellent [ChristophHandschuh/chatbot-ui](https://github.com/ChristophHandschuh/chatbot-ui) repository and has been specifically adapted to connect with the custom agentic backend, display its multi-step reasoning, and handle its rich data responses.

---
## Screenshots

**Welcome Screen:**
![Welcome Screen](https://github.com/nathnael-desta/neo4j_chat_bot/blob/main/frontend/Screenshot%20from%202025-09-01%2013-25-37.png)

**Answering a Simple Question:**
![simple question](https://github.com/nathnael-desta/neo4j_chat_bot/blob/main/frontend/Screenshot%20from%202025-09-01%2013-26-06.png)

**Answering a Complex Question with Agentic Steps:**
![complex question 1](https://github.com/nathnael-desta/neo4j_chat_bot/blob/main/frontend/Screenshot%20from%202025-09-01%2013-27-44.png)

![complex question 2](https://github.com/nathnael-desta/neo4j_chat_bot/blob/main/frontend/Screenshot%20from%202025-09-01%2013-27-49.png)
---
## Getting Started

1.  **Clone the repository**
    ```bash
    git clone <your-frontend-repo-url>
    cd <your-frontend-repo-name>
    ```

2.  **Install dependencies**
    ```bash
    npm install
    ```

3.  **Start the development server**
    ```bash
    npm start
    ```

## Connecting to the Backend

For the chat to function, it must be connected to the [Neo4j Agentic Chatbot API](<your-backend-repo-url>).

1.  Ensure the backend server is running, typically on `http://localhost:5000`.
2.  In the root of this frontend project, create a file named `.env.local`.
3.  Add the following line to the `.env.local` file to point the frontend to your local backend server:
    ```
    VITE_API_BASE_URL=http://localhost:5000
    ```

---
## Credits

This project was built by:
- [Leon Binder](https://github.com/LeonBinder)
- [Christoph Handschuh](https://github.com/ChristophHandschuh)

Additional contribution by:
- [CameliaK](https://github.com/CameliaK) – Implemented web search and integrated it into the LLM prompt

Some code components were inspired by and adapted from [Vercel's AI Chatbot](https://github.com/vercel/ai-chatbot).

This version was adapted for the Neo4j Agentic Chatbot by **[Your Name/Project Name Here]**.

## License

This project is licensed under the Apache License 2.0. Please note that some components were adapted from Vercel's open source AI Chatbot project.

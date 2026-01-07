import { ChatInput } from "@/components/custom/chatinput";
import { PreviewMessage, ThinkingMessage } from "../../components/custom/message";
import { useScrollToBottom } from '@/components/custom/use-scroll-to-bottom';
import { useState } from "react";
import { message } from "../../interfaces/interfaces"
import { Header } from "@/components/custom/header";
import { v4 as uuidv4 } from 'uuid';
import axios from 'axios';
import { Sidebar } from "@/components/custom/sidebar";

export function Chat() {
  const [messagesContainerRef, messagesEndRef] = useScrollToBottom<HTMLDivElement>();
  const [messages, setMessages] = useState<message[]>([]);
  const [question, setQuestion] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(window.innerWidth >= 768);

  async function handleSubmit(text?: string) {
    // Prevent sending if a request is already in progress
    if (isLoading) return;

    const messageText = text || question;
    if (!messageText) return;

    setIsLoading(true);
    // Close sidebar on mobile when a question is submitted
    if (isSidebarOpen && window.innerWidth < 768) {
      setIsSidebarOpen(false);
    }

    // A unique ID for the user message and the corresponding bot message
    const traceId = uuidv4();

    // Add user's message to the UI immediately for a responsive feel
    setMessages(prev => [...prev, { content: messageText, role: "user", id: traceId }]);
    setQuestion(""); // Clear the input box

    try {
      // Build the API URL dynamically based on the environment
      const apiUrl = `${import.meta.env.VITE_API_BASE_URL}/api/generate-query`;

      // Make the API call to your Flask backend
      const response = await axios.post(
        apiUrl,
        { question: messageText }
      );

      // Extract the final answer from the backend's JSON response
      let botAnswer = response.data.output;
      const intermediateSteps = response.data.intermediate_steps;

      // Check if the response contains the specific error message
      if (botAnswer === "Agent stopped due to iteration limit or time limit.") {
        botAnswer = "I'm sorry, I couldn't find that information in my database.";
      }

      // Add the complete bot response to the UI
      const newMessage: message = {
        content: botAnswer,
        role: "assistant",
        id: traceId,
        intermediate_steps: intermediateSteps
      };
      setMessages(prev => [...prev, newMessage]);

    } catch (error) {
      console.error("API call error:", error);
      // Add an error message to the UI
      const errorMessage: message = {
        content: "Sorry, I ran into an error. Please check the server logs.",
        role: "assistant",
        id: traceId
      };
      setMessages(prev => [...prev, errorMessage]);

    } finally {
      // This will run whether the API call succeeds or fails
      setIsLoading(false);
    }
  }

  return (
    <div className="flex h-dvh bg-background">
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        onQuestionClick={handleSubmit}
      />
      <div className="flex flex-col flex-1 min-w-0">
        <Header onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)} />
        <div className="flex flex-col min-w-0 gap-6 flex-1 overflow-y-scroll pt-4" ref={messagesContainerRef}>
            {messages.length === 0 && (
            <div className="flex h-full items-center justify-center">
              <div className="max-w-xl text-center bg-card rounded-xl shadow-lg p-8 border border-border">
              <h1 className="text-2xl font-bold mb-4 flex items-center justify-center gap-2">
                Welcome to the NBA Knowledge Graph Chatbot! 
                <span role="img" aria-label="basketball">🏀</span>
              </h1>
              <p className="mb-4">
                This chat is powered by a Neo4j database featuring NBA stars like <strong>LeBron James</strong>, <strong>Kevin Durant</strong>, <strong>Luka Doncic</strong>, and <strong>Giannis Antetokounmpo</strong>, and teams like the <strong>LA Lakers</strong>, <strong>Brooklyn Nets</strong>, and <strong>Dallas Mavericks</strong>.
              </p>
              <p>
                You can ask about player stats, team rosters, coaching staff, and game performances.
              </p>
              <p className="mt-6 text-muted-foreground">
                Select a suggestion from the sidebar or type a new question.
              </p>
              </div>
            </div>
          )}
          {messages.map((message, index) => (
            <PreviewMessage key={index} message={message} />
          ))}
          {isLoading && <ThinkingMessage />}
          <div ref={messagesEndRef} className="shrink-0 min-w-[24px] min-h-[24px]" />
        </div>
        <div className="flex mx-auto px-4 bg-background pb-4 md:pb-6 gap-2 w-full md:max-w-3xl">
          <ChatInput
            question={question}
            setQuestion={setQuestion}
            onSubmit={handleSubmit}
            isLoading={isLoading}
          />
        </div>
      </div>
    </div>
  );
};

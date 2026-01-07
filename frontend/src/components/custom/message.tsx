import { message } from "@/interfaces/interfaces";
import { Bot, ChevronDown, ChevronUp, User } from "lucide-react";
import { useState } from "react";
import { Button } from "../ui/button";
import { IntermediateSteps } from "./IntermediateSteps";
import { Markdown } from "./markdown";


export function PreviewMessage({ message }: { message: message }) {
  const [showSteps, setShowSteps] = useState(false);
  const isAssistant = message.role === "assistant";

  return (
    <div className="flex flex-col group md:items-center">
      <div className="flex gap-4 p-4 md:max-w-3xl md:w-full">
        <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center text-primary shrink-0">
          {isAssistant ? <Bot size={20} /> : <User size={20} />}
        </div>
        <div className="flex flex-col min-w-0 w-full">
          <div className="font-semibold">
            {isAssistant ? "Assistant" : "You"}
          </div>
          <div className="min-w-0">
            <Markdown>{message.content}</Markdown>
          </div>
          {isAssistant && message.intermediate_steps && message.intermediate_steps.length > 0 && (
            <div className="mt-2">
              <Button variant="outline" size="sm" onClick={() => setShowSteps(!showSteps)}>
                {showSteps ? "Hide Steps" : "Show Steps"}
                {showSteps ? <ChevronUp className="ml-2 h-4 w-4" /> : <ChevronDown className="ml-2 h-4 w-4" />}
              </Button>
            </div>
          )}
        </div>
      </div>
      {showSteps && message.intermediate_steps && (
        <div className="p-4 pt-0 md:max-w-3xl md:w-full md:pl-[64px]">
            <IntermediateSteps steps={message.intermediate_steps} finalAnswer={message.content} />
        </div>
      )}
    </div>
  );
}

export function ThinkingMessage() {
  return (
    <div className="flex flex-col group md:items-center">
      <div className="flex gap-4 p-4 md:max-w-3xl md:w-full">
        <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center text-primary shrink-0">
          <Bot size={20} />
        </div>
        <div className="flex flex-col min-w-0 w-full">
          <div className="font-semibold">
            Assistant
          </div>
          <div className="min-w-0 h-8 flex items-center">
            <div className="bouncing-loader">
              <div></div>
              <div></div>
              <div></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

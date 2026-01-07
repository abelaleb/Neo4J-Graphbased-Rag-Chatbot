import { Card } from "@/components/ui/card";
import { motion } from 'framer-motion';
import { BotIcon, MessageCircle } from 'lucide-react';
import { SiNeo4J } from "react-icons/si";

const templateQuestions = [
  "Who is the coach of the LA Lakers?",
  "List all players on the Brooklyn Nets.",
  "Is James Harden a teammate of Kevin Durant?",
  "Who are the teammates of the players coached by Doc Rivers?",
  "what is the age difference between Luka Doncic and LeBron James?",
  "How many points did Ja Morant score against the Lakers?",
];

interface OverviewProps {
  onQuestionClick: (question: string) => void;
}

export function Overview({ onQuestionClick }: OverviewProps) {
  return (
    <>
      <motion.div
        key="overview"
        className="max-w-3xl mx-auto md:mt-20"
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.98 }}
        transition={{ delay: 0.75 }}
      >
        <div className="rounded-xl p-6 flex flex-col gap-8 leading-relaxed text-center max-w-xl">
          <p className="flex flex-row justify-center gap-4 items-center">
            <BotIcon size={44} />
            <span>+</span>
            <MessageCircle size={44} />
          </p>
        </div>
      </motion.div>
      <div className="flex flex-col gap-4 md:max-w-3xl md:mx-auto md:w-full">
        <div className="text-2xl font-bold flex items-center gap-2">
          {/* <Icons.neo4j className="w-8 h-8" /> */}
          <SiNeo4J className="w-8 h-8" />
          <span>Chat with your Graph</span>
        </div>
        <p className="text-muted-foreground">
          Select a suggestion or type a new question.
        </p>
        <div className="grid grid-cols-1 gap-2">
          {templateQuestions.map((question, index) => (
            <Card
              key={index}
              className="p-3 flex items-center bg-background/50 cursor-pointer hover:bg-primary-foreground transition-colors"
              onClick={() => onQuestionClick(question)}
            >
              <div className="text-sm">{question}</div>
            </Card>
          ))}
        </div>
      </div>
    </>
  );
};

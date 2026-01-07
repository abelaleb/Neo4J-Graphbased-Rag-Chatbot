import { Overview } from "./overview";
import { Button } from "../ui/button";
import { PanelLeftClose } from "lucide-react";
import { cn } from "@/lib/utils";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  onQuestionClick: (question: string) => void;
  className?: string;
}

export function Sidebar({ isOpen, onClose, onQuestionClick, className }: SidebarProps) {
  return (
    <>
      {/* Backdrop for mobile */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-30 bg-black/50 md:hidden"
        />
      )}
      <div
        className={cn(
          "fixed top-0 left-0 z-40 h-full bg-secondary text-secondary-foreground transition-transform duration-300 ease-in-out md:relative md:translate-x-0",
          isOpen ? "translate-x-0" : "-translate-x-full",
          "w-80", // Fixed width for the sidebar
          className
        )}
      >
        <div className="flex flex-col h-full">
            <div className="flex items-center justify-between p-4 pb-0 mb-4">
                <h2 className="text-lg font-semibold">Suggestions</h2>
                <Button variant="ghost" size="icon" onClick={onClose} className="md:hidden">
                <PanelLeftClose className="h-5 w-5" />
                </Button>
            </div>
            <div className="overflow-y-auto px-4">
                <Overview onQuestionClick={onQuestionClick} />
            </div>
        </div>
      </div>
    </>
  );
}

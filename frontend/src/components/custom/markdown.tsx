import { memo } from "react";
import type React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type WithChildren<T> = T & { children?: React.ReactNode };

type CodeProps = WithChildren<React.HTMLAttributes<HTMLElement>> & {
  inline?: boolean;
  className?: string;
};

type OlProps = WithChildren<React.OlHTMLAttributes<HTMLOListElement>>;
type LiProps = WithChildren<React.LiHTMLAttributes<HTMLLIElement>>;
type UlProps = WithChildren<React.HTMLAttributes<HTMLUListElement>>;
type StrongProps = WithChildren<React.HTMLAttributes<HTMLSpanElement>>;
type AnchorProps = WithChildren<React.AnchorHTMLAttributes<HTMLAnchorElement>>;
type HeadingProps = WithChildren<React.HTMLAttributes<HTMLHeadingElement>>;

const NonMemoizedMarkdown = ({ children }: { children: string }) => {
  const components = {
    code: ({ inline, className, children, ...props }: CodeProps) => {
      const match = /language-(\w+)/.exec(className || "");
      return !inline && match ? (
        <pre
          {...props}
          className={`${className} text-sm w-[80dvw] md:max-w-[500px] overflow-x-scroll bg-zinc-100 p-3 rounded-lg mt-2 dark:bg-zinc-800`}
        >
          <code className={match[1]}>{children}</code>
        </pre>
      ) : (
        <code
          className={`${className} text-sm bg-zinc-100 dark:bg-zinc-800 py-0.5 px-1 rounded-md`}
          {...props}
        >
          {children}
        </code>
      );
    },
    ol: ({ children, ...props }: OlProps) => {
      return (
        <ol className="list-decimal list-outside ml-4" {...props}>
          {children}
        </ol>
      );
    },
    li: ({ children, ...props }: LiProps) => {
      return (
        <li className="py-1" {...props}>
          {children}
        </li>
      );
    },
    ul: ({ children, ...props }: UlProps) => {
      return (
        <ul className="list-decimal list-outside ml-4" {...props}>
          {children}
        </ul>
      );
    },
    strong: ({ children, ...props }: StrongProps) => {
      return (
        <span className="font-semibold" {...props}>
          {children}
        </span>
      );
    },
    a: ({ children, ...props }: AnchorProps) => {
      return (
        <a
          className="text-blue-500 hover:underline"
          target="_blank"
          rel="noreferrer"
          {...props}
        >
          {children}
        </a>
      );
    },
    h1: ({ children, ...props }: HeadingProps) => {
      return (
        <h1 className="text-3xl font-semibold mt-6 mb-2" {...props}>
          {children}
        </h1>
      );
    },
    h2: ({ children, ...props }: HeadingProps) => {
      return (
        <h2 className="text-2xl font-semibold mt-6 mb-2" {...props}>
          {children}
        </h2>
      );
    },
    h3: ({ children, ...props }: HeadingProps) => {
      return (
        <h3 className="text-xl font-semibold mt-6 mb-2" {...props}>
          {children}
        </h3>
      );
    },
    h4: ({ children, ...props }: HeadingProps) => {
      return (
        <h4 className="text-lg font-semibold mt-6 mb-2" {...props}>
          {children}
        </h4>
      );
    },
    h5: ({ children, ...props }: HeadingProps) => {
      return (
        <h5 className="text-base font-semibold mt-6 mb-2" {...props}>
          {children}
        </h5>
      );
    },
    h6: ({ children, ...props }: HeadingProps) => {
      return (
        <h6 className="text-sm font-semibold mt-6 mb-2" {...props}>
          {children}
        </h6>
      );
    },
  };

  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
      {children}
    </ReactMarkdown>
  );
};

export const Markdown = memo(
  NonMemoizedMarkdown,
  (prevProps, nextProps) => prevProps.children === nextProps.children,
);

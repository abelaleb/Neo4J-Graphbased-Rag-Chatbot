import { FC } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface CodeBlockProps {
  language: string;
  value: string;
}

export const CodeBlock: FC<CodeBlockProps> = ({ language, value }) => {
  return (
    <div className="relative w-full font-sans text-sm">
      <div className="flex items-center justify-between w-full px-4 py-1 bg-zinc-800 text-zinc-100">
        <span className="text-xs lowercase">{language}</span>
      </div>
      <SyntaxHighlighter
        language={language}
        style={vscDarkPlus}
        PreTag="div"
        customStyle={{
          margin: 0,
          width: '100%',
          padding: '1rem',
          borderBottomLeftRadius: '0.375rem',
          borderBottomRightRadius: '0.375rem',
        }}
        codeTagProps={{
          style: {
            fontFamily: 'var(--font-geist-mono)',
          },
        }}
      >
        {value}
      </SyntaxHighlighter>
    </div>
  );
};
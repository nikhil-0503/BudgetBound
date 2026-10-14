import React from 'react';
import ReactMarkdown, { type Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MarkdownMessageProps {
  content: string;
  isDarkMode?: boolean;
}

export const MarkdownMessage: React.FC<MarkdownMessageProps> = ({ content, isDarkMode = false }) => {
  const components: Components = {
    // Headings with proper spacing
    h1: ({ ...props }) => (
      <h1 className="text-xl font-bold text-paper-900 dark:text-white mt-4 mb-3 leading-tight" {...props} />
    ),
    h2: ({ ...props }) => (
      <h2 className="text-lg font-bold text-paper-900 dark:text-white mt-4 mb-3 leading-tight" {...props} />
    ),
    h3: ({ ...props }) => (
      <h3 className="text-base font-bold text-paper-900 dark:text-white mt-3 mb-2 leading-tight" {...props} />
    ),
    h4: ({ ...props }) => (
      <h4 className="text-sm font-bold text-paper-900 dark:text-white mt-3 mb-2 leading-tight" {...props} />
    ),
    h5: ({ ...props }) => (
      <h5 className="text-sm font-semibold text-paper-900 dark:text-white mt-2 mb-2 leading-tight" {...props} />
    ),
    h6: ({ ...props }) => (
      <h6 className="text-xs font-semibold text-paper-900 dark:text-white mt-2 mb-2 leading-tight" {...props} />
    ),

    // Paragraphs with proper spacing
    p: ({ ...props }) => (
      <p className="text-sm leading-[1.65] text-paper-700 dark:text-paper-300 mb-3" {...props} />
    ),

    // Lists
    ul: ({ ...props }) => (
      <ul className="list-disc list-inside space-y-2 ml-2 mb-3 text-sm text-paper-700 dark:text-paper-300" {...props} />
    ),
    ol: ({ ...props }) => (
      <ol className="list-decimal list-inside space-y-2 ml-2 mb-3 text-sm text-paper-700 dark:text-paper-300" {...props} />
    ),
    li: ({ ...props }) => (
      <li className="ml-2 leading-relaxed" {...props} />
    ),

    // Links
    a: ({ href, ...props }: { href?: string }) => (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="text-marigold-600 dark:text-marigold-400 hover:text-marigold-700 dark:hover:text-marigold-300 underline font-medium"
        {...props}
      />
    ),

    // Bold and italic
    strong: ({ ...props }) => (
      <strong className="font-bold text-paper-900 dark:text-white" {...props} />
    ),
    em: ({ ...props }) => (
      <em className="italic text-paper-700 dark:text-paper-300" {...props} />
    ),

    // Code blocks
    code: ({ inline, ...props }: any) => {
      if (inline) {
        return (
          <code className="bg-paper-200 dark:bg-paper-900/70 text-paper-900 dark:text-paper-200 px-1.5 py-0.5 rounded text-xs font-mono" {...props} />
        );
      }
      return (
        <code
          className="block bg-paper-900/20 dark:bg-paper-900/70 border border-paper-200 dark:border-paper-700 text-paper-900 dark:text-paper-200 p-4 rounded-lg font-mono text-xs overflow-x-auto mb-3 leading-relaxed"
          {...props}
        />
      );
    },

    // Pre (code block wrapper)
    pre: ({ ...props }) => (
      <pre className="bg-paper-900/20 dark:bg-paper-900/70 border border-paper-200 dark:border-paper-700 rounded-lg p-4 overflow-x-auto mb-3" {...props} />
    ),

    // Blockquotes
    blockquote: ({ ...props }) => (
      <blockquote
        className="border-l-4 border-marigold-500 bg-marigold-500/5 dark:bg-marigold-950/20 pl-4 py-2 pr-4 my-3 text-paper-700 dark:text-paper-300 italic text-sm"
        {...props}
      />
    ),

    // Horizontal rule
    hr: ({ ...props }) => (
      <hr className="border-t border-paper-200 dark:border-paper-700 my-4" {...props} />
    ),

    // Tables
    table: ({ ...props }) => (
      <div className="overflow-x-auto mb-3 border border-paper-200 dark:border-paper-700 rounded-lg">
        <table className="w-full text-xs" {...props} />
      </div>
    ),
    thead: ({ ...props }) => (
      <thead className="bg-paper-100 dark:bg-paper-800 border-b border-paper-200 dark:border-paper-700" {...props} />
    ),
    tbody: ({ ...props }) => (
      <tbody className="divide-y divide-paper-200 dark:divide-paper-700" {...props} />
    ),
    tr: ({ ...props }) => (
      <tr className="hover:bg-paper-50 dark:hover:bg-paper-700/30 transition-colors" {...props} />
    ),
    th: ({ ...props }) => (
      <th className="px-4 py-2 text-left font-bold text-paper-900 dark:text-white" {...props} />
    ),
    td: ({ ...props }) => (
      <td className="px-4 py-2 text-paper-700 dark:text-paper-300" {...props} />
    ),

    // Images
    img: ({ alt, ...props }: any) => (
      <img alt={alt} className="max-w-full h-auto rounded-lg my-3 border border-paper-200 dark:border-paper-700" {...props} />
    ),
  };

  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={components}
    >
      {content}
    </ReactMarkdown>
  );
};

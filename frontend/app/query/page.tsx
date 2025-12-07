'use client';

import { useState, useEffect, useRef } from 'react';
import { Send, Loader2, Home, FileText, Dna } from 'lucide-react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { PaperResult } from '@/lib/api';

export default function QueryPage() {
  const searchParams = useSearchParams();
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant'; content: any }>>([]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const q = searchParams.get('q');
    if (q) {
      setQuestion(q);
      handleSubmit(null, q);
    }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent | null, initialQuestion?: string) => {
    e?.preventDefault();
    const currentQuestion = initialQuestion || question;
    if (!currentQuestion.trim() || loading) return;

    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: currentQuestion }]);
    setQuestion('');
    setLoading(true);

    // Create placeholder for streaming response
    const messageIndex = messages.length + 1;
    setMessages(prev => [
      ...prev,
      {
        role: 'assistant',
        content: {
          answer: '',
          papers: [],
          execution_time_ms: 0,
          status: 'streaming',
        },
      },
    ]);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/query/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: currentQuestion,
          mode: 'hybrid',
          limit: 10,
        }),
      });

      if (!response.body) throw new Error('No response body');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let answer = '';
      let papers: PaperResult[] = [];
      let metadata = {};

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.substring(6));

              if (data.type === 'answer_chunk') {
                answer += data.content;
                // Update message with streaming content
                setMessages(prev =>
                  prev.map((msg, idx) =>
                    idx === messageIndex
                      ? {
                          ...msg,
                          content: {
                            ...msg.content,
                            answer,
                          },
                        }
                      : msg
                  )
                );
              } else if (data.type === 'papers') {
                papers = data.content;
              } else if (data.type === 'metadata') {
                metadata = data.content;
              } else if (data.type === 'done') {
                // Finalize message
                setMessages(prev =>
                  prev.map((msg, idx) =>
                    idx === messageIndex
                      ? {
                          ...msg,
                          content: {
                            answer,
                            papers,
                            ...metadata,
                            status: 'complete',
                          },
                        }
                      : msg
                  )
                );
              }
            } catch (err) {
              console.error('Error parsing SSE data:', err);
            }
          }
        }
      }
    } catch (error) {
      console.error('Query failed:', error);
      setMessages(prev =>
        prev.map((msg, idx) =>
          idx === messageIndex
            ? {
                ...msg,
                content: {
                  answer: 'Sorry, I encountered an error processing your question. Please try again.',
                  papers: [],
                  execution_time_ms: 0,
                  status: 'error',
                },
              }
            : msg
        )
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white border-b sticky top-0 z-10 shadow-sm">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 text-xl font-bold text-gray-800">
            <div className="p-2 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg">
              <Dna className="w-6 h-6 text-white" />
            </div>
            BioMedical GraphRAG
          </Link>
          <Link
            href="/"
            className="flex items-center gap-2 text-gray-600 hover:text-gray-800 transition-colors"
          >
            <Home className="w-5 h-5" />
            <span className="hidden sm:inline">Home</span>
          </Link>
        </div>
      </header>

      {/* Main Chat Area */}
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="space-y-6 mb-24">
          {messages.length === 0 ? (
            <div className="text-center py-16">
              <h2 className="text-3xl font-bold text-gray-800 mb-4">
                Ask me anything about biomedical research
              </h2>
              <p className="text-gray-600 mb-8">
                I can help you explore papers, genes, authors, and research connections
              </p>
              <div className="grid md:grid-cols-2 gap-4">
                <ExampleButton
                  text="What are recent CRISPR findings?"
                  onClick={() => {
                    setQuestion('What are recent CRISPR findings?');
                    handleSubmit(null, 'What are recent CRISPR findings?');
                  }}
                />
                <ExampleButton
                  text="Who collaborates with Jennifer Doudna?"
                  onClick={() => {
                    setQuestion('Who collaborates with Jennifer Doudna?');
                    handleSubmit(null, 'Who collaborates with Jennifer Doudna?');
                  }}
                />
              </div>
            </div>
          ) : (
            messages.map((message, index) => (
              <div key={index}>
                {message.role === 'user' ? (
                  <UserMessage content={message.content} />
                ) : (
                  <AssistantMessage content={message.content} />
                )}
              </div>
            ))
          )}

          {loading && (
            <div className="flex items-center gap-3 text-gray-600">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Thinking...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t shadow-lg">
        <div className="container mx-auto px-4 py-4 max-w-4xl">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask a question about biomedical research..."
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !question.trim()}
              className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-semibold hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="w-5 h-5" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

// Components
function UserMessage({ content }: { content: string }) {
  return (
    <div className="flex justify-end">
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg px-6 py-3 max-w-2xl">
        <p>{content}</p>
      </div>
    </div>
  );
}

function AssistantMessage({ content }: { content: any }) {
  return (
    <div className="bg-white rounded-lg shadow-lg p-6 space-y-4">
      {/* Answer with Markdown */}
      <div className="prose prose-blue max-w-none text-gray-800">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            // Custom styling for markdown elements
            h1: ({ node, ...props }) => <h1 className="text-2xl font-bold mt-4 mb-2" {...props} />,
            h2: ({ node, ...props }) => <h2 className="text-xl font-bold mt-3 mb-2" {...props} />,
            h3: ({ node, ...props }) => <h3 className="text-lg font-semibold mt-2 mb-1" {...props} />,
            p: ({ node, ...props }) => <p className="mb-2 leading-relaxed" {...props} />,
            ul: ({ node, ...props }) => <ul className="list-disc list-inside mb-2 space-y-1" {...props} />,
            ol: ({ node, ...props }) => <ol className="list-decimal list-inside mb-2 space-y-1" {...props} />,
            li: ({ node, ...props }) => <li className="ml-4" {...props} />,
            code: ({ node, inline, ...props }: any) =>
              inline ? (
                <code className="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono" {...props} />
              ) : (
                <code className="block bg-gray-100 p-2 rounded my-2 text-sm font-mono overflow-x-auto" {...props} />
              ),
            strong: ({ node, ...props }) => <strong className="font-semibold text-gray-900" {...props} />,
            em: ({ node, ...props }) => <em className="italic text-gray-700" {...props} />,
            a: ({ node, ...props }) => (
              <a className="text-blue-600 hover:text-blue-800 underline" target="_blank" rel="noopener noreferrer" {...props} />
            ),
          }}
        >
          {content.answer || ''}
        </ReactMarkdown>
      </div>

      {/* Papers */}
      {content.papers && content.papers.length > 0 && (
        <div className="space-y-3">
          <h3 className="font-semibold text-gray-800 flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Related Papers ({content.papers.length})
          </h3>
          <div className="space-y-3">
            {content.papers.slice(0, 5).map((paper: PaperResult, idx: number) => (
              <PaperCard key={idx} paper={paper} />
            ))}
          </div>
        </div>
      )}

      {/* Execution Time */}
      {content.execution_time_ms > 0 && (
        <div className="text-sm text-gray-500 pt-2 border-t">
          Query completed in {content.execution_time_ms.toFixed(0)}ms
        </div>
      )}
    </div>
  );
}

function PaperCard({ paper }: { paper: PaperResult }) {
  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:border-blue-400 transition-colors">
      <h4 className="font-semibold text-gray-800 mb-2">{paper.title}</h4>
      {paper.abstract && (
        <p className="text-sm text-gray-600 mb-2 line-clamp-2">{paper.abstract}</p>
      )}
      <div className="flex flex-wrap gap-2 text-xs">
        {paper.authors.slice(0, 3).map((author, idx) => (
          <span key={idx} className="px-2 py-1 bg-blue-100 text-blue-700 rounded">
            {author}
          </span>
        ))}
        {paper.genes.slice(0, 3).map((gene, idx) => (
          <span key={idx} className="px-2 py-1 bg-purple-100 text-purple-700 rounded">
            {gene}
          </span>
        ))}
      </div>
    </div>
  );
}

function ExampleButton({ text, onClick }: { text: string; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="p-4 text-left bg-white rounded-lg shadow hover:shadow-lg transition-all hover:scale-105 border border-gray-200"
    >
      <p className="text-gray-700">{text}</p>
    </button>
  );
}

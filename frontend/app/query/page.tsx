'use client';

import { useState, useEffect, useRef, Suspense } from 'react';
import { Send, Loader2, Home, FileText, Dna, Code, Sparkles, ChevronDown, ChevronUp, RotateCcw } from 'lucide-react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { PaperResult } from '@/lib/api';

function QueryPageContent() {
  const searchParams = useSearchParams();
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant'; content: any }>>([]);
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<'simple' | 'technical'>('simple');
  const [expandedMessages, setExpandedMessages] = useState<Set<number>>(new Set());
  const [sessionId, setSessionId] = useState<string | null>(null);
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

  const handleNewConversation = () => {
    setMessages([]);
    setSessionId(null);
    setExpandedMessages(new Set());
  };

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
          session_id: sessionId,
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

              if (data.type === 'session') {
                // Store session ID for conversation continuity
                setSessionId(data.content);
              } else if (data.type === 'answer_chunk') {
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
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between mb-3">
            <Link href="/" className="flex items-center gap-2 text-xl font-bold text-gray-800">
              <div className="p-2 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg">
                <Dna className="w-6 h-6 text-white" />
              </div>
              BioQuest
            </Link>
            <div className="flex items-center gap-4">
              {messages.length > 0 && (
                <button
                  onClick={handleNewConversation}
                  className="flex items-center gap-2 text-gray-600 hover:text-gray-800 transition-colors text-sm"
                  title="Start new conversation"
                >
                  <RotateCcw className="w-4 h-4" />
                  <span className="hidden sm:inline">New Chat</span>
                </button>
              )}
              <Link
                href="/"
                className="flex items-center gap-2 text-gray-600 hover:text-gray-800 transition-colors"
              >
                <Home className="w-5 h-5" />
                <span className="hidden sm:inline">Home</span>
              </Link>
            </div>
          </div>
          {/* Mode Toggle */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">Mode:</span>
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setMode('simple')}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all flex items-center gap-2 ${
                  mode === 'simple'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                <Sparkles className="w-4 h-4" />
                Simple
              </button>
              <button
                onClick={() => setMode('technical')}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all flex items-center gap-2 ${
                  mode === 'technical'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                <Code className="w-4 h-4" />
                Technical
              </button>
            </div>
          </div>
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
                  <AssistantMessage
                    content={message.content}
                    mode={mode}
                    isExpanded={expandedMessages.has(index)}
                    onToggle={() => {
                      setExpandedMessages(prev => {
                        const next = new Set(prev);
                        if (next.has(index)) {
                          next.delete(index);
                        } else {
                          next.add(index);
                        }
                        return next;
                      });
                    }}
                  />
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

function AssistantMessage({ content, mode, isExpanded, onToggle }: {
  content: any;
  mode: 'simple' | 'technical';
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const hasTechnicalData = content.execution_time_ms > 0 || content.query_type || content.papers?.length > 0;

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
            {content.papers.slice(0, mode === 'simple' ? 3 : 10).map((paper: PaperResult, idx: number) => (
              <PaperCard key={idx} paper={paper} mode={mode} />
            ))}
          </div>
        </div>
      )}

      {/* Technical Details Section */}
      {mode === 'technical' && hasTechnicalData && (
        <div className="border-t pt-4 mt-4">
          <button
            onClick={onToggle}
            className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors w-full"
          >
            {isExpanded ? (
              <>
                <ChevronUp className="w-4 h-4" />
                Hide Technical Details
              </>
            ) : (
              <>
                <ChevronDown className="w-4 h-4" />
                Show Technical Details
              </>
            )}
          </button>
          
          {isExpanded && (
            <div className="mt-3 space-y-2 text-sm bg-gray-50 rounded-lg p-4">
              {content.execution_time_ms > 0 && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Execution Time:</span>
                  <span className="font-mono text-gray-800">{content.execution_time_ms.toFixed(0)}ms</span>
                </div>
              )}
              {content.query_type && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Query Type:</span>
                  <span className="font-mono text-gray-800">{content.query_type}</span>
                </div>
              )}
              {content.papers && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Papers Retrieved:</span>
                  <span className="font-mono text-gray-800">{content.papers.length}</span>
                </div>
              )}
              {content.mode && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Search Mode:</span>
                  <span className="font-mono text-gray-800">{content.mode}</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Simple mode - minimal execution time */}
      {mode === 'simple' && content.execution_time_ms > 0 && (
        <div className="text-xs text-gray-400 pt-2 border-t">
          Answered in {(content.execution_time_ms / 1000).toFixed(1)}s
        </div>
      )}
    </div>
  );
}

function PaperCard({ paper, mode }: { paper: PaperResult; mode?: 'simple' | 'technical' }) {
  const showFullDetails = mode === 'technical';
  
  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:border-blue-400 transition-colors">
      <h4 className="font-semibold text-gray-800 mb-2">{paper.title}</h4>
      {paper.abstract && (
        <p className={`text-sm text-gray-600 mb-2 ${showFullDetails ? '' : 'line-clamp-2'}`}>
          {paper.abstract}
        </p>
      )}
      <div className="flex flex-wrap gap-2 text-xs">
        {paper.authors.slice(0, showFullDetails ? 5 : 3).map((author, idx) => (
          <span key={idx} className="px-2 py-1 bg-blue-100 text-blue-700 rounded">
            {author}
          </span>
        ))}
        {paper.genes.slice(0, showFullDetails ? 5 : 3).map((gene, idx) => (
          <span key={idx} className="px-2 py-1 bg-purple-100 text-purple-700 rounded">
            {gene}
          </span>
        ))}
      </div>
      {showFullDetails && (
        <div className="mt-2 pt-2 border-t text-xs text-gray-500">
          {paper.pmid && <div>PMID: {paper.pmid}</div>}
          {paper.publication_date && <div>Published: {paper.publication_date}</div>}
          {paper.score && <div>Relevance Score: {paper.score.toFixed(3)}</div>}
        </div>
      )}
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

export default function QueryPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading query interface...</p>
        </div>
      </div>
    }>
      <QueryPageContent />
    </Suspense>
  );
}

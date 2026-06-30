import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'

function Chat({ endpoint, placeholder = "Posez votre question...", onCvReady, stateful = false }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [threadId, setThreadId] = useState(null);
  const [currentSection, setCurrentSection] = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  async function sendMessage() {
    if (!input.trim() || isLoading) return;

    const userMessage = { role: 'user', content: input };
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInput('');
    setIsLoading(true);

    const body = stateful
      ? { message: input, thread_id: threadId }
      : { message: input, history: messages };

    try {
      const response = await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const data = await response.json();
      if (data.response) {
        setMessages([...updatedMessages, { role: 'assistant', content: data.response }]);
      }
      if (stateful && data.thread_id) {
        setThreadId(data.thread_id);
        setCurrentSection(data.current_section ?? null);
      }
      if (data.cv_ready) {
        onCvReady?.();
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages([...updatedMessages, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }]);
    } finally {
      setIsLoading(false);
    }
  }

  function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }

  return (
    <div className="w-full max-w-2xl bg-white rounded-2xl shadow-lg flex flex-col h-[600px]">
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 && (
          <p className="text-center text-gray-400 mt-8">
            Posez votre première question pour commencer !
          </p>
        )}
        {messages.map((message, index) => (
          <div key={index} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[75%] px-4 py-2 rounded-2xl text-sm ${message.role === "user" ? "bg-blue-500 text-white" : "bg-gray-100 text-gray-800 prose prose-sm"}`}>
              {message.role === "assistant" ? (
                <ReactMarkdown>{message.content}</ReactMarkdown>
              ) : (
                message.content
              )}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 text-gray-500 px-4 py-2 rounded-2xl text-sm">
              En train de répondre...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {(currentSection || threadId) && (
        <div className="px-4 py-1 border-t text-xs text-gray-400 flex justify-between">
          {currentSection && (
            <span>Section : <span className="font-medium text-blue-500">{currentSection}</span></span>
          )}
          {threadId && (
            <span className="font-mono text-gray-300">{threadId}</span>
          )}
        </div>
      )}

      <div className="p-4 border-t flex gap-2 items-end">
        <textarea
          className="flex-1 border border-gray-300 rounded-xl px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 resize-none max-h-32"
          rows={2}
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
        />
        <button
          className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-xl text-sm font-medium disabled:opacity-50"
          onClick={sendMessage}
          disabled={isLoading}
        >
          Envoyer
        </button>
      </div>
    </div>
  );
}

export default Chat;

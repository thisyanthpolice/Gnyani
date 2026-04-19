import { useState, useRef, useEffect } from "react";
import { sendChat } from "./api";

/**
 * Chat Component
 * - Message list with user/bot bubbles
 * - Input box + send button
 * - Loading state
 * - Source links display
 */
export default function Chat({ websiteId, websiteUrl }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    const question = input.trim();
    if (!question || loading) return;

    // Add user message
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setInput("");
    setLoading(true);

    try {
      const data = await sendChat(question, websiteId);
      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          content: data.answer,
          sources: data.sources || [],
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "bot", content: `Error: ${err.message}`, isError: true },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="chat-header-dot"></div>
        <span>Chatting about: <strong>{websiteUrl}</strong></span>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">
            <div className="chat-empty-icon">💬</div>
            <p>Ask anything about the website!</p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`chat-bubble ${msg.role}`}>
            <div className="bubble-label">
              {msg.role === "user" ? "You" : "AI"}
            </div>
            <div className={`bubble-content ${msg.isError ? "error" : ""}`}>
              {msg.content}
            </div>
            {msg.sources && msg.sources.length > 0 && (
              <div className="bubble-sources">
                <span className="sources-label">Sources:</span>
                {msg.sources.map((src, j) => (
                  <a
                    key={j}
                    href={src}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="source-link"
                  >
                    {new URL(src).pathname || src}
                  </a>
                ))}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="chat-bubble bot">
            <div className="bubble-label">AI</div>
            <div className="bubble-content">
              <div className="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about the website..."
          disabled={loading}
          className="chat-input"
        />
        <button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          className="chat-send-btn"
        >
          {loading ? "..." : "Send"}
        </button>
      </div>
    </div>
  );
}

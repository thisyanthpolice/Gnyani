import { useState, useEffect } from "react";
import Chat from "./Chat";
import { trainWebsite, getStatus, getWebsites } from "./api";

/**
 * Main App Component
 * - Train section: input a URL and train the chatbot
 * - Chat section: ask questions once training is done
 * - Website selector: switch between trained websites
 */
export default function App() {
  const [url, setUrl] = useState("");
  const [websites, setWebsites] = useState([]);
  const [activeWebsite, setActiveWebsite] = useState(null);
  const [training, setTraining] = useState(false);
  const [trainStatus, setTrainStatus] = useState(null);
  const [error, setError] = useState("");

  // Load existing websites on mount
  useEffect(() => {
    loadWebsites();
  }, []);

  // Poll training status
  useEffect(() => {
    if (!trainStatus || trainStatus.status === "ready" || trainStatus.status === "failed") {
      return;
    }
    const interval = setInterval(async () => {
      try {
        const status = await getStatus(trainStatus.website_id);
        setTrainStatus(status);
        if (status.status === "ready") {
          setActiveWebsite(status);
          loadWebsites();
        }
      } catch (e) {
        console.error(e);
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [trainStatus]);

  const loadWebsites = async () => {
    try {
      const list = await getWebsites();
      setWebsites(list);
    } catch (e) {
      console.error(e);
    }
  };

  const handleTrain = async () => {
    if (!url.trim()) return;
    setError("");
    setTraining(true);
    setTrainStatus(null);

    try {
      const result = await trainWebsite(url.trim());
      setTrainStatus({
        website_id: result.website_id,
        url: url.trim(),
        status: result.status,
        page_count: 0,
      });
    } catch (e) {
      setError(e.message);
    } finally {
      setTraining(false);
    }
  };

  const selectWebsite = (w) => {
    setActiveWebsite(w);
    setTrainStatus(null);
  };

  const statusColor = (status) => {
    const colors = {
      ready: "#4ade80",
      pending: "#facc15",
      crawling: "#60a5fa",
      embedding: "#c084fc",
      failed: "#f87171",
    };
    return colors[status] || "#94a3b8";
  };

  return (
    <div className="app">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="brand-icon">🤖</span>
          <h1>RAG Chatbot</h1>
        </div>

        {/* Train Section */}
        <div className="train-section">
          <h2>Train on Website</h2>
          <div className="train-input-group">
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com"
              className="train-input"
              disabled={training}
            />
            <button
              onClick={handleTrain}
              disabled={training || !url.trim()}
              className="train-btn"
            >
              {training ? "Starting..." : "Train"}
            </button>
          </div>

          {error && <div className="error-msg">{error}</div>}

          {trainStatus && (
            <div className="status-card">
              <div className="status-row">
                <span>Status:</span>
                <span
                  className="status-badge"
                  style={{ backgroundColor: statusColor(trainStatus.status) }}
                >
                  {trainStatus.status}
                </span>
              </div>
              {trainStatus.page_count > 0 && (
                <div className="status-row">
                  <span>Pages:</span>
                  <span>{trainStatus.page_count}</span>
                </div>
              )}
              {trainStatus.error && (
                <div className="error-msg">{trainStatus.error}</div>
              )}
            </div>
          )}
        </div>

        {/* Website List */}
        <div className="website-list">
          <h2>Trained Websites</h2>
          {websites.length === 0 && (
            <p className="no-websites">No websites trained yet</p>
          )}
          {websites.map((w) => (
            <button
              key={w.id}
              onClick={() => selectWebsite(w)}
              className={`website-item ${activeWebsite?.id === w.id ? "active" : ""}`}
            >
              <span
                className="website-dot"
                style={{ backgroundColor: statusColor(w.status) }}
              ></span>
              <span className="website-url">
                {w.url.replace(/^https?:\/\//, "").slice(0, 30)}
              </span>
              <span className="website-badge">{w.status}</span>
            </button>
          ))}
        </div>
      </aside>

      {/* ── Main Area ── */}
      <main className="main-area">
        {activeWebsite && activeWebsite.status === "ready" ? (
          <Chat websiteId={activeWebsite.id} websiteUrl={activeWebsite.url} />
        ) : (
          <div className="welcome">
            <div className="welcome-icon">🌐</div>
            <h2>Website AI Chatbot</h2>
            <p>
              Enter a website URL in the sidebar to train the chatbot.<br />
              Once training is complete, you can ask questions about the website.
            </p>
            <div className="welcome-steps">
              <div className="step">
                <span className="step-num">1</span>
                <span>Enter a website URL</span>
              </div>
              <div className="step">
                <span className="step-num">2</span>
                <span>Click Train &amp; wait</span>
              </div>
              <div className="step">
                <span className="step-num">3</span>
                <span>Ask questions!</span>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

/**
 * API Client — communicates with the FastAPI backend.
 *
 * Base URL: http://localhost:8000 (change if backend runs elsewhere)
 */

// ── Change this if your backend runs on a different host/port ──
const API_BASE = "http://localhost:8000";

/**
 * Submit a website URL for training.
 * @param {string} url - The website URL to crawl and train on
 * @returns {Promise<{website_id: number, status: string, message: string}>}
 */
export async function trainWebsite(url) {
  const res = await fetch(`${API_BASE}/train`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Training failed (${res.status})`);
  }
  return res.json();
}

/**
 * Check training status for a website.
 * @param {number} websiteId
 * @returns {Promise<{website_id: number, url: string, status: string, page_count: number, error: string|null}>}
 */
export async function getStatus(websiteId) {
  const res = await fetch(`${API_BASE}/status/${websiteId}`);
  if (!res.ok) throw new Error("Failed to fetch status");
  return res.json();
}

/**
 * Send a chat question about a trained website.
 * @param {string} question
 * @param {number} websiteId
 * @returns {Promise<{answer: string, sources: string[]}>}
 */
export async function sendChat(question, websiteId) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, website_id: websiteId }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Chat failed (${res.status})`);
  }
  return res.json();
}

/**
 * List all trained websites.
 * @returns {Promise<Array>}
 */
export async function getWebsites() {
  const res = await fetch(`${API_BASE}/websites`);
  if (!res.ok) throw new Error("Failed to fetch websites");
  return res.json();
}

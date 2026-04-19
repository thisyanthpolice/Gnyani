# 🤖 RAG Chatbot — Website AI Assistant

A production-ready MVP that crawls any website, creates embeddings, and lets you ask questions with AI-powered answers grounded in the website's content.

## ✨ Features

- 🌐 **Website Crawling** — Crawls all pages with BFS (depth limit, dedup, robots.txt)
- 🧠 **Smart Chunking** — Splits content into overlapping chunks preserving context
- 🔢 **Vector Embeddings** — OpenAI `text-embedding-3-small` for fast, cheap embeddings
- 🔍 **FAISS Search** — Lightning-fast similarity search
- 💬 **RAG Answers** — GPT-4o-mini generates grounded answers (no hallucination)
- 📊 **PostgreSQL** — Stores metadata, documents, and chat logs
- ⚡ **Redis Cache** — Optional caching for repeated queries
- 🎨 **React UI** — Clean dark-themed chat interface

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, Uvicorn |
| Database | PostgreSQL + FAISS |
| AI | OpenAI (text-embedding-3-small, GPT-4o-mini) |
| Crawling | BeautifulSoup + Playwright |
| Frontend | React (Vite) |
| Cache | Redis (optional) |

## 📁 Project Structure

```
rag-chatbot/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py             # Environment config
│   ├── routes/
│   │   ├── train.py          # POST /train, GET /status, GET /websites
│   │   └── chat.py           # POST /chat
│   ├── services/
│   │   ├── crawler.py        # Website crawling (BS4 + Playwright)
│   │   ├── chunking.py       # Text chunking with overlap
│   │   ├── embeddings.py     # OpenAI embeddings
│   │   ├── vector_store.py   # FAISS index management
│   │   └── rag_pipeline.py   # Query → Search → LLM answer
│   ├── db/
│   │   ├── database.py       # SQLAlchemy async engine
│   │   └── models.py         # ORM models (Website, Document, Chat)
│   └── utils/
│       └── helpers.py         # URL normalization, text cleaning
├── frontend/
│   ├── src/
│   │   ├── App.jsx           # Main app (sidebar + chat)
│   │   ├── Chat.jsx          # Chat UI component
│   │   ├── api.js            # API client
│   │   ├── index.css         # Styles (dark theme)
│   │   └── main.jsx          # React entry point
│   ├── index.html
│   └── package.json
├── .env                       # ⚠️  Your credentials go here
├── .env.example               # Template
├── requirements.txt           # Python dependencies
└── README.md
```

---

## 🚀 Setup & Run Locally

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL** running locally
- **OpenAI API Key** ([get one here](https://platform.openai.com/api-keys))

### Step 1: Clone & Configure

```bash
cd rag-chatbot

# Edit .env and add your credentials:
#   - OPENAI_API_KEY=sk-your-key-here
#   - DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/ragchatbot
```

### Step 2: Create PostgreSQL Database

```sql
-- In psql or pgAdmin:
CREATE DATABASE ragchatbot;
```

### Step 3: Install Backend Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser (for JS-rendered pages)
playwright install chromium
```

### Step 4: Start Backend

```bash
uvicorn backend.main:app --reload --port 8000
```

The API is now running at **http://localhost:8000**
Swagger docs at **http://localhost:8000/docs**

### Step 5: Install & Start Frontend

```bash
cd frontend
npm install
npm run dev
```

The UI is now running at **http://localhost:5173**

---

## 📡 API Endpoints

### Train a Website
```bash
POST /train
Body: { "url": "https://example.com" }
Response: { "website_id": 1, "status": "pending", "message": "..." }
```

### Check Training Status
```bash
GET /status/{website_id}
Response: { "website_id": 1, "url": "...", "status": "ready", "page_count": 12 }
```

### Ask a Question
```bash
POST /chat
Body: { "question": "What is this website about?", "website_id": 1 }
Response: { "answer": "...", "sources": ["url1", "url2"] }
```

### List All Websites
```bash
GET /websites
Response: [{ "id": 1, "url": "...", "status": "ready", ... }]
```

---

## 🔁 How It Works

```
User enters URL → Backend crawls all pages
                → Text extracted & cleaned
                → Split into overlapping chunks
                → OpenAI creates embeddings
                → Stored in FAISS index

User asks question → Question embedded
                   → FAISS finds top 5 relevant chunks
                   → GPT-4o-mini generates grounded answer
                   → Answer + sources displayed in UI
```

---

## 🚀 Deployment

### Backend (Render / Railway)

1. Push code to GitHub
2. Create a new Web Service on [Render](https://render.com)
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables from `.env`
6. Add a PostgreSQL database (Render provides free tier)

### Frontend (Vercel)

1. Push `frontend/` to GitHub
2. Import project on [Vercel](https://vercel.com)
3. Set root directory to `frontend`
4. Update `API_BASE` in `src/api.js` to your deployed backend URL

---

## 💰 Cost Estimates

| Component | Cost |
|-----------|------|
| Embeddings (text-embedding-3-small) | ~$0.02 per 1M tokens |
| Chat (GPT-4o-mini) | ~$0.15 per 1M input tokens |
| 50-page website training | ~$0.01 |
| 100 chat questions | ~$0.05 |

---

## ⚠️ Important Notes

- **Never commit your `.env` file** — it contains your API key
- FAISS indexes are stored locally in `./faiss_indexes/`
- Playwright is optional — only needed for JavaScript-heavy websites
- Redis is optional — the app works without it, caching just improves repeated query speed

## License

MIT

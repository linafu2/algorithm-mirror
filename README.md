# Algorithm Mirror

A transparent mock social feed for learning how recommendation systems work. Like, skip, or mark posts as not interested, then see exactly how those choices build a profile and shape what you see next.

This is currently a **simplified simulation** for algorithmic literacy, not a replica of any real platform's algorithm.

## What you can do

### Feed

- Browse 16 mock posts at [http://localhost:3000](http://localhost:3000)
- **Like**, **Skip**, or **Not interested** on each post
- Get the next recommendation from a deterministic tag-scoring engine

### Sidebar (always visible)

- **Visible user model** — live tag weights inferred from your session
- **Why this recommendation?** — plain-English summary plus per-tag match scores for the current post

### Deep dive

Two analysis modes below the feed:

**Trace this recommendation** (`POST /trace`)

Deterministic, fully explainable scoring — no LLM involved.

- Tag-level score breakdown for the current top pick
- Full candidate ranking of every unseen post still in the queue

**Audit my algorithm** (`POST /audit`)

Session-level reflection combining deterministic metrics with Claude interpretation.

- Diversity and concentration scores (Shannon entropy over topics you liked)
- Dominant topic and top topic shares
- AI summary of patterns, narrowing level, a reflection question, and a suggested next action

Requires an Anthropic API key. Metrics are always computed locally; the LLM only interprets them.

## How the algorithm works

Each post has tags. Every action updates your visible profile:

| Action           | Effect per tag |
|------------------|----------------|
| Like             | +2             |
| Skip             | −0.5           |
| Not interested   | −2             |

The next post is the **unseen post with the highest total tag score** (ties broken by post ID).

Posts live in `backend/main.py` as the `POSTS` list. Edit titles, tags, tone, and intensity there to change the mock catalog.

## Project structure

```
algorithm-mirror/
├── backend/
│   ├── main.py          # FastAPI app, POSTS catalog, /recommend /trace /audit
│   ├── rec_trace.py     # Profile building, scoring, recommendation trace
│   ├── audit.py         # Diversity metrics (deterministic)
│   ├── llm.py           # Claude structured output for feed audit
│   └── tests/
├── frontend/
│   └── app/page.tsx     # Feed UI, sidebar, deep-dive panels
└── README.md
```

## Run locally

Use two terminals — backend first, then frontend.

### Backend (port 8000)

First-time setup:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional: needed for AI feed audit
uvicorn main:app --reload
```

If port 8000 is already in use:

```bash
kill $(lsof -ti :8000)
```

### Frontend (port 3000)

First-time setup:

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The frontend expects the API at `http://localhost:8000`.

## API endpoints

| Method | Path         | Purpose                                      |
|--------|--------------|----------------------------------------------|
| GET    | `/posts`     | Return all mock posts                        |
| POST   | `/recommend` | Next post, profile, and reason               |
| POST   | `/trace`     | Full recommendation trace                    |
| POST   | `/audit`     | Feed metrics + AI analysis                   |
| POST   | `/explain`   | Standalone Claude explanation (not wired in UI)|

## Environment

Create `backend/.env`:

```
ANTHROPIC_API_KEY=your_key_here
```

- **Feed, profile, trace** — work without a key
- **Feed audit (AI section)** — requires a key and `langchain-anthropic` (install separately if audit fails)

## Tests

```bash
cd backend
source venv/bin/activate
PYTHONPATH=. pytest tests/ -v
```

## Stack

- **Backend:** Python, FastAPI, Anthropic SDK, LangChain (audit)
- **Frontend:** Next.js, React, Tailwind CSS

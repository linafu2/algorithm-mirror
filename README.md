# Algorithm Mirror

A transparent mock social feed that shows how likes, skips, and "not interested" clicks shape what you see next.

## MVP features

- Mock feed at `localhost:3000`
- Like / skip / not interested on posts
- Live visible user profile (tag weights)
- Plain-English explanation of why each post was recommended
- Ask Claude to explain your feed

## Run locally

### Backend (port 8000)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your Anthropic API key
uvicorn main:app --reload
```

Without an API key, the explain button still works using a built-in fallback summary.

### Frontend (port 3000)

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## How it works

Each post has tags. Actions update a visible profile:

- **Like** → +2 per tag
- **Skip** → -0.5 per tag
- **Not interested** → -2 per tag

The next post is the unseen post with the highest total tag score. The sidebar shows the inferred profile and the reasoning for each recommendation.

This is a simplified simulation, not a real platform algorithm.

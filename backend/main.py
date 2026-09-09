import os
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

import anthropic
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from audit import build_feed_metrics
from llm import generate_feed_audit
from rec_trace import build_recommendation_trace

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=api_key) if api_key else None


POSTS = [
    {
        "id": 1,
        "title": "Why cities should build more trains",
        "tags": ["urbanism", "transportation", "policy"],
        "tone": "educational",
        "intensity": 2,
    },
    {
        "id": 2,
        "title": "Outfit ideas for walking around Boston",
        "tags": ["fashion", "lifestyle"],
        "tone": "aesthetic",
        "intensity": 1,
    },
    {
        "id": 3,
        "title": "A cat slowly knocking over a glass",
        "tags": ["animals", "humor"],
        "tone": "funny",
        "intensity": 1,
    },
    {
        "id": 4,
        "title": "The psychology of doomscrolling",
        "tags": ["psychology", "internet", "attention"],
        "tone": "reflective",
        "intensity": 3,
    },
    {
        "id": 5,
        "title": "How recommendation algorithms shape desire",
        "tags": ["technology", "philosophy", "internet"],
        "tone": "analytical",
        "intensity": 3,
    },
    {
        "id": 6,
        "title": "Beginner pottery wheel mistakes",
        "tags": ["art", "pottery", "education"],
        "tone": "educational",
        "intensity": 1,
    },
    {
        "id": 7,
        "title": "Gym motivation edit",
        "tags": ["fitness", "lifestyle"],
        "tone": "motivational",
        "intensity": 2,
    },
    {
        "id": 8,
        "title": "Political outrage clip",
        "tags": ["politics", "conflict", "news"],
        "tone": "outrage",
        "intensity": 5,
    },
    {
        "id": 9,
        "title": "Why Boston keeps redesigning its streets",
        "tags": [
            "urbanism",
            "transportation",
            "policy",
        ],
        "tone": "analytical",
        "intensity": 2,
    },
    {
        "id": 10,
        "title": "The weird psychology of infinite scroll",
        "tags": [
            "psychology",
            "internet",
            "attention",
        ],
        "tone": "reflective",
        "intensity": 3,
    },
    {
        "id": 11,
        "title": "A week of outfits I actually wore",
        "tags": [
            "fashion",
            "lifestyle",
        ],
        "tone": "casual",
        "intensity": 1,
    },
    {
        "id": 12,
        "title": "Making a tiny ceramic lamp from scratch",
        "tags": [
            "art",
            "pottery",
            "education",
        ],
        "tone": "creative",
        "intensity": 2,
    },
    {
        "id": 13,
        "title": "Why your feed starts feeling like you",
        "tags": [
            "technology",
            "internet",
            "psychology",
        ],
        "tone": "reflective",
        "intensity": 3,
    },
    {
        "id": 14,
        "title": "The case against car-dependent cities",
        "tags": [
            "urbanism",
            "transportation",
            "politics",
        ],
        "tone": "argumentative",
        "intensity": 4,
    },
    {
        "id": 15,
        "title": "Slow morning routine before class",
        "tags": [
            "lifestyle",
            "attention",
        ],
        "tone": "calm",
        "intensity": 1,
    },
    {
        "id": 16,
        "title": "Why outrage performs so well online",
        "tags": [
            "politics",
            "conflict",
            "internet",
            "attention",
        ],
        "tone": "analytical",
        "intensity": 4,
    },
]

ACTION_WEIGHTS = {
    "like": 2,
    "skip": -0.5,
    "not_interested": -2,
}


class Interaction(BaseModel):
    post_id: int
    action: str


class ExplainRequest(BaseModel):
    profile: Dict[str, float]
    recent_interactions: List[Dict[str, Any]]


class InteractionDetail(BaseModel):
    post_id: int
    action: str
    title: str


class InteractionRequest(BaseModel):
    interactions: List[InteractionDetail]


def build_profile(interactions: List[Interaction]) -> Dict[str, float]:
    profile: Dict[str, float] = {}

    for interaction in interactions:
        post = next((p for p in POSTS if p["id"] == interaction.post_id), None)
        if not post:
            continue

        weight = ACTION_WEIGHTS.get(interaction.action, 0)
        for tag in post["tags"]:
            profile[tag] = profile.get(tag, 0) + weight

    return profile


def build_reason(post: Dict[str, Any], profile: Dict[str, float], score: float) -> Dict[str, Any]:
    tag_scores = {tag: profile.get(tag, 0) for tag in post["tags"]}
    positive_tags = [tag for tag, value in tag_scores.items() if value > 0]
    negative_tags = [tag for tag, value in tag_scores.items() if value < 0]

    if not profile:
        summary = "Cold start: no preferences yet, so this is the default first post."
    elif score > 0:
        summary = (
            f"Recommended because you seem interested in {', '.join(positive_tags)} "
            f"(combined score: {score})."
        )
    elif score < 0:
        summary = (
            f"Shown despite negative signals for {', '.join(negative_tags)} "
            f"because it was the best remaining option (score: {score})."
        )
    else:
        summary = "No strong tag match yet; this post was chosen from the remaining pool."

    return {
        "summary": summary,
        "score": score,
        "matched_tags": post["tags"],
        "tag_scores": tag_scores,
    }


def fallback_explanation(req: ExplainRequest) -> str:
    if not req.profile:
        return (
            "You have not interacted with any posts yet, so the feed is still in cold-start mode. "
            "The algorithm has not formed a profile. Like a few posts you enjoy, skip ones you do not, "
            "and use Not interested for topics you want to avoid. "
            "This is a simplified simulation, not TikTok's actual algorithm."
        )

    top_tags = sorted(req.profile.items(), key=lambda item: item[1], reverse=True)[:3]
    top_summary = ", ".join(f"{tag} ({score:+.1f})" for tag, score in top_tags)

    recent = req.recent_interactions[-3:]
    if recent:
        behavior = "; ".join(
            f'{"liked" if i.get("action") == "like" else i.get("action", "interacted with").replace("_", " ")} '
            f'"{i.get("title", "a post")}"'
            for i in recent
        )
    else:
        behavior = "your recent clicks"

    return (
        f"The algorithm currently weights {top_summary} highest in your visible profile. "
        f"That profile was shaped by {behavior}. "
        "If you keep reinforcing the same tags, the feed will narrow toward similar content. "
        "Try liking posts from different tags to rebalance what you see. "
        "This is a simplified simulation, not TikTok's actual algorithm."
    )


@app.get("/posts")
def get_posts():
    return POSTS


@app.post("/recommend")
def recommend(interactions: List[Interaction]):
    profile = build_profile(interactions)
    scored_posts = []
    seen_ids = {i.post_id for i in interactions}

    for post in POSTS:
        if post["id"] in seen_ids:
            continue

        score = sum(profile.get(tag, 0) for tag in post["tags"])
        scored_posts.append(
            {
                "post": post,
                "score": score,
                "reason": build_reason(post, profile, score),
            }
        )

    scored_posts.sort(key=lambda item: item["score"], reverse=True)

    if not scored_posts:
        return {
            "next_post": None,
            "profile": profile,
            "reason": {
                "summary": "No more posts available.",
                "score": 0,
                "matched_tags": [],
                "tag_scores": {},
            },
        }

    best = scored_posts[0]
    return {
        "next_post": best["post"],
        "profile": profile,
        "reason": best["reason"],
    }


@app.post("/explain")
def explain(req: ExplainRequest):
    if not client:
        return {"explanation": fallback_explanation(req)}

    prompt = f"""
You are explaining a transparent recommendation algorithm to a user.

The app is called Algorithm Mirror. It shows users how their likes, skips, and not-interested clicks change their recommendation profile.

Current inferred user profile:
{req.profile}

Recent interactions:
{req.recent_interactions}

Write a concise explanation in 4-6 sentences:
1. What the algorithm currently thinks the user is interested in.
2. Which behaviors shaped that conclusion.
3. Whether the feed may be narrowing.
4. One suggestion for how the user could rebalance the feed.
Be honest that this is a simplified simulation, not TikTok's actual algorithm.
"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        return {"explanation": message.content[0].text}
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Claude request failed: {exc}",
        ) from exc


@app.post("/audit")
def audit_feed(req: InteractionRequest):

    interactions = [
        interaction.model_dump()
        for interaction in req.interactions
    ]

    metrics = build_feed_metrics(
        interactions,
        POSTS,
    )

    recent_interactions = interactions[-10:]

    try:
        ai_audit = generate_feed_audit(
            metrics=metrics,
            recent_interactions=recent_interactions,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Feed audit failed: {exc}",
        ) from exc

    return {
        "metrics": metrics,
        "ai_analysis": ai_audit.model_dump(),
    }

@app.post("/trace")
def trace_recommendation(
    req: InteractionRequest,
):
    interactions = [
        interaction.model_dump()
        for interaction in req.interactions
    ]

    return build_recommendation_trace(
        interactions=interactions,
        posts=POSTS,
    )
from pathlib import Path
from typing import List, Literal

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).resolve().parent / ".env")

class FeedAudit(BaseModel):
    summary: str = Field(
        description=(
            "A concise explanation of how the user's "
            "recommendation profile developed."
        )
    )

    dominant_patterns: List[str] = Field(
        description=(
            "Two or three important behavioral or "
            "recommendation patterns visible in the session."
        )
    )

    narrowing_level: Literal[
        "low",
        "moderate",
        "high",
    ] = Field(
        description=(
            "How concentrated the feed appears based strictly "
            "on the supplied diversity metrics."
        )
    )

    user_reflection: str = Field(
        description=(
            "One thoughtful question that encourages the user "
            "to reflect on whether the feed reflects or reinforces "
            "their preferences."
        )
    )

    suggested_action: str = Field(
        description=(
            "One concrete action the user could take to change "
            "or diversify the simulated feed."
        )
    )


model = ChatAnthropic(
    model="claude-sonnet-5"
)


structured_model = model.with_structured_output(
    FeedAudit,
    method="json_schema",
)


def generate_feed_audit(
    metrics: dict,
    recent_interactions: list,
) -> FeedAudit:

    prompt = f"""
You are the interpretation layer of Algorithm Mirror,
an educational recommendation-system transparency tool.

Algorithm Mirror is a SIMULATION.

You must never imply that:
- these are TikTok's actual recommendation signals,
- you know the user's true personality,
- you know the user's real beliefs,
- or the inferred profile is objectively correct.

The application's deterministic analytics system calculated:

{metrics}

The user's recent interactions were:

{recent_interactions}

Interpret these results for the user.

Important rules:

1. Treat the supplied metrics as authoritative.
2. Do not invent additional statistics.
3. Explain patterns rather than diagnosing the user.
4. Clearly distinguish between observed behavior and inferred preference.
5. The purpose is algorithmic literacy, not judgment.
6. Be concise.
"""

    return structured_model.invoke(prompt)
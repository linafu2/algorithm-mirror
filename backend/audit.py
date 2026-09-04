from collections import Counter
from math import log
from typing import Any, Dict, List


ACTION_WEIGHTS = {
    "like": 2.0,
    "skip": -0.5,
    "not_interested": -2.0,
}


def calculate_topic_distribution(
    interactions: List[Dict[str, Any]],
    posts: List[Dict[str, Any]],
) -> Dict[str, float]:
    """
    Calculates how much positive attention each topic has received.
    Deterministic, not decided by LLM.
    """

    post_lookup = {post["id"]: post for post in posts}

    scores: Counter[str] = Counter()

    for interaction in interactions:
        post = post_lookup.get(interaction["post_id"])

        if not post:
            continue

        action = interaction["action"]
        weight = ACTION_WEIGHTS.get(action, 0)

        # Diversity should primarily represent positive feed affinity.
        # Negative signals shouldn't create negative probabilities.
        if weight <= 0:
            continue

        for tag in post["tags"]:
            scores[tag] += weight

    total = sum(scores.values())

    if total == 0:
        return {}

    return {
        tag: score / total
        for tag, score in scores.items()
    }


def calculate_diversity_score(
    distribution: Dict[str, float],
) -> float:
    """
    Uses normalized Shannon entropy, where 
    0 is extremely concentrated "echo chamber", 
    100 is evenly distributed across observed interests "diverse".
    """

    if len(distribution) <= 1:
        return 0.0

    entropy = -sum(
        probability * log(probability)
        for probability in distribution.values()
        if probability > 0
    )

    max_entropy = log(len(distribution))

    normalized = entropy / max_entropy

    return round(normalized * 100, 1)


def build_feed_metrics(
    interactions: List[Dict[str, Any]],
    posts: List[Dict[str, Any]],
) -> Dict[str, Any]:

    distribution = calculate_topic_distribution(
        interactions,
        posts,
    )

    diversity_score = calculate_diversity_score(distribution)

    concentration_score = round(
        100 - diversity_score,
        1,
    )

    sorted_topics = sorted(
        distribution.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    dominant_topic = (
        sorted_topics[0][0]
        if sorted_topics
        else None
    )

    top_topics = [
        {
            "topic": topic,
            "share": round(share * 100, 1),
        }
        for topic, share in sorted_topics[:5]
    ]

    return {
        "diversity_score": diversity_score,
        "concentration_score": concentration_score,
        "dominant_topic": dominant_topic,
        "top_topics": top_topics,
        "interaction_count": len(interactions),
    }
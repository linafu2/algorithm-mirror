from typing import Any, Dict, List


ACTION_WEIGHTS = {
    "like": 2.0,
    "skip": -0.5,
    "not_interested": -2.0,
}


def build_profile(
    interactions: List[Dict[str, Any]],
    posts: List[Dict[str, Any]],
) -> Dict[str, float]:
    """
    Reconstruct the simulated user profile from interaction history.
    Each interaction changes score of every tag associated with post.
    """

    post_lookup = {
        post["id"]: post
        for post in posts
    }

    profile: Dict[str, float] = {}

    for interaction in interactions:
        post = post_lookup.get(
            interaction["post_id"]
        )

        if not post:
            continue

        action = interaction["action"]

        weight = ACTION_WEIGHTS.get(
            action,
            0.0,
        )

        for tag in post["tags"]:
            profile[tag] = (
                profile.get(tag, 0.0)
                + weight
            )

    return profile


def score_post(
    post: Dict[str, Any],
    profile: Dict[str, float],
) -> Dict[str, Any]:
    """
    Calculate the ranking score for one candidate post.
    The score is sum of user's current affinity scores for candidate's tags.
    """

    contributions = []

    total_score = 0.0

    for tag in post["tags"]:
        contribution = profile.get(
            tag,
            0.0,
        )

        total_score += contribution

        contributions.append({
            "tag": tag,
            "contribution": round(
                contribution,
                2,
            ),
        })

    return {
        "post_id": post["id"],
        "title": post["title"],
        "tags": post["tags"],
        "score": round(
            total_score,
            2,
        ),
        "contributions": contributions,
    }


def build_recommendation_trace(
    interactions: List[Dict[str, Any]],
    posts: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build complete deterministic explanation of recommendation process.

    Returns:
    - current simulated profile
    - every unseen candidate and its score
    - the selected recommendation
    - tag-level contributions for the winner
    """

    profile = build_profile(
        interactions,
        posts,
    )

    seen_post_ids = {
        interaction["post_id"]
        for interaction in interactions
    }

    unseen_posts = [
        post
        for post in posts
        if post["id"] not in seen_post_ids
    ]

    candidates = [
        score_post(
            post,
            profile,
        )
        for post in unseen_posts
    ]

    candidates.sort(
        key=lambda candidate: (
            candidate["score"],
            -candidate["post_id"],
        ),
        reverse=True,
    )

    selected = (
        candidates[0]
        if candidates
        else None
    )

    return {
        "profile": profile,
        "selected": selected,
        "candidates": candidates,
    }
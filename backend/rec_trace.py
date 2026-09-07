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

def build_interaction_impact(
    interactions: List[Dict[str, Any]],
    posts: List[Dict[str, Any]],
) -> Dict[str, Any] | None:
    """
    Explain how the user's most recent interaction changed:

    1. the simulated user profile
    2. candidate ranking scores
    3. candidate ranking positions

    Comparison uses same future candidate pool before and after 
    interaction so score/rank changes are directly comparable.
    """

    if not interactions:
        return None

    last_interaction = interactions[-1]
    previous_interactions = interactions[:-1]

    post_lookup = {
        post["id"]: post
        for post in posts
    }

    interacted_post = post_lookup.get(
        last_interaction["post_id"]
    )

    if not interacted_post:
        return None

    before_profile = build_profile(
        previous_interactions,
        posts,
    )

    after_profile = build_profile(
        interactions,
        posts,
    )

    profile_changes = []

    for tag in interacted_post["tags"]:
        before_value = before_profile.get(
            tag,
            0.0,
        )

        after_value = after_profile.get(
            tag,
            0.0,
        )

        profile_changes.append({
            "tag": tag,
            "before": round(
                before_value,
                2,
            ),
            "after": round(
                after_value,
                2,
            ),
            "delta": round(
                after_value - before_value,
                2,
            ),
        })

    # Use unseen posts after most recent nteraction for consistent 
    # future candidate pool for before/after comparison
    seen_post_ids = {
        interaction["post_id"]
        for interaction in interactions
    }

    future_posts = [
        post
        for post in posts
        if post["id"] not in seen_post_ids
    ]

    before_candidates = [
        score_post(
            post,
            before_profile,
        )
        for post in future_posts
    ]

    after_candidates = [
        score_post(
            post,
            after_profile,
        )
        for post in future_posts
    ]

    before_candidates.sort(
        key=lambda candidate: (
            candidate["score"],
            -candidate["post_id"],
        ),
        reverse=True,
    )

    after_candidates.sort(
        key=lambda candidate: (
            candidate["score"],
            -candidate["post_id"],
        ),
        reverse=True,
    )

    before_rank_lookup = {
        candidate["post_id"]: index + 1
        for index, candidate
        in enumerate(before_candidates)
    }

    after_rank_lookup = {
        candidate["post_id"]: index + 1
        for index, candidate
        in enumerate(after_candidates)
    }

    before_score_lookup = {
        candidate["post_id"]: candidate["score"]
        for candidate in before_candidates
    }

    candidate_changes = []

    for candidate in after_candidates:
        post_id = candidate["post_id"]

        before_score = before_score_lookup.get(
            post_id,
            0.0,
        )

        after_score = candidate["score"]

        before_rank = before_rank_lookup.get(
            post_id
        )

        after_rank = after_rank_lookup.get(
            post_id
        )

        candidate_changes.append({
            "post_id": post_id,
            "title": candidate["title"],
            "before_score": before_score,
            "after_score": after_score,
            "score_delta": round(
                after_score - before_score,
                2,
            ),
            "before_rank": before_rank,
            "after_rank": after_rank,
            "rank_change": (
                before_rank - after_rank
                if before_rank is not None
                and after_rank is not None
                else 0
            ),
        })

    candidate_changes.sort(
        key=lambda candidate: (
            abs(candidate["score_delta"]),
            abs(candidate["rank_change"]),
        ),
        reverse=True,
    )

    return {
        "interaction": {
            "post_id": interacted_post["id"],
            "title": interacted_post["title"],
            "action": last_interaction["action"],
        },
        "profile_changes": profile_changes,
        "candidate_changes": candidate_changes,
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

    impact = build_interaction_impact(
        interactions,
        posts,
    )

    return {
        "profile": profile,
        "selected": selected,
        "candidates": candidates,
        "impact": impact,
    }
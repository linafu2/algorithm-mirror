from rec_trace import (
    build_profile,
    score_post,
    build_interaction_impact,
    build_recommendation_trace,
)


TEST_POSTS = [
    {
        "id": 1,
        "title": "Train video",
        "tags": [
            "urbanism",
            "transportation",
        ],
    },
    {
        "id": 2,
        "title": "Algorithm video",
        "tags": [
            "technology",
            "internet",
        ],
    },
    {
        "id": 3,
        "title": "Another tech video",
        "tags": [
            "technology",
        ],
    },
]


def test_like_increases_profile_tags():
    interactions = [
        {
            "post_id": 2,
            "action": "like",
            "title": "Algorithm video",
        }
    ]

    profile = build_profile(
        interactions,
        TEST_POSTS,
    )

    assert profile["technology"] == 2.0
    assert profile["internet"] == 2.0


def test_post_score_is_sum_of_tag_affinities():
    profile = {
        "technology": 3.0,
        "internet": 2.0,
    }

    post = {
        "id": 2,
        "title": "Algorithm video",
        "tags": [
            "technology",
            "internet",
        ],
    }

    result = score_post(
        post,
        profile,
    )

    assert result["score"] == 5.0


def test_highest_scoring_post_is_selected():
    interactions = [
        {
            "post_id": 2,
            "action": "like",
            "title": "Algorithm video",
        }
    ]

    result = build_recommendation_trace(
        interactions,
        TEST_POSTS,
    )

    assert result["selected"]["post_id"] == 3

def test_not_interested_reduces_candidate_score():

    profile = {
        "technology": -2.0,
        "internet": -2.0,
    }

    post = {
        "id": 2,
        "title": "Algorithm video",
        "tags": [
            "technology",
            "internet",
        ],
    }

    result = score_post(
        post,
        profile,
    )

    assert result["score"] == -4.0

def test_interaction_impact_tracks_profile_change():
    posts = [
        {
            "id": 1,
            "title": "Fashion post",
            "tags": [
                "fashion",
                "lifestyle",
            ],
        },
        {
            "id": 2,
            "title": "Fitness post",
            "tags": [
                "fitness",
                "lifestyle",
            ],
        },
    ]

    interactions = [
        {
            "post_id": 1,
            "action": "like",
            "title": "Fashion post",
        }
    ]

    impact = build_interaction_impact(
        interactions,
        posts,
    )

    assert impact is not None

    changes = {
        change["tag"]: change
        for change
        in impact["profile_changes"]
    }

    assert changes["fashion"]["before"] == 0
    assert changes["fashion"]["after"] == 2
    assert changes["fashion"]["delta"] == 2

    assert changes["lifestyle"]["before"] == 0
    assert changes["lifestyle"]["after"] == 2
    assert changes["lifestyle"]["delta"] == 2


def test_like_can_raise_future_candidate_score():
    posts = [
        {
            "id": 1,
            "title": "Fashion post",
            "tags": [
                "fashion",
                "lifestyle",
            ],
        },
        {
            "id": 2,
            "title": "Fitness post",
            "tags": [
                "fitness",
                "lifestyle",
            ],
        },
    ]

    interactions = [
        {
            "post_id": 1,
            "action": "like",
            "title": "Fashion post",
        }
    ]

    impact = build_interaction_impact(
        interactions,
        posts,
    )

    fitness_change = next(
        candidate
        for candidate
        in impact["candidate_changes"]
        if candidate["post_id"] == 2
    )

    assert fitness_change["before_score"] == 0
    assert fitness_change["after_score"] == 2
    assert fitness_change["score_delta"] == 2
from trace import (
    build_profile,
    score_post,
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
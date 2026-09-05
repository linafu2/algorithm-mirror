from audit import calculate_diversity_score

def test_single_topic_has_zero_diversity():
    distribution = {
        "urbanism": 1.0,
    }

    assert calculate_diversity_score(
        distribution
    ) == 0.0


def test_equal_topics_have_max_diversity():
    distribution = {
        "urbanism": 0.25,
        "fashion": 0.25,
        "music": 0.25,
        "politics": 0.25,
    }

    assert calculate_diversity_score(
        distribution
    ) == 100.0


def test_imbalanced_topics_have_lower_diversity():
    distribution = {
        "urbanism": 0.9,
        "fashion": 0.05,
        "music": 0.05,
    }

    score = calculate_diversity_score(
        distribution
    )

    assert score < 60
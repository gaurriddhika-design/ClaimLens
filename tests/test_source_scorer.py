
import pytest

from services.source_scorer import SourceScorer


@pytest.fixture
def scorer():
    return SourceScorer()


# ---------------- Basic scoring tests ----------------


def test_empty_source_has_zero_score(scorer):
    result = scorer.score_source({})

    assert result["quality_score"] == 0
    assert result["indicators"] == []
    assert result["text_length"] == 0


def test_https_url_receives_expected_points(scorer):
    result = scorer.score_source({
        "url": "https://example.com"
    })

    assert result["quality_score"] == 20

    indicator_names = [
        indicator["name"] for indicator in result["indicators"]
    ]

    assert "valid_web_address" in indicator_names
    assert "https" in indicator_names


def test_http_url_does_not_receive_https_points(scorer):
    result = scorer.score_source({
        "url": "http://example.com"
    })

    assert result["quality_score"] == 10

    indicator_names = [
        indicator["name"] for indicator in result["indicators"]
    ]

    assert "valid_web_address" in indicator_names
    assert "https" not in indicator_names


def test_official_domain_pattern_receives_points(scorer):
    result = scorer.score_source({
        "url": "https://example.gov.in"
    })

    assert result["quality_score"] == 45

    indicator_names = [
        indicator["name"] for indicator in result["indicators"]
    ]

    assert "official_domain_pattern" in indicator_names


@pytest.mark.parametrize(
    "url",
    [
        "https://example.gov",
        "https://example.nic.in",
        "https://university.edu",
        "https://university.edu.in",
    ],
)
def test_supported_official_domain_suffixes(scorer, url):
    result = scorer.score_source({"url": url})

    indicator_names = [
        indicator["name"] for indicator in result["indicators"]
    ]

    assert "official_domain_pattern" in indicator_names


def test_title_and_publication_date_add_points(scorer):
    result = scorer.score_source({
        "url": "http://example.com",
        "title": "Research Report",
        "published_date": "2026-10-20",
    })

    # URL: 10, title: 10, publication date: 15
    assert result["quality_score"] == 35

    indicator_names = [
        indicator["name"] for indicator in result["indicators"]
    ]

    assert "page_title" in indicator_names
    assert "publication_date" in indicator_names


# ---------------- Text-length scoring tests ----------------


def test_short_text_receives_no_content_points(scorer):
    result = scorer.score_source({
        "text": "a" * 149
    })

    assert result["quality_score"] == 0
    assert result["text_length"] == 149


def test_text_of_150_characters_receives_10_points(scorer):
    result = scorer.score_source({
        "text": "a" * 150
    })

    assert result["quality_score"] == 10
    assert result["text_length"] == 150


def test_text_of_499_characters_receives_10_points(scorer):
    result = scorer.score_source({
        "text": "a" * 499
    })

    assert result["quality_score"] == 10


def test_text_of_500_characters_receives_20_points(scorer):
    result = scorer.score_source({
        "text": "a" * 500
    })

    assert result["quality_score"] == 20


def test_snippet_is_used_when_text_is_missing(scorer):
    result = scorer.score_source({
        "snippet": "a" * 150
    })

    assert result["text_length"] == 150
    assert result["quality_score"] == 10


def test_text_is_preferred_over_snippet(scorer):
    result = scorer.score_source({
        "text": "short text",
        "snippet": "a" * 500,
    })

    assert result["text_length"] == len("short text")
    assert result["quality_score"] == 0


# ---------------- Output structure tests ----------------


def test_result_contains_expected_fields(scorer):
    result = scorer.score_source({
        "url": "https://example.com",
        "title": "Example",
        "text": "Article text",
    })

    assert set(result.keys()) == {
        "title",
        "url",
        "quality_score",
        "indicators",
        "text_length",
        "method",
        "warning",
    }

    assert result["method"] == "rule_based_source_assessment"
    assert isinstance(result["indicators"], list)
    assert isinstance(result["warning"], str)


def test_whitespace_is_not_counted_as_content(scorer):
    result = scorer.score_source({
        "text": "   \n\t   "
    })

    assert result["text_length"] == 0
    assert result["quality_score"] == 0


def test_score_does_not_exceed_100(scorer):
    result = scorer.score_source({
        "url": "https://research.gov.in",
        "title": "Official Research Report",
        "published_date": "2026-10-20",
        "text": "a" * 600,
    })

    assert result["quality_score"] == 90


# ---------------- Input validation tests ----------------


@pytest.mark.parametrize(
    "source",
    [
        None,
        [],
        "not a dictionary",
        123,
    ],
)
def test_rejects_non_dictionary_source(scorer, source):
    with pytest.raises(TypeError, match="dictionary"):
        scorer.score_source(source)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("url", 123, "URL must be a string"),
        ("title", 123, "title must be a string"),
        ("text", 123, "text must be a string"),
    ],
)
def test_rejects_invalid_field_types(
    scorer, field, value, message
):
    with pytest.raises(TypeError, match=message):
        scorer.score_source({field: value})


def test_rejects_non_list_sources(scorer):
    with pytest.raises(TypeError, match="list"):
        scorer.score_sources("not a list")


# ---------------- Multiple-source sorting tests ----------------


def test_score_sources_sorts_highest_score_first(scorer):
    sources = [
        {
            "url": "http://example.com",
            "title": "Short report",
        },
        {
            "url": "https://example.com",
            "title": "Detailed report",
            "published_date": "2026-10-20",
            "text": "a" * 500,
        },
        {},
    ]

    results = scorer.score_sources(sources)

    scores = [item["quality_score"] for item in results]

    assert scores == sorted(scores, reverse=True)


def test_score_sources_preserves_all_sources(scorer):
    sources = [
        {"url": "https://one.example"},
        {"url": "https://two.example"},
        {"url": "https://three.example"},
    ]

    results = scorer.score_sources(sources)

    assert len(results) == len(sources)


def test_score_sources_handles_empty_list(scorer):
    assert scorer.score_sources([]) == []


def test_score_sources_rejects_invalid_source_inside_list(scorer):
    sources = [
        {"url": "https://example.com"},
        None,
    ]

    with pytest.raises(TypeError):
        scorer.score_sources(sources)

import pytest
from textminer.cleaner import remove_stopwords, extract_keywords

def test_remove_stopwords_english():
    text = "Who is your favorite movie star? I like the main character of Spider-Man."
    result = remove_stopwords(text, lang='en')
    assert isinstance(result, str)
    lowered = result.lower()
    assert "is" not in lowered
    assert "the" not in lowered
    assert "your" not in lowered
    assert "spider-man" in lowered or "spider" in lowered


def test_remove_stopwords_invalid_lang():
    text = "이 문장은 한국어입니다."
    result = remove_stopwords(text, lang='ko')
    assert result == "[지원되지 않는 언어]"

def test_extract_keywords_basic():
    text = "You’re misunderstanding right now. Hear me out."
    keywords = extract_keywords(text, top_n=3)
    assert isinstance(keywords, list)
    assert len(keywords) == 3
    for kw in keywords:
        assert isinstance(kw, str)
        assert len(kw) > 0

def test_extract_keywords_empty():
    keywords = extract_keywords("", top_n=3)
    assert keywords == []

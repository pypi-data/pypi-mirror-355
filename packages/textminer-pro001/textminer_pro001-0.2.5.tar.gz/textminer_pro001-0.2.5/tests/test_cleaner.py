from textminer.cleaner import remove_stopwords, extract_keywords

def test_remove_stopwords_basic():
    text = "This is a simple test sentence with some stopwords."
    result = remove_stopwords(text)
    assert "is" not in result.lower()
    assert "a" not in result.lower()
    assert "stopwords" in result.lower()

def test_remove_stopwords_only_stopwords():
    text = "The is an a at by"
    result = remove_stopwords(text)
    assert result.strip() == ""

def test_extract_keywords_basic():
    text = "Artificial intelligence and machine learning are core technologies of the future."
    keywords = extract_keywords(text, top_n=3)
    assert isinstance(keywords, list)
    assert len(keywords) == 3
    assert any(word in keywords for word in ["artificial", "intelligence", "learning"])

def test_extract_keywords_empty():
    assert extract_keywords("") == []

def test_extract_keywords_stopwords_only():
    text = "the and a is in it"
    assert extract_keywords(text) == []

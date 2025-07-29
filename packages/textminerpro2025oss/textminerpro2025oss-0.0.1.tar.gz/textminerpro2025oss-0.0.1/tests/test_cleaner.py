from textminer.cleaner import remove_stopwords

def test_remove_stopwords():
    text = "This is a sample sentence"
    result = remove_stopwords(text)
    assert "is" not in result and "a" not in result

from textminer.cleaner import remove_stopwords
from nltk.tokenize import word_tokenize

def test_remove_stopwords():
    text = "This is a sample sentence"
    result = remove_stopwords(text)
    tokens = word_tokenize(result)

    assert "is" not in tokens
    assert "a" not in tokens
    assert "sample" in tokens
    assert "sentence" in tokens

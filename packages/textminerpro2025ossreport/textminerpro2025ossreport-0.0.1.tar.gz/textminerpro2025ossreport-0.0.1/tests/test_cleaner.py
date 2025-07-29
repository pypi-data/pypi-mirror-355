from textminer.cleaner import remove_stopwords
from nltk.tokenize import word_tokenize

def test_remove_stopwords():
    text = "This is a sample sentence"
    result = remove_stopwords(text)
    tokens = word_tokenize(result)

    # 단어 목록 기준으로 비교해야 함 (부분 문자열이 아닌)
    assert "is" not in tokens
    assert "a" not in tokens
    assert "sample" in tokens
    assert "sentence" in tokens

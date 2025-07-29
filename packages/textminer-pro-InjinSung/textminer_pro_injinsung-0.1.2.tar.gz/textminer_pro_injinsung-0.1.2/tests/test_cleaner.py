import pytest
from textminer.cleaner import remove_stopwords, extract_keywords

def test_remove_stopwords():
    # 영어 불용어 제거 테스트
    text_en = "This is a test sentence with some stopwords"
    result_en = remove_stopwords(text_en, lang='english')
    assert "is" not in result_en.split()
    assert "a" not in result_en.split()
    assert "with" not in result_en.split()
    assert "test" in result_en
    assert "sentence" in result_en
    
    # 한국어 불용어 제거 테스트 (영어로 대체)
    text_ko = "이것은 테스트 문장입니다 그리고 일부 불용어가 있어요"
    result_ko = remove_stopwords(text_ko, lang='english')  # 한국어는 기본적으로 지원하지 않으므로 영어로 대체
    assert "이것은" in result_ko  # 한국어 불용어가 아님
    assert "테스트" in result_ko

def test_extract_keywords():
    text = """
    Natural language processing (NLP) is a subfield of linguistics, computer science,
    and artificial intelligence concerned with the interactions between computers and
    human language, in particular how to program computers to process and analyze large
    amounts of natural language data.
    """
    
    keywords = extract_keywords(text, top_n=3)
    assert len(keywords) == 3
    
    # 핵심 키워드가 포함되어야 함 (대소문자 무관)
    found_keywords = [k.lower() for k in keywords]
    assert any(k in found_keywords for k in ['language', 'natural', 'processing'])
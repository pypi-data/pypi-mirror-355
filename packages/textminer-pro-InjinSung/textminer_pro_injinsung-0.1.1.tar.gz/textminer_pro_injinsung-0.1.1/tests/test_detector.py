import pytest
from textminer.detector import detect_language

def test_detect_language():
    # 영어 텍스트 감지
    text_en = "This is a sample text in English language."
    assert detect_language(text_en) == 'en'
    
    # 한국어 텍스트 감지
    text_ko = "이것은 한국어로 작성된 샘플 텍스트입니다."
    assert detect_language(text_ko) == 'ko'
    
    # 일본어 텍스트 감지
    text_ja = "これは日本語のサンプルテキストです。"
    assert detect_language(text_ja) == 'ja'
    
    # 중국어 텍스트 감지
    text_zh = "这是一个中文样本文本。"
    assert detect_language(text_zh) == 'zh-cn'
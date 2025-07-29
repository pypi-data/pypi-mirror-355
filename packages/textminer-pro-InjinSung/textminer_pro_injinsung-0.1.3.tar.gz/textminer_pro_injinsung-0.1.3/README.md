# TextMiner Pro

[![Python Package](https://github.com/jagari/textminer-pro/actions/workflows/pypi.yml/badge.svg)](https://github.com/jagari/textminer-pro/actions/workflows/pypi.yml)
[![PyPI version](https://badge.fury.io/py/textminer-pro-InjinSung.svg)](https://badge.fury.io/py/textminer-pro-InjinSung)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

`textminer-pro`는 파이썬 기반의 고급 텍스트 분석 도구입니다.  
불용어 제거, 핵심 키워드 추출, 텍스트 요약, 언어 감지 기능을 제공합니다.

---

## 🧩 설치 방법

```bash
pip install textminer-pro-InjinSung
```

## 📌 주요 기능

### 불용어 제거 (Stopwords Removal)
```python
from textminer import remove_stopwords

text = "This is a sample text with some stopwords"
clean_text = remove_stopwords(text)
print(clean_text)  # "This sample text stopwords"
```

### 키워드 추출 (Keyword Extraction)
```python
from textminer import extract_keywords

text = "자연어 처리는 컴퓨터가 인간의 언어를 이해하고 처리하는 기술입니다."
keywords = extract_keywords(text, top_n=3)
print(keywords)  # ['자연어', '처리', '기술']
```

### 텍스트 요약 (Text Summarization)
```python
from textminer import summarize

long_text = """
자연어 처리(NLP)는 언어학, 컴퓨터 과학, 인공지능의 하위 분야로, 
컴퓨터와 인간 언어 간의 상호작용에 관한 분야입니다. 특히 컴퓨터가 
대량의 자연어 데이터를 처리하고 분석하도록 프로그래밍하는 방법에 관한 
연구입니다. 자연어 처리의 과제로는 언어 이해, 생성, 번역 등이 있습니다.
"""
summary = summarize(long_text, ratio=0.3)
print(summary)
```

### 언어 감지 (Language Detection)
```python
from textminer import detect_language

text_en = "This is English text."
text_ko = "이것은 한국어 텍스트입니다."
print(detect_language(text_en))  # 'en'
print(detect_language(text_ko))  # 'ko'
```

## 🔧 시스템 요구사항

- Python 3.7 이상
- 종속성: nltk, scikit-learn, langdetect

## 📜 라이센스

MIT 라이센스를 따릅니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🤝 기여하기

기여는 언제든지 환영합니다! 다음과 같은 방법으로 기여할 수 있습니다:

1. 이슈 등록하기
2. 풀 리퀘스트 제출하기
3. 기능 개선 제안하기
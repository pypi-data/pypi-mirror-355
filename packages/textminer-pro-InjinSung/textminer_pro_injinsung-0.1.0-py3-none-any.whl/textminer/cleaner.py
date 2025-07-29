import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer

# 테스트를 위해 다운로드 확실히 처리
nltk.download('stopwords', quiet=True)
nltk.download('punkt', quiet=True)

def remove_stopwords(text: str, lang='english') -> str:
    """
    불용어를 제거하는 함수
    
    Args:
        text (str): 원본 텍스트
        lang (str): 언어 코드 (기본값: 'english')
        
    Returns:
        str: 불용어가 제거된 텍스트
    """
    try:
        stops = set(stopwords.words(lang))
        words = text.split()
        return ' '.join([w for w in words if w.lower() not in stops])
    except LookupError:
        # 해당 언어의 불용어 데이터가 없는 경우
        return text

def extract_keywords(text: str, top_n=5) -> list:
    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform([text])
    scores = zip(vectorizer.get_feature_names_out(), X.toarray()[0])
    sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_scores[:top_n]]
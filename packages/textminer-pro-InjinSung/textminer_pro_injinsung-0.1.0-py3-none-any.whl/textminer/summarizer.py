import nltk
from nltk.tokenize import sent_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer

# 처음에 다운로드 한 번 필요
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

def summarize(text: str, ratio=0.2) -> str:
    """
    TF-IDF 기반 텍스트 요약 함수
    
    Args:
        text (str): 요약할 원본 텍스트
        ratio (float): 원본 대비 요약 비율 (0.0~1.0)
        
    Returns:
        str: 요약된 텍스트
    """
    # 문장 토큰화
    sentences = sent_tokenize(text)
    
    # 텍스트가 너무 짧은 경우 원본 반환
    if len(sentences) <= 3:
        return text
    
    # 요약 문장 수 계산
    num_sentences = max(1, int(len(sentences) * ratio))
    
    # TF-IDF 벡터화
    vectorizer = TfidfVectorizer(stop_words='english')
    vectors = vectorizer.fit_transform(sentences)
    
    # 문장별 중요도 점수 계산
    scores = [(i, sum(vectors[i].toarray()[0])) for i in range(len(sentences))]
    scores = sorted(scores, key=lambda x: x[1], reverse=True)
    
    # 상위 문장 추출 (원래 순서 유지)
    top_indices = sorted([i for i, _ in scores[:num_sentences]])
    summary = " ".join([sentences[i] for i in top_indices])
    
    return summary
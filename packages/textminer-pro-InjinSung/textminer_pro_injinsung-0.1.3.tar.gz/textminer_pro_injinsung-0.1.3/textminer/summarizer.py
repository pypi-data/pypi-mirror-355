import re
from sklearn.feature_extraction.text import TfidfVectorizer

# 간단한 문장 분리 함수 구현 (NLTK 의존성 제거)
def simple_sentence_tokenize(text):
    # 마침표, 물음표, 느낌표 뒤에 공백이 오면 문장 경계로 간주
    return re.split(r'(?<=[.!?])\s+', text)

def summarize(text: str, ratio=0.2) -> str:
    """
    TF-IDF 기반 텍스트 요약 함수
    
    Args:
        text (str): 요약할 원본 텍스트
        ratio (float): 원본 대비 요약 비율 (0.0~1.0)
        
    Returns:
        str: 요약된 텍스트
    """
    # 문장 토큰화 (단순화된 방법)
    sentences = simple_sentence_tokenize(text)
    
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
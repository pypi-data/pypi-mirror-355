import pytest
from textminer.summarizer import summarize

def test_summarize():
    text = """
    자연어 처리(NLP)는 언어학, 컴퓨터 과학, 인공지능의 하위 분야로, 
    컴퓨터와 인간 언어 간의 상호작용에 관한 분야입니다. 특히 컴퓨터가 
    대량의 자연어 데이터를 처리하고 분석하도록 프로그래밍하는 방법에 관한 
    연구입니다. 자연어 처리의 과제로는 언어 이해, 생성, 번역 등이 있습니다. 
    현대의 접근 방식은 딥러닝에 크게 의존하고 있습니다. 자연어 처리 기술은 
    음성 인식, 문서 분류, 기계 번역, 스팸 필터링, 가상 비서 등 다양한 분야에서 
    응용됩니다.
    """
    
    # 요약 길이 테스트
    summary = summarize(text, ratio=0.3)
    assert len(summary) < len(text)
    assert len(summary) > 0
    
    # 짧은 텍스트 처리 테스트
    short_text = "이것은 짧은 텍스트입니다."
    short_summary = summarize(short_text)
    assert short_summary == short_text  # 너무 짧은 경우 원본 반환

def test_summarize_with_different_ratios():
    text = """
    Machine learning (ML) is a field of inquiry devoted to understanding and building 
    methods that 'learn', that is, methods that leverage data to improve performance 
    on some set of tasks. It is seen as a part of artificial intelligence. Machine 
    learning algorithms build a model based on sample data, known as training data, 
    in order to make predictions or decisions without being explicitly programmed to 
    do so. Machine learning algorithms are used in a wide variety of applications, such 
    as in medicine, email filtering, speech recognition, agriculture, and computer vision, 
    where it is difficult or unfeasible to develop conventional algorithms to perform the 
    needed tasks. A subset of machine learning is closely related to computational statistics, 
    which focuses on making predictions using computers, but not all machine learning is 
    statistical learning.
    """
    
    # 다양한 비율 테스트
    summary_10 = summarize(text, ratio=0.1)
    summary_30 = summarize(text, ratio=0.3)
    summary_50 = summarize(text, ratio=0.5)
    
    # 비율에 따라 요약 길이가 달라지는지 확인
    assert len(summary_10) <= len(summary_30) <= len(summary_50)

from langdetect import detect
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

def detect_language(text: str) -> str:
    return detect(text)

def extract_keywords(text: str, top_n: int = 5) -> list[str]:
    # Vectorizer 설정
    vectorizer = TfidfVectorizer(stop_words='english')

    # 하나의 문서로 간주
    tfidf_matrix = vectorizer.fit_transform([text])

    # TF-IDF 점수 추출
    scores = tfidf_matrix.toarray()[0]
    feature_names = np.array(vectorizer.get_feature_names_out())

    # 상위 top_n 키워드 선택
    top_indices = scores.argsort()[::-1][:top_n]
    top_keywords = feature_names[top_indices]

    return top_keywords.tolist()
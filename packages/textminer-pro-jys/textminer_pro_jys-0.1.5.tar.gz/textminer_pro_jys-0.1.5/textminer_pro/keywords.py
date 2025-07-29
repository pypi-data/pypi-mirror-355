# textminer_pro/keywords.py
from __future__ import annotations
from typing import List
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

__all__ = ["extract_keywords"]

def extract_keywords(text: str, top_n: int = 5) -> List[str]:
    """
    한 문서에서 TF-IDF 상위 n개 토큰을 뽑는다.
    문서 집합이 1개이므로 TF는 term 빈도, IDF는 1이라 가정.

    Parameters
    ----------
    text : str
    top_n : int, default=5

    Returns
    -------
    list[str]
        상위 키워드 리스트(가중치 순).
    """

    vec = TfidfVectorizer(stop_words="english")
    tfidf = vec.fit_transform([text])
    scores = tfidf.toarray().ravel()
    top_idx = np.argsort(scores)[::-1][:top_n]
    return [vec.get_feature_names_out()[i] for i in top_idx]
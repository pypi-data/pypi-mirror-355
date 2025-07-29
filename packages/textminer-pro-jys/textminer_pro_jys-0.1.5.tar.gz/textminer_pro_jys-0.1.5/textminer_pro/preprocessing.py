# textminer_pro/preprocessing.py
from __future__ import annotations
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

__all__ = ["remove_stopwords"]


try:
    stopwords.words("english")
except LookupError:  
    nltk.download("punkt", quiet=True)
    nltk.download("stopwords", quiet=True)

def remove_stopwords(text: str, lang: str = "en") -> str:
    """
    간단한 토큰 기준 불용어 제거.

    Parameters
    ----------
    text : str
        원본 문장.
    lang : str, default="en"
        stopwords 리스트 언어 코드.

    Returns
    -------
    str
        불용어가 제거된 문장. 토큰 순서는 유지합니다.
    """
    lang = lang.lower()
    sw_set = set(stopwords.words(lang))
    tokens = word_tokenize(text)
    filtered = [tok for tok in tokens if tok.casefold() not in sw_set]
    return " ".join(filtered)
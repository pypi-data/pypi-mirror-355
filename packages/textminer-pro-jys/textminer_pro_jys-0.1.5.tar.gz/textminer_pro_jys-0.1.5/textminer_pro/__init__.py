
"""
textminer-pro
~~~~~~~~~~~~~
고급 텍스트 전처리·키워드 추출·요약·언어 감지 유틸리티
"""
from .preprocessing import remove_stopwords
from .keywords import extract_keywords
from .summary import summarize
from .language import detect_language

__all__ = [
    "remove_stopwords",
    "extract_keywords",
    "summarize",
    "detect_language",
]
__version__ = "0.1.0"
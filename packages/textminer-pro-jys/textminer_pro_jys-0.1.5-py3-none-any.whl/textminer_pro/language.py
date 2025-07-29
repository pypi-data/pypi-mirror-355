# textminer_pro/language.py
from __future__ import annotations
from langdetect import detect

__all__ = ["detect_language"]

def detect_language(text: str) -> str:
    """
    langdetect 감지 결과 ISO 639-1 코드 반환
    """
    return detect(text)
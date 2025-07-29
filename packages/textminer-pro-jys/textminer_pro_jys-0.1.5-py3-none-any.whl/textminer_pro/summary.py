# textminer_pro/summary.py
from __future__ import annotations
from typing import Literal
from math import ceil
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer

__all__ = ["summarize"]

def summarize(text: str, ratio: float = 0.2, lang: Literal["en", "ko"] = "en") -> str:
    """
    Sumy LexRank 기반 문서 요약.

    Parameters
    ----------
    text : str
    ratio : float, default=0.2
        요약문 분량 비율. (0,1]
    lang : {"en","ko"}, default="en"
        Tokenizer 언어 코드.

    Returns
    -------
    str
        결괏값 요약문.
    """
    parser = PlaintextParser.from_string(text, Tokenizer(lang))
    sent_total = len(parser.document.sentences)
    sent_n = max(1, ceil(sent_total * ratio))
    summarizer = LexRankSummarizer()
    summary_sents = summarizer(parser.document, sentences_count=sent_n)
    return " ".join(map(str, summary_sents))
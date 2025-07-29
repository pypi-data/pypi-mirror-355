# textminer-pro-jys

**고급 텍스트 분석 유틸리티**

- Stop-word 제거: `remove_stopwords`
- TF-IDF 키워드: `extract_keywords`
- Sumy 요약: `summarize`
- 언어 감지: `detect_language`

```python
from textminer_pro import summarize
print(summarize("고급 텍스트 분석 패키지 입니다.", ratio=0.5))
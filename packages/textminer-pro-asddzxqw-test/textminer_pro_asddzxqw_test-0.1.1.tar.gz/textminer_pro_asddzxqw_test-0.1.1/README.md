고급 텍스트 분석을 위한 Python 패키지입니다.

## 기능

- **불용어 제거** (`remove_stopwords`): NLTK를 사용한 불용어 제거
- **키워드 추출** (`extract_keywords`): TF-IDF 기반 핵심 키워드 추출 
- **텍스트 요약** (`summarize`): Gensim을 활용한 텍스트 요약
- **언어 감지** (`detect_language`): langdetect를 사용한 언어 감지

## 설치

```bash
pip install textminer-pro-asddzxqw
```

## 사용법
```python
from textminer import remove_stopwords, extract_keywords, summarize, detect_language
```
# 불용어 제거
text = "This is a sample text with some common stopwords"
clean_text = remove_stopwords(text)
print(clean_text)

# 키워드 추출 (상위 5개)
keywords = extract_keywords(text, top_n=5)
print(keywords)

# 텍스트 요약 (20% 길이로)
long_text = "여기에 긴 텍스트를 입력..."
summary = summarize(long_text, ratio=0.2)
print(summary)

# 언어 감지
language = detect_language(text)
print(f"감지된 언어: {language}")
라이선스
MIT License
저자
asddzxqw (kk020929@naver.com)

## 5단계: VSCode에서 테스트 실행

**VSCode 터미널에서 다음 명령어로 테스트:**
```bash
# 현재 위치 확인 (프로젝트 루트에 있어야 함)
pwd

# 패키지가 제대로 import되는지 테스트
python -c "from textminer import remove_stopwords; print('Import 성공!')"

# 단위 테스트 실행
python -m pytest tests/ -v

# 또는 unittest로 실행
python -m unittest discover tests/
```
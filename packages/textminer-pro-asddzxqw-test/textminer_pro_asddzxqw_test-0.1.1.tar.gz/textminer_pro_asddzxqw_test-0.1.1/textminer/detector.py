from langdetect import detect, DetectorFactory

# 일관된 결과를 위해 시드 설정
DetectorFactory.seed = 0

def detect_language(text: str) -> str:
    """텍스트의 언어를 감지합니다."""
    try:
        language = detect(text)
        return language
    except Exception as e:
        return f"Error: {str(e)}"
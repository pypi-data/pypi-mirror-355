"""
textminer-pro: 고급 텍스트 분석 패키지
"""

from .cleaner import remove_stopwords, extract_keywords
from .summarizer import summarize
from .detector import detect_language

__version__ = "0.1.0"
__author__ = "asddzxqw"
__email__ = "kk020929@naver.com"

__all__ = [
    "remove_stopwords",
    "extract_keywords", 
    "summarize",
    "detect_language"
]
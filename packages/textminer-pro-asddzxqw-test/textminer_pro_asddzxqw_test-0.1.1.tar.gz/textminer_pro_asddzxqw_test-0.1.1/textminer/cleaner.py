import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

def remove_stopwords(text: str, lang: str = 'english') -> str:
    """불용어를 제거합니다."""
    try:
        nltk.download('stopwords', quiet=True)
        nltk.download('punkt', quiet=True)
        
        stop_words = set(stopwords.words(lang))
        word_tokens = word_tokenize(text.lower())
        
        filtered_text = [word for word in word_tokens if word not in stop_words and word.isalpha()]
        return ' '.join(filtered_text)
    except Exception as e:
        return f"Error: {str(e)}"

def extract_keywords(text: str, top_n: int = 5) -> list:
    """TF-IDF를 사용하여 키워드를 추출합니다."""
    try:
        vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        tfidf_matrix = vectorizer.fit_transform([text])
        
        feature_names = vectorizer.get_feature_names_out()
        tfidf_scores = tfidf_matrix.toarray()[0]
        
        # 상위 키워드 추출
        top_indices = np.argsort(tfidf_scores)[::-1][:top_n]
        keywords = [(feature_names[i], tfidf_scores[i]) for i in top_indices]
        
        return keywords
    except Exception as e:
        return [f"Error: {str(e)}"]
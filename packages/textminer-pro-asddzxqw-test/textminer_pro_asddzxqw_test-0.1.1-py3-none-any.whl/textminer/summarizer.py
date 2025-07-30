import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from collections import Counter
import re

def summarize(text: str, ratio: float = 0.2) -> str:
    """텍스트를 요약합니다 (빈도 기반 간단 요약)."""
    try:
        # NLTK 데이터 다운로드
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        
        if len(text.split()) < 20:
            return "텍스트가 너무 짧습니다. 최소 20단어 이상이어야 합니다."
        
        # 문장 분리
        sentences = sent_tokenize(text)
        if len(sentences) <= 1:
            return text
        
        # 텍스트 정제 및 단어 토큰화
        clean_text = re.sub(r'[^a-zA-Z\s]', '', text.lower())
        words = word_tokenize(clean_text)
        
        # 불용어 제거
        try:
            stop_words = set(stopwords.words('english'))
        except:
            stop_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])
        
        # 유효한 단어만 필터링
        words = [word for word in words if word.isalpha() and word not in stop_words and len(word) > 2]
        
        # 단어 빈도 계산
        word_freq = Counter(words)
        
        # 문장별 점수 계산
        sentence_scores = {}
        for sentence in sentences:
            clean_sentence = re.sub(r'[^a-zA-Z\s]', '', sentence.lower())
            words_in_sentence = word_tokenize(clean_sentence)
            score = 0
            word_count = 0
            
            for word in words_in_sentence:
                if word in word_freq:
                    score += word_freq[word]
                    word_count += 1
            
            # 문장 길이로 정규화
            if word_count > 0:
                sentence_scores[sentence] = score / word_count
            else:
                sentence_scores[sentence] = 0
        
        # 상위 문장 선택
        num_sentences = max(1, int(len(sentences) * ratio))
        top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:num_sentences]
        
        # 원래 순서대로 정렬
        summary_sentences = []
        for sentence in sentences:
            if any(sentence == s[0] for s in top_sentences):
                summary_sentences.append(sentence)
        
        summary = ' '.join(summary_sentences)
        return summary if summary.strip() else "요약을 생성할 수 없습니다."
        
    except Exception as e:
        return f"Error: {str(e)}"
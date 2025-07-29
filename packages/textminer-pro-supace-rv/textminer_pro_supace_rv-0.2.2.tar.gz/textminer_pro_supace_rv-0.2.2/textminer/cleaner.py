import nltk
import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer


LANG_MAP = {
    'en': 'english',
    'ko': 'korean',
    'fr': 'french',
    'de': 'german',
    'es': 'spanish',
    'it': 'italian'
} 

def remove_stopwords(text: str, lang: str = 'en') -> str:
    # 다운로드 (최초 1회)
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('punkt')
        nltk.download('stopwords')

    # 언어명 변환
    lang = LANG_MAP.get(lang, lang)

    try:
        available_langs = stopwords.fileids()
        if lang not in available_langs:
            return "[지원되지 않는 언어]"

        stop_words = set(stopwords.words(lang))
        words = word_tokenize(text)

        # 영문 단어 + 하이픈 허용
        filtered = [
            w for w in words
            if w.lower() not in stop_words and re.fullmatch(r"[a-zA-Z\-]+", w)
        ]

        return ' '.join(filtered)
    except Exception as e:
        return f"[처리 오류: {str(e)}]"


def extract_keywords(text: str, lang: str = 'en', top_n: int = 5) -> list:
    if not text.strip():
        return []

    lang = LANG_MAP.get(lang, lang)
    stopword_list = None

    try:
        if lang in stopwords.fileids():
            stopword_list = stopwords.words(lang)
    except LookupError:
        pass

    try:
        vectorizer = TfidfVectorizer(stop_words=stopword_list)
        X = vectorizer.fit_transform([text])
        scores = zip(vectorizer.get_feature_names_out(), X.toarray()[0])
        sorted_keywords = sorted(scores, key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_keywords[:top_n]]
    except Exception:
        return []


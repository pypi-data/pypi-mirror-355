import nltk
import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer

nltk.download('punkt')
nltk.download('stopwords')

def remove_stopwords(text: str) -> str:
    stop_words = set(stopwords.words("english"))
    words = word_tokenize(text)
    filtered = [w for w in words if w.lower() not in stop_words and w.isalpha()]
    return " ".join(filtered)

def extract_keywords(text: str, top_n: int = 5) -> list:
    if not text.strip():
        return []

    stopword_list = stopwords.words("english")
    vectorizer = TfidfVectorizer(stop_words=stopword_list)

    try:
        X = vectorizer.fit_transform([text])
        if not vectorizer.get_feature_names_out().size:
            return []
        scores = zip(vectorizer.get_feature_names_out(), X.toarray()[0])
        sorted_keywords = sorted(scores, key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_keywords[:top_n]]
    except ValueError:
        
        return []
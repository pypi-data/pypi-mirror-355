import nltk
import os

NLTK_PATH = "/content/nltk_data"
nltk.data.path.append(NLTK_PATH)

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer

def remove_stopwords(text: str) -> str:
    stop_words = set(stopwords.words('english'))
    words = word_tokenize(text)
    filtered = [word for word in words if word.lower() not in stop_words]
    return ' '.join(filtered)

def extract_keywords(text: str, top_n=5) -> list:
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform([text])
    scores = zip(vectorizer.get_feature_names_out(), tfidf_matrix.toarray()[0])
    sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)
    keywords = [word for word, score in sorted_scores[:top_n]]
    return keywords
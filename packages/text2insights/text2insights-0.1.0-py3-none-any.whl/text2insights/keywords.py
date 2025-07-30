from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

def extract_keywords(text, top_n=5):
    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform([text])
    indices = np.argsort(X.toarray()[0])[::-1]
    features = vectorizer.get_feature_names_out()
    return [features[i] for i in indices[:top_n]]

from .sentiment import analyze_sentiment
from .keywords import extract_keywords
from .ner import extract_entities

def analyze_text(text):
    return {
        "sentiment": analyze_sentiment(text),
        "keywords": extract_keywords(text),
        "entities": extract_entities(text),
    }

# utils/sentiment.py
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk

# Ensure NLTK data is present. On first run this will download lexicon.
try:
    _ = nltk.data.find("sentiment/vader_lexicon.zip")
except Exception:
    nltk.download("vader_lexicon")

sia = SentimentIntensityAnalyzer()

def analyze_sentiment(text: str) -> dict:
    """
    Returns a dictionary with compound score and a label:
    { "compound": 0.12, "label": "neutral" }
    """
    if not text:
        return {"compound": 0.0, "label": "neutral"}

    scores = sia.polarity_scores(text)
    compound = scores.get("compound", 0.0)
    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"
    return {"compound": compound, "label": label, "raw": scores}

import re

# Try to import NLTK stopwords; if unavailable, fall back to sklearn's list
try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem.porter import PorterStemmer

    STOPWORDS = set(stopwords.words("english"))
    STEMMER   = PorterStemmer()

except (LookupError, ImportError):
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
    from nltk.stem.porter import PorterStemmer

    STOPWORDS = set(ENGLISH_STOP_WORDS)
    STEMMER   = PorterStemmer()


# Always keep “not” for polarity
STOPWORDS.discard("not")


def clean_review(text: str) -> str:
    """
    Lowercase, remove punctuation, keep only alphanumerics & spaces.
    """
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return text

def tokenize_review(text: str) -> list[str]:
    """
    Split on whitespace, remove stopwords, apply Porter stemmer.
    """
    cleaned = clean_review(text)
    return [
        STEMMER.stem(tok)
        for tok in cleaned.split()
        if tok not in STOPWORDS
    ]

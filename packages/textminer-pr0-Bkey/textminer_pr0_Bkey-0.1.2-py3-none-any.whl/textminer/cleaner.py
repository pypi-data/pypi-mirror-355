import nltk
from nltk.corpus import stopwords


def remove_stopwords(text: str, lang: str = 'en') -> str:
    stop_words = set(stopwords.words(lang))
    words = text.split()
    filtered = [w for w in words if w.lower() not in stop_words]
    return ' '.join(filtered)


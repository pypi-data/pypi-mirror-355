import nltk
from .cleaner import remove_stopwords, extract_keywords
from .detector import detect_language
from .summarizer import summarize_text

nltk.download('stopwords')
nltk.download('punkt')

__all__ = [
    "remove_stopwords",
    "extract_keywords",
    "summarize_text",
    "detect_language"
]


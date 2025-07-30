import nltk
from .cleaner import remove_stopwords
from .detector import detect_language, extract_keywords
from .summarizer import summarize_text

nltk.download('stopwords')
nltk.download('punkt')
nltk.download('punkt_tab')

__all__ = [
    "remove_stopwords",
    "extract_keywords",
    "summarize_text",
    "detect_language"
]


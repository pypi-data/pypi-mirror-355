from .cleaner import remove_stopwords, extract_keywords
from .summarizer import summarize
from .detector import detect_language

__version__ = "0.1.4"

__all__ = [
    "remove_stopwords",
    "extract_keywords",
    "summarize",
    "detect_language"
]
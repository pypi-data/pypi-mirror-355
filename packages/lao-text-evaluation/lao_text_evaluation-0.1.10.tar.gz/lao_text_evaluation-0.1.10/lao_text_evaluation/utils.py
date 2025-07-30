
import unicodedata
import regex
from .config import LAO_CATEGORIES

def normalize(text):
    return unicodedata.normalize("NFC", text.strip())

def grapheme_split(text):
    return regex.findall(r'\X', normalize(text))

def char_split(text):
    return list(normalize(text))

def classify_char(ch):
    for category, chars in LAO_CATEGORIES.items():
        if ch in chars:
            return category
    LAO_CATEGORIES["other"].add(ch)
    return "other"

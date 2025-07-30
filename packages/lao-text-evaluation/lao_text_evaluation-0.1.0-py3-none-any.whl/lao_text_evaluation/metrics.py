import unicodedata
import regex
from difflib import SequenceMatcher

def normalize(text):
    return unicodedata.normalize("NFC", text.strip())

def grapheme_split(text):
    return regex.findall(r'\X', normalize(text))

def compute_cer(ref, hyp):
    r, h = grapheme_split(ref), grapheme_split(hyp)
    matcher = SequenceMatcher(None, r, h)
    S = D = I = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace': S += max(i2 - i1, j2 - j1)
        elif tag == 'delete': D += (i2 - i1)
        elif tag == 'insert': I += (j2 - j1)
    return round((S + D + I) / len(r), 4) if r else 0.0

def compute_wer(ref, hyp):
    r, h = normalize(ref).split(), normalize(hyp).split()
    matcher = SequenceMatcher(None, r, h)
    S = D = I = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace': S += max(i2 - i1, j2 - j1)
        elif tag == 'delete': D += (i2 - i1)
        elif tag == 'insert': I += (j2 - j1)
    return round((S + D + I) / len(r), 4) if r else 0.0

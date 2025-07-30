

import unicodedata
import regex
from difflib import SequenceMatcher
from collections import Counter

# === Lao Character Groups ===
LAO_CONSONANTS = set([
    'ກ', 'ຂ', 'ຄ', 'ງ', 'ຈ', 'ສ', 'ຊ', 'ຍ', 'ດ', 'ຕ', 'ຖ', 'ທ', 'ນ', 'ບ', 'ປ',
    'ຜ', 'ຝ', 'ພ', 'ຟ', 'ມ', 'ຢ', 'ຣ', 'ລ', 'ວ', 'ຫ', 'ອ', 'ຮ', 'ໜ', 'ໝ'
])
LAO_VOWELS_FRONT = set(['ເ', 'ແ', 'ໂ', 'ໄ', 'ໃ'])
LAO_VOWELS_ABOVE = set(['ິ', 'ີ', 'ຶ', 'ື'])
LAO_VOWELS_BELOW = set(['ຸ', 'ູ'])
LAO_VOWELS_BELOW_SPECIAL = set(['ຼ'])
LAO_VOWELS_REAR = set(['ະ', 'ັ', 'າ', 'ຳ', 'ຽ'])
LAO_TONE_MARKS = set(['່', '້', '໊', '໋'])

CHAR_CATEGORIES = {
    'consonant': LAO_CONSONANTS,
    'vowel_upper': LAO_VOWELS_ABOVE,
    'vowel_lower': LAO_VOWELS_BELOW,
    'vowel_below_special': LAO_VOWELS_BELOW_SPECIAL,
    'vowel_front': LAO_VOWELS_FRONT,
    'vowel_rear': LAO_VOWELS_REAR,
    'tone': LAO_TONE_MARKS
}

def normalize(text):
    return unicodedata.normalize("NFC", text.strip())

def grapheme_split(text):
    return regex.findall(r'\X', normalize(text))

def align_by_levenshtein(gt, pred):
    m, n = len(gt), len(pred)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1): dp[i][0] = i
    for j in range(n + 1): dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if gt[i - 1] == pred[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j - 1] + cost,
                           dp[i - 1][j] + 1,
                           dp[i][j - 1] + 1)
    aligned_gt, aligned_pred = [], []
    i, j = m, n
    while i > 0 or j > 0:
        if i > 0 and j > 0 and dp[i][j] == dp[i-1][j-1] + (0 if gt[i-1] == pred[j-1] else 1):
            aligned_gt.insert(0, gt[i - 1])
            aligned_pred.insert(0, pred[j - 1])
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i-1][j] + 1:
            aligned_gt.insert(0, gt[i - 1])
            aligned_pred.insert(0, ' ')
            i -= 1
        else:
            aligned_gt.insert(0, ' ')
            aligned_pred.insert(0, pred[j - 1])
            j -= 1
    return aligned_gt, aligned_pred

def detailed_breakdown_errors(gt_text, pred_text):
    gt, pr = list(normalize(gt_text)), list(normalize(pred_text))
    aligned_gt, aligned_pr = align_by_levenshtein(gt, pr)

    stats = {k: {"total": 0, "error": 0} for k in CHAR_CATEGORIES}
    missing_chars = {k: [] for k in CHAR_CATEGORIES}
    inserted_chars = {k: [] for k in CHAR_CATEGORIES}
    replacements = []

    def classify(ch):
        for cat, group in CHAR_CATEGORIES.items():
            if ch in group:
                return cat
        return None

    for g, p in zip(aligned_gt, aligned_pr):
        g_class = classify(g)
        p_class = classify(p)
        if g != ' ' and g_class:
            stats[g_class]["total"] += 1
        if g != p:
            if g == ' ' and p_class:
                inserted_chars[p_class].append(p)
            elif p == ' ' and g_class:
                stats[g_class]["error"] += 1
                missing_chars[g_class].append(g)
            elif g_class:
                stats[g_class]["error"] += 1
                missing_chars[g_class].append(g)
                if p_class:
                    inserted_chars[p_class].append(p)
                replacements.append((g, p))

    return stats, missing_chars, inserted_chars, replacements
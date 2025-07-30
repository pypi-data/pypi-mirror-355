

import unicodedata
import regex
from difflib import SequenceMatcher
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter


def normalize(text):
    return unicodedata.normalize("NFC", text.strip())

def grapheme_split(text):
    return regex.findall(r'\X', normalize(text))

def compute_cer(ref, hyp):
    ref_units = grapheme_split(ref)
    hyp_units = grapheme_split(hyp)
    matcher = SequenceMatcher(None, ref_units, hyp_units)
    S = D = I = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace':
            S += max(i2 - i1, j2 - j1)
        elif tag == 'delete':
            D += (i2 - i1)
        elif tag == 'insert':
            I += (j2 - j1)
    N = len(ref_units)
    return round((S + D + I) / N, 4) if N > 0 else 0.0

def compute_wer(ref, hyp):
    ref_words = normalize(ref).split()
    hyp_words = normalize(hyp).split()
    matcher = SequenceMatcher(None, ref_words, hyp_words)
    S = D = I = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace':
            S += max(i2 - i1, j2 - j1)
        elif tag == 'delete':
            D += (i2 - i1)
        elif tag == 'insert':
            I += (j2 - j1)
    N = len(ref_words)
    return round((S + D + I) / N, 4) if N > 0 else 0.0


# --- Alignment and Visualization Utilities ---

def align_by_levenshtein(gt, pred):
    m, n = len(gt), len(pred)
    dp = np.zeros((m + 1, n + 1), dtype=int)
    for i in range(m + 1): dp[i][0] = i
    for j in range(n + 1): dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if gt[i - 1] == pred[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j - 1] + cost, dp[i - 1][j] + 1, dp[i][j - 1] + 1)

    aligned_gt, aligned_pred = [], []
    i, j = m, n
    while i > 0 or j > 0:
        if i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + (0 if gt[i - 1] == pred[j - 1] else 1):
            aligned_gt.insert(0, gt[i - 1])
            aligned_pred.insert(0, pred[j - 1])
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            aligned_gt.insert(0, gt[i - 1])
            aligned_pred.insert(0, ' ')
            i -= 1
        else:
            aligned_gt.insert(0, ' ')
            aligned_pred.insert(0, pred[j - 1])
            j -= 1
    return aligned_gt, aligned_pred

def plot_ocr_alignment(gt_text, pred_text, title="Lao OCR Alignment Visualization"):
    gt = list(normalize(gt_text))
    pred = list(normalize(pred_text))
    aligned_gt, aligned_pred = align_by_levenshtein(gt, pred)
    max_len = len(aligned_gt)

    fig, ax = plt.subplots(figsize=(0.6 * max_len, 3))
    ax.set_xlim(0, max_len)
    ax.set_ylim(0, 2)

    for i in range(max_len):
        g = aligned_gt[i]
        p = aligned_pred[i]
        color = 'lightgreen' if g == p else ('orange' if g != ' ' and p != ' ' else 'red')
        ax.add_patch(plt.Rectangle((i, 1), 1, 1, edgecolor='black', facecolor=color))
        ax.add_patch(plt.Rectangle((i, 0), 1, 1, edgecolor='black', facecolor=color))
        ax.text(i + 0.5, 1.5, g, ha='center', va='center', fontsize=16)
        ax.text(i + 0.5, 0.5, p, ha='center', va='center', fontsize=16)

    ax.text(-0.5, 1.5, "GT", ha='right', va='center', fontsize=14, fontweight='bold')
    ax.text(-0.5, 0.5, "PRED", ha='right', va='center', fontsize=14, fontweight='bold')

    ax.set_title(title, fontsize=16, pad=10)
    ax.axis('off')
    plt.tight_layout()
    plt.show()


# --- Lao Error Analysis Function ---
def analyze_detailed_errors(gt_text, pred_text):
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

    def classify(ch):
        if ch in LAO_CONSONANTS: return "consonant"
        if ch in LAO_VOWELS_ABOVE: return "vowel_upper"
        if ch in LAO_VOWELS_BELOW: return "vowel_lower"
        if ch in LAO_VOWELS_BELOW_SPECIAL: return "vowel_below_special"
        if ch in LAO_VOWELS_FRONT: return "vowel_front"
        if ch in LAO_VOWELS_REAR: return "vowel_rear"
        if ch in LAO_TONE_MARKS: return "tone"
        return None

    gt = list(normalize(gt_text))
    pr = list(normalize(pred_text))
    aligned_gt, aligned_pr = align_by_levenshtein(gt, pr)

    categories = ["consonant", "vowel_upper", "vowel_lower", "vowel_below_special", "vowel_front", "vowel_rear", "tone"]
    stats = {k: {"total": 0, "error": 0} for k in categories}
    missing_chars = {k: [] for k in categories}
    inserted_chars = {k: [] for k in categories}
    replacements = []

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

    return {
        "stats": stats,
        "missing_chars": missing_chars,
        "inserted_chars": inserted_chars,
        "replacements": replacements
    }

# --- Lao Error Breakdown ---
def detailed_breakdown_errors(gt_text, pred_text,
                              show_detailed=False,
                              show_all=False,
                              show_replaced=False,
                              show_inserted=False,
                              show_errors=False):
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

    def classify(ch):
        if ch in LAO_CONSONANTS: return "consonant"
        if ch in LAO_VOWELS_ABOVE: return "vowel_upper"
        if ch in LAO_VOWELS_BELOW: return "vowel_lower"
        if ch in LAO_VOWELS_BELOW_SPECIAL: return "vowel_below_special"
        if ch in LAO_VOWELS_FRONT: return "vowel_front"
        if ch in LAO_VOWELS_REAR: return "vowel_rear"
        if ch in LAO_TONE_MARKS: return "tone"
        return None

    gt = list(normalize(gt_text))
    pr = list(normalize(pred_text))
    aligned_gt, aligned_pr = align_by_levenshtein(gt, pr)

    categories = ["consonant", "vowel_upper", "vowel_lower", "vowel_below_special", "vowel_front", "vowel_rear", "tone"]
    stats = {k: {"total": 0, "error": 0} for k in categories}
    missing_chars = {k: [] for k in categories}
    inserted_chars = {k: [] for k in categories}
    replacements = []

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

    if show_detailed or show_all:
        print("===== Detailed Error Breakdown =====")
        for key in categories:
            t, e = stats[key]["total"], stats[key]["error"]
            rate = e / t if t else 0
            print(f"{key.replace('_', ' ').title():30} - Total: {t}, Errors: {e}, Error Rate: {rate:.4f}")

    if show_errors or show_all:
        print("\n===== Error Characters =====")
        for key in categories:
            print(f"{key.replace('_', ' ').title():30}: {missing_chars[key]}")

    if show_inserted or show_all:
        print("\n===== Inserted Characters =====")
        for key in categories:
            print(f"{key.replace('_', ' ').title():30}: {inserted_chars[key]}")

    if show_replaced or show_all:
        print("\n===== Replaced Characters =====")
        for g, p in replacements:
            print(f"'{g}' -> '{p}'")

    return stats, missing_chars, inserted_chars, replacements

import csv
import numpy as np
from difflib import SequenceMatcher
from .utils import grapheme_split, char_split, normalize, classify_char
from .config import CATEGORY_LIST
import os

def compute_cer(gt, pred):
    r, h = grapheme_split(gt), grapheme_split(pred)
    if not r: return 0.0
    m = SequenceMatcher(None, r, h, autojunk=False)
    S = D = I = 0
    for tag, i1, i2, j1, j2 in m.get_opcodes():
        if tag == 'replace': S += max(i2 - i1, j2 - j1)
        elif tag == 'delete': D += i2 - i1
        elif tag == 'insert': I += j2 - j1
    return round((S + D + I) / len(r), 4)

def compute_wer(gt, pred):
    r, h = normalize(gt).split(), normalize(pred).split()
    if not r: return 0.0
    m = SequenceMatcher(None, r, h, autojunk=False)
    S = D = I = 0
    for tag, i1, i2, j1, j2 in m.get_opcodes():
        if tag == 'replace': S += max(i2 - i1, j2 - j1)
        elif tag == 'delete': D += i2 - i1
        elif tag == 'insert': I += j2 - j1
    return round((S + D + I) / len(r), 4)

def align_sequences(seq1, seq2):
    m, n = len(seq1), len(seq2)
    dp = np.zeros((m + 1, n + 1), dtype=int)
    for i in range(m + 1): dp[i, 0] = i
    for j in range(n + 1): dp[0, j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if seq1[i - 1] == seq2[j - 1] else 1
            dp[i, j] = min(dp[i - 1, j - 1] + cost, dp[i - 1, j] + 1, dp[i, j - 1] + 1)

    aligned1, aligned2 = [], []
    i, j = m, n
    while i > 0 or j > 0:
        current_cost = dp[i, j]
        sub_cost = 0 if i > 0 and j > 0 and seq1[i-1] == seq2[j-1] else 1
        diag_path_cost = (dp[i-1, j-1] + sub_cost) if i > 0 and j > 0 else float('inf')
        vert_path_cost = (dp[i-1, j] + 1) if i > 0 else float('inf')
        horiz_path_cost = (dp[i, j-1] + 1) if j > 0 else float('inf')
        if current_cost == horiz_path_cost:
            aligned1.insert(0, ' '); aligned2.insert(0, seq2[j-1]); j -= 1
        elif current_cost == vert_path_cost:
            aligned1.insert(0, seq1[i-1]); aligned2.insert(0, ' '); i -= 1
        elif current_cost == diag_path_cost:
            aligned1.insert(0, seq1[i-1]); aligned2.insert(0, seq2[j-1]); i -= 1; j -= 1
        else:
            if j > 0: aligned1.insert(0, ' '); aligned2.insert(0, seq2[j-1]); j -= 1
            elif i > 0: aligned1.insert(0, seq1[i-1]); aligned2.insert(0, ' '); i -= 1
            else: break
    return aligned1, aligned2

def analyze_grapheme_errors(gt, pred):
    gt_g, pred_g = grapheme_split(gt), grapheme_split(pred)
    aligned_gt, aligned_pred = align_sequences(gt_g, pred_g)
    removed = {k: [] for k in CATEGORY_LIST}
    inserted = {k: [] for k in CATEGORY_LIST}
    replaced = []

    for g, p in zip(aligned_gt, aligned_pred):
        if g == p: continue
        g_set, p_set = set(g) if g.strip() else set(), set(p) if p.strip() else set()
        if g.strip() and p.strip():
            replaced.append(f"{g}→{p}")
            for ch in g_set - p_set: removed[classify_char(ch)].append(ch)
            for ch in p_set - g_set: inserted[classify_char(ch)].append(ch)
        elif g.strip():
            for ch in g: removed[classify_char(ch)].append(ch)
        elif p.strip():
            for ch in p: inserted[classify_char(ch)].append(ch)
    return removed, inserted, replaced


def save_to_csv(data, filename="ocr_detailed_output.csv"):
    header = ["Filename", "GT", "PRED", "CER", "WER"]
    header += [f"Remove_{c}" for c in CATEGORY_LIST]
    header += [f"Insert_{c}" for c in CATEGORY_LIST]
    header += ["Replaced_Graphemes", "Error_Avg"]

    file_exists = os.path.exists(filename)

    with open(filename, "a" if file_exists else "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(header)
        writer.writerows(data)

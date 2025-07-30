import matplotlib.pyplot as plt
from .align import align_by_levenshtein
import unicodedata
import regex
from .error_analysis import normalize
from collections import Counter

def plot_ocr_alignment(gt_text, pred_text, title="Lao OCR Alignment", save_path=None):
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
        ax.text(i + 0.5, 1.5, g, ha='center', va='center', fontsize=14)
        ax.text(i + 0.5, 0.5, p, ha='center', va='center', fontsize=14)

    ax.text(-0.5, 1.5, "GT", ha='right', va='center', fontsize=12, fontweight='bold')
    ax.text(-0.5, 0.5, "PRED", ha='right', va='center', fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14)
    ax.axis('off')
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path)
        plt.close()
    else:
        plt.show()
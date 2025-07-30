import matplotlib.pyplot as plt
from .align import align_by_levenshtein

def plot_ocr_alignment(gt, pred, title="Lao OCR Alignment"):
    aligned_gt, aligned_pred = align_by_levenshtein(gt, pred)
    max_len = len(aligned_gt)
    fig, ax = plt.subplots(figsize=(0.6 * max_len, 3))
    ax.set_xlim(0, max_len)
    ax.set_ylim(0, 2)
    for i in range(max_len):
        g, p = aligned_gt[i], aligned_pred[i]
        color = 'lightgreen' if g == p else ('red' if ' ' in [g, p] else 'orange')
        ax.add_patch(plt.Rectangle((i, 1), 1, 1, edgecolor='black', facecolor=color))
        ax.add_patch(plt.Rectangle((i, 0), 1, 1, edgecolor='black', facecolor=color))
        ax.text(i + 0.5, 1.5, g, ha='center', va='center')
        ax.text(i + 0.5, 0.5, p, ha='center', va='center')
    ax.axis('off')
    plt.title(title)
    plt.tight_layout()
    plt.show()
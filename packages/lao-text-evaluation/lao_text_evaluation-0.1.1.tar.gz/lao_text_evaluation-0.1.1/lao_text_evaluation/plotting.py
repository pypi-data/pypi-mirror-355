import matplotlib.pyplot as plt
from .utils import char_split
from .metrics import align_sequences

def plot_character_alignment(gt, pred, filename, save_path=None):
    aligned_gt, aligned_pred = align_sequences(char_split(gt), char_split(pred))
    fig, ax = plt.subplots(figsize=(0.7 * len(aligned_gt), 4))
    ax.set_title(f"Character Alignment: {filename}", fontsize=16, pad=20)
    ax.set_xlim(0, len(aligned_gt))
    ax.set_ylim(0, 3)

    for i, (g, p) in enumerate(zip(aligned_gt, aligned_pred)):
        is_match = g == p
        is_substitution = g != ' ' and p != ' ' and not is_match
        color = 'lightgreen' if is_match else ('orange' if is_substitution else '#FF9999')

        ax.add_patch(plt.Rectangle((i, 2), 1, 1, edgecolor='black', facecolor=color))
        ax.add_patch(plt.Rectangle((i, 1), 1, 1, edgecolor='black', facecolor=color))
        ax.text(i + 0.5, 2.5, g, ha='center', va='center', fontsize=16)
        ax.text(i + 0.5, 1.5, p, ha='center', va='center', fontsize=16)
        ax.text(i + 0.5, 0.3, str(i), ha='center', va='center', fontsize=12)

    ax.text(-0.5, 2.5, "GT", ha='right', va='center', fontsize=14, fontweight='bold')
    ax.text(-0.5, 1.5, "PRED", ha='right', va='center', fontsize=14, fontweight='bold')
    ax.text(-0.5, 0.3, "Index", ha='right', va='center', fontsize=12)
    ax.axis('off')
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])

    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"🖼️ Saved plot to: {save_path}")
    else:
        plt.show()

    plt.close()
import matplotlib.pyplot as plt
from .utils import char_split
from .metrics import align_sequences

def plot_character_alignment(gt, pred, filename, save_path=None):
    aligned_gt, aligned_pred = align_sequences(char_split(gt), char_split(pred))
    fig, ax = plt.subplots(figsize=(0.7 * len(aligned_gt), 4))
    ax.set_title(f"Character Alignment: {filename}", fontsize=16, pad=20)
    ax.set_xlim(0, len(aligned_gt))
    ax.set_ylim(0, 4)
    ax.axis('off')

    for i, (g, p) in enumerate(zip(aligned_gt, aligned_pred)):
        if g == p:
            color = 'lightgreen'         # ✅ Match
        elif g != ' ' and p != ' ':
            color = 'orange'             # 🟧 Replace
        elif g != ' ' and p == ' ':
            color = '#FF9999'            # 🟥 Removed
        else:
            color = '#66ccff'            # 🟦 Inserted

        ax.add_patch(plt.Rectangle((i, 3), 1, 1, edgecolor='black', facecolor=color))
        ax.add_patch(plt.Rectangle((i, 2), 1, 1, edgecolor='black', facecolor=color))

        ax.text(i + 0.5, 3.5, g if g.strip() else '␣', ha='center', va='center', fontsize=16)
        ax.text(i + 0.5, 2.5, p if p.strip() else '␣', ha='center', va='center', fontsize=16)
        ax.text(i + 0.5, 1.2, str(i), ha='center', va='center', fontsize=10)

    # Labels
    ax.text(-0.5, 3.5, "GT", ha='right', va='center', fontsize=12, fontweight='bold')
    ax.text(-0.5, 2.5, "PRED", ha='right', va='center', fontsize=12, fontweight='bold')
    ax.text(-0.5, 1.2, "Index", ha='right', va='center', fontsize=10)

    # Add legend manually
    legend_elements = [
        plt.Rectangle((0, 0), 1, 1, facecolor='lightgreen', edgecolor='black', label='Match'),
        plt.Rectangle((0, 0), 1, 1, facecolor='orange', edgecolor='black', label='Replaced'),
        plt.Rectangle((0, 0), 1, 1, facecolor='#FF9999', edgecolor='black', label='Removed'),
        plt.Rectangle((0, 0), 1, 1, facecolor='#66ccff', edgecolor='black', label='Inserted')
    ]
    ax.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, -0.25),
              ncol=4, frameon=False)

    plt.tight_layout(rect=[0, 0.1, 1, 0.95])

    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"🖼️ Saved plot to: {save_path}")
    else:
        plt.show()

    plt.close()
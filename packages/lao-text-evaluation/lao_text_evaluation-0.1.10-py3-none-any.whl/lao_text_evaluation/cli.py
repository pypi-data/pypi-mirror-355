import argparse
import random
import os
from glob import glob

from lao_text_evaluation.metrics import (
    compute_cer, compute_wer,
    analyze_grapheme_errors, save_to_csv
)
from lao_text_evaluation.plotting import plot_character_alignment
from lao_text_evaluation.config import CATEGORY_LIST


def analyze_pair(filename, gt, pred, plot=False, plot_dir=None):
    cer = compute_cer(gt, pred)
    wer = compute_wer(gt, pred)
    removed, inserted, replaced = analyze_grapheme_errors(gt, pred)
    avg_err = round((cer + wer) / 2, 4)

    print("=" * 40)
    print(f"📄 Analysis for: {filename}")
    print(f"GT:   {gt}")
    print(f"PRED: {pred}")
    print(f"CER: {cer} | WER: {wer} | Avg Error: {avg_err}")
    print("🔴 Removed:", {k: v for k, v in removed.items() if v})
    print("🟢 Inserted:", {k: v for k, v in inserted.items() if v})
    print("🟠 Replaced Graphemes:", replaced)

    if plot or plot_dir:
        plot_path = os.path.join(plot_dir, filename + ".png") if plot_dir else None
        plot_character_alignment(gt, pred, filename, save_path=plot_path)

    row = [filename, gt, pred, cer, wer]
    row += ["".join(removed[c]) for c in CATEGORY_LIST]
    row += ["".join(inserted[c]) for c in CATEGORY_LIST]
    row.append(", ".join(replaced))
    row.append(avg_err)
    return row


def main():
    parser = argparse.ArgumentParser(description="Lao OCR Evaluation CLI")
    parser.add_argument('--gt-path', type=str, help="Path to folder with .txt files")
    parser.add_argument('--pred-path', type=str, help="Path to folder with predicted .txt files")
    parser.add_argument('--plot-sample', type=int, default=1, help="Number of random samples to visualize")
    parser.add_argument('--plot-dir', type=str, help="Directory to save plot images")
    parser.add_argument('--save-csv', type=str, help="CSV output path")
    parser.add_argument('--append-csv', action='store_true', help="Append to existing CSV instead of overwriting")

    parser.add_argument('--gt', type=str, help="Ground truth string (for single mode)")
    parser.add_argument('--pred', type=str, help="Prediction string (for single mode)")
    parser.add_argument('--filename', type=str, default="sample.png", help="Filename label for single mode")
    parser.add_argument('--plot', action='store_true', help="Plot alignment (only for single mode)")

    args = parser.parse_args()
    rows = []

    if args.plot_dir:
        os.makedirs(args.plot_dir, exist_ok=True)

    if args.gt and args.pred:
        # Single string comparison mode
        row = analyze_pair(args.filename, args.gt, args.pred, args.plot, args.plot_dir)
        rows.append(row)

    elif args.gt_path and args.pred_path:
        # Folder mode
        gt_files = sorted(glob(os.path.join(args.gt_path, "*.txt")))
        for gt_file in gt_files:
            filename = os.path.basename(gt_file).replace(".txt", "")
            pred_file = os.path.join(args.pred_path, filename + ".txt")
            if not os.path.exists(pred_file):
                print(f"⚠️ Skipping {filename}, prediction not found.")
                continue
            with open(gt_file, encoding="utf-8") as f1, open(pred_file, encoding="utf-8") as f2:
                gt = f1.read().strip()
                pred = f2.read().strip()
            row = analyze_pair(filename, gt, pred, False, None)
            rows.append(row)

        # Random visualization for N samples
        if args.plot_sample > 0 and rows:
            sample = random.sample(rows, min(args.plot_sample, len(rows)))
            for r in sample:
                plot_character_alignment(r[1], r[2], r[0],
                                         save_path=os.path.join(args.plot_dir, r[0] + ".png") if args.plot_dir else None)

    if args.save_csv and rows:
        if args.append_csv:
            save_to_csv(rows, args.save_csv)
        else:
            if os.path.exists(args.save_csv):
                os.remove(args.save_csv)
            save_to_csv(rows, args.save_csv)
        print(f"✅ CSV saved to {args.save_csv}")


if __name__ == "__main__":
    main()
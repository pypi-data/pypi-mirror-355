import argparse
import csv
from .eval import compute_cer, compute_wer, detailed_breakdown_errors
from .visual import plot_ocr_alignment

def export_to_csv(gt, pred, filename="ocr_eval_output.csv"):
    from .eval import analyze_detailed_errors  # helper version of detailed_breakdown_errors

    cer = compute_cer(gt, pred)
    wer = compute_wer(gt, pred)
    result = analyze_detailed_errors(gt, pred)

    # Write CSV
    with open(filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Summary
        writer.writerow(["Ground Truth", gt])
        writer.writerow(["Prediction", pred])
        writer.writerow(["CER", cer])
        writer.writerow(["WER", wer])
        writer.writerow([])

        # Error Breakdown
        writer.writerow(["Category", "Total", "Errors", "Error Rate"])
        for cat, stat in result["stats"].items():
            writer.writerow([cat, stat["total"], stat["error"], f'{stat["error"] / stat["total"]:.4f}' if stat["total"] else 0])
        writer.writerow([])

        # Error Characters
        writer.writerow(["Error Characters"])
        for cat, chars in result["missing_chars"].items():
            writer.writerow([cat, ", ".join(chars)])
        writer.writerow([])

        # Inserted Characters
        writer.writerow(["Inserted Characters"])
        for cat, chars in result["inserted_chars"].items():
            writer.writerow([cat, ", ".join(chars)])
        writer.writerow([])

        # Replaced Characters
        writer.writerow(["Replaced Characters"])
        writer.writerow(["GT", "Predicted"])
        for gt_char, pred_char in result["replacements"]:
            writer.writerow([gt_char, pred_char])

    print(f"\n✅ CSV saved to: {filename}")
    
def main():
    parser = argparse.ArgumentParser(description="Evaluate Lao OCR outputs.")
    parser.add_argument("ground_truth", help="Ground truth text or directory")
    parser.add_argument("prediction", help="Predicted text or directory")
    parser.add_argument("-d", "--detail", action="store_true", help="Show inserted, error, and replaced characters")
    parser.add_argument("-a", "--all", action="store_true", help="Show all outputs")
    parser.add_argument("-r", "--replaced", action="store_true", help="Show replaced characters")
    parser.add_argument("-I", "--inserted", action="store_true", help="Show inserted characters")
    parser.add_argument("-e", "--errors", action="store_true", help="Show error characters")
    parser.add_argument("-p", "--plot", action="store_true", help="Plot character alignment")
    parser.add_argument("--batch", action="store_true", help="Run batch evaluation on folders")
    parser.add_argument("--outdir", default="batch_eval_output.csv", help="CSV output path")
    parser.add_argument("-analy", "--analyze", action="store_true", help="Print batch summary analysis")
    parser.add_argument("-b", "--bar", action="store_true", help="Plot bar chart of average stats")
    parser.add_argument("-l", "--line", type=int, nargs='?', const=4, help="Show N random alignment visualizations (default 4)")
    args = parser.parse_args()

    if args.batch:
        from .eval import analyze_detailed_errors
        import os

        gt_dir = args.ground_truth
        pred_dir = args.prediction
        output_csv = args.outdir

        rows = []

        for filename in os.listdir(gt_dir):
            gt_path = os.path.join(gt_dir, filename)
            pred_path = os.path.join(pred_dir, filename)
            if not os.path.exists(pred_path):
                print(f"[Warning] Missing prediction for {filename}")
                continue
            with open(gt_path, 'r', encoding='utf-8') as f_gt, open(pred_path, 'r', encoding='utf-8') as f_pred:
                gt = f_gt.read().strip()
                pred = f_pred.read().strip()

            cer = compute_cer(gt, pred)
            wer = compute_wer(gt, pred)
            result = analyze_detailed_errors(gt, pred)

            row = {
                "filename": filename,
                "gt": gt,
                "pred": pred,
                "cer": cer,
                "wer": wer,
                "missing": "; ".join([f"{k}: {','.join(v)}" for k, v in result["missing_chars"].items() if v]),
                "inserted": "; ".join([f"{k}: {','.join(v)}" for k, v in result["inserted_chars"].items() if v]),
                "replacements": "; ".join([f"'{g}'→'{p}'" for g, p in result["replacements"]])
            }
            rows.append(row)

        import statistics
        avg_cer = statistics.mean([row["cer"] for row in rows])
        avg_wer = statistics.mean([row["wer"] for row in rows])
        total_repl = sum([len(row["replacements"].split("; ")) for row in rows if row["replacements"]])
        total_insert = sum([len(row["inserted"].split("; ")) for row in rows if row["inserted"]])
        total_miss = sum([len(row["missing"].split("; ")) for row in rows if row["missing"]])

        with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["filename", "gt", "pred", "cer", "wer", "missing", "inserted", "replacements"])
            writer.writeheader()
            writer.writerows(rows)
            writer.writerow({})
            writer.writerow({"filename": "Batch Summary"})
            writer.writerow({"filename": "Average CER", "cer": avg_cer})
            writer.writerow({"filename": "Average WER", "wer": avg_wer})
            writer.writerow({"filename": "Total Insertions", "inserted": total_insert})
            writer.writerow({"filename": "Total Deletions", "missing": total_miss})
            writer.writerow({"filename": "Total Replacements", "replacements": total_repl})

        print(f"\n✅ Batch evaluation completed. CSV saved to: {output_csv}")

        if args.analyze:
            print("\n===== Batch Summary Analysis =====")
            print(f"Average CER: {avg_cer:.4f}")
            print(f"Average WER: {avg_wer:.4f}")
            print(f"Total Insertions: {total_insert}")
            print(f"Total Deletions: {total_miss}")
            print(f"Total Replacements: {total_repl}")

        if args.bar:
            import matplotlib.pyplot as plt
            labels = ['CER', 'WER', 'Insert', 'Delete', 'Replace']
            values = [avg_cer, avg_wer, total_insert, total_miss, total_repl]
            plt.bar(labels, values)
            plt.title("Batch Evaluation Summary")
            plt.ylabel("Count / Rate")
            plt.tight_layout()
            plt.show()

        if args.line:
            import matplotlib.pyplot as plt
            import random
            from .visual import plot_ocr_alignment

            num_samples = min(args.line, len(rows))
            print(f"\n📊 Showing Alignment Visualization for {num_samples} Random Files:")
            sample_rows = random.sample(rows, num_samples)
            for row in sample_rows:
                plot_ocr_alignment(row["gt"], row["pred"], title=f"GT vs Pred - {row['filename']}")

        return

    gt = args.ground_truth
    pred = args.prediction

    print("Ground Truth:", gt)
    print("Prediction  :", pred)
    print("CER:", compute_cer(gt, pred))
    print("WER:", compute_wer(gt, pred))

    if args.detail or args.all:
        detailed_breakdown_errors(
            gt, pred,
            show_all=True,
            show_replaced=True,
            show_inserted=True,
            show_errors=True
        )

    if args.plot or args.all:
        plot_ocr_alignment(gt, pred)

    if args.outdir and not args.batch:
        export_to_csv(gt, pred, args.outdir)

if __name__ == "__main__":
    main()
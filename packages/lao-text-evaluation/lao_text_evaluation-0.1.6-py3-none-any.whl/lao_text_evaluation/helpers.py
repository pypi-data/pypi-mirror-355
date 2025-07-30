def run_batch_evaluation(gt_folder, pred_folder, outdir="results"):
    import os
    from .eval import compute_cer, compute_wer, analyze_detailed_errors
    os.makedirs(outdir, exist_ok=True)

    for fname in os.listdir(gt_folder):
        gt_path = os.path.join(gt_folder, fname)
        pred_path = os.path.join(pred_folder, fname)
        if not os.path.exists(pred_path):
            print(f"❌ Skipped {fname} (prediction missing)")
            continue

        with open(gt_path, encoding="utf-8") as f:
            gt_text = f.read().strip()
        with open(pred_path, encoding="utf-8") as f:
            pred_text = f.read().strip()

        result = analyze_detailed_errors(gt_text, pred_text)
        cer = compute_cer(gt_text, pred_text)
        wer = compute_wer(gt_text, pred_text)

        output_path = os.path.join(outdir, f"{fname}.csv")
        with open(output_path, "w", encoding="utf-8", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Ground Truth", gt_text])
            writer.writerow(["Prediction", pred_text])
            writer.writerow(["CER", cer])
            writer.writerow(["WER", wer])
            writer.writerow([])

            writer.writerow(["Category", "Total", "Errors", "Error Rate"])
            for k, v in result["stats"].items():
                rate = v["error"] / v["total"] if v["total"] else 0
                writer.writerow([k, v["total"], v["error"], f"{rate:.4f}"])

            writer.writerow([])
            writer.writerow(["Error Characters"])
            for k, chars in result["missing_chars"].items():
                writer.writerow([k, ", ".join(chars)])
            writer.writerow([])
            writer.writerow(["Inserted Characters"])
            for k, chars in result["inserted_chars"].items():
                writer.writerow([k, ", ".join(chars)])
            writer.writerow([])
            writer.writerow(["Replaced Characters"])
            writer.writerow(["GT", "Predicted"])
            for gt_char, pred_char in result["replacements"]:
                writer.writerow([gt_char, pred_char])

        print(f"✅ Saved: {output_path}")
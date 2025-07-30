
import unittest
from lao_text_evaluation.eval import detailed_breakdown_errors, plot_ocr_alignment

class TestDisplay(unittest.TestCase):
    def test_detailed_breakdown_output(self):
        gt = "ສະບາຍດີຫຼວງພະບາງ"
        pred = "ສະບາຍດືຫວງພ:ບາງ"
        # Expect this to run and print without error
        detailed_breakdown_errors(gt, pred)

    def test_plot_ocr_alignment_output(self):
        gt = "ສະບາຍດີຫຼວງພະບາງ"
        pred = "ສະບາຍດືຫວງພ:ບາງ"
        # Expect this to plot without raising error
        plot_ocr_alignment(gt, pred)

if __name__ == "__main__":
    unittest.main()
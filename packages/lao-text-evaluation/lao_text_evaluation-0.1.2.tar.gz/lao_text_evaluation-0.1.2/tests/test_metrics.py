import unittest
from lao_text_evaluation.metrics import compute_cer, compute_wer

class TestMetrics(unittest.TestCase):
    
    def test_compute_cer_exact_match(self):
        ref = "ສະບາຍດີ"
        hyp = "ສະບາຍດີ"
        self.assertEqual(compute_cer(ref, hyp), 0.0)

    def test_compute_cer_substitution(self):
        ref = "ສະບາຍດີ"
        hyp = "ສະບາຍດື"
        self.assertGreater(compute_cer(ref, hyp), 0.0)

    def test_compute_wer_exact_match(self):
        ref = "ສະບາຍດີ"
        hyp = "ສະບາຍດີ"
        self.assertEqual(compute_wer(ref, hyp), 0.0)

    def test_compute_wer_single_word_diff(self):
        ref = "ສະບາຍດີ"
        hyp = "ສະບາຍບໍ"
        self.assertGreater(compute_wer(ref, hyp), 0.0)

if __name__ == '__main__':
    unittest.main()
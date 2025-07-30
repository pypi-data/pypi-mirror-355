# tests/test_cli.py

import subprocess
import unittest

class TestCLI(unittest.TestCase):
    def test_cli_output(self):
        result = subprocess.run([
            "python", "-m", "lao_text_evaluation.cli",
            "-g", "ສະບາຍດີຫຼວງພະບາງ",
            "-p", "ສະບາຍດືຫວງພ:ບາງ",
            "-d", "-r", "-e", "-I"
        ], capture_output=True, text=True)
        
        self.assertIn("===== Detailed Error Breakdown =====", result.stdout)
        self.assertIn("===== Replaced Characters =====", result.stdout)
        self.assertEqual(result.returncode, 0)

if __name__ == "__main__":
    unittest.main()
from .eval import compute_cer, compute_wer, detailed_breakdown_errors
from .visual import plot_ocr_alignment

__all__ = [
    "compute_cer",
    "compute_wer",
    "detailed_breakdown_errors",
    "plot_ocr_alignment"
]
"""
OCR Feature for Charlie AI using PaddleOCR.

Provides optical character recognition to extract text from images,
scanned PDFs, and other visual documents.
"""

from features.ocr.glm_ocr_adapter import GLMOCRAdapter
from features.ocr.paddleocr_adapter import PaddleOCRAdapter

__all__ = ["GLMOCRAdapter", "PaddleOCRAdapter"]

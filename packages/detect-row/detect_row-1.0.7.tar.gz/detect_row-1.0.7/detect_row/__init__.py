"""
Thư viện detect_row - phát hiện và cắt các hàng từ bảng trong ảnh

Module này cung cấp các công cụ để trích xuất hàng từ bảng trong ảnh
dựa trên phương pháp phát hiện đường kẻ ngang và phân tích histogram.

Classes:
    BasicRowExtractor: Trích xuất hàng cơ bản
    AdvancedRowExtractor: Trích xuất hàng nâng cao với phát hiện bảng
    TesseractOCRExtractor: Trích xuất hàng và OCR với Tesseract
"""

from .base import BaseRowExtractor
from .basic_row_extractor import BasicRowExtractor
from .advanced_row_extractor import AdvancedRowExtractor, AdvancedRowExtractorMain
from .advanced_table_extractor import AdvancedTableExtractor
from .tesseract_ocr_extractor import TesseractRowExtractor

__all__ = [
    'BaseRowExtractor',
    'BasicRowExtractor',
    'AdvancedRowExtractor',
    'AdvancedRowExtractorMain',
    'TesseractRowExtractor',
    'AdvancedTableExtractor'
]

__version__ = '1.0.7'

"""
Module trích xuất bảng nâng cao
--------------------------

Module này cung cấp các chức năng trích xuất bảng từ ảnh, bao gồm:
- Phát hiện vị trí các bảng trong ảnh
- Phát hiện cấu trúc bảng (đường kẻ ngang, dọc)
- Trích xuất nội dung các ô trong bảng
- Hỗ trợ nhiều loại bảng khác nhau
"""

import os
import cv2
import numpy as np
import logging
import argparse
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional, NamedTuple
from .advanced_row_extractor import AdvancedRowExtractor
from .base import BaseRowExtractor, logger

# ... (phần còn lại của code, đã đọc ở trên) ... 
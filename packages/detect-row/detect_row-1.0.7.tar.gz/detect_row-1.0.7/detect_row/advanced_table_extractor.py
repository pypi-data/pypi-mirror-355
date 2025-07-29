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

# Sửa import để hoạt động trong cả môi trường development và production
try:
    from .advanced_row_extractor import AdvancedRowExtractor
    from .base import BaseRowExtractor, logger
except ImportError:
    from detect_row.advanced_row_extractor import AdvancedRowExtractor
    from detect_row.base import BaseRowExtractor, logger

logger = logging.getLogger(__name__)

class TableStructure(NamedTuple):
    """Cấu trúc bảng"""
    horizontal_lines: List[int]  # Tọa độ y của các đường kẻ ngang
    vertical_lines: List[int]    # Tọa độ x của các đường kẻ dọc
    cells: List[List[Tuple[int, int, int, int]]]  # Danh sách các ô trong bảng [row][col] = (x1,y1,x2,y2)
    header_rows: List[int]       # Chỉ số các hàng tiêu đề
    merged_cells: List[Tuple[int, int, int, int, int, int]]  # Danh sách các ô gộp (row1,col1,row2,col2,x,y)

class AdvancedTableExtractor(AdvancedRowExtractor):
    """Lớp trích xuất bảng nâng cao"""
    
    def __init__(self, 
                 input_dir: str = "input", 
                 output_dir: str = "output/tables",
                 debug_dir: str = "debug/tables",
                 min_table_size: int = 100):
        """Khởi tạo AdvancedTableExtractor
        
        Args:
            input_dir: Thư mục chứa ảnh đầu vào
            output_dir: Thư mục lưu kết quả
            debug_dir: Thư mục lưu ảnh debug
            min_table_size: Kích thước tối thiểu của bảng (pixel)
        """
        super().__init__(input_dir, output_dir, debug_dir)
        self.min_table_size = min_table_size
        
    def detect_horizontal_lines(self, image: np.ndarray, min_line_length_ratio: float = 0.3) -> List[int]:
        """Phát hiện các đường kẻ ngang trong ảnh"""
        height, width = image.shape[:2]
        min_line_length = int(width * min_line_length_ratio)
        
        # Tăng kích thước kernel để bắt được đường kẻ mờ
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (min_line_length // 8, 1))
        horizontal_lines = cv2.morphologyEx(image, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
        
        # Lọc đường kẻ với ngưỡng thấp hơn
        filtered_horizontal_lines = np.zeros_like(horizontal_lines)
        contours, _ = cv2.findContours(horizontal_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        max_length = max((cv2.boundingRect(cnt)[2] for cnt in contours), default=0)
        min_length_threshold = int(max_length * 0.5)  # Giảm ngưỡng xuống 50%
        
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w >= min_length_threshold:
                cv2.drawContours(filtered_horizontal_lines, [cnt], -1, 255, -1)
        
        # Chiếu tổng theo trục x để tìm vị trí đường kẻ ngang
        h_projection = cv2.reduce(filtered_horizontal_lines, 1, cv2.REDUCE_SUM, dtype=cv2.CV_32S)
        h_projection = h_projection.flatten()
        
        # Lọc nhiễu và tìm vị trí đường kẻ với ngưỡng thấp hơn
        line_positions = []
        threshold = width / 6  # Giảm ngưỡng để bắt được đường kẻ mờ
        
        for y in range(1, height - 1):
            if h_projection[y] > threshold:
                if (h_projection[y] >= h_projection[y-1] and 
                    h_projection[y] >= h_projection[y+1]):
                    line_positions.append(y)
        
        # Lọc đường kẻ gần nhau với khoảng cách nhỏ hơn
        filtered_positions = self._filter_close_lines(line_positions, min_distance=8)
        
        # Thêm biên với khoảng cách lớn hơn
        if filtered_positions and filtered_positions[0] > 30:
            filtered_positions.insert(0, 0)
        if filtered_positions and filtered_positions[-1] < height - 30:
            filtered_positions.append(height)
        
        filtered_positions.sort()
        return filtered_positions
    
    def detect_vertical_lines(self, image: np.ndarray, min_line_length_ratio: float = 0.3) -> List[int]:
        """Phát hiện các đường kẻ dọc trong ảnh"""
        height, width = image.shape[:2]
        min_line_length = int(height * min_line_length_ratio)
        
        # Tăng kích thước kernel để bắt được đường kẻ mờ
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, min_line_length // 8))
        vertical_lines = cv2.morphologyEx(image, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
        
        # Lọc đường kẻ với ngưỡng thấp hơn
        filtered_vertical_lines = np.zeros_like(vertical_lines)
        contours, _ = cv2.findContours(vertical_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        max_length = max((cv2.boundingRect(cnt)[3] for cnt in contours), default=0)
        min_length_threshold = int(max_length * 0.5)  # Giảm ngưỡng xuống 50%
        
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if h >= min_length_threshold:
                cv2.drawContours(filtered_vertical_lines, [cnt], -1, 255, -1)
        
        # Chiếu tổng theo trục y để tìm vị trí đường kẻ dọc
        v_projection = cv2.reduce(filtered_vertical_lines, 0, cv2.REDUCE_SUM, dtype=cv2.CV_32S)
        v_projection = v_projection.flatten()
        
        # Lọc nhiễu và tìm vị trí đường kẻ với ngưỡng thấp hơn
        line_positions = []
        threshold = height / 6  # Giảm ngưỡng để bắt được đường kẻ mờ
        
        for x in range(1, width - 1):
            if v_projection[x] > threshold:
                if (v_projection[x] >= v_projection[x-1] and 
                    v_projection[x] >= v_projection[x+1]):
                    line_positions.append(x)
        
        # Lọc đường kẻ gần nhau với khoảng cách nhỏ hơn
        filtered_positions = self._filter_close_lines(line_positions, min_distance=8)
        
        # Thêm biên với khoảng cách lớn hơn
        if filtered_positions and filtered_positions[0] > 30:
            filtered_positions.insert(0, 0)
        if filtered_positions and filtered_positions[-1] < width - 30:
            filtered_positions.append(width)
        
        filtered_positions.sort()
        return filtered_positions
    
    def detect_table_structure(self, table_image: np.ndarray) -> TableStructure:
        """Phát hiện cấu trúc bảng
        
        Args:
            table_image: Ảnh bảng
            
        Returns:
            TableStructure: Cấu trúc bảng đã phát hiện
        """
        # Tiền xử lý ảnh
        processed = self.preprocess_image(table_image)
        
        # Phát hiện đường kẻ ngang và dọc
        h_lines = self.detect_horizontal_lines(processed)
        v_lines = self.detect_vertical_lines(processed)
        
        # Phát hiện các ô trong bảng
        cells = []
        merged_cells = []
        header_rows = []
        
        # Duyệt qua các hàng
        for i in range(len(h_lines) - 1):
            y1, y2 = h_lines[i], h_lines[i+1]
            row_cells = []
            
            # Duyệt qua các cột
            for j in range(len(v_lines) - 1):
                x1, x2 = v_lines[j], v_lines[j+1]
                cell = (x1, y1, x2, y2)
                row_cells.append(cell)
                
                # Kiểm tra ô gộp ngang
                if j < len(v_lines) - 2:
                    cell_img = table_image[y1:y2, x1:x2]
                    next_cell_img = table_image[y1:y2, x2:v_lines[j+2]]
                    if self._is_merged_cell(cell_img, next_cell_img):
                        merged_cells.append((i, j, i, j+1, x1, y1))
                
                # Kiểm tra ô gộp dọc
                if i < len(h_lines) - 2:
                    cell_img = table_image[y1:y2, x1:x2]
                    next_cell_img = table_image[y2:h_lines[i+2], x1:x2]
                    if self._is_merged_cell(cell_img, next_cell_img):
                        merged_cells.append((i, j, i+1, j, x1, y1))
            
            cells.append(row_cells)
            
            # Phát hiện hàng tiêu đề
            if i == 0 or self._is_header_row(table_image[y1:y2, :]):
                header_rows.append(i)
        
        return TableStructure(h_lines, v_lines, cells, header_rows, merged_cells)
    
    def _is_merged_cell(self, cell1: np.ndarray, cell2: np.ndarray) -> bool:
        """Kiểm tra xem hai ô có được gộp không
        
        Args:
            cell1: Ảnh ô thứ nhất
            cell2: Ảnh ô thứ hai
            
        Returns:
            bool: True nếu hai ô được gộp
        """
        # Kiểm tra đường kẻ giữa hai ô
        if cell1.shape != cell2.shape:
            return False
            
        # Tính độ tương đồng giữa hai ô
        similarity = cv2.matchTemplate(cell1, cell2, cv2.TM_CCOEFF_NORMED)
        return similarity[0][0] > 0.8
    
    def _is_header_row(self, row_image: np.ndarray) -> bool:
        """Kiểm tra xem một hàng có phải là tiêu đề không
        
        Args:
            row_image: Ảnh của hàng
            
        Returns:
            bool: True nếu là hàng tiêu đề
        """
        # Chuyển sang ảnh xám
        if len(row_image.shape) == 3:
            gray = cv2.cvtColor(row_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = row_image
            
        # Tính độ tương phản và độ đậm của text
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        text_density = np.sum(binary == 255) / binary.size
        
        # Hàng tiêu đề thường có text đậm và mật độ cao
        return text_density > 0.1
    
    def extract_tables(self, image_path: str, 
                      min_table_area: int = 5000,
                      save_debug: bool = True) -> List[Tuple[np.ndarray, TableStructure]]:
        """Trích xuất tất cả các bảng từ ảnh
        
        Args:
            image_path: Đường dẫn đến ảnh
            min_table_area: Diện tích tối thiểu của bảng
            save_debug: Có lưu ảnh debug không
            
        Returns:
            List[Tuple[np.ndarray, TableStructure]]: Danh sách (ảnh bảng, cấu trúc bảng)
        """
        # Đọc ảnh
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Không thể đọc ảnh: {image_path}")
            
        # Phát hiện các bảng trong ảnh
        tables = self.detect_table(image)
        
        results = []
        for i, (x, y, w, h) in enumerate(tables):
            # Kiểm tra kích thước tối thiểu
            if w * h < min_table_area:
                continue
                
            # Cắt ảnh bảng
            table_img = image[y:y+h, x:x+w]
            
            # Phát hiện cấu trúc bảng
            structure = self.detect_table_structure(table_img)
            
            # Lưu ảnh debug
            if save_debug:
                debug_img = table_img.copy()
                self._draw_table_structure(debug_img, structure)
                debug_path = os.path.join(self.debug_dir, f"table_{i}.jpg")
                cv2.imwrite(debug_path, debug_img)
            
            results.append((table_img, structure))
            
        return results
    
    def _draw_table_structure(self, image: np.ndarray, structure: TableStructure):
        """Vẽ cấu trúc bảng lên ảnh để debug
        
        Args:
            image: Ảnh cần vẽ
            structure: Cấu trúc bảng
        """
        # Vẽ đường kẻ ngang
        for y in structure.horizontal_lines:
            cv2.line(image, (0, y), (image.shape[1], y), (0, 255, 0), 2)
            
        # Vẽ đường kẻ dọc
        for x in structure.vertical_lines:
            cv2.line(image, (x, 0), (x, image.shape[0]), (255, 0, 0), 2)
            
        # Đánh dấu ô gộp
        for r1, c1, r2, c2, x, y in structure.merged_cells:
            cv2.rectangle(image, (x, y), 
                        (structure.vertical_lines[c2+1], structure.horizontal_lines[r2+1]),
                        (0, 0, 255), 2)
            
        # Đánh dấu hàng tiêu đề
        for row_idx in structure.header_rows:
            y1 = structure.horizontal_lines[row_idx]
            y2 = structure.horizontal_lines[row_idx + 1]
            cv2.rectangle(image, (0, y1), (image.shape[1], y2), (255, 255, 0), 2)

    def process_image(self, image_path: str, margin: int = 5, check_text: bool = True) -> List[np.ndarray]:
        """Xử lý ảnh và trích xuất các bảng
        
        Args:
            image_path: Đường dẫn tới ảnh cần xử lý
            margin: Kích thước lề (pixel)
            check_text: Có kiểm tra text trong hàng hay không
            
        Returns:
            List[np.ndarray]: Danh sách các bảng đã trích xuất
        """
        try:
            # Đọc ảnh
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Không thể đọc ảnh {image_path}")
                return []
            
            # Phát hiện các bảng
            tables = self.detect_table(image)
            logger.info(f"Đã phát hiện {len(tables)} bảng")
            
            # Trích xuất và lưu các bảng
            extracted_tables = []
            for i, (x1, y1, x2, y2) in enumerate(tables):
                # Cắt bảng từ ảnh gốc
                table = image[y1:y2, x1:x2]
                
                # Thêm lề nếu cần
                if margin > 0:
                    h, w = table.shape[:2]
                    table_with_margin = np.ones((h + 2*margin, w + 2*margin, 3), dtype=np.uint8) * 255
                    table_with_margin[margin:margin+h, margin:margin+w] = table
                    table = table_with_margin
                
                # Lưu bảng
                output_path = os.path.join(self.output_dir, f"table_{i}.jpg")
                cv2.imwrite(output_path, table)
                logger.info(f"Đã lưu bảng {i} vào {output_path}")
                
                extracted_tables.append(table)
            
            return extracted_tables
            
        except Exception as e:
            logger.error(f"Lỗi khi xử lý ảnh {image_path}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    def detect_table(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Phát hiện bảng trong ảnh"""
        # Chuyển sang ảnh xám
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Áp dụng threshold
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Lưu ảnh binary để debug
        debug_binary_path = os.path.join(self.debug_dir, "binary.jpg")
        cv2.imwrite(debug_binary_path, binary)
        logger.info(f"Đã lưu ảnh binary vào {debug_binary_path}")
        
        # Áp dụng morphology để nối các thành phần liền kề
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))  # Tăng kích thước kernel
        morph = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)  # Giảm số lần lặp
        
        # Lưu ảnh sau morphology để debug
        debug_morph_path = os.path.join(self.debug_dir, "morph.jpg")
        cv2.imwrite(debug_morph_path, morph)
        logger.info(f"Đã lưu ảnh sau morphology vào {debug_morph_path}")
        
        # Tìm contour
        contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        logger.info(f"Đã tìm thấy {len(contours)} contour")
        
        # Vẽ tất cả contour lên ảnh để debug
        debug_contours = image.copy()
        cv2.drawContours(debug_contours, contours, -1, (0, 255, 0), 2)
        debug_contours_path = os.path.join(self.debug_dir, "all_contours.jpg")
        cv2.imwrite(debug_contours_path, debug_contours)
        logger.info(f"Đã lưu ảnh contour vào {debug_contours_path}")
        
        # Lọc các contour theo kích thước
        h, w = image.shape[:2]
        min_area = 0.03 * h * w  # Giảm diện tích tối thiểu xuống 3%
        logger.info(f"Diện tích tối thiểu của bảng: {min_area:.0f} pixel")
        
        table_boxes = []
        debug_filtered = image.copy()
        
        for i, cnt in enumerate(contours):
            area = cv2.contourArea(cnt)
            logger.info(f"Contour {i}: diện tích = {area:.0f} pixel")
            
            if area < min_area:
                continue
            
            # Tính bounding rectangle
            x, y, width, height = cv2.boundingRect(cnt)
            aspect_ratio = width / height
            logger.info(f"Contour {i}: tỷ lệ khung = {aspect_ratio:.2f}")
            
            # Mở rộng phạm vi tỷ lệ khung hình
            if 0.1 <= aspect_ratio <= 10.0:  # Mở rộng phạm vi chấp nhận
                table_boxes.append((x, y, x + width, y + height))
                cv2.rectangle(debug_filtered, (x, y), (x + width, y + height), (0, 0, 255), 3)
                logger.info(f"Đã thêm bảng {len(table_boxes)}: ({x}, {y}, {width}, {height})")
        
        # Lưu ảnh debug với các contour đã lọc
        debug_filtered_path = os.path.join(self.debug_dir, "filtered_tables.jpg")
        cv2.imwrite(debug_filtered_path, debug_filtered)
        logger.info(f"Đã lưu ảnh bảng đã lọc vào {debug_filtered_path}")
        
        # Nếu không phát hiện được bảng, coi toàn bộ ảnh là một bảng
        if not table_boxes:
            logger.info("Không phát hiện được bảng, coi toàn bộ ảnh là một bảng")
            table_boxes = [(0, 0, w, h)]
            cv2.rectangle(debug_filtered, (0, 0), (w, h), (0, 0, 255), 3)
            debug_fallback_path = os.path.join(self.debug_dir, "fallback_table.jpg")
            cv2.imwrite(debug_fallback_path, debug_filtered)
        
        logger.info(f"Đã phát hiện {len(table_boxes)} bảng")
        return table_boxes

def main():
    """Hàm chính"""
    parser = argparse.ArgumentParser(description='Trích xuất bảng từ ảnh')
    
    parser.add_argument('image', type=str,
                        help='Đường dẫn tới ảnh cần xử lý')
    
    parser.add_argument('--output', type=str, default='output/tables',
                        help='Thư mục lưu các bảng đã trích xuất (mặc định: output/tables)')
    
    parser.add_argument('--debug', type=str, default='debug/tables',
                        help='Thư mục lưu ảnh debug (mặc định: debug/tables)')
    
    parser.add_argument('--margin', type=int, default=5,
                        help='Kích thước lề cho bảng (mặc định: 5px)')
    
    parser.add_argument('--no-check-text', action='store_true',
                        help='Không kiểm tra text trong hàng')
    
    args = parser.parse_args()
    
    # Tạo các thư mục nếu chưa tồn tại
    os.makedirs(os.path.dirname(args.image), exist_ok=True)
    os.makedirs(args.output, exist_ok=True)
    os.makedirs(args.debug, exist_ok=True)
    
    # Tạo đối tượng AdvancedTableExtractor
    extractor = AdvancedTableExtractor(
        input_dir=os.path.dirname(args.image),
        output_dir=args.output,
        debug_dir=args.debug
    )
    
    # Xử lý ảnh
    tables = extractor.process_image(
        image_path=args.image,
        margin=args.margin,
        check_text=not args.no_check_text
    )
    
    print(f"Đã phát hiện {len(tables)} bảng")

if __name__ == "__main__":
    main() 
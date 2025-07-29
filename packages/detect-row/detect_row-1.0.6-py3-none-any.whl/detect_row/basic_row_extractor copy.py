import os
import cv2
import numpy as np
import logging
import argparse
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List, Tuple, Dict, Any

from .base import BaseRowExtractor, logger

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('table_row_extractor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BasicRowExtractor(BaseRowExtractor):
    """Lớp phát hiện đường kẻ ngang và cắt các hàng trong bảng"""
    
    def __init__(self, input_dir="input", output_dir="output/rows", debug_dir="debug/lines"):
        """Khởi tạo BasicRowExtractor
        """
        super().__init__(input_dir, output_dir, debug_dir)
        
        # Tạo thư mục output và debug nếu chưa tồn tại
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(debug_dir, exist_ok=True)
        
        logger.info(f"Đã khởi tạo BasicRowExtractor - Input dir: {input_dir}, Output dir: {output_dir}")
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Tiền xử lý ảnh để tăng độ tương phản và làm nổi bật đường kẻ ngang
        
        Args:
            image: Ảnh đầu vào (numpy array)
            
        Returns:
            np.ndarray: Ảnh đã xử lý
        """
        # Chuyển sang ảnh xám
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Tăng cường độ tương phản
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Áp dụng threshold để làm nổi bật đường kẻ ngang
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Áp dụng Gaussian blur để giảm nhiễu
        blurred = cv2.GaussianBlur(binary, (5, 5), 0)
        
        # Lưu ảnh đã xử lý để debug
        debug_path = os.path.join(self.debug_dir, "preprocessed.jpg")
        cv2.imwrite(debug_path, blurred)
        
        return blurred
    
    def detect_horizontal_lines(self, image: np.ndarray, min_line_length_ratio: float = 2/3) -> List[int]:
        """Phát hiện các đường kẻ ngang trong ảnh
        
        Args:
            image: Ảnh đã tiền xử lý
            min_line_length_ratio: Tỷ lệ tối thiểu của chiều dài đường kẻ so với chiều rộng ảnh
            
        Returns:
            List[int]: Danh sách các tọa độ y của đường kẻ ngang
        """
        # Kích thước ảnh
        height, width = image.shape[:2]
        
        # Tính chiều dài tối thiểu của đường kẻ
        min_line_length = int(width * min_line_length_ratio)
        logger.info(f"Chiều dài tối thiểu của đường kẻ ngang: {min_line_length}px (={min_line_length_ratio:.2f} × {width}px)")
        
        # Tạo kernel ngang để phát hiện đường kẻ ngang
        # Dùng kernel dài hơn để bắt các đường kẻ dài
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (min_line_length // 10, 1))
        
        # Áp dụng phép toán mở để phát hiện đường kẻ ngang
        horizontal_lines = cv2.morphologyEx(image, cv2.MORPH_OPEN, horizontal_kernel, iterations=3)
        
        # Lọc các đường ngang có chiều dài nhỏ hơn 70% đường dài nhất
        filtered_horizontal_lines = np.zeros_like(horizontal_lines)
        contours, _ = cv2.findContours(horizontal_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Tìm chiều dài lớn nhất của đường kẻ
        max_length = 0
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            max_length = max(max_length, w)
        
        # Lọc các đường kẻ có chiều dài lớn hơn 70% đường dài nhất
        min_length_threshold = int(max_length * 0.7)
        logger.info(f"Chiều dài tối thiểu của đường kẻ (70% đường dài nhất): {min_length_threshold}px")
        
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w >= min_length_threshold:
                # Vẽ đường kẻ đã lọc vào ảnh mới
                cv2.drawContours(filtered_horizontal_lines, [cnt], -1, 255, -1)
        
        # Làm dày đường kẻ để dễ phát hiện
        dilate_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (min_line_length // 20, 3))
        filtered_horizontal_lines = cv2.dilate(filtered_horizontal_lines, dilate_kernel, iterations=2)
        
        # Lưu ảnh đường kẻ ngang gốc và đã lọc để debug
        debug_path_original = os.path.join(self.debug_dir, "horizontal_lines_original.jpg")
        cv2.imwrite(debug_path_original, horizontal_lines)
        
        debug_path_filtered = os.path.join(self.debug_dir, "horizontal_lines.jpg")
        cv2.imwrite(debug_path_filtered, filtered_horizontal_lines)
        
        # Phát hiện đường kẻ ngang bằng histogram theo phương ngang
        # Chiếu tổng theo trục x để tìm vị trí các đường kẻ ngang
        h_projection = cv2.reduce(filtered_horizontal_lines, 1, cv2.REDUCE_SUM, dtype=cv2.CV_32S)
        
        # Chuẩn hóa histogram
        h_projection = h_projection / 255
        
        # Tìm giá trị lớn nhất trong histogram để lọc
        max_projection_value = np.max(h_projection)
        threshold_value = max_projection_value * 0.5  # Lọc giá trị < 50% đỉnh cao nhất
        logger.info(f"Giá trị ngưỡng lọc histogram (50% giá trị lớn nhất): {threshold_value:.2f}")
        
        # Áp dụng ngưỡng để lọc histogram
        filtered_projection = np.copy(h_projection)
        filtered_projection[filtered_projection < threshold_value] = 0
        
        # Lưu histogram gốc để debug
        plt.figure(figsize=(10, height // 50))
        plt.plot(h_projection, range(height), color='blue', alpha=0.5, label='Original')
        plt.plot(filtered_projection, range(height), color='red', label='Filtered (>50%)')
        plt.axhline(y=threshold_value, color='green', linestyle='--', label=f'Threshold (50%): {threshold_value:.2f}')
        plt.gca().invert_yaxis()  # Đảo ngược trục y để phù hợp với tọa độ ảnh
        plt.title('Horizontal Projection Histogram')
        plt.legend()
        plt.savefig(os.path.join(self.debug_dir, 'h_projection.png'), bbox_inches='tight')
        plt.close()
        
        # Lưu histogram đã lọc để debug
        plt.figure(figsize=(10, height // 50))
        plt.plot(filtered_projection, range(height), color='red')
        plt.gca().invert_yaxis()  # Đảo ngược trục y để phù hợp với tọa độ ảnh
        plt.title('Filtered Horizontal Projection (>50%)')
        plt.savefig(os.path.join(self.debug_dir, 'h_projection_filtered.png'), bbox_inches='tight')
        plt.close()
        
        # Tìm vị trí các đỉnh trong histogram
        line_positions = []
        threshold = width / 5  # Ngưỡng cơ bản để xác định đường kẻ ngang
        
        for y in range(1, height - 1):
            # Sử dụng histogram đã lọc
            if filtered_projection[y] > threshold:
                # Kiểm tra xem có phải đỉnh cục bộ không
                if filtered_projection[y] >= filtered_projection[y-1] and filtered_projection[y] >= filtered_projection[y+1]:
                    line_positions.append(y)
                    continue
                    
                # Hoặc vẫn là phần của đường kẻ
                is_peak = True
                for i in range(1, 3):  # Kiểm tra 3 pixel lân cận
                    if y + i < height and filtered_projection[y] < filtered_projection[y+i]:
                        is_peak = False
                        break
                    if y - i >= 0 and filtered_projection[y] < filtered_projection[y-i]:
                        is_peak = False
                        break
                
                if is_peak:
                    line_positions.append(y)
        
        # Lọc các đường kẻ quá gần nhau
        filtered_positions = self._filter_close_lines(line_positions, min_distance=10)
        
        # Thêm vị trí đầu và cuối ảnh
        if len(filtered_positions) > 0 and filtered_positions[0] > 20:
            filtered_positions.insert(0, 0)
        if len(filtered_positions) > 0 and filtered_positions[-1] < height - 20:
            filtered_positions.append(height)
        
        # Sắp xếp lại các vị trí
        filtered_positions.sort()
        
        # Vẽ các đường kẻ ngang lên ảnh để debug
        debug_image = cv2.cvtColor(image.copy(), cv2.COLOR_GRAY2BGR)
        for y in filtered_positions:
            cv2.line(debug_image, (0, y), (width, y), (0, 0, 255), 2)
        
        debug_lines_path = os.path.join(self.debug_dir, "detected_lines.jpg")
        cv2.imwrite(debug_lines_path, debug_image)
        
        logger.info(f"Đã phát hiện {len(filtered_positions)} đường kẻ ngang sau khi lọc")
        return filtered_positions
    
    def _filter_close_lines(self, line_positions: List[int], min_distance: int = 10) -> List[int]:
        """Lọc các đường kẻ ngang quá gần nhau
        
        Args:
            line_positions: Danh sách các tọa độ y của đường kẻ
            min_distance: Khoảng cách tối thiểu giữa các đường kẻ
            
        Returns:
            List[int]: Danh sách các tọa độ y của đường kẻ sau khi lọc
        """
        if not line_positions:
            return []
        
        # Sắp xếp các vị trí
        sorted_positions = sorted(line_positions)
        
        # Giữ lại đường kẻ đầu tiên
        filtered = [sorted_positions[0]]
        
        for i in range(1, len(sorted_positions)):
            # Nếu khoảng cách với đường kẻ trước đó đủ lớn
            if sorted_positions[i] - filtered[-1] >= min_distance:
                filtered.append(sorted_positions[i])
        
        return filtered
    
    def _has_text(self, image: np.ndarray, threshold_ratio: float = 0.005) -> bool:
        """Kiểm tra xem ảnh có chứa text hay không
        
        Args:
            image: Ảnh cần kiểm tra
            threshold_ratio: Tỷ lệ ngưỡng để xác định có text (tỷ lệ pixel trắng sau khi threshold)
            
        Returns:
            bool: True nếu có text, False nếu không có
        """
        # Chuyển sang ảnh xám
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Áp dụng threshold để tách text (giả định text là tối, nền là sáng)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Đếm số pixel trắng (pixel text)
        white_pixels = np.sum(binary == 255)
        total_pixels = binary.size
        
        # Tính tỷ lệ
        white_ratio = white_pixels / total_pixels
        
        # Kiểm tra có text hay không
        return white_ratio > threshold_ratio

    def extract_rows_from_table(self, table_image: np.ndarray, table_id: int) -> List[np.ndarray]:
        """Cắt các hàng từ ảnh bảng dựa trên đường kẻ ngang
        
        Args:
            table_image: Ảnh bảng
            table_id: ID của bảng
            
        Returns:
            List[np.ndarray]: Danh sách các ảnh hàng đã cắt
        """
        # Tiền xử lý ảnh
        processed = self.preprocess_image(table_image)
        
        # Phát hiện các đường kẻ ngang
        line_positions = self.detect_horizontal_lines(processed)
        
        # Nếu không phát hiện được đường kẻ nào
        if len(line_positions) <= 1:
            logger.warning("Không phát hiện được đủ đường kẻ ngang, dùng phương pháp dự phòng")
            return self._extract_rows_fallback(table_image, table_id)
        
        # Lấy kích thước ảnh
        height, width = table_image.shape[:2]
        
        # Tạo ảnh debug
        debug_image = table_image.copy()
        
        # Cắt các hàng dựa trên vị trí các đường kẻ
        rows = []
        empty_rows_count = 0
        
        for i in range(len(line_positions) - 1):
            # Vị trí đường kẻ trên và dưới
            y_top = max(0, line_positions[i] - 3)  # Thêm lề 3px ở trên
            y_bottom = min(height, line_positions[i + 1] + 10)  # Thêm lề 10px ở dưới
            
            # Đảm bảo chiều cao hàng đủ lớn
            if y_bottom - y_top < 5:
                continue
            
            # Cắt hàng từ ảnh gốc
            row = table_image[y_top:y_bottom, 0:width]
            
            # Kiểm tra xem hàng có chứa text không
            has_text = self._has_text(row)
            
            if not has_text:
                empty_rows_count += 1
                logger.warning(f"Cảnh báo: Hàng {i+1} của bảng {table_id} không có text")
                # Vẽ bounding box với màu khác để đánh dấu hàng không có text
                cv2.rectangle(debug_image, (0, y_top), (width, y_bottom), (0, 0, 255), 2)
                cv2.putText(debug_image, f"Empty Row {i+1}", (10, y_top+20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                # Vẽ bounding box lên ảnh debug
                cv2.rectangle(debug_image, (0, y_top), (width, y_bottom), (0, 255, 0), 2)
                cv2.putText(debug_image, f"Row {i+1}", (10, y_top+20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            rows.append(row)
        
        # Lưu ảnh debug
        debug_path = os.path.join(self.debug_dir, f"table_{table_id}_rows.jpg")
        cv2.imwrite(debug_path, debug_image)
        
        if empty_rows_count > 0:
            logger.warning(f"Cảnh báo: Có {empty_rows_count}/{len(rows)} hàng không có text trong bảng {table_id}")
        
        logger.info(f"Đã cắt {len(rows)} hàng từ bảng {table_id}")
        return rows
    
    def _extract_rows_fallback(self, table_image: np.ndarray, table_id: int) -> List[np.ndarray]:
        """Phương pháp dự phòng để cắt các hàng khi không phát hiện được đường kẻ ngang
        
        Args:
            table_image: Ảnh bảng
            table_id: ID của bảng
            
        Returns:
            List[np.ndarray]: Danh sách các ảnh hàng đã cắt
        """
        # Chuyển sang ảnh xám
        gray = cv2.cvtColor(table_image, cv2.COLOR_BGR2GRAY)
        
        # Áp dụng threshold
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Tính histogram theo phương ngang
        h_projection = cv2.reduce(binary, 1, cv2.REDUCE_SUM, dtype=cv2.CV_32S)
        
        # Chuẩn hóa histogram
        h_projection = h_projection / 255
        
        # Lưu histogram để debug
        height, width = table_image.shape[:2]
        plt.figure(figsize=(10, height // 50))
        plt.plot(h_projection, range(height), color='black')
        plt.gca().invert_yaxis()
        plt.title('Fallback Horizontal Projection')
        plt.savefig(os.path.join(self.debug_dir, f'table_{table_id}_fallback_projection.png'), bbox_inches='tight')
        plt.close()
        
        # Tìm các khoảng trống (vùng có ít text) dựa trên histogram
        row_boundaries = []
        threshold = width / 10
        
        for y in range(1, height - 1):
            if h_projection[y] < threshold and h_projection[y-1] >= threshold:
                row_boundaries.append(y)
            elif h_projection[y] < threshold and h_projection[y+1] >= threshold:
                row_boundaries.append(y)
        
        # Nếu không tìm thấy khoảng trống, chia đều ảnh
        if len(row_boundaries) <= 1:
            logger.warning(f"Không tìm thấy khoảng trống, chia đều bảng {table_id} thành 10 hàng")
            row_height = height // 10
            row_boundaries = [i * row_height for i in range(11)]
        else:
            # Thêm vị trí đầu và cuối ảnh
            if row_boundaries[0] > 10:
                row_boundaries.insert(0, 0)
            if row_boundaries[-1] < height - 10:
                row_boundaries.append(height)
            
            # Sắp xếp lại
            row_boundaries.sort()
        
        # Cắt các hàng
        rows = []
        debug_image = table_image.copy()
        empty_rows_count = 0
        
        for i in range(len(row_boundaries) - 1):
            y_top = max(0, row_boundaries[i] - 3)  # Thêm lề 3px ở trên
            y_bottom = min(height, row_boundaries[i + 1] + 10)  # Thêm lề 10px ở dưới
            
            # Đảm bảo chiều cao hàng đủ lớn
            if y_bottom - y_top < 5:
                continue
            
            # Cắt hàng
            row = table_image[y_top:y_bottom, 0:width]
            
            # Kiểm tra xem hàng có chứa text không
            has_text = self._has_text(row)
            
            if not has_text:
                empty_rows_count += 1
                logger.warning(f"Cảnh báo: Hàng {i+1} của bảng {table_id} (fallback) không có text")
                # Vẽ bounding box với màu khác để đánh dấu hàng không có text
                cv2.rectangle(debug_image, (0, y_top), (width, y_bottom), (0, 0, 255), 2)
                cv2.putText(debug_image, f"Empty Row {i+1}", (10, y_top+20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            else:
                # Vẽ bounding box lên ảnh debug
                cv2.rectangle(debug_image, (0, y_top), (width, y_bottom), (0, 255, 0), 2)
                cv2.putText(debug_image, f"Row {i+1}", (10, y_top+20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            
            rows.append(row)
        
        # Lưu ảnh debug
        debug_path = os.path.join(self.debug_dir, f"table_{table_id}_fallback_rows.jpg")
        cv2.imwrite(debug_path, debug_image)
        
        if empty_rows_count > 0:
            logger.warning(f"Cảnh báo: Có {empty_rows_count}/{len(rows)} hàng không có text trong bảng {table_id} (fallback)")
        
        logger.info(f"Đã cắt {len(rows)} hàng từ bảng {table_id} bằng phương pháp dự phòng")
        return rows 
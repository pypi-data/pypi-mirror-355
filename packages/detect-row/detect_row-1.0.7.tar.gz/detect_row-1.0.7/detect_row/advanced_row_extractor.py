import os
import cv2
import numpy as np
import logging
import argparse
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Sửa import để hoạt động trong cả môi trường development và production
try:
    from .base import BaseRowExtractor, logger
except ImportError:
    from detect_row.base import BaseRowExtractor, logger

class AdvancedRowExtractor(BaseRowExtractor):
    """Lớp phát hiện đường kẻ ngang và cắt các hàng trong bảng"""
    
    def __init__(self, input_dir="input", output_dir="output/advanced_rows", debug_dir="debug/lines"):
        """Khởi tạo AdvancedRowExtractor
        
        Args:
            input_dir: Thư mục chứa ảnh đầu vào
            output_dir: Thư mục lưu các hàng đã cắt
            debug_dir: Thư mục lưu ảnh debug
        """
        super().__init__(input_dir, output_dir, debug_dir)
    
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
        
        # Lọc các đường kẻ có chiều dài lớn hơn 90% đường dài nhất
        min_length_threshold = int(max_length * 0.9)
        logger.info(f"Chiều dài tối thiểu của đường kẻ (90% đường dài nhất): {min_length_threshold}px")
        
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
    
    def extract_rows_from_table(self, table_image: np.ndarray, table_id: int, check_text: bool = True, min_row_height: int = 20) -> List[np.ndarray]:
        """Cắt các hàng từ ảnh bảng dựa trên đường kẻ ngang
        
        Args:
            table_image: Ảnh bảng
            table_id: ID của bảng
            check_text: Có kiểm tra text trong hàng hay không
            min_row_height: Chiều cao tối thiểu của hàng (pixel)
            
        Returns:
            List[np.ndarray]: Danh sách các ảnh hàng đã cắt
        """
        # Tiền xử lý ảnh
        processed = self.preprocess_image(table_image)
        
        # Phát hiện các đường kẻ ngang
        line_positions = self.detect_horizontal_lines(processed)
        
        # Lấy kích thước ảnh
        height, width = table_image.shape[:2]
        
        # Điều chỉnh min_row_height dựa trên chiều cao bảng (1/30 chiều cao)
        adaptive_min_row_height = max(int(height / 30), 10)  # Đảm bảo ít nhất 10px
        logger.info(f"Điều chỉnh min_row_height: {adaptive_min_row_height}px (1/30 chiều cao bảng)")
        
        # Sử dụng giá trị thích ứng thay vì tham số đầu vào
        min_row_height = adaptive_min_row_height
        
        # Nếu không phát hiện được đường kẻ nào
        if len(line_positions) <= 1:
            logger.warning("Không phát hiện được đủ đường kẻ ngang, dùng phương pháp dự phòng")
            return self._extract_rows_fallback(table_image, table_id, check_text, min_row_height)
        
        # Tạo ảnh debug
        debug_image = table_image.copy()
        
        # Cắt các hàng dựa trên vị trí các đường kẻ
        rows = []
        empty_rows_count = 0
        skipped_small_rows_count = 0
        
        # Bỏ qua hàng đầu tiên bằng cách bắt đầu từ i = 1
        for i in range(1, len(line_positions) - 1):
            # Vị trí đường kẻ trên và dưới
            y_top = max(0, line_positions[i] + 7)  # Thêm lề 3px ở trên
            y_bottom = min(height, line_positions[i + 1] + 0)  # Thêm lề 10px ở dưới
            
            # Vị trí trái phải của hàng
            x_left = max(0, 10)  # Cách lề trái 55px
            x_right = min(width, width - 10)  # Cách lề phải 65px
            
            # Kiểm tra chiều cao hàng, bỏ qua nếu quá nhỏ
            row_height = y_bottom - y_top
            if row_height < min_row_height:
                logger.warning(f"Bỏ qua hàng {i+1} của bảng {table_id} do chiều cao quá nhỏ: {row_height}px < {min_row_height}px")
                skipped_small_rows_count += 1
                # Vẽ bounding box với màu khác để đánh dấu hàng bị bỏ qua do quá nhỏ
                cv2.rectangle(debug_image, (x_left, y_top), (x_right, y_bottom), (255, 0, 255), 2)  # Màu tím
                cv2.putText(debug_image, f"Small Row {i+1} ({row_height}px)", (x_left+10, y_top+20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
                continue
            
            # Cắt hàng từ ảnh gốc với vị trí x_left và x_right
            row = table_image[y_top:y_bottom, x_left:x_right]
            
            # Kiểm tra xem hàng có chứa text không
            has_text = self._has_text(row) if check_text else True
            
            if not has_text:
                empty_rows_count += 1
                logger.warning(f"Cảnh báo: Hàng {i+1} của bảng {table_id} không có text")
                # Vẽ bounding box với màu khác để đánh dấu hàng không có text
                cv2.rectangle(debug_image, (x_left, y_top), (x_right, y_bottom), (0, 0, 255), 2)
                cv2.putText(debug_image, f"Empty Row {i+1}", (x_left+10, y_top+20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                # Vẽ bounding box lên ảnh debug
                cv2.rectangle(debug_image, (x_left, y_top), (x_right, y_bottom), (0, 255, 0), 2)
                cv2.putText(debug_image, f"Row {i+1} ({row_height}px)", (x_left+10, y_top+20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            rows.append(row)
        
        # Lưu ảnh debug
        debug_path = os.path.join(self.debug_dir, f"table_{table_id}_rows.jpg")
        cv2.imwrite(debug_path, debug_image)
        
        if empty_rows_count > 0:
            logger.warning(f"Cảnh báo: Có {empty_rows_count}/{len(rows)} hàng không có text trong bảng {table_id}")
        
        if skipped_small_rows_count > 0:
            logger.warning(f"Cảnh báo: Đã bỏ qua {skipped_small_rows_count} hàng có chiều cao < {min_row_height}px trong bảng {table_id}")
        
        logger.info(f"Đã cắt {len(rows)} hàng từ bảng {table_id} (đã bỏ qua hàng đầu tiên)")
        return rows
    
    def _extract_rows_fallback(self, table_image: np.ndarray, table_id: int, check_text: bool = True, min_row_height: int = 20) -> List[np.ndarray]:
        """Phương pháp dự phòng để cắt các hàng khi không phát hiện được đường kẻ ngang
        
        Args:
            table_image: Ảnh bảng
            table_id: ID của bảng
            check_text: Có kiểm tra text trong hàng hay không
            min_row_height: Chiều cao tối thiểu của hàng (pixel)
            
        Returns:
            List[np.ndarray]: Danh sách các ảnh hàng đã cắt
        """
        # Lấy kích thước ảnh
        height, width = table_image.shape[:2]
        
        # Điều chỉnh min_row_height dựa trên chiều cao bảng (1/30 chiều cao)
        adaptive_min_row_height = max(int(height / 30), 10)  # Đảm bảo ít nhất 10px
        logger.info(f"Phương pháp dự phòng - Điều chỉnh min_row_height: {adaptive_min_row_height}px (1/30 chiều cao bảng)")
        
        # Sử dụng giá trị thích ứng thay vì tham số đầu vào
        min_row_height = adaptive_min_row_height
        
        # Chuyển sang ảnh xám
        gray = cv2.cvtColor(table_image, cv2.COLOR_BGR2GRAY)
        
        # Áp dụng threshold
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Tính histogram theo phương ngang
        h_projection = cv2.reduce(binary, 1, cv2.REDUCE_SUM, dtype=cv2.CV_32S)
        
        # Chuẩn hóa histogram
        h_projection = h_projection / 255
        
        # Lưu histogram để debug
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
        skipped_small_rows_count = 0
        
        # Vị trí trái phải của hàng
        x_left = max(0, 55)  # Cách lề trái 55px
        x_right = min(width, width - 65)  # Cách lề phải 65px
        
        # Bỏ qua hàng đầu tiên bằng cách bắt đầu từ i = 1
        for i in range(1, len(row_boundaries) - 1):
            y_top = max(0, row_boundaries[i] - 3)  # Thêm lề 3px ở trên
            y_bottom = min(height, row_boundaries[i + 1] + 10)  # Thêm lề 10px ở dưới
            
            # Kiểm tra chiều cao hàng, bỏ qua nếu quá nhỏ
            row_height = y_bottom - y_top
            if row_height < min_row_height:
                logger.warning(f"Bỏ qua hàng {i+1} của bảng {table_id} (fallback) do chiều cao quá nhỏ: {row_height}px < {min_row_height}px")
                skipped_small_rows_count += 1
                # Vẽ bounding box với màu khác để đánh dấu hàng bị bỏ qua do quá nhỏ
                cv2.rectangle(debug_image, (x_left, y_top), (x_right, y_bottom), (255, 0, 255), 2)  # Màu tím
                cv2.putText(debug_image, f"Small Row {i+1} ({row_height}px)", (x_left+10, y_top+20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
                continue
            
            # Cắt hàng với vị trí x_left và x_right
            row = table_image[y_top:y_bottom, x_left:x_right]
            
            # Kiểm tra xem hàng có chứa text không
            has_text = self._has_text(row) if check_text else True
            
            if not has_text:
                empty_rows_count += 1
                logger.warning(f"Cảnh báo: Hàng {i+1} của bảng {table_id} (fallback) không có text")
                # Vẽ bounding box với màu khác để đánh dấu hàng không có text
                cv2.rectangle(debug_image, (x_left, y_top), (x_right, y_bottom), (0, 0, 255), 2)
                cv2.putText(debug_image, f"Empty Row {i+1}", (x_left+10, y_top+20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            else:
                # Vẽ bounding box lên ảnh debug
                cv2.rectangle(debug_image, (x_left, y_top), (x_right, y_bottom), (0, 255, 0), 2)
                cv2.putText(debug_image, f"Row {i+1} ({row_height}px)", (x_left+10, y_top+20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            
            rows.append(row)
        
        # Lưu ảnh debug
        debug_path = os.path.join(self.debug_dir, f"table_{table_id}_fallback_rows.jpg")
        cv2.imwrite(debug_path, debug_image)
        
        if empty_rows_count > 0:
            logger.warning(f"Cảnh báo: Có {empty_rows_count}/{len(rows)} hàng không có text trong bảng {table_id} (fallback)")
        
        if skipped_small_rows_count > 0:
            logger.warning(f"Cảnh báo: Đã bỏ qua {skipped_small_rows_count} hàng có chiều cao < {min_row_height}px trong bảng {table_id} (fallback)")
        
        logger.info(f"Đã cắt {len(rows)} hàng từ bảng {table_id} bằng phương pháp dự phòng (đã bỏ qua hàng đầu tiên)")
        return rows

class AdvancedRowExtractorMain(AdvancedRowExtractor):
    """Lớp mở rộng AdvancedRowExtractor với phương thức phát hiện bảng"""
    
    def detect_table(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Phát hiện bảng trong ảnh
        
        Args:
            image: Ảnh đầu vào
            
        Returns:
            List[Tuple[int, int, int, int]]: Danh sách các bounding box của bảng [x1, y1, x2, y2]
        """
        # Chuyển sang ảnh xám
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Áp dụng threshold
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Áp dụng morphology để nối các thành phần liền kề
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=3)
        
        # Lưu ảnh đã xử lý để debug
        debug_path = os.path.join(self.debug_dir, "table_detection_binary.jpg")
        cv2.imwrite(debug_path, binary)
        
        # Tìm contour
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Vẽ tất cả contour lên ảnh để debug
        debug_contours = image.copy()
        cv2.drawContours(debug_contours, contours, -1, (0, 255, 0), 2)
        debug_contours_path = os.path.join(self.debug_dir, "all_contours.jpg")
        cv2.imwrite(debug_contours_path, debug_contours)
        
        # Lọc các contour theo kích thước
        h, w = image.shape[:2]
        min_area = 0.05 * h * w  # Diện tích tối thiểu (5% diện tích ảnh)
        
        table_boxes = []
        debug_filtered = image.copy()
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            
            if area < min_area:
                continue
                
            # Tính bounding rectangle
            x, y, width, height = cv2.boundingRect(cnt)
            
            # Kiểm tra tỷ lệ khung hình
            aspect_ratio = width / height
            
            if 0.2 <= aspect_ratio <= 5.0:
                table_boxes.append((x, y, x + width, y + height))
                cv2.rectangle(debug_filtered, (x, y), (x + width, y + height), (0, 0, 255), 3)
        
        # Nếu không phát hiện được bảng, coi toàn bộ ảnh là một bảng
        if not table_boxes:
            logger.info("Không phát hiện được bảng, coi toàn bộ ảnh là một bảng")
            table_boxes = [(0, 0, w, h)]
            cv2.rectangle(debug_filtered, (0, 0), (w, h), (0, 0, 255), 3)
        
        # Lưu ảnh debug với các contour đã lọc
        debug_filtered_path = os.path.join(self.debug_dir, "filtered_tables.jpg")
        cv2.imwrite(debug_filtered_path, debug_filtered)
        
        logger.info(f"Đã phát hiện {len(table_boxes)} bảng trong ảnh")
        return table_boxes
    
    def process_image(self, image_path, add_margin=False, margin=5, check_text=True, min_row_height=20):
        """Xử lý ảnh và trích xuất các hàng
        
        Args:
            image_path: Đường dẫn tới ảnh cần xử lý
            add_margin: Có thêm lề cho các hàng được trích xuất hay không
            margin: Kích thước lề (pixel)
            check_text: Có kiểm tra text trong hàng hay không
            min_row_height: Chiều cao tối thiểu của hàng (pixel)
            
        Returns:
            List[np.ndarray]: Danh sách các hàng đã trích xuất
        """
        try:
            # Đọc ảnh
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Không thể đọc ảnh {image_path}")
                return []
                
            # Lấy tên file không có phần mở rộng
            file_name = os.path.splitext(os.path.basename(image_path))[0]
            
            # Trích xuất các bảng từ ảnh
            table_boxes = self.detect_table(image)
            
            all_rows = []
            for i, (x1, y1, x2, y2) in enumerate(table_boxes):
                # Cắt bảng từ ảnh
                table_img = image[y1:y2, x1:x2]
                # Trích xuất hàng từ bảng
                rows = self.extract_rows_from_table(table_img, file_name, check_text, min_row_height)
                
                # Thêm lề nếu cần
                if add_margin and rows:
                    rows_with_margin = []
                    for row in rows:
                        h, w = row.shape[:2]
                        # Tạo ảnh mới với lề
                        row_with_margin = np.ones((h + 2 * margin, w + 2 * margin, 3), dtype=np.uint8) * 255
                        # Sao chép hàng vào ảnh có lề
                        row_with_margin[margin:margin + h, margin:margin + w] = row
                        rows_with_margin.append(row_with_margin)
                    rows = rows_with_margin
                
                all_rows.extend(rows)
            
            # Lưu các hàng
            for i, row in enumerate(all_rows):
                output_path = os.path.join(self.output_dir, f"row_{i}.jpg")
                cv2.imwrite(output_path, row)
                logger.info(f"Đã lưu hàng {i} vào {output_path}")
            
            logger.info(f"Đã trích xuất tổng cộng {len(all_rows)} hàng từ ảnh {image_path}")
            return all_rows
            
        except Exception as e:
            logger.error(f"Lỗi khi xử lý ảnh {image_path}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []

def parse_arguments():
    """Phân tích các tham số dòng lệnh"""
    parser = argparse.ArgumentParser(description='Cắt các hàng từ bảng dựa trên đường kẻ ngang')
    
    parser.add_argument('--input', type=str, default='input',
                        help='Thư mục chứa ảnh đầu vào (mặc định: input)')
    
    parser.add_argument('--output', type=str, default='output/advanced_rows',
                        help='Thư mục lưu các hàng đã cắt (mặc định: output/advanced_rows)')
    
    parser.add_argument('--debug', type=str, default='debug/lines',
                        help='Thư mục lưu ảnh debug (mặc định: debug/lines)')
    
    parser.add_argument('--image', type=str, required=True,
                        help='Tên file ảnh cần xử lý (trong thư mục input)')
    
    parser.add_argument('--margin', type=int, default=5,
                        help='Kích thước margin cho hàng (mặc định: 5px)')
    
    parser.add_argument('--no-margin', action='store_true',
                        help='Không thêm margin cho hàng')
                        
    parser.add_argument('--no-check-text', action='store_true',
                        help='Không kiểm tra text trong hàng')
    
    parser.add_argument('--min-row-height', type=int, default=20,
                        help='Chiều cao tối thiểu của hàng (mặc định: 20px)')
    
    return parser.parse_args()

def main():
    """Hàm chính"""
    args = parse_arguments()
    
    # Tạo các thư mục nếu chưa tồn tại
    os.makedirs(args.input, exist_ok=True)
    
    # Đường dẫn đầy đủ đến file ảnh
    image_path = os.path.join(args.input, args.image)
    
    # Kiểm tra xem file ảnh có tồn tại không
    if not os.path.exists(image_path):
        logger.error(f"Không tìm thấy file ảnh: {image_path}")
        return
    
    # Tạo AdvancedRowExtractor
    extractor = AdvancedRowExtractorMain(
        input_dir=args.input,
        output_dir=args.output,
        debug_dir=args.debug
    )
    
    # Xử lý ảnh
    rows = extractor.process_image(
        image_path=image_path,
        add_margin=not args.no_margin,
        margin=args.margin,
        check_text=not args.no_check_text,
        min_row_height=args.min_row_height
    )
    
    if rows:
        logger.info(f"Hoàn thành xử lý ảnh: {os.path.basename(image_path)}")
        logger.info(f"Đã trích xuất {len(rows)} hàng từ ảnh")
    else:
        logger.error("Lỗi khi xử lý ảnh")

if __name__ == "__main__":
    main() 
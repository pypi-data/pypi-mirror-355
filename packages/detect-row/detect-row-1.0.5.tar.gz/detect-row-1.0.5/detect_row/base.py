import os
import cv2
import numpy as np
import logging
from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('row_detector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ImageQualityChecker:
    """Lớp kiểm tra chất lượng ảnh trước khi xử lý
    
    Cung cấp các phương thức kiểm tra độ tương phản, độ nhiễu, độ nghiêng, và độ phân giải
    để cảnh báo nếu ảnh không phù hợp với các kỹ thuật xử lý
    """
    
    def __init__(self, debug_dir="debug/quality", threshold_config=None):
        """Khởi tạo ImageQualityChecker
        
        Args:
            debug_dir: Thư mục lưu ảnh debug
            threshold_config: Cấu hình các ngưỡng kiểm tra chất lượng
        """
        self.debug_dir = debug_dir
        os.makedirs(debug_dir, exist_ok=True)
        
        # Thiết lập ngưỡng mặc định nếu không được cung cấp
        self.thresholds = {
            "min_resolution": 300,  # DPI tối thiểu
            "min_contrast": 40,     # Độ tương phản tối thiểu (0-255)
            "max_noise": 0.05,      # Tỷ lệ nhiễu tối đa (0-1)
            "max_skew": 5.0,        # Độ nghiêng tối đa (độ)
            "min_width": 200,       # Chiều rộng tối thiểu (pixel)
            "min_height": 200       # Chiều cao tối thiểu (pixel)
        }
        
        # Cập nhật ngưỡng từ cấu hình đầu vào
        if threshold_config:
            self.thresholds.update(threshold_config)
    
    def check_resolution(self, image: np.ndarray) -> Tuple[bool, float]:
        """Kiểm tra độ phân giải của ảnh
        
        Args:
            image: Ảnh cần kiểm tra
            
        Returns:
            Tuple[bool, float]: (Đạt ngưỡng hay không, DPI ước tính)
        """
        height, width = image.shape[:2]
        
        # Kiểm tra kích thước tối thiểu
        if width < self.thresholds["min_width"] or height < self.thresholds["min_height"]:
            logger.warning(f"Ảnh có kích thước quá nhỏ: {width}x{height}px. "
                          f"Ngưỡng tối thiểu: {self.thresholds['min_width']}x{self.thresholds['min_height']}px")
            return False, 0
            
        # Ước tính DPI dựa trên kích thước ảnh (giả định khổ A4)
        # A4 = 210mm x 297mm, chúng ta giả định ảnh là scan của A4
        estimated_dpi_width = width / 8.27  # 8.27 inch = 210mm
        estimated_dpi_height = height / 11.7  # 11.7 inch = 297mm
        estimated_dpi = (estimated_dpi_width + estimated_dpi_height) / 2
        
        if estimated_dpi < self.thresholds["min_resolution"]:
            logger.warning(f"Độ phân giải ảnh ước tính thấp: {estimated_dpi:.1f} DPI. "
                          f"Ngưỡng tối thiểu: {self.thresholds['min_resolution']} DPI")
            return False, estimated_dpi
            
        return True, estimated_dpi
    
    def check_contrast(self, image: np.ndarray) -> Tuple[bool, float]:
        """Kiểm tra độ tương phản của ảnh
        
        Args:
            image: Ảnh cần kiểm tra
            
        Returns:
            Tuple[bool, float]: (Đạt ngưỡng hay không, Độ tương phản)
        """
        # Chuyển sang ảnh xám
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Tính histogram
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        
        # Tìm các giá trị pixel không rỗng từ histogram
        non_zero_indices = np.where(hist > 0)[0]
        if len(non_zero_indices) == 0:
            logger.warning("Ảnh rỗng hoặc có vấn đề về histogram")
            return False, 0
            
        min_val = non_zero_indices[0]
        max_val = non_zero_indices[-1]
        
        # Tính độ tương phản
        contrast = max_val - min_val
        
        # Tính độ tương phản theo RMS (Root Mean Square)
        mean_intensity = np.mean(gray)
        rms_contrast = np.sqrt(np.mean((gray - mean_intensity) ** 2))
        
        # Lưu histogram để debug
        plt_path = os.path.join(self.debug_dir, "contrast_histogram.png")
        try:
            import matplotlib.pyplot as plt
            plt.figure(figsize=(10, 5))
            plt.plot(hist)
            plt.xlim([0, 256])
            plt.title(f'Histogram: Contrast={contrast}, RMS={rms_contrast:.2f}')
            plt.savefig(plt_path)
            plt.close()
        except ImportError:
            logger.warning("Không thể tạo histogram do thiếu matplotlib")
        
        if contrast < self.thresholds["min_contrast"]:
            logger.warning(f"Độ tương phản của ảnh thấp: {contrast}. "
                          f"Ngưỡng tối thiểu: {self.thresholds['min_contrast']}")
            return False, contrast
            
        return True, contrast
    
    def check_noise(self, image: np.ndarray) -> Tuple[bool, float]:
        """Kiểm tra độ nhiễu của ảnh
        
        Args:
            image: Ảnh cần kiểm tra
            
        Returns:
            Tuple[bool, float]: (Đạt ngưỡng hay không, Tỷ lệ nhiễu)
        """
        # Chuyển sang ảnh xám
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Áp dụng lọc trung vị để làm mờ ảnh
        filtered = cv2.medianBlur(gray, 3)
        
        # Tính sự khác biệt giữa ảnh gốc và ảnh đã lọc
        diff = cv2.absdiff(gray, filtered)
        
        # Tính tỷ lệ nhiễu
        noise_ratio = np.sum(diff > 15) / (gray.shape[0] * gray.shape[1])
        
        # Lưu ảnh nhiễu để debug
        noise_path = os.path.join(self.debug_dir, "noise_detection.jpg")
        cv2.imwrite(noise_path, diff)
        
        if noise_ratio > self.thresholds["max_noise"]:
            logger.warning(f"Ảnh có nhiều nhiễu: {noise_ratio:.4f}. "
                          f"Ngưỡng tối đa: {self.thresholds['max_noise']}")
            return False, noise_ratio
            
        return True, noise_ratio
    
    def check_skew(self, image: np.ndarray) -> Tuple[bool, float]:
        """Kiểm tra độ nghiêng của ảnh
        
        Args:
            image: Ảnh cần kiểm tra
            
        Returns:
            Tuple[bool, float]: (Đạt ngưỡng hay không, Độ nghiêng (độ))
        """
        # Chuyển sang ảnh xám
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Áp dụng phép toán Canny để phát hiện cạnh
        edges = cv2.Canny(gray, 100, 200, apertureSize=3)
        
        # Sử dụng phép biến đổi Hough để phát hiện đường thẳng
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
        
        # Nếu không phát hiện được đường thẳng nào
        if lines is None or len(lines) == 0:
            logger.warning("Không phát hiện được đường thẳng nào để xác định độ nghiêng")
            return True, 0  # Giả định không nghiêng
        
        # Tính độ nghiêng từ các đường thẳng
        angles = []
        for line in lines:
            rho, theta = line[0]
            # Chỉ quan tâm đến đường ngang (gần 0 hoặc 180 độ)
            if abs(theta) < 0.3 or abs(theta - np.pi) < 0.3 or abs(theta - np.pi/2) < 0.3:
                angle_degrees = np.degrees(theta) % 180
                if angle_degrees > 90:
                    angle_degrees = 180 - angle_degrees
                angles.append(angle_degrees)
        
        if not angles:
            logger.warning("Không tìm thấy đường ngang để xác định độ nghiêng")
            return True, 0
        
        # Tính độ nghiêng trung bình
        mean_angle = np.median(angles)  # Sử dụng trung vị để tránh nhiễu
        skew_angle = abs(mean_angle - 90) if mean_angle > 45 else mean_angle
        
        # Lưu ảnh debug với các đường thẳng được phát hiện
        debug_img = image.copy()
        for line in lines:
            rho, theta = line[0]
            a = np.cos(theta)
            b = np.sin(theta)
            x0 = a * rho
            y0 = b * rho
            x1 = int(x0 + 1000 * (-b))
            y1 = int(y0 + 1000 * (a))
            x2 = int(x0 - 1000 * (-b))
            y2 = int(y0 - 1000 * (a))
            cv2.line(debug_img, (x1, y1), (x2, y2), (0, 0, 255), 2)
        
        skew_path = os.path.join(self.debug_dir, "skew_detection.jpg")
        cv2.imwrite(skew_path, debug_img)
        
        if skew_angle > self.thresholds["max_skew"]:
            logger.warning(f"Ảnh bị nghiêng: {skew_angle:.2f} độ. "
                          f"Ngưỡng tối đa: {self.thresholds['max_skew']} độ")
            return False, skew_angle
            
        return True, skew_angle
    
    def check_image_quality(self, image: np.ndarray) -> Tuple[bool, Dict[str, Any]]:
        """Kiểm tra tổng thể chất lượng của ảnh
        
        Args:
            image: Ảnh cần kiểm tra
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (Tất cả các kiểm tra đều đạt, Kết quả chi tiết)
        """
        results = {
            "resolution": self.check_resolution(image),
            "contrast": self.check_contrast(image),
            "noise": self.check_noise(image),
            "skew": self.check_skew(image)
        }
        
        # Kiểm tra xem tất cả các test có đạt không
        all_passed = all(result[0] for result in results.values())
        
        return all_passed, results

class BaseRowExtractor(ABC):
    """Lớp cơ sở trừu tượng cho các phương pháp trích xuất hàng"""
    
    def __init__(self, input_dir="input", output_dir="output", debug_dir="debug"):
        """Khởi tạo BaseRowExtractor
        
        Args:
            input_dir: Thư mục chứa ảnh đầu vào
            output_dir: Thư mục lưu kết quả
            debug_dir: Thư mục lưu ảnh debug
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.debug_dir = debug_dir
        
        # Tạo các thư mục nếu chưa tồn tại
        for dir_path in [input_dir, output_dir, debug_dir]:
            os.makedirs(dir_path, exist_ok=True)
            
        # Khởi tạo bộ kiểm tra chất lượng ảnh
        self.quality_checker = ImageQualityChecker(
            debug_dir=os.path.join(debug_dir, "quality")
        )
    
    def check_image_quality(self, image: np.ndarray, fail_on_low_quality: bool = False) -> bool:
        """Kiểm tra chất lượng ảnh trước khi xử lý
        
        Args:
            image: Ảnh cần kiểm tra
            fail_on_low_quality: Nếu True, raise exception khi chất lượng thấp
            
        Returns:
            bool: True nếu ảnh đạt yêu cầu
            
        Raises:
            ValueError: Nếu fail_on_low_quality=True và chất lượng ảnh thấp
        """
        passed, results = self.quality_checker.check_image_quality(image)
        
        if not passed and fail_on_low_quality:
            error_msg = "Chất lượng ảnh không đạt yêu cầu:\n"
            for test_name, (test_passed, value) in results.items():
                if not test_passed:
                    error_msg += f"- {test_name}: {value}\n"
            raise ValueError(error_msg)
            
        return passed
    
    @abstractmethod
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Tiền xử lý ảnh
        
        Args:
            image: Ảnh đầu vào
            
        Returns:
            np.ndarray: Ảnh đã được tiền xử lý
        """
        pass
    
    @abstractmethod
    def detect_horizontal_lines(self, image: np.ndarray, **kwargs) -> List[int]:
        """Phát hiện các đường ngang trong ảnh
        
        Args:
            image: Ảnh đã được tiền xử lý
            **kwargs: Các tham số bổ sung
            
        Returns:
            List[int]: Danh sách vị trí y của các đường ngang
        """
        pass
    
    @abstractmethod
    def extract_rows_from_table(self, table_image: np.ndarray, table_id: int) -> List[np.ndarray]:
        """Trích xuất các hàng từ ảnh bảng
        
        Args:
            table_image: Ảnh bảng
            table_id: ID của bảng
            
        Returns:
            List[np.ndarray]: Danh sách các ảnh hàng
        """
        pass
    
    def _filter_close_lines(self, line_positions: List[int], min_distance: int = 10) -> List[int]:
        """Lọc các đường quá gần nhau
        
        Args:
            line_positions: Danh sách vị trí y của các đường
            min_distance: Khoảng cách tối thiểu giữa các đường
            
        Returns:
            List[int]: Danh sách vị trí y đã được lọc
        """
        if not line_positions:
            return []
            
        # Sắp xếp các vị trí
        sorted_positions = sorted(line_positions)
        
        # Lọc các vị trí quá gần nhau
        filtered_positions = [sorted_positions[0]]
        for pos in sorted_positions[1:]:
            if pos - filtered_positions[-1] >= min_distance:
                filtered_positions.append(pos)
                
        return filtered_positions
    
    def _has_text(self, image: np.ndarray, threshold_ratio: float = 0.005) -> bool:
        """Kiểm tra xem ảnh có chứa text hay không
        
        Args:
            image: Ảnh cần kiểm tra
            threshold_ratio: Tỷ lệ pixel trắng tối thiểu để xác định có text
            
        Returns:
            bool: True nếu ảnh có chứa text
        """
        # Chuyển sang ảnh xám
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Áp dụng threshold
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Đếm số pixel trắng (pixel text)
        white_pixels = np.sum(binary == 255)
        total_pixels = binary.size
        
        # Tính tỷ lệ
        white_ratio = white_pixels / total_pixels
        
        return white_ratio > threshold_ratio
    
    @abstractmethod
    def process_image(self, image_path: str, **kwargs) -> Any:
        """Xử lý ảnh và trích xuất các hàng
        
        Args:
            image_path: Đường dẫn đến ảnh
            **kwargs: Các tham số bổ sung
            
        Returns:
            Any: Kết quả xử lý
        """
        pass 
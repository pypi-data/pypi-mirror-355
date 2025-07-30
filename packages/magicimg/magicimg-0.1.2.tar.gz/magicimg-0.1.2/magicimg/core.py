"""
Xử lý và tiền xử lý ảnh cho hệ thống OCR
"""

import cv2
import numpy as np
import os
import logging
import time
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union
from dataclasses import dataclass
import json

# Thiết lập logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ImageQualityMetrics:
    """Lưu trữ các chỉ số chất lượng ảnh"""
    blur_index: float
    dark_ratio: float
    brightness: float
    contrast: float
    resolution: Tuple[int, int]
    quality_score: float = 0.0
    warnings: List[str] = None
    
    def __post_init__(self):
        self.warnings = self.warnings or []
        
    def to_dict(self) -> Dict:
        return {
            "blur_index": self.blur_index,
            "dark_ratio": self.dark_ratio,
            "brightness": self.brightness,
            "contrast": self.contrast,
            "resolution": self.resolution,
            "quality_score": self.quality_score,
            "warnings": self.warnings
        }

@dataclass
class ProcessingResult:
    """Kết quả xử lý ảnh"""
    success: bool
    image: Optional[np.ndarray]
    quality_metrics: ImageQualityMetrics
    processing_steps: List[str]
    output_path: Optional[str] = None
    error_message: Optional[str] = None
    debug_images: Dict[str, str] = None
    rotation_angle: float = 0.0  # Thêm góc xoay
    
    def __post_init__(self):
        self.debug_images = self.debug_images or {}
        
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "quality_metrics": self.quality_metrics.to_dict(),
            "processing_steps": self.processing_steps,
            "output_path": self.output_path,
            "error_message": self.error_message,
            "debug_images": self.debug_images,
            "rotation_angle": self.rotation_angle
        }

class ImageProcessor:
    """Xử lý và tiền xử lý ảnh"""
    
    def __init__(self, debug_dir: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """Khởi tạo với cấu hình tùy chỉnh
        
        Args:
            debug_dir: Thư mục lưu ảnh debug, nếu None thì tắt chế độ debug
            config: Cấu hình tùy chỉnh cho xử lý ảnh
        """
        # Cấu hình mặc định dựa trên ảnh mẫu phiếu bầu
        self.config = {
            # Ngưỡng chất lượng
            "min_blur_index": 80.0,       # Giảm yêu cầu độ nét vì ảnh scan thường hơi mờ
            "max_dark_ratio": 0.2,        # Giảm ngưỡng pixel tối vì ảnh phiếu thường sáng
            "min_brightness": 180.0,      # Tăng yêu cầu độ sáng vì cần đọc text rõ ràng
            "min_contrast": 50.0,         # Tăng yêu cầu độ tương phản để phân biệt text và nền
            "min_resolution": (1000, 1400), # Tăng độ phân giải tối thiểu cho ảnh phiếu
            "min_quality_score": 0.7,     # Tăng yêu cầu chất lượng tổng thể
            
            # Ngưỡng xử lý
            "min_skew_angle": 0.3,        # Giảm ngưỡng phát hiện góc nghiêng
            "max_skew_angle": 30.0,       # Giảm góc nghiêng tối đa vì phiếu thường không bị nghiêng nhiều
            "min_rotation_confidence": 0.8,# 
            
            # Cấu hình debug
            "debug": debug_dir is not None,
            "debug_dir": debug_dir,
            
            # Cấu hình xử lý
            "skip_rotation": False,        # Thêm flag để bỏ qua xoay ảnh
            "reuse_rotation": None,        # Góc xoay được tái sử dụng
            
            # Từ khóa bổ sung cho phiếu bầu
            "ballot_keywords": [
                "phieu bau cu", "doan dai bieu", "dai hoi", "dang bo",
                "nhiem ky", "stt", "ho va ten", "ha noi", "ngay", "thang", "nam"
            ],

            # Tham số phát hiện đường kẻ ngang
            "line_detection": {
                "min_line_length_ratio": 0.6,     # Giảm yêu cầu chiều dài đường kẻ
                "min_length_threshold_ratio": 0.7, # Giảm ngưỡng lọc
                "max_line_height": 3,            # Giữ nguyên
                "morph_iterations": 1,           # Giữ nguyên
                "histogram_threshold_ratio": 0.5, # Giảm ngưỡng histogram
                "min_line_distance": 20,         # Giảm khoảng cách tối thiểu
                "dilate_kernel_div": 30,         # Giảm về giá trị cũ
                "horizontal_kernel_div": 5,       # Giảm về giá trị cũ
                "projection_threshold_div": 4     # Giảm về giá trị cũ
            },

            # Tham số cắt hàng
            "row_extraction": {
                "top_margin": 8,        # Lề trên khi cắt hàng (pixel)
                "bottom_margin": 8,     # Lề dưới khi cắt hàng (pixel)
                "safe_zone": 5,         # Vùng an toàn xung quanh đường kẻ (pixel)
                "min_row_height": 20,   # Chiều cao tối thiểu của hàng
                "check_text": True,     # Có kiểm tra text trong hàng không
                "text_margin": 3,       # Lề thêm nếu phát hiện text gần biên
                "min_text_area": 0.003  # Tỷ lệ diện tích text tối thiểu để coi là có text
            }
        }
        
        # Cập nhật cấu hình từ tham số
        if config:
            self.config.update(config)
            
        # Tạo thư mục debug nếu cần
        if self.config["debug"] and self.config["debug_dir"]:
            os.makedirs(self.config["debug_dir"], exist_ok=True)
            
        # Ghi log cấu hình
        logger.info("Khởi tạo ImageProcessor với cấu hình:")
        for key, value in self.config.items():
            logger.info(f"  - {key}: {value}")
        
        self.debug_dir = self.config["debug_dir"]
        self.debug = self.config["debug"]
        
        # Cập nhật từ khóa tiếng Việt
        self.keywords = self.config.get("ballot_keywords", []) + [
            # Từ khóa hành chính
            "bau cu", "dang", "cong hoa", "xa hoi", "viet nam",
            "phieu", "ho ten", "stt", "so thu tu", "chu ky",
            
            # Từ và họ phổ biến trong phiếu bầu
            "nguyen", "tran", "le", "pham", "hoang", "do",
            "thi", "van", "duc", "anh", "quang", "thanh"
        ]
        
        # Chữ cái đặc biệt để xác định hướng dựa trên contour
        self.orientation_chars = ['c', 'C', 'a', 'A', 'v', 'V', 'n', 'N', '9', '6', 'p', 'q', 'g']
    
    def _check_image_quality(self, image) -> ImageQualityMetrics:
        """Kiểm tra chất lượng ảnh và trả về metrics
        
        Args:
            image: Ảnh cần kiểm tra (numpy array)
            
        Returns:
            ImageQualityMetrics: Thông tin chất lượng ảnh
        """
        # Chuyển đổi sang ảnh xám nếu cần
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            
        # Tính các chỉ số chất lượng
        blur_index = cv2.Laplacian(gray, cv2.CV_64F).var()
        dark_pixels = np.sum(gray < 50)
        dark_ratio = dark_pixels / (gray.shape[0] * gray.shape[1])
        brightness = np.mean(gray)
        contrast = np.std(gray.astype(np.float32))
        resolution = image.shape[:2][::-1]  # width, height
        
        # Thu thập cảnh báo
        warnings = []
        if blur_index < self.config["min_blur_index"]:
            warnings.append("Ảnh quá mờ")
        if dark_ratio > self.config["max_dark_ratio"]:
            warnings.append("Ảnh quá tối")
        if brightness < self.config["min_brightness"]:
            warnings.append("Độ sáng không đủ")
        if contrast < self.config["min_contrast"]:
            warnings.append("Độ tương phản không đủ")
        if resolution[0] < self.config["min_resolution"][0] or resolution[1] < self.config["min_resolution"][1]:
            warnings.append("Độ phân giải không đủ")
            
        # Tính điểm chất lượng tổng hợp
        quality_score = (
            (min(blur_index / self.config["min_blur_index"], 2.0) * 0.3) +
            ((1 - dark_ratio / self.config["max_dark_ratio"]) * 0.2) +
            (min(brightness / self.config["min_brightness"], 1.5) * 0.25) +
            (min(contrast / self.config["min_contrast"], 1.5) * 0.25)
        )
        quality_score = min(1.0, max(0.0, quality_score))
        
        return ImageQualityMetrics(
            blur_index=blur_index,
            dark_ratio=dark_ratio,
            brightness=brightness,
            contrast=contrast,
            resolution=resolution,
            quality_score=quality_score,
            warnings=warnings
        )
    
    def check_quality(self, image, prefix=None):
        """Kiểm tra chất lượng ảnh
        Args:
            image: Ảnh cần kiểm tra (numpy array)
            prefix: Tiền tố cho tên file debug
        Returns:
            tuple: (is_good, quality_info, enhanced_image)
                is_good: Boolean cho biết ảnh có đạt chất lượng không
                quality_info: Dict chứa thông tin chất lượng
                enhanced_image: Ảnh đã được nâng cao chất lượng nếu cần
        """
        # Kiểm tra ảnh có hợp lệ không
        if image is None or image.size == 0:
            logger.error("Ảnh không hợp lệ hoặc trống")
            return False, {"error": "invalid_image"}, None
            
        # Chuyển đổi sang ảnh xám nếu cần
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            
        # Kiểm tra độ phân giải
        height, width = image.shape[:2]
        resolution_ok = width >= self.config["min_resolution"][0] and height >= self.config["min_resolution"][1]
        
        # Tính chỉ số mờ (blur index) sử dụng Laplacian variance
        blur_index = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Tính tỷ lệ pixel tối (dark pixel ratio)
        dark_pixels = np.sum(gray < 50)
        dark_ratio = dark_pixels / (gray.shape[0] * gray.shape[1])
        
        # Tính độ sáng trung bình
        brightness = np.mean(gray)
        
        # Tính độ tương phản
        contrast = np.std(gray.astype(np.float32))
        
        # Vẽ histogram để debug
        if self.debug and prefix:
            plt_available = True
            try:
                import matplotlib.pyplot as plt
            except ImportError:
                plt_available = False
                
            if plt_available:
                plt.figure(figsize=(10, 6))
                plt.hist(gray.ravel(), 256, [0, 256])
                plt.title(f'Histogram: Brightness={brightness:.2f}, Contrast={contrast:.2f}')
                plt.xlabel('Pixel Value')
                plt.ylabel('Frequency')
                hist_path = os.path.join(self.debug_dir, f"{prefix}_quality_histogram.jpg")
                plt.savefig(hist_path)
                plt.close()
                logger.info(f"Đã lưu biểu đồ histogram: {hist_path}")
        
        # Thu thập thông tin chất lượng
        quality_info = {
            "blur_index": blur_index,
            "dark_ratio": dark_ratio,
            "brightness": brightness,
            "contrast": contrast,
            "resolution": (width, height)
        }
        
        # Kiểm tra các tiêu chí chất lượng
        blur_ok = blur_index >= self.config["min_blur_index"]
        dark_ok = dark_ratio <= self.config["max_dark_ratio"]
        brightness_ok = brightness >= self.config["min_brightness"]
        contrast_ok = contrast >= self.config["min_contrast"]
        
        # Đánh giá tổng thể
        is_good = blur_ok and dark_ok and brightness_ok and contrast_ok and resolution_ok
        
        # Ghi log kết quả kiểm tra
        logger.info(f"Kiểm tra chất lượng ảnh:")
        logger.info(f"  - Chỉ số mờ (blur index): {blur_index:.2f} (tối thiểu: {self.config['min_blur_index']})")
        logger.info(f"  - Tỷ lệ pixel tối: {dark_ratio:.4f} (tối đa: {self.config['max_dark_ratio']})")
        logger.info(f"  - Độ sáng trung bình: {brightness:.2f} (tối thiểu: {self.config['min_brightness']})")
        logger.info(f"  - Độ tương phản: {contrast:.2f} (tối thiểu: {self.config['min_contrast']})")
        logger.info(f"  - Độ phân giải: {width}x{height} (tối thiểu: {self.config['min_resolution'][0]}x{self.config['min_resolution'][1]})")
        
        if not is_good:
            logger.warning("Ảnh không đạt chất lượng yêu cầu!")
            if not blur_ok:
                logger.warning("  - Ảnh quá mờ")
            if not dark_ok:
                logger.warning("  - Ảnh quá tối")
            if not brightness_ok:
                logger.warning("  - Độ sáng không đủ")
            if not contrast_ok:
                logger.warning("  - Độ tương phản không đủ")
            if not resolution_ok:
                logger.warning("  - Độ phân giải không đủ")
        
        # Nâng cao chất lượng ảnh nếu cần
        enhanced_image = self.enhance_image(image, quality_info, prefix)
        
        return is_good, quality_info, enhanced_image
    
    def enhance_image(self, image, quality_info, prefix=None):
        """Nâng cao chất lượng ảnh dựa trên kết quả kiểm tra
        Args:
            image: Ảnh cần xử lý
            quality_info: Thông tin chất lượng ảnh
            prefix: Tiền tố cho tên file debug
        Returns:
            Ảnh đã được nâng cao chất lượng
        """
        # Giữ nguyên ảnh gốc để so sánh
        original = image.copy()
        enhanced = image.copy()
        
        # Chuyển đổi sang BGR nếu là ảnh xám
        if len(image.shape) == 2:
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
            
        # Tăng cường kênh màu xanh lam (blue) lên gấp 2
        if len(enhanced.shape) == 3:
            enhanced[:, :, 0] = cv2.multiply(enhanced[:, :, 0], 2.0)  # Blue channel * 2
            enhanced[:, :, 0] = np.clip(enhanced[:, :, 0], 0, 255)  # Giới hạn giá trị trong khoảng [0, 255]
        
        # Nâng cao độ sáng và tương phản nếu cần
        if quality_info["brightness"] < self.config["min_brightness"] or quality_info["contrast"] < self.config["min_contrast"]:
            logger.info("Nâng cao độ sáng và tương phản")
            
            # Tính toán hệ số alpha (tương phản) và beta (độ sáng)
            alpha = 1.0
            if quality_info["contrast"] < self.config["min_contrast"]:
                alpha = self.config["min_contrast"] / quality_info["contrast"]
                alpha = min(2.5, alpha)  # Giới hạn trên để tránh làm biến dạng ảnh
            
            beta = 0
            if quality_info["brightness"] < self.config["min_brightness"]:
                beta = (self.config["min_brightness"] - quality_info["brightness"]) * 0.5  # Giảm mức thay đổi để tránh quá sáng
            
            logger.info(f"  - Hệ số tương phản (alpha): {alpha:.2f}")
            logger.info(f"  - Hệ số độ sáng (beta): {beta:.2f}")
            
            # Áp dụng tăng cường
            enhanced = cv2.convertScaleAbs(enhanced, alpha=alpha, beta=beta)
        
        # Xử lý ảnh mờ nếu cần (sử dụng sharpening filter)
        if quality_info["blur_index"] < self.config["min_blur_index"]:
            logger.info("Áp dụng bộ lọc làm sắc nét ảnh")
            
            # Tạo kernel cho bộ lọc sharpening
            kernel = np.array([[-1,-1,-1], 
                              [-1, 9,-1],
                              [-1,-1,-1]])
            
            # Áp dụng filter2D để làm sắc nét
            enhanced = cv2.filter2D(enhanced, -1, kernel)
        
        # Lưu ảnh đã nâng cao chất lượng để debug
        if self.debug and prefix:
            enhanced_path = os.path.join(self.debug_dir, f"{prefix}_enhanced.jpg")
            cv2.imwrite(enhanced_path, enhanced)
            logger.info(f"Đã lưu ảnh nâng cao chất lượng: {enhanced_path}")
            
            # Tạo ảnh so sánh
            if len(original.shape) == 2:
                original_bgr = cv2.cvtColor(original, cv2.COLOR_GRAY2BGR)
            else:
                original_bgr = original.copy()
                
            # Ghép ảnh gốc và ảnh đã nâng cao để so sánh
            h, w = original.shape[:2]
            comparison = np.zeros((h, w*2, 3), dtype=np.uint8)
            comparison[:, :w] = original_bgr
            comparison[:, w:] = enhanced
            
            # Thêm nhãn
            cv2.putText(comparison, "Original", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.putText(comparison, "Enhanced", (w+10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            # Lưu ảnh so sánh
            comparison_path = os.path.join(self.debug_dir, f"{prefix}_comparison.jpg")
            cv2.imwrite(comparison_path, comparison)
            logger.info(f"Đã lưu ảnh so sánh: {comparison_path}")
        
        return enhanced
    
    def enhance_image_for_ocr(self, image):
        """Tăng cường chất lượng ảnh để OCR nhận diện tốt hơn
        Args:
            image: Ảnh đầu vào (numpy array)
        Returns:
            numpy array: Ảnh đã tăng cường
        """
        # Kiểm tra số kênh màu và chuyển đổi ảnh sang ảnh xám nếu cần
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Kiểm tra chất lượng ảnh
        blur_index = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Nếu ảnh quá mờ, áp dụng tăng cường
        if blur_index < 100:
            logger.info(f"Ảnh chất lượng kém (blur index: {blur_index:.2f}), đang áp dụng tăng cường...")
            
            # Thử áp dụng nhiều phương pháp tăng cường khác nhau
            
            # 1. Tăng độ tương phản
            alpha = 1.5  # Điều chỉnh độ tương phản
            beta = 10    # Điều chỉnh độ sáng
            enhanced = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)
            
            # 2. Binarization với Otsu's thresholding
            _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # 3. Giảm nhiễu với bộ lọc Gaussian
            denoised = cv2.GaussianBlur(binary, (3, 3), 0)
            
            # 4. Áp dụng Adaptive Thresholding
            adaptive = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Lưu ảnh đã tăng cường để debug
            if self.debug:
                enhanced_path = os.path.join(self.debug_dir, "enhanced_for_ocr.jpg")
                cv2.imwrite(enhanced_path, adaptive)
                logger.info(f"Đã lưu ảnh đã tăng cường: {enhanced_path}")
            
            return adaptive
        
        return gray
    
    def rotate_image(self, image, angle):
        """Xoay ảnh theo góc cho trước
        Args:
            image: Ảnh đầu vào
            angle: Góc xoay (0, 90, 180, 270)
        Returns:
            numpy array: Ảnh đã xoay
        """
        # Xử lý góc xoay ngoài phạm vi
        angle = angle % 360
        
        # Xoay ảnh với góc thích hợp
        if angle == 90:
            return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        elif angle == 180:
            return cv2.rotate(image, cv2.ROTATE_180)
        elif angle == 270:
            return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        else:
            return image
    
    def detect_orientation(self, image):
        """Phát hiện hướng ảnh dựa trên OCR và tìm từ khóa
        Args:
            image: Ảnh đầu vào
        Returns:
            int: Góc xoay cần điều chỉnh (0, 90, 180, 270)
        """
        logger.info("Bắt đầu phát hiện hướng ảnh...")
        start_time = time.time()
        
        # Kiểm tra xem có Tesseract OCR không
        try:
            import pytesseract
            OCR_AVAILABLE = True
        except ImportError:
            logger.warning("Không tìm thấy pytesseract. Không thể phát hiện hướng ảnh bằng OCR.")
            return 0
        
        best_score = -1
        best_angle = 0
        
        # Thử từng góc và đánh giá kết quả
        for angle in [0, 90, 180, 270]:
            # Xoay ảnh theo góc hiện tại
            rotated = self.rotate_image(image, angle)
            
            # Lấy kích thước ảnh
            height, width = rotated.shape[:2]
            
            # Trích xuất 1/3 phía trên của ảnh để tìm text
            top_third = rotated[:height//3, :]
            
            # Tăng cường chất lượng ảnh
            enhanced = self.enhance_image_for_ocr(top_third)
            
            # Lưu ảnh vùng 1/3 trên để debug
            if self.debug:
                top_path = os.path.join(self.debug_dir, f"top_third_angle_{angle}.jpg")
                cv2.imwrite(top_path, enhanced)
                logger.info(f"Đã lưu ảnh vùng 1/3 trên góc {angle}°: {top_path}")
            
            # Thực hiện OCR với Tesseract
            try:
                text = pytesseract.image_to_string(enhanced, lang='eng', config='--psm 6')
                
                # Lưu text OCR để debug
                if self.debug:
                    text_path = os.path.join(self.debug_dir, f"ocr_text_angle_{angle}.txt")
                    with open(text_path, 'w', encoding='utf-8') as f:
                        f.write(text)
                    logger.info(f"Đã lưu text OCR góc {angle}°: {text_path}")
                
                # Tính điểm dựa trên số từ và từ khóa
                num_words = len(text.split())
                num_chars = len(text)
                
                # Tìm kiếm từ khóa trong văn bản
                import unicodedata
                import re
                
                # Chuyển text về chữ thường không dấu
                def remove_accents(text):
                    text = text.lower()
                    text = unicodedata.normalize('NFD', text)
                    text = ''.join(c for c in text if not unicodedata.combining(c))
                    text = text.replace('đ', 'd').replace('Đ', 'd')
                    return text
                
                normalized_text = remove_accents(text)
                normalized_text = re.sub(r'[^\w\s]', ' ', normalized_text)
                
                # Đếm từ khóa tìm thấy
                found_keywords = []
                for keyword in self.keywords:
                    if keyword in normalized_text:
                        found_keywords.append(keyword)
                
                num_keywords = len(found_keywords)
                

####################################################################################

                # Tính điểm tổng hợp (ưu tiên số từ khóa, sau đó là số từ và ký tự)
                direction_score = num_keywords * 50 + num_words * 0.3 + num_chars * 0.2
                
                logger.info(f"Góc {angle}°: {num_keywords} từ khóa, {num_words} từ, {num_chars} ký tự → điểm = {direction_score:.2f}")
####################################################################################


                # Cập nhật góc tốt nhất
                if direction_score > best_score:
                    best_score = direction_score
                    best_angle = angle
                
            except Exception as e:
                logger.warning(f"Lỗi khi thực hiện OCR ở góc {angle}°: {str(e)}")
        
        # Góc cần xoay chính là góc phát hiện được
        rotation_angle = best_angle
        logger.info(f"Góc OCR tốt nhất: {best_angle}° → cần xoay {rotation_angle}° để đúng hướng")
        
        elapsed = time.time() - start_time
        logger.info(f"Hoàn thành phát hiện hướng ảnh sau {elapsed:.2f} giây")
        
        return rotation_angle
    
    def process_image(self, input_path: str, output_path: str, auto_rotate: bool = True) -> ProcessingResult:
        """Xử lý ảnh với các bước tối ưu
        
        Args:
            input_path: Đường dẫn ảnh đầu vào
            output_path: Đường dẫn lưu ảnh đã xử lý
            auto_rotate: Có tự động xoay ảnh hay không
            
        Returns:
            ProcessingResult: Kết quả xử lý ảnh
        """
        start_time = time.time()
        logger.info("Bắt đầu xử lý ảnh...")
        
        # Đọc ảnh
        image = cv2.imread(input_path)
        if image is None:
            return ProcessingResult(
                success=False,
                image=None,
                quality_metrics=None,
                processing_steps=[],
                error_message=f"Không thể đọc ảnh từ {input_path}"
            )
            
        processing_steps = []

        # Kiểm tra và sửa nghiêng ảnh
        skew_angle = self.detect_skew(image)
        if abs(skew_angle) >= self.config["min_skew_angle"]:
            logger.info(f"Phát hiện ảnh nghiêng {skew_angle:.2f} độ, đang điều chỉnh...")
            image = self.correct_skew(image, skew_angle)
            processing_steps.append(f"Điều chỉnh nghiêng {skew_angle:.2f}°")
            
            # Lưu ảnh debug sau khi sửa nghiêng
            if self.debug:
                skew_corrected_path = os.path.join(self.debug_dir, "skew_corrected.jpg")
                cv2.imwrite(skew_corrected_path, image)
                logger.info(f"Đã lưu ảnh sau khi sửa nghiêng: {skew_corrected_path}")
        
        # Kiểm tra chất lượng ảnh
        quality_metrics = self._check_image_quality(image)
        logger.info("Kiểm tra chất lượng ảnh:")
        logger.info(f"  - Chỉ số mờ (blur index): {quality_metrics.blur_index:.2f} (tối thiểu: {self.config['min_blur_index']})")
        logger.info(f"  - Tỷ lệ pixel tối: {quality_metrics.dark_ratio:.4f} (tối đa: {self.config['max_dark_ratio']})")
        logger.info(f"  - Độ sáng trung bình: {quality_metrics.brightness:.2f} (tối thiểu: {self.config['min_brightness']})")
        logger.info(f"  - Độ tương phản: {quality_metrics.contrast:.2f} (tối thiểu: {self.config['min_contrast']})")
        logger.info(f"  - Độ phân giải: {quality_metrics.resolution[0]}x{quality_metrics.resolution[1]} (tối thiểu: {self.config['min_resolution'][0]}x{self.config['min_resolution'][1]})")
        
        if quality_metrics.warnings:
            logger.warning("Ảnh không đạt chất lượng yêu cầu!")
            for warning in quality_metrics.warnings:
                logger.warning(f"  - {warning}")
                
        # Xử lý xoay ảnh nếu cần
        rotation_angle = 0.0
        if auto_rotate and not self.config["skip_rotation"]:
            if self.config["reuse_rotation"] is not None:
                # Tái sử dụng góc xoay đã biết
                rotation_angle = self.config["reuse_rotation"]
                logger.info(f"Tái sử dụng góc xoay: {rotation_angle}°")
                image = self.rotate_image(image, rotation_angle)
                processing_steps.append(f"Xoay ảnh {rotation_angle}°")
            else:
                # Phát hiện và xoay ảnh
                logger.info("Bắt đầu phát hiện hướng ảnh...")
                orientation_start = time.time()
                orientation_result = self.detect_orientation(image)
                
                if orientation_result != 0:
                    rotation_angle = orientation_result
                    image = self.rotate_image(image, rotation_angle)
                    processing_steps.append(f"Xoay ảnh {rotation_angle}°")
                    logger.info(f"Hoàn thành phát hiện hướng ảnh sau {time.time() - orientation_start:.2f} giây")
        
        # Nâng cao chất lượng ảnh nếu cần
        if quality_metrics.quality_score < self.config["min_quality_score"]:
            image = self.enhance_image_for_ocr(image)
            processing_steps.append("Nâng cao chất lượng ảnh")
            
        # Lưu ảnh đã xử lý
        cv2.imwrite(output_path, image)
        logger.info(f"Đã lưu ảnh đã xử lý vào: {output_path}")
        
        # Hoàn thành xử lý
        process_time = time.time() - start_time
        logger.info(f"Đã hoàn thành xử lý ảnh trong {process_time:.2f} giây")
        
        return ProcessingResult(
            success=True,
            image=image,
            quality_metrics=quality_metrics,
            processing_steps=processing_steps,
            output_path=output_path,
            rotation_angle=rotation_angle
        )
    
    def detect_skew(self, image, prefix=None):
        """Phát hiện góc nghiêng của ảnh sử dụng minAreaRect
        Args:
            image: Ảnh đầu vào (numpy array)
            prefix: Tiền tố cho tên file debug
        Returns:
            float: Góc nghiêng (độ)
        """
        # Chuyển sang grayscale và nhị phân hóa
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        
        # Tìm các contour
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Lọc các contour quá nhỏ và tìm contour lớn nhất (có thể là bảng)
        min_area = 1000
        max_area = 0
        largest_contour = None
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > min_area and area > max_area:
                max_area = area
                largest_contour = cnt
                
        if largest_contour is None:
            return 0.0
            
        # Sử dụng minAreaRect để tìm góc nghiêng
        rect = cv2.minAreaRect(largest_contour)
        angle = rect[-1]
        
        # Chuẩn hóa góc về khoảng [-45, 45]
        if angle < -45:
            angle = 90 + angle
        elif angle > 45:
            angle = angle - 90
            
        # Debug: vẽ hình chữ nhật bao quanh contour lớn nhất
        if self.debug_dir:
            debug_img = image.copy()
            box = cv2.boxPoints(rect)
            box = np.int32(box)
            cv2.drawContours(debug_img, [box], 0, (0, 0, 255), 2)
            
            # Lưu ảnh debug
            debug_path = os.path.join(self.debug_dir, "skew_detection.jpg")
            if prefix:
                debug_path = os.path.join(self.debug_dir, f"{prefix}_skew_detection.jpg")
            cv2.imwrite(debug_path, debug_img)
            logger.info(f"Đã lưu ảnh debug phát hiện góc nghiêng: {debug_path}")
        
        # Làm tròn góc về bước 0.2 độ
        angle = round(angle / 0.2) * 0.2
        
        logger.info(f"Phát hiện góc nghiêng: {angle:.2f} độ")
        return angle
        
    def correct_skew(self, image, angle):
        """Chỉnh sửa góc nghiêng của ảnh
        Args:
            image: Ảnh đầu vào (numpy array)
            angle: Góc nghiêng cần chỉnh sửa (độ)
        Returns:
            numpy array: Ảnh đã được chỉnh sửa
        """
        if abs(angle) < self.config["min_skew_angle"]:  # Bỏ qua các góc nghiêng nhỏ
            return image
            
        # Lấy kích thước ảnh
        height, width = image.shape[:2]
        
        # Tính tâm xoay
        center = (width // 2, height // 2)
        
        # Tạo ma trận xoay
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Xoay ảnh
        rotated = cv2.warpAffine(image, rotation_matrix, (width, height), 
                                flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        
        return rotated

    def detect_horizontal_lines(self, image: np.ndarray, min_line_length_ratio: Optional[float] = None) -> List[int]:
        """Phát hiện các đường kẻ ngang trong ảnh
        
        Args:
            image: Ảnh đã tiền xử lý
            min_line_length_ratio: Tỷ lệ tối thiểu của chiều dài đường kẻ so với chiều rộng ảnh
            
        Returns:
            List[int]: Danh sách các tọa độ y của đường kẻ ngang
        """
        # Lấy các tham số từ config
        line_config = self.config["line_detection"]
        min_line_length_ratio = min_line_length_ratio or line_config["min_line_length_ratio"]
        min_length_threshold_ratio = line_config["min_length_threshold_ratio"]
        max_line_height = line_config["max_line_height"]
        morph_iterations = line_config["morph_iterations"]
        histogram_threshold_ratio = line_config["histogram_threshold_ratio"]
        min_line_distance = line_config["min_line_distance"]
        dilate_kernel_div = line_config["dilate_kernel_div"]
        horizontal_kernel_div = line_config["horizontal_kernel_div"]
        projection_threshold_div = line_config["projection_threshold_div"]

        # Kích thước ảnh
        height, width = image.shape[:2]
        
        # Tính chiều dài tối thiểu của đường kẻ
        min_line_length = int(width * min_line_length_ratio)
        logger.info(f"Chiều dài tối thiểu của đường kẻ ngang: {min_line_length}px (={min_line_length_ratio:.2f} × {width}px)")
        
        # Tạo kernel ngang để phát hiện đường kẻ ngang
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (min_line_length // horizontal_kernel_div, 1))
        
        # Áp dụng phép toán mở để phát hiện đường kẻ ngang
        horizontal_lines = cv2.morphologyEx(image, cv2.MORPH_OPEN, horizontal_kernel, iterations=morph_iterations)
        
        # Lọc các đường ngang có chiều dài nhỏ
        filtered_horizontal_lines = np.zeros_like(horizontal_lines)
        contours, _ = cv2.findContours(horizontal_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Tìm chiều dài lớn nhất của đường kẻ
        max_length = 0
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            max_length = max(max_length, w)
        
        # Tính ngưỡng chiều dài tối thiểu
        min_length_threshold = int(max_length * min_length_threshold_ratio)
        logger.info(f"Chiều dài tối thiểu của đường kẻ ({min_length_threshold_ratio*100}% đường dài nhất): {min_length_threshold}px")
        
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w >= min_length_threshold:
                # Kiểm tra thêm chiều cao để loại bỏ gạch ngang của chữ
                if h <= max_line_height:
                    cv2.drawContours(filtered_horizontal_lines, [cnt], -1, 255, -1)
        
        # Làm dày đường kẻ
        dilate_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (min_line_length // dilate_kernel_div, 2))
        filtered_horizontal_lines = cv2.dilate(filtered_horizontal_lines, dilate_kernel, iterations=1)
        
        # Lưu ảnh đường kẻ ngang để debug
        if self.debug:
            debug_path_original = os.path.join(self.debug_dir, "horizontal_lines_original.jpg")
            cv2.imwrite(debug_path_original, horizontal_lines)
            
            debug_path_filtered = os.path.join(self.debug_dir, "horizontal_lines_filtered.jpg")
            cv2.imwrite(debug_path_filtered, filtered_horizontal_lines)
        
        # Phát hiện đường kẻ ngang bằng histogram
        h_projection = cv2.reduce(filtered_horizontal_lines, 1, cv2.REDUCE_SUM, dtype=cv2.CV_32S)
        h_projection = h_projection / 255
        
        # Áp dụng ngưỡng histogram
        max_projection_value = np.max(h_projection)
        threshold_value = max_projection_value * histogram_threshold_ratio
        logger.info(f"Giá trị ngưỡng lọc histogram ({histogram_threshold_ratio*100}% giá trị lớn nhất): {threshold_value:.2f}")
        
        filtered_projection = np.copy(h_projection)
        filtered_projection[filtered_projection < threshold_value] = 0
        
        # Tìm vị trí các đỉnh trong histogram
        line_positions = []
        threshold = width / projection_threshold_div
        
        for y in range(1, height - 1):
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
        filtered_positions = self._filter_close_lines(line_positions, min_distance=min_line_distance)
        
        # Thêm vị trí đầu và cuối ảnh nếu cần
        if len(filtered_positions) > 0 and filtered_positions[0] > 20:
            filtered_positions.insert(0, 0)
        if len(filtered_positions) > 0 and filtered_positions[-1] < height - 20:
            filtered_positions.append(height)
        
        # Sắp xếp lại các vị trí
        filtered_positions.sort()
        
        # Vẽ các đường kẻ ngang lên ảnh để debug
        if self.debug:
            debug_image = cv2.cvtColor(image.copy(), cv2.COLOR_GRAY2BGR)
            for y in filtered_positions:
                cv2.line(debug_image, (0, y), (width, y), (0, 0, 255), 2)
            
            debug_lines_path = os.path.join(self.debug_dir, "detected_lines.jpg")
            cv2.imwrite(debug_lines_path, debug_image)
        
        logger.info(f"Đã phát hiện {len(filtered_positions)} đường kẻ ngang sau khi lọc")
        return filtered_positions

    @staticmethod
    def preprocess_image_for_api(
        image_path: str, 
        provider: str = "google", 
        output_dir: Optional[str] = None,
        debug_dir: Optional[str] = None,
        min_quality_score: float = 0.4,
        auto_rotate: bool = False
    ) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """
        Tiền xử lý ảnh trước khi gửi đến API của các nhà cung cấp khác nhau
        
        Args:
            image_path: Đường dẫn đến file ảnh cần xử lý
            provider: Nhà cung cấp API ("google", "anthropic", "local")
            output_dir: Thư mục để lưu ảnh đã xử lý (mặc định là thư mục của ảnh gốc)
            debug_dir: Thư mục để lưu các ảnh debug (nếu None sẽ không lưu)
            min_quality_score: Điểm chất lượng tối thiểu để tiếp tục xử lý (0-1)
            auto_rotate: Có tự động phát hiện và xoay ảnh hay không
            
        Returns:
            Tuple[bool, Dict[str, Any], Optional[str]]:
                - bool: True nếu tiền Xử lý xong, False nếu thất bại
                - Dict[str, Any]: Thông tin về quá trình xử lý
                - Optional[str]: Đường dẫn đến ảnh đã xử lý (None nếu thất bại nghiêm trọng)
        """
        start_time = time.time()
        
        # Xác thực đường dẫn ảnh
        if not os.path.exists(image_path):
            return False, {"message": f"File không tồn tại: {image_path}"}, None
        
        # Chuẩn bị thư mục đầu ra nếu không được chỉ định
        if output_dir is None:
            output_dir = os.path.dirname(image_path)
        
        # Tạo thư mục đầu ra và debug nếu cần
        os.makedirs(output_dir, exist_ok=True)
        if debug_dir:
            os.makedirs(debug_dir, exist_ok=True)
        
        # Thông tin xử lý
        processing_info = {
            "original_path": image_path,
            "processing_steps": [],
            "warnings": [],
            "metrics": {
                "start_time": start_time,
                "original_size": os.path.getsize(image_path) / (1024 * 1024)  # MB
            },
            "provider": provider,
            "auto_rotate": auto_rotate
        }
        
        try:
            # Đọc ảnh
            img = cv2.imread(image_path)
            if img is None:
                # Thử đọc với PIL nếu OpenCV không đọc được
                try:
                    from PIL import Image
                    pil_img = Image.open(image_path)
                    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                    processing_info["warnings"].append("OpenCV không đọc được ảnh, sử dụng PIL")
                    processing_info["processing_steps"].append("fallback_to_pil")
                except Exception as e:
                    return False, {"message": f"Không thể đọc file ảnh: {str(e)}"}, None
            
            # Lưu kích thước gốc
            original_height, original_width = img.shape[:2]
            processing_info["metrics"]["original_dimensions"] = (original_width, original_height)
            
            # Lưu ảnh gốc để debug
            if debug_dir:
                original_debug_path = os.path.join(debug_dir, f"original_{os.path.basename(image_path)}")
                cv2.imwrite(original_debug_path, img)
            
            # Khởi tạo bộ kiểm tra chất lượng
            processor = ImageProcessor(debug_dir)
            filename, ext = os.path.splitext(os.path.basename(image_path))
            
            # Kiểm tra chất lượng ảnh
            is_good_quality, quality_info, enhanced_img = processor.check_quality(img, prefix=filename)
            
            # Tính điểm chất lượng tổng hợp (nếu chưa được tính trong check_quality)
            if "quality_score" not in quality_info:
                quality_score = (
                    (min(quality_info["blur_index"] / processor.config["min_blur_index"], 2.0) * 0.3) +
                    ((1 - quality_info["dark_ratio"] / processor.config["max_dark_ratio"]) * 0.2) +
                    (min(quality_info["brightness"] / processor.config["min_brightness"], 1.5) * 0.25) +
                    (min(quality_info["contrast"] / processor.config["min_contrast"], 1.5) * 0.25)
                )
                quality_score = min(1.0, max(0.0, quality_score))
                quality_info["quality_score"] = quality_score
            else:
                quality_score = quality_info["quality_score"]
            
            # Thêm thông tin chất lượng vào processing_info
            processing_info["metrics"]["quality"] = quality_info
            processing_info["metrics"]["quality_passed"] = is_good_quality
            
            # Nếu ảnh chất lượng quá kém, dừng xử lý
            if quality_score < min_quality_score:
                error_msg = f"Ảnh có chất lượng quá kém (điểm: {quality_score:.2f}), không thể xử lý"
                processing_info["warnings"].append(error_msg)
                processing_info["message"] = error_msg
                logger.error(error_msg)
                return False, processing_info, None
            
            # Sử dụng ảnh đã nâng cao chất lượng nếu có
            if enhanced_img is not None:
                img = enhanced_img
                processing_info["processing_steps"].append("quality_enhancement")
                
                # Lưu ảnh đã nâng cao chất lượng để debug
                if debug_dir:
                    enhanced_debug_path = os.path.join(debug_dir, f"enhanced_{os.path.basename(image_path)}")
                    cv2.imwrite(enhanced_debug_path, img)
            
            # Xử lý nghiêng/xoay ảnh
            processed_img, _ = processor.process_image(img, output_path=None, auto_rotate=auto_rotate)
            if processed_img is not None:
                img = processed_img
                processing_info["processing_steps"].append("skew_correction")
                if auto_rotate:
                    processing_info["processing_steps"].append("auto_rotation")
            
            # Điều chỉnh hình ảnh theo nhà cung cấp API
            if provider.lower() == "google":
                # Google yêu cầu hình ảnh rõ ràng, độ phân giải cao
                # Không cần thay đổi nhiều
                pass
            elif provider.lower() == "anthropic":
                # Anthropic có thể xử lý hình ảnh hơi mờ nhưng cần tương phản tốt
                # Tăng cường tương phản
                brightness = 1.0
                contrast = 1.3  # Tăng cường tương phản cho Claude
                alpha = contrast
                beta = 10
                img = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)
                processing_info["processing_steps"].append("contrast_enhancement_for_anthropic")
            elif provider.lower() == "local":
                # Xử lý local thường cần ảnh rõ ràng hơn
                # Tăng cường độ sắc nét
                kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
                img = cv2.filter2D(img, -1, kernel)
                processing_info["processing_steps"].append("sharpening_for_local")
            
            # Chuẩn bị đường dẫn đầu ra
            filename, ext = os.path.splitext(os.path.basename(image_path))
            output_path = os.path.join(output_dir, f"{filename}_processed_{provider.lower()}{ext}")
            
            # Lưu ảnh đã xử lý
            cv2.imwrite(output_path, img)
            processing_info["output_path"] = output_path
            
            # Cập nhật metrics
            processing_info["metrics"]["processed_size"] = os.path.getsize(output_path) / (1024 * 1024)  # MB
            processing_info["metrics"]["processed_dimensions"] = img.shape[:2][::-1]  # width, height
            processing_info["metrics"]["processing_time"] = time.time() - start_time
            
            # Lưu ảnh đã xử lý để debug
            if debug_dir:
                debug_path = os.path.join(debug_dir, f"processed_{provider.lower()}_{os.path.basename(image_path)}")
                cv2.imwrite(debug_path, img)
                
                # Tạo ảnh so sánh trước-sau
                h_orig, w_orig = original_height, original_width
                h_proc, w_proc = img.shape[:2]
                
                # Đảm bảo cả hai ảnh có cùng kích thước để ghép
                if h_orig != h_proc or w_orig != w_proc:
                    orig_img = cv2.imread(image_path)
                    orig_img = cv2.resize(orig_img, (w_proc, h_proc))
                else:
                    orig_img = cv2.imread(image_path)
                
                # Ghép ảnh gốc và ảnh đã xử lý để so sánh
                comparison = np.zeros((h_proc, w_proc*2, 3), dtype=np.uint8)
                comparison[:, :w_proc] = orig_img
                comparison[:, w_proc:] = img
                
                # Thêm nhãn
                cv2.putText(comparison, "Original", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.putText(comparison, f"Processed ({provider})", (w_proc+10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                # Lưu ảnh so sánh
                comparison_path = os.path.join(debug_dir, f"comparison_{provider.lower()}_{os.path.basename(image_path)}")
                cv2.imwrite(comparison_path, comparison)
                logger.info(f"Đã lưu ảnh so sánh: {comparison_path}")
            
            processing_info["message"] = "Xử lý xong"
            return True, processing_info, output_path
            
        except Exception as e:
            logger.error(f"Lỗi khi xử lý ảnh: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            processing_info["error"] = str(e)
            processing_info["traceback"] = traceback.format_exc()
            processing_info["message"] = f"Lỗi: {str(e)}"
            
            return False, processing_info, None

    def extract_rows_from_table(self, table_image: np.ndarray, table_id: int) -> List[np.ndarray]:
        """Cắt các hàng từ ảnh bảng dựa trên đường kẻ ngang
        
        Args:
            table_image: Ảnh bảng
            table_id: ID của bảng
            
        Returns:
            List[np.ndarray]: Danh sách các ảnh hàng đã cắt
        """
        # Lấy các tham số từ config
        row_config = self.config["row_extraction"]
        top_margin = row_config["top_margin"]
        bottom_margin = row_config["bottom_margin"]
        safe_zone = row_config["safe_zone"]
        min_row_height = row_config["min_row_height"]
        check_text = row_config["check_text"]
        text_margin = row_config["text_margin"]
        min_text_area = row_config["min_text_area"]

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

        def check_text_in_region(img: np.ndarray, region: Tuple[int, int, int, int]) -> bool:
            """Kiểm tra có text trong vùng ảnh không"""
            x1, y1, x2, y2 = region
            region_img = img[y1:y2, x1:x2]
            if len(region_img.shape) == 3:
                gray = cv2.cvtColor(region_img, cv2.COLOR_BGR2GRAY)
            else:
                gray = region_img
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            text_pixels = np.sum(binary == 255)
            total_pixels = binary.size
            return text_pixels / total_pixels > min_text_area

        def calculate_iou(box1, box2):
            """Tính toán IoU giữa hai box"""
            y1_1, y2_1 = box1
            y1_2, y2_2 = box2
            
            # Tính toán vùng giao
            intersection_y1 = max(y1_1, y1_2)
            intersection_y2 = min(y2_1, y2_2)
            
            if intersection_y2 <= intersection_y1:
                return 0.0
                
            intersection = intersection_y2 - intersection_y1
            
            # Tính toán vùng hợp
            box1_height = y2_1 - y1_1
            box2_height = y2_2 - y1_2
            union = box1_height + box2_height - intersection
            
            return intersection / union if union > 0 else 0.0

        # Bước 1: Tính toán chiều cao trung bình của các hàng
        row_heights = []
        for i in range(len(line_positions) - 1):
            line_top = line_positions[i]
            line_bottom = line_positions[i + 1]
            safe_top = line_top + safe_zone
            safe_bottom = line_bottom - safe_zone
            y_top = max(0, safe_top - top_margin)
            y_bottom = min(height, safe_bottom + bottom_margin)
            row_height = y_bottom - y_top
            row_heights.append(row_height)
            
        avg_row_height = sum(row_heights) / len(row_heights) if row_heights else min_row_height
        logger.info(f"Chiều cao trung bình của hàng: {avg_row_height:.2f}px")
        
        # Bước 2: Cắt và xử lý các hàng
        rows = []
        row_boxes = []  # Lưu tọa độ các hàng để tính IoU
        empty_rows_count = 0
        skipped_small_rows_count = 0
        
        for i in range(len(line_positions) - 1):
            line_top = line_positions[i]
            line_bottom = line_positions[i + 1]
            
            # Kiểm tra vùng an toàn xung quanh đường kẻ
            safe_top = line_top + safe_zone
            safe_bottom = line_bottom - safe_zone
            
            # Thêm lề cơ bản
            y_top = max(0, safe_top - top_margin)
            y_bottom = min(height, safe_bottom + bottom_margin)
            
            # Kiểm tra text trong vùng lề để điều chỉnh biên
            if check_text:
                top_margin_region = (0, y_top, width, safe_top)
                if check_text_in_region(table_image, top_margin_region):
                    y_top = max(0, y_top - text_margin)
                    logger.info(f"Điều chỉnh lề trên cho hàng {i+1} do phát hiện text")
                
                bottom_margin_region = (0, safe_bottom, width, y_bottom)
                if check_text_in_region(table_image, bottom_margin_region):
                    y_bottom = min(height, y_bottom + text_margin)
                    logger.info(f"Điều chỉnh lề dưới cho hàng {i+1} do phát hiện text")
            
            # Kiểm tra chiều cao hàng
            row_height = y_bottom - y_top
            current_box = (y_top, y_bottom)
            
            # Xử lý hàng nhỏ
            if row_height < avg_row_height * 0.1:  # Hàng nhỏ hơn 10% chiều cao trung bình
                logger.info(f"Phát hiện hàng nhỏ {i+1}: {row_height}px < {avg_row_height * 0.1:.2f}px")
                
                # Kiểm tra IoU với hàng trước và sau
                prev_box = row_boxes[-1] if row_boxes else None
                next_box = (line_positions[i+1], line_positions[i+2]) if i < len(line_positions) - 2 else None
                
                prev_iou = calculate_iou(current_box, prev_box) if prev_box else 0
                next_iou = calculate_iou(current_box, next_box) if next_box else 0
                
                if (prev_iou > 0.5 or next_iou > 0.5):  # IoU > 50%
                    # Tính khoảng cách đến hàng trước và sau
                    dist_to_prev = abs(y_top - prev_box[1]) if prev_box else float('inf')
                    dist_to_next = abs(y_bottom - next_box[0]) if next_box else float('inf')
                    
                    # Mở rộng về phía có khoảng cách lớn hơn
                    if dist_to_prev > dist_to_next and prev_box:
                        # Mở rộng lên trên
                        y_top = max(0, y_top - (avg_row_height - row_height))
                        logger.info(f"Mở rộng hàng {i+1} lên trên")
                    elif next_box:
                        # Mở rộng xuống dưới
                        y_bottom = min(height, y_bottom + (avg_row_height - row_height))
                        logger.info(f"Mở rộng hàng {i+1} xuống dưới")
                    
                    row_height = y_bottom - y_top
                    current_box = (y_top, y_bottom)
            
            # Kiểm tra lại chiều cao sau khi xử lý
            if row_height < min_row_height:
                logger.warning(f"Bỏ qua hàng {i+1} do chiều cao quá nhỏ: {row_height}px < {min_row_height}px")
                skipped_small_rows_count += 1
                cv2.rectangle(debug_image, (0, y_top), (width, y_bottom), (255, 0, 255), 2)
                cv2.putText(debug_image, f"Small Row {i+1} ({row_height}px)", (10, y_top+20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
                continue
            
            # Cắt hàng từ ảnh gốc
            row = table_image[y_top:y_bottom, 0:width]
            
            # Kiểm tra text trong hàng
            has_text = True
            if check_text:
                has_text = check_text_in_region(row, (0, 0, width, row_height))
            
            if not has_text:
                empty_rows_count += 1
                logger.warning(f"Cảnh báo: Hàng {i+1} không có text")
                cv2.rectangle(debug_image, (0, y_top), (width, y_bottom), (0, 0, 255), 2)
                cv2.putText(debug_image, f"Empty Row {i+1}", (10, y_top+20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                cv2.rectangle(debug_image, (0, y_top), (width, y_bottom), (0, 255, 0), 2)
                cv2.putText(debug_image, f"Row {i+1} ({row_height}px)", (10, y_top+20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.line(debug_image, (0, safe_top), (width, safe_top), (255, 255, 0), 1)
                cv2.line(debug_image, (0, safe_bottom), (width, safe_bottom), (255, 255, 0), 1)
            
            rows.append(row)
            row_boxes.append(current_box)
        
        # Lưu ảnh debug
        if self.debug:
            debug_path = os.path.join(self.debug_dir, f"table_{table_id}_rows.jpg")
            cv2.imwrite(debug_path, debug_image)
            
            # Lưu từng hàng riêng biệt
            rows_dir = os.path.join(self.debug_dir, f"table_{table_id}_rows")
            os.makedirs(rows_dir, exist_ok=True)
            for i, row in enumerate(rows):
                row_path = os.path.join(rows_dir, f"row_{i+1}.jpg")
                cv2.imwrite(row_path, row)
        
        if empty_rows_count > 0:
            logger.warning(f"Cảnh báo: Có {empty_rows_count}/{len(rows)} hàng không có text")
        
        if skipped_small_rows_count > 0:
            logger.warning(f"Cảnh báo: Đã bỏ qua {skipped_small_rows_count} hàng có chiều cao < {min_row_height}px")
        
        logger.info(f"Đã cắt {len(rows)} hàng từ bảng {table_id}")
        return rows

    def test_extract_rows_comparison(self, image_path: str) -> None:
        """So sánh kết quả extract rows giữa phương pháp hiện tại và phương pháp OCR
        
        Args:
            image_path: Đường dẫn đến ảnh cần test
        """
        try:
            import pytesseract
            from PIL import Image
            OCR_AVAILABLE = True
        except ImportError:
            logger.error("Không tìm thấy pytesseract. Vui lòng cài đặt: pip install pytesseract")
            return

        # Đọc và tiền xử lý ảnh
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"Không thể đọc ảnh từ {image_path}")
            return

        # Tạo thư mục debug cho test này
        test_debug_dir = os.path.join(self.debug_dir, "extract_rows_test")
        os.makedirs(test_debug_dir, exist_ok=True)

        # 1. Phương pháp hiện tại
        logger.info("1. Đang thử nghiệm phương pháp hiện tại...")
        current_rows = self.extract_rows_from_table(image, table_id=1)
        
        # Lưu các hàng được phát hiện bởi phương pháp hiện tại
        current_debug_dir = os.path.join(test_debug_dir, "current_method")
        os.makedirs(current_debug_dir, exist_ok=True)
        for i, row in enumerate(current_rows):
            row_path = os.path.join(current_debug_dir, f"row_{i+1}.jpg")
            cv2.imwrite(row_path, row)
        logger.info(f"Phương pháp hiện tại phát hiện được {len(current_rows)} hàng")

        # 2. Phương pháp OCR
        logger.info("2. Đang thử nghiệm phương pháp OCR...")
        
        # Tiền xử lý ảnh cho OCR
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Lưu ảnh đã tiền xử lý
        preprocessed_path = os.path.join(test_debug_dir, "preprocessed.jpg")
        cv2.imwrite(preprocessed_path, binary)

        # Thực hiện OCR với bounding boxes
        ocr_debug_image = image.copy()
        height, width = image.shape[:2]

        # Lấy thông tin về boxes và text
        ocr_data = pytesseract.image_to_data(binary, output_type=pytesseract.Output.DICT)
        
        # Lọc và gom nhóm các boxes theo hàng
        boxes = []
        for i in range(len(ocr_data['text'])):
            # Chỉ xử lý các box có text và độ tin cậy cao
            if not ocr_data['text'][i].strip() or int(ocr_data['conf'][i]) < 50:  # Tăng ngưỡng tin cậy
                continue
                
            x = ocr_data['left'][i]
            y = ocr_data['top'][i]
            w = ocr_data['width'][i]
            h = ocr_data['height'][i]
            text = ocr_data['text'][i].strip()
            boxes.append((x, y, w, h, text))
        
        # Sắp xếp boxes theo y
        boxes.sort(key=lambda box: box[1])
        
        # Gom nhóm boxes thành các hàng
        row_boxes = []
        current_row = []
        min_row_gap = 40  # Tăng khoảng cách tối thiểu giữa các hàng
        min_row_height = 25  # Tăng chiều cao tối thiểu của hàng
        min_text_ratio = 0.1  # Tỷ lệ diện tích text tối thiểu
        
        def get_row_bounds(row_boxes):
            """Tính toán biên của một hàng"""
            min_x = min(box[0] for box in row_boxes)
            min_y = min(box[1] for box in row_boxes)
            max_x = max(box[0] + box[2] for box in row_boxes)
            max_y = max(box[1] + box[3] for box in row_boxes)
            return min_x, min_y, max_x, max_y
        
        def check_horizontal_alignment(box1, box2, tolerance=0.5):
            """Kiểm tra căn chỉnh ngang giữa hai box"""
            _, y1, _, y1_max = get_row_bounds([box1])
            _, y2, _, y2_max = get_row_bounds([box2])
            h1 = y1_max - y1
            h2 = y2_max - y2
            overlap = min(y1_max, y2_max) - max(y1, y2)
            return overlap >= min(h1, h2) * tolerance
        
        for box in boxes:
            x, y, w, h, text = box
            
            # Nếu là box đầu tiên hoặc gần với hàng hiện tại và căn chỉnh ngang
            if not current_row or (
                abs(y - current_row[-1][1]) < min_row_gap and 
                check_horizontal_alignment(box, current_row[-1])
            ):
                current_row.append(box)
            else:
                # Kiểm tra chiều cao và tỷ lệ text của hàng hiện tại
                if current_row:
                    min_x, min_y, max_x, max_y = get_row_bounds(current_row)
                    row_height = max_y - min_y
                    row_width = max_x - min_x
                    text_area = sum(b[2] * b[3] for b in current_row)
                    row_area = row_height * row_width
                    
                    if (row_height >= min_row_height and 
                        text_area / row_area >= min_text_ratio):
                        row_boxes.append(current_row)
                
                current_row = [box]
        
        # Thêm hàng cuối cùng nếu thỏa mãn điều kiện
        if current_row:
            min_x, min_y, max_x, max_y = get_row_bounds(current_row)
            row_height = max_y - min_y
            row_width = max_x - min_x
            text_area = sum(b[2] * b[3] for b in current_row)
            row_area = row_height * row_width
            
            if (row_height >= min_row_height and 
                text_area / row_area >= min_text_ratio):
                row_boxes.append(current_row)

        # Cắt và lưu các hàng từ phương pháp OCR
        ocr_rows = []
        ocr_debug_dir = os.path.join(test_debug_dir, "ocr_method")
        os.makedirs(ocr_debug_dir, exist_ok=True)

        for i, row_box_list in enumerate(row_boxes):
            if not row_box_list:
                continue

            # Tính toán bounding box cho cả hàng
            min_x, min_y, max_x, max_y = get_row_bounds(row_box_list)

            # Thêm padding
            padding = 10
            min_x = max(0, min_x - padding)
            min_y = max(0, min_y - padding)
            max_x = min(width, max_x + padding)
            max_y = min(height, max_y + padding)

            # Cắt hàng
            row_img = image[min_y:max_y, min_x:max_x]
            
            # Kiểm tra kích thước tối thiểu và tỷ lệ chiều rộng
            if (row_img.shape[0] >= min_row_height and 
                row_img.shape[1] >= width * 0.3):
                ocr_rows.append(row_img)

                # Lưu ảnh hàng
                row_path = os.path.join(ocr_debug_dir, f"row_{len(ocr_rows)}.jpg")
                cv2.imwrite(row_path, row_img)

                # Vẽ bounding box và text trên ảnh debug
                cv2.rectangle(ocr_debug_image, (min_x, min_y), (max_x, max_y), (0, 255, 0), 2)
                cv2.putText(ocr_debug_image, f"Row {len(ocr_rows)}", (min_x, min_y-5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Vẽ text được phát hiện
                text_list = [box[4] for box in row_box_list]
                text = " | ".join(text_list)
                cv2.putText(ocr_debug_image, text[:50], (min_x, max_y+15),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 1)

        # Lưu ảnh debug với các bounding box
        cv2.imwrite(os.path.join(test_debug_dir, "ocr_detection.jpg"), ocr_debug_image)

        # So sánh kết quả
        logger.info("\nKết quả so sánh:")
        logger.info(f"1. Phương pháp hiện tại: {len(current_rows)} hàng")
        logger.info(f"2. Phương pháp OCR: {len(ocr_rows)} hàng")
        logger.info(f"Chênh lệch: {abs(len(current_rows) - len(ocr_rows))} hàng")
        logger.info(f"\nĐã lưu kết quả debug trong thư mục: {test_debug_dir}")
        logger.info("- current_method/: Các hàng được phát hiện bởi phương pháp hiện tại")
        logger.info("- ocr_method/: Các hàng được phát hiện bởi phương pháp OCR")
        logger.info("- ocr_detection.jpg: Ảnh với các bounding box từ OCR")
        logger.info("- preprocessed.jpg: Ảnh đã tiền xử lý cho OCR")

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Tiền xử lý ảnh trước khi phát hiện đường kẻ
        
        Args:
            image: Ảnh đầu vào
            
        Returns:
            np.ndarray: Ảnh đã tiền xử lý
        """
        # Chuyển sang ảnh xám nếu cần
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            
        # Làm mịn ảnh để giảm nhiễu
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Nhị phân hóa với Otsu's thresholding
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Lưu ảnh đã tiền xử lý để debug
        if self.debug:
            debug_path = os.path.join(self.debug_dir, "preprocessed.jpg")
            cv2.imwrite(debug_path, binary)
            logger.info(f"Đã lưu ảnh đã tiền xử lý: {debug_path}")
        
        return binary

    def _filter_close_lines(self, line_positions: List[int], min_distance: int = 15) -> List[int]:
        """Lọc các đường kẻ quá gần nhau
        
        Args:
            line_positions: Danh sách vị trí các đường kẻ
            min_distance: Khoảng cách tối thiểu giữa các đường kẻ
            
        Returns:
            List[int]: Danh sách vị trí đường kẻ sau khi lọc
        """
        if not line_positions:
            return []
            
        # Sắp xếp các vị trí
        sorted_positions = sorted(line_positions)
        
        # Lọc các đường kẻ quá gần nhau
        filtered = [sorted_positions[0]]  # Giữ lại đường kẻ đầu tiên
        
        for pos in sorted_positions[1:]:
            # So sánh với đường kẻ gần nhất đã được giữ lại
            if pos - filtered[-1] >= min_distance:
                filtered.append(pos)
                
        return filtered

    def _extract_rows_fallback(self, table_image: np.ndarray, table_id: int) -> List[np.ndarray]:
        """Phương pháp dự phòng để cắt các hàng khi không phát hiện được đường kẻ
        
        Args:
            table_image: Ảnh bảng
            table_id: ID của bảng
            
        Returns:
            List[np.ndarray]: Danh sách các ảnh hàng đã cắt
        """
        logger.info("Sử dụng phương pháp dự phòng để cắt hàng...")
        
        # Chuyển sang ảnh xám và nhị phân hóa
        if len(table_image.shape) == 3:
            gray = cv2.cvtColor(table_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = table_image.copy()
        
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Tính histogram theo chiều dọc
        v_projection = np.sum(binary, axis=1)
        
        # Chuẩn hóa histogram
        v_projection = v_projection / np.max(v_projection)
        
        # Tìm các vùng trống (khoảng trắng giữa các hàng)
        height = table_image.shape[0]
        min_gap = 10  # Khoảng trống tối thiểu
        gap_threshold = 0.1  # Ngưỡng để xác định khoảng trống
        
        # Tìm các điểm bắt đầu và kết thúc của khoảng trống
        gaps = []
        start_gap = None
        
        for y in range(height):
            if v_projection[y] < gap_threshold:
                if start_gap is None:
                    start_gap = y
            elif start_gap is not None:
                if y - start_gap >= min_gap:
                    gaps.append((start_gap, y))
                start_gap = None
        
        # Thêm điểm cuối nếu đang trong khoảng trống
        if start_gap is not None and height - start_gap >= min_gap:
            gaps.append((start_gap, height))
        
        # Cắt các hàng dựa trên khoảng trống
        rows = []
        prev_end = 0
        
        for gap_start, gap_end in gaps:
            if gap_start > prev_end:
                # Cắt hàng từ điểm kết thúc trước đến điểm bắt đầu khoảng trống
                row = table_image[prev_end:gap_start]
                if row.shape[0] >= 20:  # Chỉ lấy các hàng đủ cao
                    rows.append(row)
            prev_end = gap_end
        
        # Thêm hàng cuối cùng nếu cần
        if prev_end < height:
            row = table_image[prev_end:height]
            if row.shape[0] >= 20:
                rows.append(row)
        
        logger.info(f"Đã cắt được {len(rows)} hàng bằng phương pháp dự phòng")
        
        # Lưu ảnh debug
        if self.debug:
            debug_image = table_image.copy()
            for i, row in enumerate(rows):
                y_start = sum(r.shape[0] for r in rows[:i])
                y_end = y_start + row.shape[0]
                cv2.rectangle(debug_image, (0, y_start), (table_image.shape[1], y_end), (0, 255, 0), 2)
                cv2.putText(debug_image, f"Row {i+1}", (10, y_start+20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            debug_path = os.path.join(self.debug_dir, f"table_{table_id}_rows_fallback.jpg")
            cv2.imwrite(debug_path, debug_image)
        
        return rows

    def extract_rows_using_ocr(self, image_path: str, output_dir: Optional[str] = None,
                                min_row_height: int = 30) -> List[str]:
        """
        Phát hiện và trích xuất các hàng từ ảnh sử dụng OCR.
        
        Args:
            image_path: Đường dẫn đến ảnh
            output_dir: Thư mục để lưu ảnh các hàng (nếu None, sử dụng thư mục của ảnh gốc)
            min_row_height: Chiều cao tối thiểu của mỗi hàng
            
        Returns:
            List: Danh sách đường dẫn đến ảnh các hàng
        """
        try:
            # Kiểm tra pytesseract
            import pytesseract
            
            # Đọc ảnh
            img = cv2.imread(image_path)
            if img is None:
                logger.error(f"Không thể đọc ảnh: {image_path}")
                return []
                
            # Tiền xử lý ảnh
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (3, 3), 0)
            thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                         cv2.THRESH_BINARY, 11, 2)
                                         
            # Thực hiện OCR
            config = r'--oem 3 --psm 6'
            boxes = pytesseract.image_to_boxes(thresh, config=config)
            
            if not boxes:
                logger.warning("Không phát hiện được text trong ảnh")
                return []
                
            # Chuyển đổi boxes thành danh sách tọa độ
            height = img.shape[0]
            boxes_list = []
            for b in boxes.splitlines():
                b = b.split(' ')
                boxes_list.append({
                    'x': int(b[1]),
                    'y': height - int(b[2]),  # Chuyển đổi tọa độ y
                    'w': int(b[3]) - int(b[1]),
                    'h': int(b[4]) - int(b[2]),
                    'char': b[0]
                })
                
            # Lọc các box có độ tin cậy thấp
            boxes_list = [b for b in boxes_list if b['h'] >= min_row_height * 0.3]
            
            # Nhóm các box thành hàng
            rows = []
            current_row = [boxes_list[0]]
            min_gap = min_row_height * 0.5  # Giảm khoảng cách tối thiểu
            
            for box in boxes_list[1:]:
                # Kiểm tra overlap với hàng hiện tại
                current_y = sum(b['y'] for b in current_row) / len(current_row)
                if abs(box['y'] - current_y) < min_gap:
                    current_row.append(box)
                else:
                    if len(current_row) > 0:
                        rows.append(current_row)
                    current_row = [box]
                    
            if len(current_row) > 0:
                rows.append(current_row)
                
            # Sắp xếp các hàng theo y
            rows.sort(key=lambda r: sum(b['y'] for b in r) / len(r))
            
            # Cắt và lưu ảnh các hàng
            if output_dir is None:
                output_dir = os.path.dirname(image_path)
                
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            row_paths = []
            for i, row in enumerate(rows):
                # Tính toán vùng cắt
                min_x = min(b['x'] for b in row)
                max_x = max(b['x'] + b['w'] for b in row)
                min_y = min(b['y'] - b['h'] for b in row)
                max_y = max(b['y'] for b in row)
                
                # Thêm margin
                margin = min_row_height // 4
                min_x = max(0, min_x - margin)
                max_x = min(img.shape[1], max_x + margin)
                min_y = max(0, min_y - margin)
                max_y = min(img.shape[0], max_y + margin)
                
                # Cắt hàng
                row_img = img[min_y:max_y, min_x:max_x]
                
                # Lưu ảnh hàng
                row_filename = f"row_{i+1}.jpg"
                row_path = os.path.join(output_dir, row_filename)
                cv2.imwrite(row_path, row_img)
                row_paths.append(row_path)
                
            logger.info(f"Đã trích xuất {len(row_paths)} hàng sử dụng OCR")
            return row_paths
            
        except Exception as e:
            logger.error(f"Lỗi khi trích xuất hàng bằng OCR: {str(e)}")
            return []

 
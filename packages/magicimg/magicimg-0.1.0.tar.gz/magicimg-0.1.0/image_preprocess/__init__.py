"""
image-preprocess: Package xử lý và tiền xử lý ảnh cho OCR và computer vision

Tác giả: Tác giả
Email: tacgia@email.com
Phiên bản: 0.1.0
"""

__version__ = "0.1.0"
__author__ = "Tác giả"
__email__ = "tacgia@email.com"
__license__ = "MIT"

# Import các class và function chính
from .core import (
    ImageProcessor,
    ImageQualityMetrics,
    ProcessingResult
)

# Import các utility functions
from .utils import (
    check_tesseract_installed,
    validate_image_path,
    create_debug_dir
)

# Định nghĩa các hàm tiện ích
def preprocess_for_ocr(image_path, output_path=None, **kwargs):
    """
    Hàm tiện ích để tiền xử lý ảnh cho OCR
    
    Args:
        image_path (str): Đường dẫn đến ảnh đầu vào
        output_path (str, optional): Đường dẫn lưu ảnh đã xử lý
        **kwargs: Các tham số tùy chỉnh
        
    Returns:
        ProcessingResult: Kết quả xử lý ảnh
    """
    processor = ImageProcessor(**kwargs)
    return processor.process_image(image_path, output_path)

def check_image_quality(image_path, **kwargs):
    """
    Hàm kiểm tra chất lượng ảnh
    
    Args:
        image_path (str): Đường dẫn đến ảnh
        **kwargs: Các tham số tùy chỉnh
        
    Returns:
        tuple: (is_good, quality_info, enhanced_image)
    """
    import cv2
    processor = ImageProcessor(**kwargs)
    image = cv2.imread(image_path)
    return processor.check_quality(image)

def detect_orientation(image_path, **kwargs):
    """
    Hàm phát hiện hướng ảnh
    
    Args:
        image_path (str): Đường dẫn đến ảnh
        **kwargs: Các tham số tùy chỉnh
        
    Returns:
        int: Góc xoay cần điều chỉnh (0, 90, 180, 270)
    """
    import cv2
    processor = ImageProcessor(**kwargs)
    image = cv2.imread(image_path)
    return processor.detect_orientation(image)

# Định nghĩa các hằng số
DEFAULT_CONFIG = {
    "min_blur_index": 80.0,
    "max_dark_ratio": 0.2,
    "min_brightness": 180.0,
    "min_contrast": 50.0,
    "min_resolution": (1000, 1400),
    "min_quality_score": 0.7,
}

# Export tất cả public API
__all__ = [
    # Classes
    "ImageProcessor",
    "ImageQualityMetrics", 
    "ProcessingResult",
    # Utility functions
    "preprocess_for_ocr",
    "check_image_quality",
    "detect_orientation",
    "check_tesseract_installed",
    "validate_image_path",
    "create_debug_dir",
    # Constants
    "DEFAULT_CONFIG",
] 
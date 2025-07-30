"""
image-preprocess: Package xử lý và tiền xử lý ảnh cho OCR và computer vision

Tác giả: Tác giả
Email: shumi2011@gmail.com
Phiên bản: 0.1.0
"""

__version__ = "0.1.3"
__author__ = "Tác giả"
__email__ = "shumi2011@gmail.com"
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

# Định nghĩa các hàm tiện ích từ ImageProcessor
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

def process_image(image_path, output_path=None, auto_rotate=True, **kwargs):
    """
    Hàm xử lý ảnh với các bước tối ưu
    
    Args:
        image_path (str): Đường dẫn đến ảnh đầu vào
        output_path (str, optional): Đường dẫn lưu ảnh đã xử lý
        auto_rotate (bool): Có tự động xoay ảnh hay không
        **kwargs: Các tham số tùy chỉnh
        
    Returns:
        ProcessingResult: Kết quả xử lý ảnh
    """
    processor = ImageProcessor(**kwargs)
    return processor.process_image(image_path, output_path, auto_rotate)

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

def enhance_image(image_path, output_path=None, **kwargs):
    """
    Hàm tăng cường chất lượng ảnh
    
    Args:
        image_path (str): Đường dẫn đến ảnh
        output_path (str, optional): Đường dẫn lưu ảnh đã tăng cường
        **kwargs: Các tham số tùy chỉnh
        
    Returns:
        numpy.ndarray: Ảnh đã tăng cường chất lượng
    """
    import cv2
    processor = ImageProcessor(**kwargs)
    image = cv2.imread(image_path)
    _, quality_info, enhanced = processor.check_quality(image)
    
    if output_path and enhanced is not None:
        cv2.imwrite(output_path, enhanced)
    
    return enhanced

def enhance_image_for_ocr(image_path, output_path=None, **kwargs):
    """
    Hàm tăng cường ảnh đặc biệt cho OCR
    
    Args:
        image_path (str): Đường dẫn đến ảnh
        output_path (str, optional): Đường dẫn lưu ảnh đã tăng cường
        **kwargs: Các tham số tùy chỉnh
        
    Returns:
        numpy.ndarray: Ảnh đã tăng cường cho OCR
    """
    import cv2
    processor = ImageProcessor(**kwargs)
    image = cv2.imread(image_path)
    enhanced = processor.enhance_image_for_ocr(image)
    
    if output_path:
        cv2.imwrite(output_path, enhanced)
    
    return enhanced

def rotate_image(image_path, angle, output_path=None, **kwargs):
    """
    Hàm xoay ảnh theo góc cho trước
    
    Args:
        image_path (str): Đường dẫn đến ảnh
        angle (int): Góc xoay (0, 90, 180, 270)
        output_path (str, optional): Đường dẫn lưu ảnh đã xoay
        **kwargs: Các tham số tùy chỉnh
        
    Returns:
        numpy.ndarray: Ảnh đã xoay
    """
    import cv2
    processor = ImageProcessor(**kwargs)
    image = cv2.imread(image_path)
    rotated = processor.rotate_image(image, angle)
    
    if output_path:
        cv2.imwrite(output_path, rotated)
    
    return rotated

def detect_skew(image_path, **kwargs):
    """
    Hàm phát hiện góc nghiêng của ảnh
    
    Args:
        image_path (str): Đường dẫn đến ảnh
        **kwargs: Các tham số tùy chỉnh
        
    Returns:
        float: Góc nghiêng (độ)
    """
    import cv2
    processor = ImageProcessor(**kwargs)
    image = cv2.imread(image_path)
    return processor.detect_skew(image)

def correct_skew(image_path, angle=None, output_path=None, **kwargs):
    """
    Hàm chỉnh sửa góc nghiêng của ảnh
    
    Args:
        image_path (str): Đường dẫn đến ảnh
        angle (float, optional): Góc nghiêng cần sửa. Nếu None sẽ tự động phát hiện
        output_path (str, optional): Đường dẫn lưu ảnh đã sửa
        **kwargs: Các tham số tùy chỉnh
        
    Returns:
        numpy.ndarray: Ảnh đã sửa góc nghiêng
    """
    import cv2
    processor = ImageProcessor(**kwargs)
    image = cv2.imread(image_path)
    
    if angle is None:
        angle = processor.detect_skew(image)
    
    corrected = processor.correct_skew(image, angle)
    
    if output_path:
        cv2.imwrite(output_path, corrected)
    
    return corrected

def detect_horizontal_lines(image_path, **kwargs):
    """
    Hàm phát hiện các đường kẻ ngang trong ảnh
    
    Args:
        image_path (str): Đường dẫn đến ảnh
        **kwargs: Các tham số tùy chỉnh
        
    Returns:
        List[int]: Danh sách các tọa độ y của đường kẻ ngang
    """
    import cv2
    processor = ImageProcessor(**kwargs)
    image = cv2.imread(image_path)
    processed = processor.preprocess_image(image)
    return processor.detect_horizontal_lines(processed)

def extract_rows_from_table(image_path, table_id=1, output_dir=None, **kwargs):
    """
    Hàm cắt các hàng từ ảnh bảng
    
    Args:
        image_path (str): Đường dẫn đến ảnh bảng
        table_id (int): ID của bảng
        output_dir (str, optional): Thư mục lưu ảnh các hàng
        **kwargs: Các tham số tùy chỉnh
        
    Returns:
        List[numpy.ndarray]: Danh sách các ảnh hàng đã cắt
    """
    import cv2
    import os
    processor = ImageProcessor(**kwargs)
    image = cv2.imread(image_path)
    rows = processor.extract_rows_from_table(image, table_id)
    
    # Lưu các hàng nếu có output_dir
    if output_dir and rows:
        os.makedirs(output_dir, exist_ok=True)
        for i, row in enumerate(rows):
            row_path = os.path.join(output_dir, f"row_{i+1}.jpg")
            cv2.imwrite(row_path, row)
    
    return rows

def extract_rows_using_ocr(image_path, output_dir=None, min_row_height=30, **kwargs):
    """
    Hàm cắt các hàng từ ảnh sử dụng OCR
    
    Args:
        image_path (str): Đường dẫn đến ảnh
        output_dir (str, optional): Thư mục lưu ảnh các hàng
        min_row_height (int): Chiều cao tối thiểu của hàng
        **kwargs: Các tham số tùy chỉnh
        
    Returns:
        List[str]: Danh sách đường dẫn đến ảnh các hàng
    """
    processor = ImageProcessor(**kwargs)
    return processor.extract_rows_using_ocr(image_path, output_dir, min_row_height)

def preprocess_image(image_path, output_path=None, **kwargs):
    """
    Hàm tiền xử lý ảnh
    
    Args:
        image_path (str): Đường dẫn đến ảnh
        output_path (str, optional): Đường dẫn lưu ảnh đã tiền xử lý
        **kwargs: Các tham số tùy chỉnh
        
    Returns:
        numpy.ndarray: Ảnh đã tiền xử lý
    """
    import cv2
    processor = ImageProcessor(**kwargs)
    image = cv2.imread(image_path)
    processed = processor.preprocess_image(image)
    
    if output_path:
        cv2.imwrite(output_path, processed)
    
    return processed

# Static methods từ ImageProcessor
def preprocess_image_for_api(image_path, provider="google", output_dir=None, debug_dir=None, 
                            min_quality_score=0.4, auto_rotate=False):
    """
    Hàm tiền xử lý ảnh cho các API nhà cung cấp
    
    Args:
        image_path (str): Đường dẫn đến ảnh
        provider (str): Nhà cung cấp API ("google", "anthropic", "local")
        output_dir (str, optional): Thư mục lưu ảnh đã xử lý
        debug_dir (str, optional): Thư mục lưu ảnh debug
        min_quality_score (float): Điểm chất lượng tối thiểu
        auto_rotate (bool): Có tự động xoay ảnh hay không
        
    Returns:
        Tuple[bool, Dict[str, Any], Optional[str]]: (success, info, output_path)
    """
    return ImageProcessor.preprocess_image_for_api(
        image_path, provider, output_dir, debug_dir, min_quality_score, auto_rotate
    )

def test_extract_rows_comparison(image_path, **kwargs):
    """
    Hàm so sánh kết quả extract rows giữa các phương pháp
    
    Args:
        image_path (str): Đường dẫn đến ảnh test
        **kwargs: Các tham số tùy chỉnh
    """
    processor = ImageProcessor(**kwargs)
    return processor.test_extract_rows_comparison(image_path)

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
    
    # Main processing functions
    "preprocess_for_ocr",
    "process_image",
    
    # Quality and enhancement functions
    "check_image_quality",
    "enhance_image",
    "enhance_image_for_ocr",
    
    # Orientation and skew functions
    "detect_orientation",
    "rotate_image", 
    "detect_skew",
    "correct_skew",
    
    # Table processing functions
    "detect_horizontal_lines",
    "extract_rows_from_table",
    "extract_rows_using_ocr",
    
    # Image preprocessing functions
    "preprocess_image",
    "preprocess_image_for_api",
    
    # Testing and utility functions
    "test_extract_rows_comparison",
    "check_tesseract_installed",
    "validate_image_path",
    "create_debug_dir",
    
    # Constants
    "DEFAULT_CONFIG",
] 
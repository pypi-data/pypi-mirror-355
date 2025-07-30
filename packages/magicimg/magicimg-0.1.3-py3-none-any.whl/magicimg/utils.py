"""
Các hàm tiện ích cho package image-preprocess
"""

import os
import sys
import logging
import shutil
from pathlib import Path
from typing import Optional, Union, List

logger = logging.getLogger(__name__)

def check_tesseract_installed() -> bool:
    """
    Kiểm tra xem Tesseract OCR có được cài đặt hay không
    
    Returns:
        bool: True nếu Tesseract được cài đặt, False nếu không
    """
    try:
        import pytesseract
        # Thử gọi pytesseract để kiểm tra
        pytesseract.get_tesseract_version()
        return True
    except ImportError:
        logger.warning("pytesseract không được cài đặt. Cài đặt bằng: pip install pytesseract")
        return False
    except Exception as e:
        logger.warning(f"Tesseract không khả dụng: {str(e)}")
        return False

def validate_image_path(image_path: Union[str, Path]) -> bool:
    """
    Kiểm tra đường dẫn ảnh có hợp lệ hay không
    
    Args:
        image_path: Đường dẫn đến file ảnh
        
    Returns:
        bool: True nếu đường dẫn hợp lệ, False nếu không
    """
    if not image_path:
        logger.error("Đường dẫn ảnh không được để trống")
        return False
    
    path = Path(image_path)
    
    if not path.exists():
        logger.error(f"File không tồn tại: {image_path}")
        return False
    
    if not path.is_file():
        logger.error(f"Đường dẫn không phải file: {image_path}")
        return False
    
    # Kiểm tra phần mở rộng file
    valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}
    if path.suffix.lower() not in valid_extensions:
        logger.error(f"Định dạng file không được hỗ trợ: {path.suffix}")
        return False
    
    return True

def create_debug_dir(base_dir: Union[str, Path], name: str = "debug") -> str:
    """
    Tạo thư mục debug
    
    Args:
        base_dir: Thư mục gốc
        name: Tên thư mục debug
        
    Returns:
        str: Đường dẫn đến thư mục debug
    """
    debug_dir = Path(base_dir) / name
    debug_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Đã tạo thư mục debug: {debug_dir}")
    return str(debug_dir)

def get_image_info(image_path: Union[str, Path]) -> dict:
    """
    Lấy thông tin cơ bản về ảnh
    
    Args:
        image_path: Đường dẫn đến file ảnh
        
    Returns:
        dict: Thông tin về ảnh
    """
    import cv2
    
    if not validate_image_path(image_path):
        return {}
    
    try:
        # Đọc ảnh
        image = cv2.imread(str(image_path))
        if image is None:
            return {"error": "Không thể đọc ảnh"}
        
        # Lấy thông tin cơ bản
        height, width = image.shape[:2]
        channels = image.shape[2] if len(image.shape) == 3 else 1
        
        # Lấy thông tin file
        file_path = Path(image_path)
        file_size = file_path.stat().st_size
        
        return {
            "file_path": str(file_path.absolute()),
            "file_name": file_path.name,
            "file_size": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "width": width,
            "height": height,
            "channels": channels,
            "total_pixels": width * height,
            "aspect_ratio": round(width / height, 2) if height > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Lỗi khi lấy thông tin ảnh: {str(e)}")
        return {"error": str(e)}

def clean_debug_dir(debug_dir: Union[str, Path], keep_latest: int = 5) -> None:
    """
    Dọn dẹp thư mục debug, chỉ giữ lại những file mới nhất
    
    Args:
        debug_dir: Thư mục debug
        keep_latest: Số lượng file mới nhất cần giữ lại
    """
    debug_path = Path(debug_dir)
    
    if not debug_path.exists():
        return
    
    try:
        # Lấy danh sách tất cả file
        files = list(debug_path.glob("*"))
        files = [f for f in files if f.is_file()]
        
        if len(files) <= keep_latest:
            return
        
        # Sắp xếp theo thời gian sửa đổi
        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Xóa các file cũ
        files_to_delete = files[keep_latest:]
        deleted_count = 0
        
        for file in files_to_delete:
            try:
                file.unlink()
                deleted_count += 1
            except Exception as e:
                logger.warning(f"Không thể xóa file {file}: {str(e)}")
        
        if deleted_count > 0:
            logger.info(f"Đã xóa {deleted_count} file cũ trong thư mục debug")
            
    except Exception as e:
        logger.error(f"Lỗi khi dọn dẹp thư mục debug: {str(e)}")

def check_dependencies() -> dict:
    """
    Kiểm tra các dependency có được cài đặt hay không
    
    Returns:
        dict: Trạng thái các dependency
    """
    dependencies = {
        "opencv-python": False,
        "numpy": False,
        "matplotlib": False,
        "pytesseract": False,
        "Pillow": False
    }
    
    # Kiểm tra OpenCV
    try:
        import cv2
        dependencies["opencv-python"] = True
    except ImportError:
        pass
    
    # Kiểm tra NumPy
    try:
        import numpy
        dependencies["numpy"] = True
    except ImportError:
        pass
    
    # Kiểm tra Matplotlib
    try:
        import matplotlib
        dependencies["matplotlib"] = True
    except ImportError:
        pass
    
    # Kiểm tra pytesseract
    try:
        import pytesseract
        dependencies["pytesseract"] = True
    except ImportError:
        pass
    
    # Kiểm tra Pillow
    try:
        from PIL import Image
        dependencies["Pillow"] = True
    except ImportError:
        pass
    
    return dependencies

def get_missing_dependencies() -> List[str]:
    """
    Lấy danh sách các dependency bị thiếu
    
    Returns:
        List[str]: Danh sách các package bị thiếu
    """
    deps = check_dependencies()
    missing = [name for name, installed in deps.items() if not installed]
    return missing

def print_system_info():
    """In thông tin hệ thống và dependencies"""
    print("=== THÔNG TIN HỆ THỐNG ===")
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    
    print("\n=== TRẠNG THÁI DEPENDENCIES ===")
    deps = check_dependencies()
    for name, installed in deps.items():
        status = "✓ Đã cài đặt" if installed else "✗ Chưa cài đặt"
        print(f"{name}: {status}")
    
    missing = get_missing_dependencies()
    if missing:
        print(f"\nCác package cần cài đặt: {', '.join(missing)}")
        print("Chạy lệnh: pip install " + " ".join(missing))
    else:
        print("\n✓ Tất cả dependencies đã được cài đặt!")

def create_sample_config() -> dict:
    """
    Tạo cấu hình mẫu cho ImageProcessor
    
    Returns:
        dict: Cấu hình mẫu
    """
    return {
        # Ngưỡng chất lượng
        "min_blur_index": 80.0,
        "max_dark_ratio": 0.2,
        "min_brightness": 180.0,
        "min_contrast": 50.0,
        "min_resolution": (1000, 1400),
        "min_quality_score": 0.7,
        
        # Ngưỡng xử lý
        "min_skew_angle": 0.3,
        "max_skew_angle": 30.0,
        "min_rotation_confidence": 0.8,
        
        # Cấu hình xử lý
        "skip_rotation": False,
        "reuse_rotation": None,
        
        # Từ khóa tìm kiếm
        "ballot_keywords": [
            "phieu bau cu", "doan dai bieu", "dai hoi", "dang bo",
            "nhiem ky", "stt", "ho va ten", "ha noi", "ngay", "thang", "nam"
        ],

        # Tham số phát hiện đường kẻ ngang
        "line_detection": {
            "min_line_length_ratio": 0.6,
            "min_length_threshold_ratio": 0.7,
            "max_line_height": 3,
            "morph_iterations": 1,
            "histogram_threshold_ratio": 0.5,
            "min_line_distance": 20,
            "dilate_kernel_div": 30,
            "horizontal_kernel_div": 5,
            "projection_threshold_div": 4
        },

        # Tham số cắt hàng
        "row_extraction": {
            "top_margin": 8,
            "bottom_margin": 8,
            "safe_zone": 5,
            "min_row_height": 20,
            "check_text": True,
            "text_margin": 3,
            "min_text_area": 0.003
        }
    } 
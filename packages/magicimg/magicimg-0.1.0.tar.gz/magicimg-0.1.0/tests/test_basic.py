"""
Test cơ bản cho image-preprocess package
"""

import unittest
import tempfile
import os
import numpy as np
import cv2
from pathlib import Path

# Import package
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from image_preprocess import ImageProcessor, check_image_quality
from image_preprocess.utils import validate_image_path, get_image_info, check_dependencies


class TestImagePreprocess(unittest.TestCase):
    """Test case cho image preprocess package"""
    
    def setUp(self):
        """Thiết lập test"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_image_path = self.create_test_image()
        
    def tearDown(self):
        """Dọn dẹp sau test"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_image(self):
        """Tạo ảnh test đơn giản"""
        # Tạo ảnh 500x700 với văn bản
        image = np.ones((700, 500, 3), dtype=np.uint8) * 255
        
        # Thêm text
        cv2.putText(image, "TEST IMAGE", (50, 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)
        cv2.putText(image, "Line 1: Some text here", (50, 200), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(image, "Line 2: More text content", (50, 300), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        # Vẽ một số đường kẻ ngang
        cv2.line(image, (50, 150), (450, 150), (0, 0, 0), 2)
        cv2.line(image, (50, 250), (450, 250), (0, 0, 0), 2)
        cv2.line(image, (50, 350), (450, 350), (0, 0, 0), 2)
        
        # Lưu ảnh
        image_path = os.path.join(self.temp_dir, "test_image.jpg")
        cv2.imwrite(image_path, image)
        return image_path
    
    def test_validate_image_path(self):
        """Test hàm validate_image_path"""
        # Test đường dẫn hợp lệ
        self.assertTrue(validate_image_path(self.test_image_path))
        
        # Test đường dẫn không tồn tại
        self.assertFalse(validate_image_path("nonexistent.jpg"))
        
        # Test đường dẫn trống
        self.assertFalse(validate_image_path(""))
        self.assertFalse(validate_image_path(None))
    
    def test_get_image_info(self):
        """Test hàm get_image_info"""
        info = get_image_info(self.test_image_path)
        
        # Kiểm tra thông tin cơ bản
        self.assertIn("width", info)
        self.assertIn("height", info)
        self.assertIn("channels", info)
        self.assertIn("file_size", info)
        
        # Kiểm tra kích thước
        self.assertEqual(info["width"], 500)
        self.assertEqual(info["height"], 700)
        self.assertEqual(info["channels"], 3)
    
    def test_check_dependencies(self):
        """Test kiểm tra dependencies"""
        deps = check_dependencies()
        
        # Kiểm tra các dependency chính
        expected_deps = ["opencv-python", "numpy", "matplotlib", "Pillow"]
        for dep in expected_deps:
            self.assertIn(dep, deps)
            self.assertTrue(deps[dep], f"{dep} should be installed")
    
    def test_image_processor_init(self):
        """Test khởi tạo ImageProcessor"""
        # Test khởi tạo cơ bản
        processor = ImageProcessor()
        self.assertIsNotNone(processor)
        self.assertIsNotNone(processor.config)
        
        # Test khởi tạo với debug_dir
        debug_dir = os.path.join(self.temp_dir, "debug")
        processor = ImageProcessor(debug_dir=debug_dir)
        self.assertTrue(os.path.exists(debug_dir))
        
        # Test khởi tạo với config
        custom_config = {"min_blur_index": 100.0}
        processor = ImageProcessor(config=custom_config)
        self.assertEqual(processor.config["min_blur_index"], 100.0)
    
    def test_check_image_quality(self):
        """Test kiểm tra chất lượng ảnh"""
        is_good, quality_info, enhanced_image = check_image_quality(self.test_image_path)
        
        # Kiểm tra kết quả
        self.assertIsInstance(is_good, bool)
        self.assertIsInstance(quality_info, dict)
        
        # Kiểm tra thông tin chất lượng
        expected_keys = ["blur_index", "dark_ratio", "brightness", "contrast", "resolution"]
        for key in expected_keys:
            self.assertIn(key, quality_info)
            self.assertIsInstance(quality_info[key], (int, float, tuple))
    
    def test_image_processor_check_quality(self):
        """Test kiểm tra chất lượng với ImageProcessor"""
        processor = ImageProcessor()
        image = cv2.imread(self.test_image_path)
        
        is_good, quality_info, enhanced_image = processor.check_quality(image)
        
        # Kiểm tra kết quả
        self.assertIsInstance(is_good, bool)
        self.assertIsInstance(quality_info, dict)
        
        # Enhanced image có thể là None hoặc numpy array
        if enhanced_image is not None:
            self.assertIsInstance(enhanced_image, np.ndarray)
    
    def test_image_processor_process_image(self):
        """Test xử lý ảnh hoàn chỉnh"""
        processor = ImageProcessor()
        output_path = os.path.join(self.temp_dir, "processed.jpg")
        
        result = processor.process_image(
            input_path=self.test_image_path,
            output_path=output_path,
            auto_rotate=False  # Tắt auto rotate để test nhanh hơn
        )
        
        # Kiểm tra kết quả
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, 'success'))
        self.assertTrue(hasattr(result, 'quality_metrics'))
        self.assertTrue(hasattr(result, 'processing_steps'))
        
        # Nếu thành công, file output phải tồn tại
        if result.success:
            self.assertTrue(os.path.exists(output_path))
    
    def test_image_processor_detect_skew(self):
        """Test phát hiện góc nghiêng"""
        processor = ImageProcessor()
        image = cv2.imread(self.test_image_path)
        
        angle = processor.detect_skew(image)
        
        # Góc nghiêng phải là số thực
        self.assertIsInstance(angle, (int, float))
        # Góc nghiêng thường trong khoảng [-45, 45]
        self.assertGreaterEqual(angle, -45)
        self.assertLessEqual(angle, 45)
    
    def test_image_processor_rotate_image(self):
        """Test xoay ảnh"""
        processor = ImageProcessor()
        image = cv2.imread(self.test_image_path)
        original_shape = image.shape
        
        # Test xoay 90 độ
        rotated_90 = processor.rotate_image(image, 90)
        self.assertEqual(rotated_90.shape[:2], (original_shape[1], original_shape[0]))
        
        # Test xoay 180 độ
        rotated_180 = processor.rotate_image(image, 180)
        self.assertEqual(rotated_180.shape, original_shape)
        
        # Test xoay 0 độ (không đổi)
        rotated_0 = processor.rotate_image(image, 0)
        np.testing.assert_array_equal(rotated_0, image)
    
    def test_enhance_image_for_ocr(self):
        """Test tăng cường chất lượng ảnh cho OCR"""
        processor = ImageProcessor()
        image = cv2.imread(self.test_image_path)
        
        enhanced = processor.enhance_image_for_ocr(image)
        
        # Enhanced image phải là numpy array
        self.assertIsInstance(enhanced, np.ndarray)
        
        # Kích thước phải giống nhau (hoặc gần giống)
        self.assertEqual(len(enhanced.shape), 2)  # Ảnh xám
        self.assertEqual(enhanced.shape[:2], image.shape[:2])


class TestImageProcessorEdgeCases(unittest.TestCase):
    """Test các trường hợp đặc biệt"""
    
    def test_invalid_image_path(self):
        """Test với đường dẫn ảnh không hợp lệ"""
        processor = ImageProcessor()
        
        result = processor.process_image("nonexistent.jpg", "output.jpg")
        
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error_message)
    
    def test_none_image(self):
        """Test với ảnh None"""
        processor = ImageProcessor()
        
        is_good, quality_info, enhanced = processor.check_quality(None)
        
        self.assertFalse(is_good)
        self.assertIn("error", quality_info)
        self.assertIsNone(enhanced)


if __name__ == '__main__':
    # Chạy tests
    unittest.main(verbosity=2) 
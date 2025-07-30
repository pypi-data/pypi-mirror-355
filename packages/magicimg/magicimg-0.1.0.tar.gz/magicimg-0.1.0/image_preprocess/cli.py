"""
Command Line Interface cho image-preprocess package
"""

import argparse
import sys
import logging
from pathlib import Path
from .core import ImageProcessor
from .utils import (
    validate_image_path, 
    create_debug_dir, 
    print_system_info,
    get_image_info
)

def setup_logging(verbose: bool = False):
    """Thiết lập logging"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def cmd_process(args):
    """Xử lý ảnh"""
    # Kiểm tra đường dẫn ảnh
    if not validate_image_path(args.input):
        return False
    
    # Tạo thư mục debug nếu cần
    debug_dir = None
    if args.debug_dir:
        debug_dir = create_debug_dir(args.debug_dir)
    
    # Xác định đường dẫn đầu ra
    if args.output:
        output_path = args.output
    else:
        input_path = Path(args.input)
        output_path = input_path.parent / f"{input_path.stem}_processed{input_path.suffix}"
    
    # Tạo processor
    config = {}
    if args.min_quality:
        config["min_quality_score"] = args.min_quality
    
    processor = ImageProcessor(debug_dir=debug_dir, config=config)
    
    # Xử lý ảnh
    try:
        result = processor.process_image(
            input_path=args.input,
            output_path=str(output_path),
            auto_rotate=not args.no_rotation
        )
        
        if result.success:
            print(f"✓ Đã xử lý xong ảnh: {args.input}")
            print(f"✓ Ảnh đã xử lý: {result.output_path}")
            
            if result.processing_steps:
                print(f"✓ Các bước xử lý: {', '.join(result.processing_steps)}")
            
            if result.quality_metrics:
                print(f"✓ Điểm chất lượng: {result.quality_metrics.quality_score:.2f}")
            
            return True
        else:
            print(f"✗ Không thể xử lý ảnh: {result.error_message}")
            return False
            
    except Exception as e:
        print(f"✗ Lỗi khi xử lý ảnh: {str(e)}")
        return False

def cmd_check_quality(args):
    """Kiểm tra chất lượng ảnh"""
    if not validate_image_path(args.input):
        return False
    
    try:
        import cv2
        # Tạo processor
        debug_dir = create_debug_dir(args.debug_dir) if args.debug_dir else None
        processor = ImageProcessor(debug_dir=debug_dir)
        
        # Đọc và kiểm tra ảnh
        image = cv2.imread(args.input)
        is_good, quality_info, enhanced_image = processor.check_quality(image)
        
        print(f"=== CHẤT LƯỢNG ẢNH: {args.input} ===")
        print(f"Chỉ số mờ (blur index): {quality_info['blur_index']:.2f}")
        print(f"Tỷ lệ pixel tối: {quality_info['dark_ratio']:.4f}")
        print(f"Độ sáng trung bình: {quality_info['brightness']:.2f}")
        print(f"Độ tương phản: {quality_info['contrast']:.2f}")
        print(f"Độ phân giải: {quality_info['resolution'][0]}x{quality_info['resolution'][1]}")
        
        status = "✓ ĐẠT" if is_good else "✗ KHÔNG ĐẠT"
        print(f"Đánh giá tổng thể: {status}")
        
        return is_good
        
    except Exception as e:
        print(f"✗ Lỗi khi kiểm tra chất lượng: {str(e)}")
        return False

def cmd_detect_orientation(args):
    """Phát hiện hướng ảnh"""
    if not validate_image_path(args.input):
        return False
    
    try:
        import cv2
        # Tạo processor
        debug_dir = create_debug_dir(args.debug_dir) if args.debug_dir else None
        processor = ImageProcessor(debug_dir=debug_dir)
        
        # Đọc và phát hiện hướng ảnh
        image = cv2.imread(args.input)
        angle = processor.detect_orientation(image)
        
        print(f"=== HƯỚNG ẢNH: {args.input} ===")
        print(f"Góc cần xoay: {angle}°")
        
        if angle == 0:
            print("✓ Ảnh đã đúng hướng")
        else:
            print(f"⚠ Cần xoay ảnh {angle}° để đúng hướng")
        
        return True
        
    except Exception as e:
        print(f"✗ Lỗi khi phát hiện hướng: {str(e)}")
        return False

def cmd_info(args):
    """Hiển thị thông tin ảnh"""
    if not validate_image_path(args.input):
        return False
    
    info = get_image_info(args.input)
    if "error" in info:
        print(f"✗ Lỗi: {info['error']}")
        return False
    
    print(f"=== THÔNG TIN ẢNH: {info['file_name']} ===")
    print(f"Đường dẫn: {info['file_path']}")
    print(f"Kích thước file: {info['file_size_mb']} MB")
    print(f"Độ phân giải: {info['width']}x{info['height']} pixels")
    print(f"Số kênh màu: {info['channels']}")
    print(f"Tổng số pixel: {info['total_pixels']:,}")
    print(f"Tỷ lệ khung hình: {info['aspect_ratio']}")
    
    return True

def cmd_system_info(args):
    """Hiển thị thông tin hệ thống"""
    print_system_info()
    return True

def main():
    """Hàm chính của CLI"""
    parser = argparse.ArgumentParser(
        description='Image Preprocessing CLI - Xử lý và tiền xử lý ảnh cho OCR',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
  image-preprocess process input.jpg --output output.jpg
  image-preprocess quality input.jpg --debug-dir debug/
  image-preprocess orientation input.jpg
  image-preprocess info input.jpg
  image-preprocess system-info
        """
    )
    
    # Tham số chung
    parser.add_argument('--verbose', '-v', action='store_true', help='Chi tiết hơn trong log')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Các lệnh có sẵn')
    
    # Command: process
    process_parser = subparsers.add_parser('process', help='Xử lý ảnh')
    process_parser.add_argument('input', help='Đường dẫn ảnh đầu vào')
    process_parser.add_argument('--output', '-o', help='Đường dẫn ảnh đầu ra')
    process_parser.add_argument('--debug-dir', help='Thư mục lưu ảnh debug')
    process_parser.add_argument('--min-quality', type=float, default=0.7, 
                               help='Điểm chất lượng tối thiểu (0-1)')
    process_parser.add_argument('--no-rotation', action='store_true', 
                               help='Không tự động xoay ảnh')
    
    # Command: quality
    quality_parser = subparsers.add_parser('quality', help='Kiểm tra chất lượng ảnh')
    quality_parser.add_argument('input', help='Đường dẫn ảnh đầu vào')
    quality_parser.add_argument('--debug-dir', help='Thư mục lưu ảnh debug')
    
    # Command: orientation
    orientation_parser = subparsers.add_parser('orientation', help='Phát hiện hướng ảnh')
    orientation_parser.add_argument('input', help='Đường dẫn ảnh đầu vào')
    orientation_parser.add_argument('--debug-dir', help='Thư mục lưu ảnh debug')
    
    # Command: info
    info_parser = subparsers.add_parser('info', help='Hiển thị thông tin ảnh')
    info_parser.add_argument('input', help='Đường dẫn ảnh đầu vào')
    
    # Command: system-info
    system_parser = subparsers.add_parser('system-info', help='Hiển thị thông tin hệ thống')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Thiết lập logging
    setup_logging(args.verbose)
    
    # Thực thi lệnh
    if args.command == 'process':
        success = cmd_process(args)
    elif args.command == 'quality':
        success = cmd_check_quality(args)
    elif args.command == 'orientation':
        success = cmd_detect_orientation(args)
    elif args.command == 'info':
        success = cmd_info(args)
    elif args.command == 'system-info':
        success = cmd_system_info(args)
    else:
        parser.print_help()
        success = False
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main() 
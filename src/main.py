#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF轉HTML主程式
整合所有模組提供完整的轉換功能
"""

import argparse
import sys
import os
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# 添加src目錄到路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from pdf_processor import PDFProcessor
    from ocr_processor import OCRProcessor  
    from image_region_detector import ImageRegionDetector
    from html_generator import HTMLGenerator
except ImportError as e:
    print(f"導入模組失敗: {e}")
    print("請確保所有模組檔案都在src目錄中")
    sys.exit(1)

class PDFToHTMLConverter:
    """PDF轉HTML轉換器主程式"""
    
    def __init__(self, project_root: str = "D:/pdf-to-html-converter", 
                 language: str = 'chi_tra+eng'):
        """
        初始化轉換器
        
        Args:
            project_root: 專案根目錄
            language: OCR識別語言
        """
        self.project_root = Path(project_root)
        self.language = language
        self.logger = self._setup_logger()
        
        # 初始化各模組
        try:
            self.pdf_processor = PDFProcessor(project_root)
            self.ocr_processor = OCRProcessor(project_root, language)
            self.region_detector = ImageRegionDetector(project_root)
            self.html_generator = HTMLGenerator(project_root)
            
            self.logger.info("所有模組初始化完成")
            
        except Exception as e:
            self.logger.error(f"模組初始化失敗: {e}")
            raise
    
    def _setup_logger(self) -> logging.Logger:
        """設定日誌系統"""
        logs_dir = self.project_root / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_dir / f"main_converter_{timestamp}.log"
        
        logger = logging.getLogger('PDFToHTMLConverter')
        logger.setLevel(logging.INFO)
        
        if logger.handlers:
            return logger
            
        # 檔案處理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 控制台處理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 格式化
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def validate_environment(self) -> bool:
        """驗證執行環境"""
        self.logger.info("檢查執行環境...")
        
        # 檢查Tesseract安裝
        if not self.ocr_processor.validate_tesseract_installation():
            self.logger.error("Tesseract OCR未正確安裝")
            return False
            
        # 檢查專案目錄
        required_dirs = ['output/images', 'output/text', 'output/html', 'logs']
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            
        self.logger.info("執行環境檢查通過")
        return True
    
    def convert_pdf_to_html(self, pdf_path: str, 
                           page_range: Optional[tuple] = None,
                           show_progress: bool = True) -> Dict[str, Any]:
        """
        完整的PDF轉HTML轉換流程
        
        Args:
            pdf_path: PDF檔案路徑
            page_range: 頁面範圍 (start, end)
            show_progress: 是否顯示進度
            
        Returns:
            轉換結果資訊
        """
        start_time = time.time()
        
        try:
            # 驗證PDF檔案
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF檔案不存在: {pdf_path}")
            
            pdf_name = Path(pdf_path).stem
            self.logger.info(f"開始轉換PDF: {pdf_name}")
            
            if show_progress:
                print(f"📄 開始處理: {pdf_name}")
                print("=" * 60)
            
            # 階段1: PDF轉圖片
            if show_progress:
                print("🔄 階段1: PDF頁面轉換...")
            
            conversion_info = self.pdf_processor.get_conversion_info(pdf_path)
            total_pages = conversion_info.get('estimated_pages', 0)
            
            # 轉換PDF頁面
            pdf_result = self.pdf_processor.convert_pdf_to_images(
                pdf_path, page_range=page_range
            )
            
            if show_progress:
                print(f"✅ 完成 {pdf_result['pages_processed']} 頁面轉換")
            
            # 階段2: OCR文字識別
            if show_progress:
                print("🔄 階段2: OCR文字識別...")
            
            ocr_stats = self.ocr_processor.process_pdf_images(pdf_name)
            
            if show_progress:
                print(f"✅ 識別 {ocr_stats['total_text_elements']} 個文字元素")
            
            # 階段3: 圖片區域檢測
            if show_progress:
                print("🔄 階段3: 圖片區域檢測...")
            
            region_results = []
            processed_pages = ocr_stats['processed_pages']
            
            for page_num in range(1, processed_pages + 1):
                # 載入OCR結果
                ocr_data = self.html_generator.load_ocr_data(pdf_name, page_num)
                if not ocr_data:
                    continue
                
                # 執行區域檢測
                image_path = self.project_root / "output" / "images" / pdf_name / f"page_{page_num:03d}.png"
                
                if image_path.exists():
                    region_result = self.region_detector.process_page_with_ocr(
                        str(image_path), ocr_data, pdf_name, page_num
                    )
                    region_results.append(region_result)
            
            total_regions = sum(len(r['image_regions']) for r in region_results)
            
            if show_progress:
                print(f"✅ 檢測 {total_regions} 個圖片區域")
            
            # 階段4: HTML生成
            if show_progress:
                print("🔄 階段4: HTML版面生成...")
            
            html_path = self.html_generator.process_pdf_pages(pdf_name, page_range)
            
            # 生成處理報告
            processing_time = time.time() - start_time
            report = self.html_generator.generate_processing_report(
                pdf_name, html_path, processed_pages
            )
            
            # 完成資訊
            result = {
                'success': True,
                'pdf_name': pdf_name,
                'html_path': html_path,
                'pages_processed': processed_pages,
                'text_elements': ocr_stats['total_text_elements'],
                'image_regions': total_regions,
                'processing_time': processing_time,
                'file_size': os.path.getsize(html_path) if os.path.exists(html_path) else 0,
                'report': report
            }
            
            if show_progress:
                print("✅ HTML生成完成")
                print("=" * 60)
                print(f"🎉 轉換完成！")
                print(f"📄 處理頁面: {processed_pages}")
                print(f"📝 文字元素: {ocr_stats['total_text_elements']}")
                print(f"🖼️  圖片區域: {total_regions}")
                print(f"⏱️  處理時間: {processing_time:.1f}秒")
                print(f"📁 輸出檔案: {html_path}")
                print(f"💾 檔案大小: {result['file_size']:,} bytes")
            
            self.logger.info(f"PDF轉換完成: {pdf_name}")
            return result
            
        except Exception as e:
            self.logger.error(f"PDF轉換失敗: {e}")
            
            result = {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }
            
            if show_progress:
                print(f"❌ 轉換失敗: {e}")
            
            return result
    
    def batch_convert(self, pdf_directory: str, 
                     output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        批次轉換目錄中的所有PDF檔案
        
        Args:
            pdf_directory: PDF檔案目錄
            output_dir: 輸出目錄
            
        Returns:
            批次處理結果
        """
        pdf_dir = Path(pdf_directory)
        
        if not pdf_dir.exists():
            raise FileNotFoundError(f"目錄不存在: {pdf_directory}")
        
        # 尋找PDF檔案
        pdf_files = list(pdf_dir.glob("*.pdf"))
        
        if not pdf_files:
            raise FileNotFoundError(f"在 {pdf_directory} 中找不到PDF檔案")
        
        print(f"📁 找到 {len(pdf_files)} 個PDF檔案")
        print("開始批次處理...")
        
        results = []
        successful = 0
        failed = 0
        
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"\n處理 {i}/{len(pdf_files)}: {pdf_file.name}")
            print("-" * 40)
            
            try:
                result = self.convert_pdf_to_html(str(pdf_file), show_progress=True)
                
                if result['success']:
                    successful += 1
                else:
                    failed += 1
                    
                results.append(result)
                
            except Exception as e:
                failed += 1
                results.append({
                    'success': False,
                    'pdf_name': pdf_file.stem,
                    'error': str(e)
                })
                print(f"❌ 處理失敗: {e}")
        
        # 批次處理總結
        batch_result = {
            'total_files': len(pdf_files),
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / len(pdf_files)) * 100,
            'results': results
        }
        
        print(f"\n批次處理完成")
        print("=" * 60)
        print(f"📊 處理結果:")
        print(f"   總檔案數: {len(pdf_files)}")
        print(f"   成功: {successful}")
        print(f"   失敗: {failed}")
        print(f"   成功率: {batch_result['success_rate']:.1f}%")
        
        return batch_result


def create_argument_parser():
    """建立命令列參數解析器"""
    parser = argparse.ArgumentParser(
        description='PDF轉HTML轉換器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  python main.py --input document.pdf
  python main.py --input document.pdf --pages 1-10
  python main.py --batch /path/to/pdf/folder
  python main.py --input document.pdf --output custom_output.html
        """
    )
    
    # 輸入選項
    input_group = parser.add_mutually_exclusive_group(required=False)
    input_group.add_argument(
        '--input', '-i',
        help='輸入PDF檔案路徑'
    )
    input_group.add_argument(
        '--batch', '-b',
        help='批次處理：PDF檔案目錄路徑'
    )
    
    # 其他選項
    parser.add_argument(
        '--output', '-o',
        help='輸出HTML檔案路徑（僅單檔案模式）'
    )
    
    parser.add_argument(
        '--pages', '-p',
        help='頁面範圍，格式: 1-10 或 1,3,5-8'
    )
    
    parser.add_argument(
        '--language', '-l',
        default='chi_tra+eng',
        help='OCR識別語言 (預設: chi_tra+eng)'
    )
    
    parser.add_argument(
        '--project-root',
        default='D:/pdf-to-html-converter',
        help='專案根目錄路徑'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='安靜模式：不顯示進度資訊'
    )
    
    parser.add_argument(
        '--check-env',
        action='store_true',
        help='只檢查執行環境，不進行轉換'
    )
    
    return parser


def parse_page_range(page_range_str: str) -> Optional[tuple]:
    """
    解析頁面範圍字串
    
    Args:
        page_range_str: 頁面範圍字串，如 "1-10"
        
    Returns:
        (start_page, end_page) 或 None
    """
    try:
        if '-' in page_range_str:
            start, end = page_range_str.split('-')
            return (int(start), int(end))
        else:
            # 單一頁面
            page = int(page_range_str)
            return (page, page)
    except ValueError:
        return None


def main():
    """主函數"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    try:
        # 建立轉換器
        converter = PDFToHTMLConverter(
            project_root=args.project_root,
            language=args.language
        )
        
        # 只檢查環境
        if args.check_env:
            print("檢查執行環境...")
            if converter.validate_environment():
                print("✅ 執行環境正常")
                return 0
            else:
                print("❌ 執行環境有問題")
                return 1
        
        # 驗證環境
        if not converter.validate_environment():
            print("❌ 執行環境檢查失敗")
            return 1
        
        # 解析頁面範圍
        page_range = None
        if args.pages:
            page_range = parse_page_range(args.pages)
            if page_range is None:
                print(f"❌ 無效的頁面範圍格式: {args.pages}")
                return 1
        
        # 執行轉換
        if args.batch:
            # 批次處理
            result = converter.batch_convert(args.batch)
            return 0 if result['successful'] > 0 else 1
            
        else:
            # 單檔案處理
            result = converter.convert_pdf_to_html(
                args.input,
                page_range=page_range,
                show_progress=not args.quiet
            )
            
            if result['success']:
                return 0
            else:
                print(f"❌ 轉換失敗: {result.get('error', '未知錯誤')}")
                return 1
                
    except KeyboardInterrupt:
        print("\n⚠️  使用者中斷操作")
        return 1
        
    except Exception as e:
        print(f"❌ 程式執行錯誤: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
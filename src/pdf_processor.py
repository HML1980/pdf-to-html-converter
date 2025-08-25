"""
PDF處理模組 - 階段2
將PDF轉換為高解析度圖片，建立D槽專案資料夾結構
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Tuple, Optional
import time
from datetime import datetime

try:
    from pdf2image import convert_from_path
    from PIL import Image
except ImportError:
    print("⚠️  缺少必要套件，請安裝：")
    print("pip install pdf2image Pillow")
    print("另外需要安裝 poppler：")
    print("Windows: 下載 poppler 並加入 PATH")
    print("或使用 conda: conda install -c conda-forge poppler")


class PDFProcessor:
    """PDF處理主類別"""
    
    def __init__(self, base_path: str = "D:/pdf-to-html-converter"):
        """
        初始化PDF處理器
        
        Args:
            base_path: 專案根目錄路徑
        """
        self.base_path = Path(base_path)
        self.output_path = self.base_path / "output"
        self.images_path = self.output_path / "images"
        self.text_path = self.output_path / "text"
        self.html_path = self.output_path / "html"
        self.logs_path = self.base_path / "logs"
        
        # 轉換參數設定
        self.dpi = 300  # 高解析度
        self.image_format = 'PNG'
        
        # 建立目錄結構
        self._create_directory_structure()
        
        # 設置日誌
        self._setup_logging()
        
    def _create_directory_structure(self):
        """建立D槽專案目錄結構"""
        directories = [
            self.base_path,
            self.output_path,
            self.images_path,
            self.text_path,
            self.html_path,
            self.logs_path
        ]
        
        created_dirs = []
        for directory in directories:
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)
                created_dirs.append(str(directory))
        
        if created_dirs:
            print("✅ 建立專案資料夾結構：")
            for dir_path in created_dirs:
                print(f"   📁 {dir_path}")
        else:
            print("✅ 專案資料夾結構已存在")
            
    def _setup_logging(self):
        """設置日誌系統"""
        log_filename = f"pdf_processor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_filepath = self.logs_path / log_filename
        
        # 建立logger
        self.logger = logging.getLogger('PDFProcessor')
        self.logger.setLevel(logging.INFO)
        
        # 建立formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 檔案handler
        file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # 終端機handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        self.logger.info(f"PDF處理器初始化完成，日誌：{log_filepath}")
        
    def validate_pdf(self, pdf_path: str) -> Tuple[bool, str]:
        """
        驗證PDF檔案
        
        Args:
            pdf_path: PDF檔案路徑
            
        Returns:
            (是否有效, 訊息)
        """
        try:
            pdf_path = Path(pdf_path)
            
            # 檢查檔案是否存在
            if not pdf_path.exists():
                return False, f"❌ 檔案不存在: {pdf_path}"
                
            # 檢查副檔名
            if pdf_path.suffix.lower() != '.pdf':
                return False, f"❌ 不是PDF檔案: {pdf_path}"
                
            # 檢查檔案大小
            file_size = pdf_path.stat().st_size
            if file_size == 0:
                return False, f"❌ 檔案為空: {pdf_path}"
                
            self.logger.info(f"✅ PDF驗證成功: {pdf_path.name} ({file_size/1024/1024:.1f} MB)")
            return True, "PDF檔案驗證成功"
            
        except Exception as e:
            error_msg = f"❌ PDF驗證失敗: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
            
    def convert_pdf_to_images(self, pdf_path: str, progress_callback=None) -> Tuple[bool, str, List[str]]:
        """
        將PDF轉換為高解析度圖片
        
        Args:
            pdf_path: PDF檔案路徑
            progress_callback: 進度回調函數 (可選)
            
        Returns:
            (成功與否, 訊息, 圖片路徑列表)
        """
        try:
            # 驗證PDF
            is_valid, message = self.validate_pdf(pdf_path)
            if not is_valid:
                return False, message, []
            
            # 建立輸出目錄
            pdf_name = Path(pdf_path).stem
            output_dir = self.images_path / pdf_name
            output_dir.mkdir(exist_ok=True)
            
            print(f"🔄 開始轉換PDF: {pdf_name}")
            print(f"📁 輸出目錄: {output_dir}")
            
            start_time = time.time()
            
            # 執行轉換
            self.logger.info(f"開始PDF轉圖片，DPI: {self.dpi}")
            
            pages = convert_from_path(
                pdf_path,
                dpi=self.dpi,
                output_folder=None,
                fmt=self.image_format.lower()
            )
            
            image_paths = []
            total_pages = len(pages)
            
            for i, page in enumerate(pages, 1):
                # 儲存圖片
                image_filename = f"page_{i:03d}.{self.image_format.lower()}"
                image_path = output_dir / image_filename
                
                page.save(str(image_path), self.image_format, optimize=True)
                image_paths.append(str(image_path))
                
                # 顯示進度
                progress = (i / total_pages) * 100
                print(f"📄 處理頁面 {i}/{total_pages} ({progress:.1f}%)")
                
                # 呼叫進度回調函數
                if progress_callback:
                    progress_callback(i, total_pages, image_path)
                    
                self.logger.info(f"頁面 {i} 轉換完成: {image_filename}")
            
            elapsed_time = time.time() - start_time
            
            success_msg = (
                f"✅ PDF轉換完成！\n"
                f"📄 總頁數: {total_pages}\n"
                f"⏱️  耗時: {elapsed_time:.2f} 秒\n"
                f"📁 圖片儲存於: {output_dir}"
            )
            
            print(success_msg)
            self.logger.info(f"PDF轉換成功，共 {total_pages} 頁，耗時 {elapsed_time:.2f} 秒")
            
            return True, success_msg, image_paths
            
        except Exception as e:
            error_msg = f"❌ PDF轉換失敗: {str(e)}"
            print(error_msg)
            self.logger.error(error_msg)
            return False, error_msg, []
            
    def get_conversion_info(self, pdf_path: str) -> dict:
        """
        取得轉換資訊（不執行轉換）
        
        Args:
            pdf_path: PDF檔案路徑
            
        Returns:
            轉換資訊字典
        """
        info = {
            'pdf_path': str(Path(pdf_path).absolute()),
            'pdf_name': Path(pdf_path).stem,
            'output_dir': str(self.images_path / Path(pdf_path).stem),
            'dpi': self.dpi,
            'format': self.image_format,
            'estimated_time': '取決於頁數和電腦效能'
        }
        return info


def main():
    """測試用主函數"""
    print("🚀 PDF處理器測試")
    print("=" * 40)
    
    # 初始化處理器
    processor = PDFProcessor()
    
    # 顯示設定資訊
    print(f"📁 專案目錄: {processor.base_path}")
    print(f"🖼️  圖片輸出: {processor.images_path}")
    print(f"📝 文字輸出: {processor.text_path}")
    print(f"🌐 HTML輸出: {processor.html_path}")
    print(f"📋 日誌目錄: {processor.logs_path}")
    print("=" * 40)
    
    # 等待使用者測試
    print("✅ PDF處理器已準備就緒！")
    print("💡 使用方式：")
    print("   processor = PDFProcessor()")
    print("   success, msg, paths = processor.convert_pdf_to_images('your_file.pdf')")


if __name__ == "__main__":
    main()
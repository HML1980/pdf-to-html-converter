"""
OCR文字識別處理模組 - 階段3
使用Tesseract進行中文繁體文字識別，提取座標位置資訊
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
import time
from datetime import datetime
import cv2
import numpy as np

try:
    import pytesseract
    from PIL import Image, ImageEnhance, ImageFilter
    import pandas as pd
except ImportError:
    print("⚠️  缺少必要套件，請安裝：")
    print("pip install pytesseract opencv-python pandas")
    print("另外需要安裝 Tesseract OCR：")
    print("Windows: 從 https://github.com/UB-Mannheim/tesseract/wiki 下載")
    print("Ubuntu: sudo apt install tesseract-ocr tesseract-ocr-chi-tra")
    print("macOS: brew install tesseract tesseract-lang")


class OCRProcessor:
    """OCR文字識別處理主類別"""
    
    def __init__(self, base_path: str = "D:/pdf-to-html-converter"):
        """
        初始化OCR處理器
        
        Args:
            base_path: 專案根目錄路徑
        """
        self.base_path = Path(base_path)
        self.output_path = self.base_path / "output"
        self.images_path = self.output_path / "images"
        self.text_path = self.output_path / "text"
        self.logs_path = self.base_path / "logs"
        
        # 確保目錄存在
        self.text_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)
        
        # 設置日誌
        self._setup_logging()
        
        # OCR設定
        self.tesseract_config = {
            'lang': 'chi_tra+eng',  # 中文繁體 + 英文
            'config': '--psm 6 --oem 3',  # 頁面分段模式 + OCR引擎模式
            'output_type': 'dict'  # 輸出字典格式
        }
        
        # 圖片前處理參數
        self.preprocessing = {
            'resize_factor': 2.0,  # 放大倍數
            'contrast_enhance': 1.2,  # 對比度增強
            'sharpness_enhance': 1.1,  # 銳利度增強
            'noise_reduction': True,  # 降噪
            'binarization': True  # 二值化
        }
        
        self.logger.info("OCR處理器初始化完成")
        
    def _setup_logging(self):
        """設置日誌系統"""
        log_filename = f"ocr_processor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_filepath = self.logs_path / log_filename
        
        # 建立logger
        self.logger = logging.getLogger('OCRProcessor')
        self.logger.setLevel(logging.INFO)
        
        # 避免重複handler
        if not self.logger.handlers:
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
    
    def check_tesseract_installation(self) -> Tuple[bool, str]:
        """
        檢查Tesseract安裝狀態
        
        Returns:
            (是否安裝, 訊息)
        """
        try:
            # 檢查Tesseract可執行檔
            version = pytesseract.get_tesseract_version()
            
            # 檢查語言包
            languages = pytesseract.get_languages()
            
            has_chi_tra = 'chi_tra' in languages
            has_eng = 'eng' in languages
            
            if has_chi_tra and has_eng:
                msg = f"✅ Tesseract {version} 已安裝，支援中文繁體和英文"
                self.logger.info(msg)
                return True, msg
            else:
                missing_langs = []
                if not has_chi_tra:
                    missing_langs.append('chi_tra')
                if not has_eng:
                    missing_langs.append('eng')
                    
                msg = f"❌ 缺少語言包: {', '.join(missing_langs)}"
                self.logger.warning(msg)
                return False, msg
                
        except Exception as e:
            msg = f"❌ Tesseract未安裝或配置錯誤: {str(e)}"
            self.logger.error(msg)
            return False, msg
    
    def preprocess_image(self, image_path: str) -> Image.Image:
        """
        圖片前處理以提高OCR識別率
        
        Args:
            image_path: 圖片檔案路徑
            
        Returns:
            處理後的PIL Image物件
        """
        try:
            # 載入圖片
            image = Image.open(image_path)
            
            # 轉換為RGB模式
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 放大圖片提高解析度
            if self.preprocessing['resize_factor'] != 1.0:
                new_size = (
                    int(image.width * self.preprocessing['resize_factor']),
                    int(image.height * self.preprocessing['resize_factor'])
                )
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # 對比度增強
            if self.preprocessing['contrast_enhance'] != 1.0:
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(self.preprocessing['contrast_enhance'])
            
            # 銳利度增強
            if self.preprocessing['sharpness_enhance'] != 1.0:
                enhancer = ImageEnhance.Sharpness(image)
                image = enhancer.enhance(self.preprocessing['sharpness_enhance'])
            
            # 降噪處理
            if self.preprocessing['noise_reduction']:
                image = image.filter(ImageFilter.MedianFilter(size=3))
            
            # 二值化處理
            if self.preprocessing['binarization']:
                # 轉換為OpenCV格式進行二值化
                cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
                
                # 自適應二值化
                binary = cv2.adaptiveThreshold(
                    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY, 11, 2
                )
                
                # 轉換回PIL格式
                image = Image.fromarray(binary)
                image = image.convert('RGB')
            
            return image
            
        except Exception as e:
            self.logger.error(f"圖片前處理失敗: {str(e)}")
            # 返回原始圖片
            return Image.open(image_path)
    
    def extract_text_with_coordinates(self, image_path: str) -> Dict[str, Any]:
        """
        從圖片中提取文字和座標資訊
        
        Args:
            image_path: 圖片檔案路徑
            
        Returns:
            包含文字和座標資訊的字典
        """
        try:
            self.logger.info(f"開始OCR識別: {Path(image_path).name}")
            
            # 前處理圖片
            processed_image = self.preprocess_image(image_path)
            
            # 執行OCR識別 - 取得詳細資料
            ocr_data = pytesseract.image_to_data(
                processed_image,
                lang=self.tesseract_config['lang'],
                config=self.tesseract_config['config'],
                output_type=pytesseract.Output.DICT
            )
            
            # 解析OCR結果
            text_blocks = []
            page_text = ""
            
            for i in range(len(ocr_data['text'])):
                text = ocr_data['text'][i].strip()
                
                # 過濾空文字和低信心度文字
                confidence = int(ocr_data['conf'][i])
                if text and confidence > 30:  # 信心度閾值
                    
                    # 座標資訊
                    x = ocr_data['left'][i]
                    y = ocr_data['top'][i]
                    width = ocr_data['width'][i]
                    height = ocr_data['height'][i]
                    
                    # 估算字體大小（基於高度）
                    font_size = max(8, min(72, int(height * 0.75)))
                    
                    # 文字區塊資訊
                    text_block = {
                        'text': text,
                        'x': x,
                        'y': y,
                        'width': width,
                        'height': height,
                        'confidence': confidence,
                        'font_size': font_size,
                        'level': ocr_data['level'][i],  # 文字層級（字元、詞、行、段落等）
                        'block_num': ocr_data['block_num'][i],
                        'par_num': ocr_data['par_num'][i],
                        'line_num': ocr_data['line_num'][i],
                        'word_num': ocr_data['word_num'][i]
                    }
                    
                    text_blocks.append(text_block)
                    page_text += text + " "
            
            # 組織結果
            result = {
                'image_path': str(image_path),
                'image_name': Path(image_path).name,
                'processing_time': datetime.now().isoformat(),
                'total_text_blocks': len(text_blocks),
                'full_text': page_text.strip(),
                'text_blocks': text_blocks,
                'image_dimensions': {
                    'original_width': processed_image.width,
                    'original_height': processed_image.height
                },
                'ocr_config': self.tesseract_config,
                'preprocessing_applied': self.preprocessing
            }
            
            self.logger.info(f"OCR完成: 識別到 {len(text_blocks)} 個文字區塊")
            return result
            
        except Exception as e:
            error_msg = f"OCR識別失敗: {str(e)}"
            self.logger.error(error_msg)
            return {
                'image_path': str(image_path),
                'error': error_msg,
                'text_blocks': [],
                'full_text': ""
            }
    
    def detect_image_regions(self, image_path: str) -> List[Dict[str, Any]]:
        """
        檢測圖片中的非文字區域（圖表、圖片等）
        
        Args:
            image_path: 圖片檔案路徑
            
        Returns:
            圖片區域列表
        """
        try:
            # 載入圖片
            image = cv2.imread(image_path)
            if image is None:
                return []
                
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 使用邊緣檢測找出可能的圖片區域
            edges = cv2.Canny(gray, 50, 150)
            
            # 尋找輪廓
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            image_regions = []
            
            for i, contour in enumerate(contours):
                # 計算輪廓面積
                area = cv2.contourArea(contour)
                
                # 過濾太小的區域
                if area < 1000:  # 可調整閾值
                    continue
                
                # 取得邊界矩形
                x, y, w, h = cv2.boundingRect(contour)
                
                # 計算長寬比
                aspect_ratio = float(w) / h
                
                # 估算是否為圖片區域（基於面積和長寬比）
                is_likely_image = area > 5000 and 0.2 < aspect_ratio < 5.0
                
                region = {
                    'region_id': f"img_region_{i:03d}",
                    'x': int(x),
                    'y': int(y),
                    'width': int(w),
                    'height': int(h),
                    'area': int(area),
                    'aspect_ratio': round(aspect_ratio, 2),
                    'is_likely_image': is_likely_image,
                    'confidence': min(100, int((area / 10000) * 100))  # 簡單的信心度計算
                }
                
                image_regions.append(region)
            
            # 按面積排序（大到小）
            image_regions.sort(key=lambda x: x['area'], reverse=True)
            
            self.logger.info(f"檢測到 {len(image_regions)} 個可能的圖片區域")
            return image_regions
            
        except Exception as e:
            self.logger.error(f"圖片區域檢測失敗: {str(e)}")
            return []
    
    def process_single_image(self, image_path: str) -> Dict[str, Any]:
        """
        處理單張圖片（文字識別 + 圖片區域檢測）
        
        Args:
            image_path: 圖片檔案路徑
            
        Returns:
            完整處理結果
        """
        start_time = time.time()
        
        # 文字識別
        text_result = self.extract_text_with_coordinates(image_path)
        
        # 圖片區域檢測
        image_regions = self.detect_image_regions(image_path)
        
        # 組合結果
        result = {
            **text_result,
            'image_regions': image_regions,
            'processing_time_seconds': round(time.time() - start_time, 2)
        }
        
        return result
    
    def save_ocr_results(self, results: Dict[str, Any], output_path: str):
        """
        儲存OCR結果到JSON檔案
        
        Args:
            results: OCR處理結果
            output_path: 輸出檔案路徑
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"OCR結果已儲存: {output_path}")
            
        except Exception as e:
            self.logger.error(f"儲存OCR結果失敗: {str(e)}")
    
    def process_pdf_images(self, pdf_name: str, progress_callback=None) -> Tuple[bool, str, List[str]]:
        """
        處理PDF對應的所有圖片頁面
        
        Args:
            pdf_name: PDF檔案名稱（不含副檔名）
            progress_callback: 進度回調函數
            
        Returns:
            (成功與否, 訊息, 結果檔案路徑列表)
        """
        try:
            # 尋找圖片目錄
            images_dir = self.images_path / pdf_name
            if not images_dir.exists():
                return False, f"找不到圖片目錄: {images_dir}", []
            
            # 尋找圖片檔案
            image_files = list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpg"))
            
            if not image_files:
                return False, f"目錄中沒有圖片檔案: {images_dir}", []
            
            # 排序檔案
            image_files.sort()
            
            # 建立輸出目錄
            text_output_dir = self.text_path / pdf_name
            text_output_dir.mkdir(exist_ok=True)
            
            print(f"🔍 開始OCR處理: {pdf_name}")
            print(f"📁 處理 {len(image_files)} 個圖片檔案")
            
            result_files = []
            total_files = len(image_files)
            
            for i, image_file in enumerate(image_files, 1):
                print(f"🔄 處理圖片 {i}/{total_files}: {image_file.name}")
                
                # 執行OCR處理
                result = self.process_single_image(str(image_file))
                
                # 儲存結果
                result_filename = f"{image_file.stem}_ocr.json"
                result_path = text_output_dir / result_filename
                self.save_ocr_results(result, str(result_path))
                
                result_files.append(str(result_path))
                
                # 進度回調
                if progress_callback:
                    progress_callback(i, total_files, result_path)
                
                # 顯示處理統計
                if 'text_blocks' in result:
                    text_count = len(result['text_blocks'])
                    region_count = len(result.get('image_regions', []))
                    print(f"   ✅ 識別文字區塊: {text_count}, 圖片區域: {region_count}")
            
            success_msg = f"✅ OCR處理完成！處理了 {total_files} 個檔案"
            print(success_msg)
            
            return True, success_msg, result_files
            
        except Exception as e:
            error_msg = f"❌ OCR批次處理失敗: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg, []


def main():
    """測試用主函數"""
    print("🔍 OCR文字識別處理器測試")
    print("=" * 50)
    
    # 初始化處理器
    processor = OCRProcessor()
    
    # 檢查Tesseract安裝
    is_installed, message = processor.check_tesseract_installation()
    print(message)
    
    if not is_installed:
        print("\n⚠️  請先安裝Tesseract OCR和中文語言包")
        return
    
    # 顯示設定資訊
    print(f"📁 文字輸出目錄: {processor.text_path}")
    print(f"🈵 支援語言: {processor.tesseract_config['lang']}")
    print("=" * 50)
    
    print("✅ OCR處理器已準備就緒！")
    print("💡 使用方式：")
    print("   processor = OCRProcessor()")
    print("   success, msg, files = processor.process_pdf_images('your_pdf_name')")


if __name__ == "__main__":
    main()
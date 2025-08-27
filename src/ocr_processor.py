#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR處理模組
負責對PDF頁面圖片進行文字識別，提取文字內容和位置資訊
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageEnhance
import pytesseract

class OCRProcessor:
    """OCR文字識別處理器"""
    
    def __init__(self, project_root: str = "D:/pdf-to-html-converter", 
                 language: str = 'chi_tra+eng'):
        """
        初始化OCR處理器
        
        Args:
            project_root: 專案根目錄
            language: OCR識別語言，預設為繁體中文+英文
        """
        self.project_root = Path(project_root)
        self.language = language
        self.logger = self._setup_logger()
        
        # OCR設定參數
        self.ocr_config = {
            'psm': 6,  # Page Segmentation Mode: 6 = 單一文字區塊
            'oem': 3,  # OCR Engine Mode: 3 = Default
            'dpi': 300,
            'tessdata_dir': None  # 如果需要自訂tessdata路徑
        }
        
        # 文字檢測參數
        self.text_detection_params = {
            'min_confidence': 30,  # 最小置信度
            'min_text_length': 1,  # 最小文字長度
            'merge_threshold': 20,  # 合併相近文字的像素閾值
        }
        
        # 支援的圖片格式
        self.supported_formats = ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']
        
        self.logger.info(f"OCR處理器初始化完成，語言：{language}")
        
    def _setup_logger(self) -> logging.Logger:
        """設定日誌系統"""
        # 確保logs目錄存在
        logs_dir = self.project_root / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # 設定日誌檔案名稱
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_dir / f"ocr_processor_{timestamp}.log"
        
        # 設定logger
        logger = logging.getLogger('OCRProcessor')
        logger.setLevel(logging.INFO)
        
        # 避免重複處理器
        if logger.handlers:
            return logger
            
        # 檔案處理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 控制台處理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 設定格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
        
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """
        圖片預處理以提升OCR效果
        
        Args:
            image_path: 圖片路徑
            
        Returns:
            處理後的圖片陣列
        """
        try:
            # 讀取圖片
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"無法讀取圖片: {image_path}")
                
            # 轉換為RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(image_rgb)
            
            # 增強對比度
            enhancer = ImageEnhance.Contrast(pil_image)
            enhanced_image = enhancer.enhance(1.2)
            
            # 增強銳利度
            sharpness_enhancer = ImageEnhance.Sharpness(enhanced_image)
            sharp_image = sharpness_enhancer.enhance(1.1)
            
            # 轉回numpy陣列
            processed_array = np.array(sharp_image)
            
            # 轉換為灰階
            gray = cv2.cvtColor(processed_array, cv2.COLOR_RGB2GRAY)
            
            # 二值化處理
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # 降噪處理
            denoised = cv2.medianBlur(binary, 3)
            
            return denoised
            
        except Exception as e:
            self.logger.error(f"圖片預處理失敗: {e}")
            raise
            
    def extract_text_with_coordinates(self, image_path: str) -> Dict[str, Any]:
        """
        從圖片提取文字和座標資訊
        
        Args:
            image_path: 圖片路徑
            
        Returns:
            包含文字和位置資訊的字典
        """
        try:
            # 預處理圖片
            processed_image = self.preprocess_image(image_path)
            
            # 構建Tesseract配置
            custom_config = f'--oem {self.ocr_config["oem"]} --psm {self.ocr_config["psm"]}'
            
            # 使用pytesseract進行OCR，獲取詳細資訊
            data = pytesseract.image_to_data(
                processed_image, 
                lang=self.language,
                config=custom_config,
                output_type=pytesseract.Output.DICT
            )
            
            # 處理識別結果
            text_elements = []
            n_boxes = len(data['level'])
            
            for i in range(n_boxes):
                confidence = int(data['conf'][i])
                text = data['text'][i].strip()
                
                # 過濾低置信度和空文字
                if (confidence < self.text_detection_params['min_confidence'] or 
                    len(text) < self.text_detection_params['min_text_length']):
                    continue
                
                # 提取位置資訊
                x = int(data['left'][i])
                y = int(data['top'][i])
                width = int(data['width'][i])
                height = int(data['height'][i])
                
                # 估算字體大小（基於高度）
                font_size = max(12, int(height * 0.8))
                
                text_element = {
                    'text': text,
                    'x': x,
                    'y': y,
                    'width': width,
                    'height': height,
                    'font_size': font_size,
                    'confidence': confidence,
                    'level': data['level'][i],
                    'page_num': data['page_num'][i],
                    'block_num': data['block_num'][i],
                    'par_num': data['par_num'][i],
                    'line_num': data['line_num'][i],
                    'word_num': data['word_num'][i]
                }
                
                text_elements.append(text_element)
            
            # 獲取完整文字內容
            full_text = pytesseract.image_to_string(
                processed_image, 
                lang=self.language,
                config=custom_config
            ).strip()
            
            # 獲取原始圖片尺寸
            original_image = Image.open(image_path)
            image_width, image_height = original_image.size
            
            result = {
                'image_path': str(image_path),
                'image_width': image_width,
                'image_height': image_height,
                'full_text': full_text,
                'text_elements': text_elements,
                'total_elements': len(text_elements),
                'language': self.language,
                'ocr_config': self.ocr_config.copy(),
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"成功提取 {len(text_elements)} 個文字元素，圖片：{image_path}")
            return result
            
        except Exception as e:
            self.logger.error(f"文字提取失敗: {e}")
            raise
            
    def merge_nearby_text_elements(self, text_elements: List[Dict]) -> List[Dict]:
        """
        合併相近的文字元素（可選功能）
        
        Args:
            text_elements: 文字元素列表
            
        Returns:
            合併後的文字元素列表
        """
        if not text_elements:
            return text_elements
            
        # 按行分組（相近的y座標）
        lines = []
        threshold = self.text_detection_params['merge_threshold']
        
        for element in sorted(text_elements, key=lambda x: x['y']):
            # 尋找相近的行
            found_line = False
            for line in lines:
                if abs(element['y'] - line[0]['y']) <= threshold:
                    line.append(element)
                    found_line = True
                    break
                    
            if not found_line:
                lines.append([element])
        
        # 在每行內按x座標排序
        merged_elements = []
        for line in lines:
            sorted_line = sorted(line, key=lambda x: x['x'])
            merged_elements.extend(sorted_line)
            
        return merged_elements
        
    def process_page_image(self, image_path: str, pdf_name: str, page_num: int) -> Dict[str, Any]:
        """
        處理單一頁面圖片
        
        Args:
            image_path: 頁面圖片路徑
            pdf_name: PDF檔案名稱
            page_num: 頁面編號
            
        Returns:
            處理結果
        """
        try:
            self.logger.info(f"開始處理頁面 {page_num}：{image_path}")
            
            # 檢查檔案是否存在
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"圖片檔案不存在: {image_path}")
                
            # 執行OCR
            ocr_result = self.extract_text_with_coordinates(image_path)
            
            # 合併相近文字元素（可選）
            if self.text_detection_params.get('merge_nearby', False):
                ocr_result['text_elements'] = self.merge_nearby_text_elements(
                    ocr_result['text_elements']
                )
            
            # 添加頁面資訊
            ocr_result['pdf_name'] = pdf_name
            ocr_result['page_number'] = page_num
            
            # 儲存結果到JSON檔案
            self.save_ocr_result(ocr_result, pdf_name, page_num)
            
            return ocr_result
            
        except Exception as e:
            self.logger.error(f"處理頁面 {page_num} 失敗: {e}")
            raise
            
    def save_ocr_result(self, ocr_result: Dict[str, Any], pdf_name: str, page_num: int):
        """
        儲存OCR結果到JSON檔案
        
        Args:
            ocr_result: OCR處理結果
            pdf_name: PDF檔案名稱  
            page_num: 頁面編號
        """
        try:
            # 建立輸出目錄
            output_dir = self.project_root / "output" / "text" / pdf_name
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 建立檔案名稱
            json_filename = f"page_{page_num:03d}.json"
            json_path = output_dir / json_filename
            
            # 儲存JSON檔案
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(ocr_result, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"OCR結果已儲存：{json_path}")
            
        except Exception as e:
            self.logger.error(f"儲存OCR結果失敗: {e}")
            raise
            
    def process_pdf_images(self, pdf_name: str, images_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        處理PDF的所有頁面圖片
        
        Args:
            pdf_name: PDF檔案名稱
            images_dir: 圖片目錄路徑（可選）
            
        Returns:
            處理統計資訊
        """
        try:
            # 確定圖片目錄
            if images_dir is None:
                images_dir = self.project_root / "output" / "images" / pdf_name
            else:
                images_dir = Path(images_dir)
                
            if not images_dir.exists():
                raise FileNotFoundError(f"圖片目錄不存在: {images_dir}")
                
            # 尋找所有圖片檔案
            image_files = []
            for ext in self.supported_formats:
                pattern = f"*{ext}"
                image_files.extend(list(images_dir.glob(pattern)))
                
            if not image_files:
                raise FileNotFoundError(f"在 {images_dir} 中找不到圖片檔案")
                
            # 排序檔案
            image_files.sort()
            
            self.logger.info(f"找到 {len(image_files)} 個圖片檔案，開始OCR處理")
            
            # 處理統計
            stats = {
                'total_pages': len(image_files),
                'processed_pages': 0,
                'failed_pages': 0,
                'total_text_elements': 0,
                'start_time': datetime.now().isoformat(),
                'failed_pages_list': []
            }
            
            # 逐頁處理
            for i, image_file in enumerate(image_files, 1):
                try:
                    result = self.process_page_image(str(image_file), pdf_name, i)
                    stats['processed_pages'] += 1
                    stats['total_text_elements'] += result['total_elements']
                    
                    # 顯示進度
                    progress = (i / len(image_files)) * 100
                    self.logger.info(f"進度: {progress:.1f}% ({i}/{len(image_files)})")
                    
                except Exception as e:
                    self.logger.error(f"處理頁面 {i} 失敗: {e}")
                    stats['failed_pages'] += 1
                    stats['failed_pages_list'].append({
                        'page': i,
                        'file': str(image_file),
                        'error': str(e)
                    })
                    
            stats['end_time'] = datetime.now().isoformat()
            stats['success_rate'] = (stats['processed_pages'] / stats['total_pages']) * 100
            
            # 儲存處理統計
            self._save_processing_stats(stats, pdf_name)
            
            self.logger.info(f"OCR處理完成！成功: {stats['processed_pages']}, 失敗: {stats['failed_pages']}")
            
            return stats
            
        except Exception as e:
            self.logger.error(f"處理PDF圖片失敗: {e}")
            raise
            
    def _save_processing_stats(self, stats: Dict[str, Any], pdf_name: str):
        """儲存處理統計資訊"""
        try:
            output_dir = self.project_root / "output" / "text" / pdf_name
            output_dir.mkdir(parents=True, exist_ok=True)
            
            stats_file = output_dir / "ocr_stats.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"儲存統計資訊失敗: {e}")
            
    def validate_tesseract_installation(self) -> bool:
        """
        驗證Tesseract安裝狀態
        
        Returns:
            是否安裝正確
        """
        try:
            version = pytesseract.get_tesseract_version()
            self.logger.info(f"Tesseract版本: {version}")
            
            # 檢查語言支援
            languages = pytesseract.get_languages()
            required_langs = self.language.split('+')
            
            missing_langs = []
            for lang in required_langs:
                if lang not in languages:
                    missing_langs.append(lang)
                    
            if missing_langs:
                self.logger.warning(f"缺少語言支援: {missing_langs}")
                return False
                
            self.logger.info("Tesseract安裝驗證成功")
            return True
            
        except Exception as e:
            self.logger.error(f"Tesseract驗證失敗: {e}")
            return False


def main():
    """測試OCR處理器功能"""
    print("🔍 OCR處理器測試")
    print("=" * 50)
    
    try:
        # 建立OCR處理器
        ocr = OCRProcessor()
        
        # 驗證Tesseract安裝
        if not ocr.validate_tesseract_installation():
            print("❌ Tesseract安裝驗證失敗，請檢查安裝狀態")
            return
            
        print("✅ OCR處理器初始化成功")
        print(f"📁 專案目錄: {ocr.project_root}")
        print(f"🌐 支援語言: {ocr.language}")
        
    except Exception as e:
        print(f"❌ 初始化失敗: {e}")


if __name__ == "__main__":
    main()
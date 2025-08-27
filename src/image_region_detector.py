#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
圖片區域檢測模組
負責識別和提取PDF頁面中的非文字區域（圖表、圖片等）
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw
import pytesseract

class ImageRegionDetector:
    """圖片區域檢測器"""
    
    def __init__(self, project_root: str = "D:/pdf-to-html-converter"):
        """
        初始化圖片區域檢測器
        
        Args:
            project_root: 專案根目錄
        """
        self.project_root = Path(project_root)
        self.logger = self._setup_logger()
        
        # 區域檢測參數
        self.detection_params = {
            'min_area': 2500,           # 最小區域面積（像素）
            'max_area_ratio': 0.8,     # 最大區域面積比例（相對於整頁）
            'text_density_threshold': 0.3,  # 文字密度閾值
            'contour_approximation': 0.02,  # 輪廓近似係數
            'morphology_kernel': (5, 5),   # 形態學核心大小
            'blur_kernel': (3, 3),         # 模糊核心大小
        }
        
        # 區域類型分類參數
        self.region_classification = {
            'aspect_ratio_threshold': 3.0,  # 長寬比閾值
            'size_threshold': 10000,        # 大小閾值
            'edge_density_threshold': 0.15, # 邊緣密度閾值
        }
        
        # 支援的圖片格式
        self.supported_formats = ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']
        
        self.logger.info("圖片區域檢測器初始化完成")
        
    def _setup_logger(self) -> logging.Logger:
        """設定日誌系統"""
        logs_dir = self.project_root / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_dir / f"image_region_detector_{timestamp}.log"
        
        logger = logging.getLogger('ImageRegionDetector')
        logger.setLevel(logging.INFO)
        
        if logger.handlers:
            return logger
            
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
        
    def preprocess_for_region_detection(self, image_path: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        預處理圖片以進行區域檢測
        
        Args:
            image_path: 圖片路徑
            
        Returns:
            (原始圖片, 處理後圖片)
        """
        try:
            # 讀取原始圖片
            original = cv2.imread(image_path)
            if original is None:
                raise ValueError(f"無法讀取圖片: {image_path}")
            
            # 轉換為灰階
            gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
            
            # 高斯模糊減少噪點
            blurred = cv2.GaussianBlur(gray, self.detection_params['blur_kernel'], 0)
            
            # 自適應二值化
            binary = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # 形態學操作：閉運算填充小空隙
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, self.detection_params['morphology_kernel'])
            processed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            return original, processed
            
        except Exception as e:
            self.logger.error(f"圖片預處理失敗: {e}")
            raise
            
    def detect_text_regions_from_ocr(self, ocr_result: Dict[str, Any]) -> List[Tuple[int, int, int, int]]:
        """
        從OCR結果中提取文字區域
        
        Args:
            ocr_result: OCR處理結果
            
        Returns:
            文字區域列表 [(x, y, width, height), ...]
        """
        text_regions = []
        
        if 'text_elements' in ocr_result:
            for element in ocr_result['text_elements']:
                if element['confidence'] > 30:  # 只考慮高置信度的文字
                    x = element['x']
                    y = element['y']
                    w = element['width']
                    h = element['height']
                    text_regions.append((x, y, w, h))
        
        return text_regions
        
    def find_image_regions(self, image_path: str, text_regions: List[Tuple[int, int, int, int]] = None) -> List[Dict[str, Any]]:
        """
        尋找圖片區域
        
        Args:
            image_path: 圖片路徑
            text_regions: 已知的文字區域列表
            
        Returns:
            圖片區域列表
        """
        try:
            # 預處理圖片
            original, processed = self.preprocess_for_region_detection(image_path)
            height, width = processed.shape
            total_area = height * width
            
            # 尋找輪廓
            contours, _ = cv2.findContours(processed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            image_regions = []
            
            for i, contour in enumerate(contours):
                # 計算輪廓面積
                area = cv2.contourArea(contour)
                
                # 過濾太小的區域
                if area < self.detection_params['min_area']:
                    continue
                    
                # 過濾太大的區域（可能是整頁）
                if area > total_area * self.detection_params['max_area_ratio']:
                    continue
                
                # 獲取邊界矩形
                x, y, w, h = cv2.boundingRect(contour)
                
                # 檢查是否與文字區域重疊
                is_text_region = self._is_overlapping_with_text(x, y, w, h, text_regions or [])
                
                if not is_text_region:
                    # 分析區域特徵
                    region_info = self._analyze_region_features(original, contour, x, y, w, h, i)
                    
                    # 分類區域類型
                    region_type = self._classify_region_type(region_info)
                    region_info['type'] = region_type
                    
                    image_regions.append(region_info)
            
            # 按面積排序（大到小）
            image_regions.sort(key=lambda x: x['area'], reverse=True)
            
            self.logger.info(f"找到 {len(image_regions)} 個潛在圖片區域")
            return image_regions
            
        except Exception as e:
            self.logger.error(f"圖片區域檢測失敗: {e}")
            raise
            
    def _is_overlapping_with_text(self, x: int, y: int, w: int, h: int, 
                                  text_regions: List[Tuple[int, int, int, int]]) -> bool:
        """
        檢查區域是否與文字區域重疊
        
        Args:
            x, y, w, h: 檢測區域的座標和尺寸
            text_regions: 文字區域列表
            
        Returns:
            是否重疊
        """
        region_area = w * h
        overlap_threshold = 0.3  # 重疊30%以上視為文字區域
        
        for tx, ty, tw, th in text_regions:
            # 計算重疊區域
            overlap_x1 = max(x, tx)
            overlap_y1 = max(y, ty)
            overlap_x2 = min(x + w, tx + tw)
            overlap_y2 = min(y + h, ty + th)
            
            if overlap_x2 > overlap_x1 and overlap_y2 > overlap_y1:
                overlap_area = (overlap_x2 - overlap_x1) * (overlap_y2 - overlap_y1)
                overlap_ratio = overlap_area / region_area
                
                if overlap_ratio > overlap_threshold:
                    return True
                    
        return False
        
    def _analyze_region_features(self, original: np.ndarray, contour: np.ndarray,
                                x: int, y: int, w: int, h: int, region_id: int) -> Dict[str, Any]:
        """
        分析區域特徵
        
        Args:
            original: 原始圖片
            contour: 輪廓
            x, y, w, h: 邊界矩形
            region_id: 區域ID
            
        Returns:
            區域特徵資訊
        """
        # 基本幾何特徵
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        aspect_ratio = w / h if h > 0 else 0
        extent = area / (w * h) if w > 0 and h > 0 else 0
        
        # 提取區域內容
        roi = original[y:y+h, x:x+w]
        roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # 計算邊緣密度
        edges = cv2.Canny(roi_gray, 50, 150)
        edge_density = np.sum(edges > 0) / (w * h) if w > 0 and h > 0 else 0
        
        # 計算顏色統計
        mean_intensity = np.mean(roi_gray)
        std_intensity = np.std(roi_gray)
        
        # 計算輪廓複雜度
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        solidity = area / hull_area if hull_area > 0 else 0
        
        return {
            'id': region_id,
            'x': int(x),
            'y': int(y),
            'width': int(w),
            'height': int(h),
            'area': int(area),
            'perimeter': float(perimeter),
            'aspect_ratio': float(aspect_ratio),
            'extent': float(extent),
            'edge_density': float(edge_density),
            'mean_intensity': float(mean_intensity),
            'std_intensity': float(std_intensity),
            'solidity': float(solidity),
            'roi_shape': roi.shape[:2]
        }
        
    def _classify_region_type(self, region_info: Dict[str, Any]) -> str:
        """
        分類區域類型
        
        Args:
            region_info: 區域資訊
            
        Returns:
            區域類型
        """
        aspect_ratio = region_info['aspect_ratio']
        area = region_info['area']
        edge_density = region_info['edge_density']
        
        # 基於特徵進行分類
        if edge_density > self.region_classification['edge_density_threshold']:
            if aspect_ratio > self.region_classification['aspect_ratio_threshold']:
                return 'diagram'  # 圖表
            elif area > self.region_classification['size_threshold']:
                return 'large_image'  # 大圖片
            else:
                return 'small_image'  # 小圖片
        else:
            if area > self.region_classification['size_threshold']:
                return 'block_image'  # 色塊圖片
            else:
                return 'graphic_element'  # 圖形元素
                
    def extract_image_regions(self, image_path: str, regions: List[Dict[str, Any]], 
                             pdf_name: str, page_num: int) -> List[str]:
        """
        提取並儲存圖片區域
        
        Args:
            image_path: 原始圖片路徑
            regions: 區域列表
            pdf_name: PDF檔案名稱
            page_num: 頁面編號
            
        Returns:
            提取的圖片路徑列表
        """
        try:
            # 讀取原始圖片
            original = cv2.imread(image_path)
            if original is None:
                raise ValueError(f"無法讀取圖片: {image_path}")
            
            # 建立輸出目錄
            regions_dir = self.project_root / "output" / "images" / pdf_name / "regions" / f"page_{page_num:03d}"
            regions_dir.mkdir(parents=True, exist_ok=True)
            
            extracted_paths = []
            
            for region in regions:
                # 提取區域
                x, y, w, h = region['x'], region['y'], region['width'], region['height']
                roi = original[y:y+h, x:x+w]
                
                # 建立檔案名稱
                region_filename = f"region_{region['id']:03d}_{region['type']}.png"
                region_path = regions_dir / region_filename
                
                # 儲存區域圖片
                cv2.imwrite(str(region_path), roi)
                extracted_paths.append(str(region_path))
                
                self.logger.info(f"提取區域: {region_filename} ({w}x{h})")
            
            return extracted_paths
            
        except Exception as e:
            self.logger.error(f"圖片區域提取失敗: {e}")
            raise
            
    def process_page_with_ocr(self, image_path: str, ocr_result: Dict[str, Any], 
                             pdf_name: str, page_num: int) -> Dict[str, Any]:
        """
        結合OCR結果處理頁面
        
        Args:
            image_path: 頁面圖片路徑
            ocr_result: OCR處理結果
            pdf_name: PDF檔案名稱
            page_num: 頁面編號
            
        Returns:
            綜合處理結果
        """
        try:
            self.logger.info(f"開始處理頁面 {page_num} 的圖片區域檢測")
            
            # 從OCR結果提取文字區域
            text_regions = self.detect_text_regions_from_ocr(ocr_result)
            self.logger.info(f"發現 {len(text_regions)} 個文字區域")
            
            # 檢測圖片區域
            image_regions = self.find_image_regions(image_path, text_regions)
            self.logger.info(f"檢測到 {len(image_regions)} 個圖片區域")
            
            # 提取圖片區域
            extracted_paths = []
            if image_regions:
                extracted_paths = self.extract_image_regions(image_path, image_regions, pdf_name, page_num)
            
            # 整合結果
            result = {
                'page_number': page_num,
                'pdf_name': pdf_name,
                'image_path': str(image_path),
                'text_regions': text_regions,
                'image_regions': image_regions,
                'extracted_region_paths': extracted_paths,
                'total_text_regions': len(text_regions),
                'total_image_regions': len(image_regions),
                'timestamp': datetime.now().isoformat()
            }
            
            # 儲存結果
            self.save_region_detection_result(result, pdf_name, page_num)
            
            return result
            
        except Exception as e:
            self.logger.error(f"頁面 {page_num} 圖片區域處理失敗: {e}")
            raise
            
    def save_region_detection_result(self, result: Dict[str, Any], pdf_name: str, page_num: int):
        """
        儲存區域檢測結果
        
        Args:
            result: 檢測結果
            pdf_name: PDF檔案名稱
            page_num: 頁面編號
        """
        try:
            # 建立輸出目錄
            output_dir = self.project_root / "output" / "text" / pdf_name
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 建立檔案名稱
            regions_filename = f"page_{page_num:03d}_regions.json"
            regions_path = output_dir / regions_filename
            
            # 儲存JSON檔案
            with open(regions_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"區域檢測結果已儲存：{regions_path}")
            
        except Exception as e:
            self.logger.error(f"儲存區域檢測結果失敗: {e}")
            raise
            
    def create_visualization(self, image_path: str, result: Dict[str, Any]) -> str:
        """
        建立視覺化圖片（顯示檢測到的區域）
        
        Args:
            image_path: 原始圖片路徑
            result: 檢測結果
            
        Returns:
            視覺化圖片路徑
        """
        try:
            # 讀取原始圖片
            original = cv2.imread(image_path)
            if original is None:
                raise ValueError(f"無法讀取圖片: {image_path}")
            
            visualization = original.copy()
            
            # 繪製文字區域（綠色）
            for tx, ty, tw, th in result['text_regions']:
                cv2.rectangle(visualization, (tx, ty), (tx + tw, ty + th), (0, 255, 0), 2)
                cv2.putText(visualization, 'TEXT', (tx, ty - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # 繪製圖片區域（紅色）
            for region in result['image_regions']:
                x, y, w, h = region['x'], region['y'], region['width'], region['height']
                cv2.rectangle(visualization, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.putText(visualization, region['type'].upper(), (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            
            # 儲存視覺化圖片
            viz_dir = self.project_root / "output" / "images" / result['pdf_name'] / "visualizations"
            viz_dir.mkdir(parents=True, exist_ok=True)
            
            viz_filename = f"page_{result['page_number']:03d}_regions_viz.png"
            viz_path = viz_dir / viz_filename
            
            cv2.imwrite(str(viz_path), visualization)
            
            self.logger.info(f"視覺化圖片已儲存：{viz_path}")
            return str(viz_path)
            
        except Exception as e:
            self.logger.error(f"建立視覺化失敗: {e}")
            raise


def main():
    """測試圖片區域檢測器功能"""
    print("🖼️  圖片區域檢測器測試")
    print("=" * 50)
    
    try:
        # 建立圖片區域檢測器
        detector = ImageRegionDetector()
        
        print("✅ 圖片區域檢測器初始化成功")
        print(f"📁 專案目錄: {detector.project_root}")
        print(f"⚙️  檢測參數: {detector.detection_params}")
        
    except Exception as e:
        print(f"❌ 初始化失敗: {e}")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML版面生成器
將OCR文字和圖片區域資料重新組合成HTML版面
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import base64
import mimetypes

class HTMLGenerator:
    """HTML版面生成器"""
    
    def __init__(self, project_root: str = "D:/pdf-to-html-converter"):
        """
        初始化HTML生成器
        
        Args:
            project_root: 專案根目錄
        """
        self.project_root = Path(project_root)
        self.logger = self._setup_logger()
        
        # HTML生成參數
        self.html_config = {
            'base_font_family': 'Arial, "Microsoft JhengHei", "微軟正黑體", sans-serif',
            'base_font_size': '14px',
            'line_height': '1.2',
            'text_selection': True,
            'responsive': True,
            'zoom_levels': [0.5, 0.75, 1.0, 1.25, 1.5, 2.0],
            'default_zoom': 1.0
        }
        
        # CSS樣式設定
        self.css_settings = {
            'container_max_width': '1200px',
            'container_margin': 'auto',
            'page_background': '#ffffff',
            'page_border': '1px solid #ddd',
            'page_shadow': '0 2px 10px rgba(0,0,0,0.1)',
            'text_color': '#333333',
            'text_selection_color': '#b3d4fc'
        }
        
        self.logger.info("HTML版面生成器初始化完成")
        
    def _setup_logger(self) -> logging.Logger:
        """設定日誌系統"""
        logs_dir = self.project_root / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_dir / f"html_generator_{timestamp}.log"
        
        logger = logging.getLogger('HTMLGenerator')
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
        
    def load_ocr_data(self, pdf_name: str, page_num: int) -> Optional[Dict[str, Any]]:
        """
        載入OCR處理結果
        
        Args:
            pdf_name: PDF檔案名稱
            page_num: 頁面編號
            
        Returns:
            OCR資料或None
        """
        try:
            ocr_file = self.project_root / "output" / "text" / pdf_name / f"page_{page_num:03d}.json"
            
            if not ocr_file.exists():
                self.logger.warning(f"OCR檔案不存在: {ocr_file}")
                return None
                
            with open(ocr_file, 'r', encoding='utf-8') as f:
                ocr_data = json.load(f)
                
            self.logger.info(f"成功載入OCR資料: {len(ocr_data.get('text_elements', []))} 個文字元素")
            return ocr_data
            
        except Exception as e:
            self.logger.error(f"載入OCR資料失敗: {e}")
            return None
            
    def load_region_data(self, pdf_name: str, page_num: int) -> Optional[Dict[str, Any]]:
        """
        載入圖片區域檢測結果
        
        Args:
            pdf_name: PDF檔案名稱
            page_num: 頁面編號
            
        Returns:
            區域資料或None
        """
        try:
            region_file = self.project_root / "output" / "text" / pdf_name / f"page_{page_num:03d}_regions.json"
            
            if not region_file.exists():
                self.logger.warning(f"區域檔案不存在: {region_file}")
                return None
                
            with open(region_file, 'r', encoding='utf-8') as f:
                region_data = json.load(f)
                
            self.logger.info(f"成功載入區域資料: {len(region_data.get('image_regions', []))} 個圖片區域")
            return region_data
            
        except Exception as e:
            self.logger.error(f"載入區域資料失敗: {e}")
            return None
            
    def encode_image_to_base64(self, image_path: str) -> Optional[str]:
        """
        將圖片編碼為base64字串
        
        Args:
            image_path: 圖片路徑
            
        Returns:
            base64編碼字串或None
        """
        try:
            if not os.path.exists(image_path):
                return None
                
            # 取得MIME類型
            mime_type, _ = mimetypes.guess_type(image_path)
            if not mime_type or not mime_type.startswith('image/'):
                mime_type = 'image/png'
                
            with open(image_path, 'rb') as f:
                image_data = f.read()
                
            base64_data = base64.b64encode(image_data).decode('utf-8')
            return f"data:{mime_type};base64,{base64_data}"
            
        except Exception as e:
            self.logger.error(f"圖片編碼失敗 {image_path}: {e}")
            return None
            
    def generate_css_styles(self, page_width: int, page_height: int) -> str:
        """
        生成CSS樣式
        
        Args:
            page_width: 頁面寬度
            page_height: 頁面高度
            
        Returns:
            CSS樣式字串
        """
        css = f"""
/* PDF轉HTML樣式表 */
* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: {self.html_config['base_font_family']};
    font-size: {self.html_config['base_font_size']};
    line-height: {self.html_config['line_height']};
    color: {self.css_settings['text_color']};
    background-color: #f5f5f5;
    padding: 20px;
}}

.container {{
    max-width: {self.css_settings['container_max_width']};
    margin: {self.css_settings['container_margin']};
}}

.page {{
    position: relative;
    width: {page_width}px;
    height: {page_height}px;
    background-color: {self.css_settings['page_background']};
    border: {self.css_settings['page_border']};
    box-shadow: {self.css_settings['page_shadow']};
    margin: 20px auto;
    overflow: hidden;
}}

.text-element {{
    position: absolute;
    user-select: text;
    cursor: text;
    white-space: nowrap;
    overflow: visible;
}}

.text-element:hover {{
    background-color: rgba(255, 255, 0, 0.1);
}}

.text-element::selection {{
    background-color: {self.css_settings['text_selection_color']};
}}

.image-region {{
    position: absolute;
    border: 1px solid transparent;
    transition: border-color 0.2s;
}}

.image-region:hover {{
    border-color: #007acc;
}}

.image-region img {{
    width: 100%;
    height: 100%;
    object-fit: contain;
}}

/* 響應式設計 */
@media (max-width: 768px) {{
    .container {{
        padding: 10px;
    }}
    
    .page {{
        transform: scale(0.8);
        transform-origin: top center;
        margin: 10px auto;
    }}
}}

/* 縮放控制 */
.zoom-controls {{
    position: fixed;
    top: 20px;
    right: 20px;
    background: white;
    padding: 10px;
    border-radius: 5px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    z-index: 1000;
}}

.zoom-controls button {{
    margin: 0 5px;
    padding: 5px 10px;
    border: 1px solid #ccc;
    background: white;
    cursor: pointer;
    border-radius: 3px;
}}

.zoom-controls button:hover {{
    background: #f0f0f0;
}}

.zoom-controls button.active {{
    background: #007acc;
    color: white;
}}

/* 頁面資訊 */
.page-info {{
    text-align: center;
    color: #666;
    font-size: 12px;
    margin: 10px 0;
}}

/* 列印樣式 */
@media print {{
    body {{
        background: white;
        padding: 0;
    }}
    
    .container {{
        max-width: none;
    }}
    
    .page {{
        box-shadow: none;
        border: none;
        margin: 0;
        page-break-after: always;
    }}
    
    .zoom-controls {{
        display: none;
    }}
}}
"""
        return css
        
    def generate_javascript(self) -> str:
        """
        生成JavaScript功能
        
        Returns:
            JavaScript程式碼字串
        """
        js = f"""
// PDF轉HTML互動功能
document.addEventListener('DOMContentLoaded', function() {{
    let currentZoom = {self.html_config['default_zoom']};
    const zoomLevels = {self.html_config['zoom_levels']};
    
    // 建立縮放控制
    function createZoomControls() {{
        const controls = document.createElement('div');
        controls.className = 'zoom-controls';
        controls.innerHTML = `
            <button onclick="zoomOut()">-</button>
            <span id="zoom-level">${{Math.round(currentZoom * 100)}}%</span>
            <button onclick="zoomIn()">+</button>
            <button onclick="resetZoom()">重設</button>
        `;
        document.body.appendChild(controls);
    }}
    
    // 縮放功能
    window.zoomIn = function() {{
        const currentIndex = zoomLevels.indexOf(currentZoom);
        if (currentIndex < zoomLevels.length - 1) {{
            currentZoom = zoomLevels[currentIndex + 1];
            applyZoom();
        }}
    }};
    
    window.zoomOut = function() {{
        const currentIndex = zoomLevels.indexOf(currentZoom);
        if (currentIndex > 0) {{
            currentZoom = zoomLevels[currentIndex - 1];
            applyZoom();
        }}
    }};
    
    window.resetZoom = function() {{
        currentZoom = 1.0;
        applyZoom();
    }};
    
    function applyZoom() {{
        const pages = document.querySelectorAll('.page');
        pages.forEach(page => {{
            page.style.transform = `scale(${{currentZoom}})`;
            page.style.transformOrigin = 'top center';
        }});
        
        document.getElementById('zoom-level').textContent = 
            Math.round(currentZoom * 100) + '%';
    }}
    
    // 文字選取統計
    function setupTextSelection() {{
        let selectedText = '';
        
        document.addEventListener('mouseup', function() {{
            const selection = window.getSelection();
            if (selection.toString().length > 0) {{
                selectedText = selection.toString();
                console.log('Selected text:', selectedText);
            }}
        }});
    }}
    
    // 鍵盤快捷鍵
    document.addEventListener('keydown', function(e) {{
        if (e.ctrlKey) {{
            switch(e.key) {{
                case '=':
                case '+':
                    e.preventDefault();
                    zoomIn();
                    break;
                case '-':
                    e.preventDefault();
                    zoomOut();
                    break;
                case '0':
                    e.preventDefault();
                    resetZoom();
                    break;
            }}
        }}
    }});
    
    // 初始化
    if (document.querySelectorAll('.page').length > 0) {{
        createZoomControls();
        setupTextSelection();
    }}
}});
"""
        return js
        
    def generate_page_html(self, ocr_data: Dict[str, Any], region_data: Optional[Dict[str, Any]] = None) -> str:
        """
        生成單頁HTML內容
        
        Args:
            ocr_data: OCR資料
            region_data: 區域資料
            
        Returns:
            HTML內容字串
        """
        page_width = ocr_data.get('image_width', 800)
        page_height = ocr_data.get('image_height', 600)
        
        html_elements = []
        
        # 生成文字元素
        text_elements = ocr_data.get('text_elements', [])
        for i, element in enumerate(text_elements):
            if element.get('confidence', 0) < 30:  # 跳過低置信度文字
                continue
                
            x = element.get('x', 0)
            y = element.get('y', 0)
            width = element.get('width', 0)
            height = element.get('height', 0)
            text = element.get('text', '').strip()
            font_size = element.get('font_size', 14)
            
            if not text:
                continue
                
            # HTML跳脫
            escaped_text = (text.replace('&', '&amp;')
                               .replace('<', '&lt;')
                               .replace('>', '&gt;')
                               .replace('"', '&quot;')
                               .replace("'", '&#x27;'))
            
            element_html = f'''
            <div class="text-element" 
                 style="left: {x}px; top: {y}px; width: {width}px; height: {height}px; font-size: {font_size}px;"
                 data-confidence="{element.get('confidence', 0)}"
                 data-element-id="{i}">
                {escaped_text}
            </div>'''
            
            html_elements.append(element_html)
            
        # 生成圖片元素
        if region_data:
            image_regions = region_data.get('image_regions', [])
            extracted_paths = region_data.get('extracted_region_paths', [])
            
            for region, image_path in zip(image_regions, extracted_paths):
                x = region.get('x', 0)
                y = region.get('y', 0)
                width = region.get('width', 100)
                height = region.get('height', 100)
                region_type = region.get('type', 'unknown')
                
                # 編碼圖片為base64
                base64_data = self.encode_image_to_base64(image_path)
                
                if base64_data:
                    image_html = f'''
                    <div class="image-region" 
                         style="left: {x}px; top: {y}px; width: {width}px; height: {height}px;"
                         data-region-type="{region_type}"
                         data-region-id="{region.get('id', 0)}">
                        <img src="{base64_data}" alt="{region_type}" />
                    </div>'''
                    
                    html_elements.append(image_html)
                    
        # 組合頁面HTML
        page_html = f'''
        <div class="page" style="width: {page_width}px; height: {page_height}px;">
            {''.join(html_elements)}
        </div>'''
        
        return page_html
        
    def generate_complete_html(self, pdf_name: str, pages_data: List[Tuple[Dict[str, Any], Optional[Dict[str, Any]]]]) -> str:
        """
        生成完整的HTML文件
        
        Args:
            pdf_name: PDF檔案名稱
            pages_data: 頁面資料列表 [(ocr_data, region_data), ...]
            
        Returns:
            完整HTML字串
        """
        if not pages_data:
            return ""
            
        # 取得第一頁的尺寸作為基準
        first_page_ocr = pages_data[0][0]
        page_width = first_page_ocr.get('image_width', 800)
        page_height = first_page_ocr.get('image_height', 600)
        
        # 生成CSS和JavaScript
        css_styles = self.generate_css_styles(page_width, page_height)
        javascript = self.generate_javascript()
        
        # 生成每頁HTML
        pages_html = []
        for page_num, (ocr_data, region_data) in enumerate(pages_data, 1):
            page_html = self.generate_page_html(ocr_data, region_data)
            pages_html.append(f'''
            <div class="page-info">第 {page_num} 頁</div>
            {page_html}
            ''')
        
        # 組合完整HTML
        full_html = f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{pdf_name} - PDF轉HTML</title>
    <style>{css_styles}</style>
</head>
<body>
    <div class="container">
        <h1 style="text-align: center; margin-bottom: 20px; color: #333;">
            {pdf_name}
        </h1>
        {''.join(pages_html)}
    </div>
    
    <script>{javascript}</script>
</body>
</html>'''
        
        return full_html
        
    def process_pdf_pages(self, pdf_name: str, page_range: Optional[Tuple[int, int]] = None) -> str:
        """
        處理PDF的所有頁面並生成HTML
        
        Args:
            pdf_name: PDF檔案名稱
            page_range: 頁面範圍 (start, end)，None表示所有頁面
            
        Returns:
            HTML檔案路徑
        """
        try:
            self.logger.info(f"開始處理PDF: {pdf_name}")
            
            # 確定頁面範圍
            text_dir = self.project_root / "output" / "text" / pdf_name
            if not text_dir.exists():
                raise FileNotFoundError(f"找不到PDF資料目錄: {text_dir}")
                
            # 尋找所有OCR檔案
            ocr_files = list(text_dir.glob("page_*.json"))
            ocr_files = [f for f in ocr_files if not f.name.endswith('_regions.json')]
            ocr_files.sort()
            
            if not ocr_files:
                raise FileNotFoundError(f"找不到OCR資料檔案在: {text_dir}")
                
            total_pages = len(ocr_files)
            self.logger.info(f"找到 {total_pages} 個頁面")
            
            # 應用頁面範圍過濾
            if page_range:
                start_page, end_page = page_range
                start_idx = max(0, start_page - 1)
                end_idx = min(total_pages, end_page)
                ocr_files = ocr_files[start_idx:end_idx]
                self.logger.info(f"處理頁面範圍: {start_page}-{end_page}")
            
            # 載入所有頁面資料
            pages_data = []
            for ocr_file in ocr_files:
                page_num = int(ocr_file.stem.split('_')[1])
                
                # 載入OCR資料
                ocr_data = self.load_ocr_data(pdf_name, page_num)
                if not ocr_data:
                    self.logger.warning(f"跳過頁面 {page_num}：無OCR資料")
                    continue
                    
                # 載入區域資料
                region_data = self.load_region_data(pdf_name, page_num)
                
                pages_data.append((ocr_data, region_data))
                
            if not pages_data:
                raise ValueError("沒有可處理的頁面資料")
                
            # 生成HTML
            html_content = self.generate_complete_html(pdf_name, pages_data)
            
            # 儲存HTML檔案
            output_dir = self.project_root / "output" / "html"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            html_filename = f"{pdf_name}_{timestamp}.html"
            html_path = output_dir / html_filename
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            self.logger.info(f"HTML檔案已生成: {html_path}")
            self.logger.info(f"處理完成，共 {len(pages_data)} 頁")
            
            return str(html_path)
            
        except Exception as e:
            self.logger.error(f"處理PDF頁面失敗: {e}")
            raise
            
    def generate_processing_report(self, pdf_name: str, html_path: str, pages_processed: int) -> Dict[str, Any]:
        """
        生成處理報告
        
        Args:
            pdf_name: PDF檔案名稱
            html_path: HTML檔案路徑
            pages_processed: 處理的頁面數
            
        Returns:
            處理報告
        """
        report = {
            'pdf_name': pdf_name,
            'html_path': html_path,
            'pages_processed': pages_processed,
            'file_size': os.path.getsize(html_path) if os.path.exists(html_path) else 0,
            'timestamp': datetime.now().isoformat(),
            'features': {
                'text_selectable': self.html_config['text_selection'],
                'responsive_design': self.html_config['responsive'],
                'zoom_controls': True,
                'keyboard_shortcuts': True
            }
        }
        
        # 儲存報告
        report_dir = self.project_root / "output" / "html"
        report_path = report_dir / f"{pdf_name}_report.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        return report


def main():
    """測試HTML生成器功能"""
    print("HTML版面生成器測試")
    print("=" * 50)
    
    try:
        # 建立HTML生成器
        generator = HTMLGenerator()
        
        print("HTML版面生成器初始化成功")
        print(f"專案目錄: {generator.project_root}")
        print(f"HTML配置: {generator.html_config}")
        
    except Exception as e:
        print(f"初始化失敗: {e}")


if __name__ == "__main__":
    main()
if __name__ == "__main__":
    main()

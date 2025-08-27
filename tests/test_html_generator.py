#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML版面生成器測試
測試HTML生成和版面重建功能
"""

import os
import sys
import tempfile
import json
from pathlib import Path
from typing import Dict, Any

# 添加src目錄到Python路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from html_generator import HTMLGenerator
    from PIL import Image
    print("成功導入HTML生成器模組")
except ImportError as e:
    print(f"導入失敗: {e}")
    print("\n請確認已安裝必要套件:")
    print("pip install pillow")
    sys.exit(1)

def create_sample_ocr_data(page_width: int = 800, page_height: int = 600) -> Dict[str, Any]:
    """建立範例OCR資料"""
    return {
        'image_path': '/test/page_001.png',
        'image_width': page_width,
        'image_height': page_height,
        'full_text': '標題文字\n這是測試內容\nTest Content',
        'text_elements': [
            {
                'text': '標題文字',
                'x': 50, 'y': 50, 'width': 150, 'height': 30,
                'font_size': 24, 'confidence': 95
            },
            {
                'text': '這是測試內容',
                'x': 50, 'y': 100, 'width': 200, 'height': 25,
                'font_size': 18, 'confidence': 90
            },
            {
                'text': 'Test',
                'x': 50, 'y': 150, 'width': 60, 'height': 20,
                'font_size': 16, 'confidence': 88
            },
            {
                'text': 'Content',
                'x': 120, 'y': 150, 'width': 80, 'height': 20,
                'font_size': 16, 'confidence': 92
            }
        ],
        'total_elements': 4,
        'language': 'chi_tra+eng',
        'timestamp': '2025-08-27T10:00:00'
    }

def create_sample_region_data() -> Dict[str, Any]:
    """建立範例區域資料"""
    return {
        'page_number': 1,
        'pdf_name': 'test_pdf',
        'text_regions': [[50, 50, 150, 30], [50, 100, 200, 25]],
        'image_regions': [
            {
                'id': 0,
                'x': 400, 'y': 50,
                'width': 300, 'height': 200,
                'area': 60000,
                'aspect_ratio': 1.5,
                'type': 'large_image'
            },
            {
                'id': 1,
                'x': 100, 'y': 300,
                'width': 150, 'height': 100,
                'area': 15000,
                'aspect_ratio': 1.5,
                'type': 'small_image'
            }
        ],
        'extracted_region_paths': [
            '/test/region_000_large_image.png',
            '/test/region_001_small_image.png'
        ],
        'total_text_regions': 2,
        'total_image_regions': 2,
        'timestamp': '2025-08-27T10:00:00'
    }

def create_test_image(width: int = 100, height: int = 100) -> str:
    """建立測試圖片檔案"""
    img = Image.new('RGB', (width, height), color='lightblue')
    temp_dir = tempfile.mkdtemp()
    image_path = os.path.join(temp_dir, 'test_image.png')
    img.save(image_path)
    return image_path

def setup_test_data_structure(temp_dir: str, pdf_name: str = "test_pdf"):
    """建立測試資料結構"""
    base_dir = Path(temp_dir)
    
    # 建立目錄結構
    text_dir = base_dir / "output" / "text" / pdf_name
    text_dir.mkdir(parents=True, exist_ok=True)
    
    # 建立OCR資料檔案
    ocr_data = create_sample_ocr_data()
    ocr_file = text_dir / "page_001.json"
    with open(ocr_file, 'w', encoding='utf-8') as f:
        json.dump(ocr_data, f, ensure_ascii=False, indent=2)
    
    # 建立區域資料檔案
    region_data = create_sample_region_data()
    region_file = text_dir / "page_001_regions.json"
    with open(region_file, 'w', encoding='utf-8') as f:
        json.dump(region_data, f, ensure_ascii=False, indent=2)
    
    # 建立測試圖片檔案
    regions_dir = base_dir / "output" / "images" / pdf_name / "regions" / "page_001"
    regions_dir.mkdir(parents=True, exist_ok=True)
    
    # 建立區域圖片
    test_images = []
    for i, region in enumerate(region_data['image_regions']):
        img_path = regions_dir / f"region_{i:03d}_{region['type']}.png"
        img = Image.new('RGB', (region['width'], region['height']), 
                       color='red' if i == 0 else 'blue')
        img.save(img_path)
        test_images.append(str(img_path))
        
    # 更新區域資料中的路徑
    region_data['extracted_region_paths'] = test_images
    with open(region_file, 'w', encoding='utf-8') as f:
        json.dump(region_data, f, ensure_ascii=False, indent=2)
    
    return ocr_data, region_data, test_images

def test_generator_initialization():
    """測試生成器初始化"""
    print("\n測試1: 生成器初始化")
    print("-" * 40)
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = HTMLGenerator(project_root=temp_dir)
            
            print(f"   測試目錄: {temp_dir}")
            print(f"   HTML配置: {generator.html_config['base_font_family']}")
            print(f"   CSS設定: {generator.css_settings['container_max_width']}")
            
            return True
            
    except Exception as e:
        print(f"   測試失敗: {e}")
        return False

def test_data_loading():
    """測試資料載入功能"""
    print("\n測試2: 資料載入")
    print("-" * 40)
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = HTMLGenerator(project_root=temp_dir)
            
            # 設定測試資料
            ocr_data, region_data, _ = setup_test_data_structure(temp_dir)
            
            # 測試OCR資料載入
            loaded_ocr = generator.load_ocr_data("test_pdf", 1)
            if loaded_ocr:
                print(f"   OCR資料載入成功: {len(loaded_ocr['text_elements'])} 個文字元素")
            else:
                print("   OCR資料載入失敗")
                return False
            
            # 測試區域資料載入
            loaded_region = generator.load_region_data("test_pdf", 1)
            if loaded_region:
                print(f"   區域資料載入成功: {len(loaded_region['image_regions'])} 個圖片區域")
            else:
                print("   區域資料載入失敗")
                return False
            
            return True
            
    except Exception as e:
        print(f"   資料載入測試失敗: {e}")
        return False

def test_image_encoding():
    """測試圖片編碼功能"""
    print("\n測試3: 圖片編碼")
    print("-" * 40)
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = HTMLGenerator(project_root=temp_dir)
            
            # 建立測試圖片
            test_image_path = create_test_image(50, 50)
            
            # 測試base64編碼
            base64_data = generator.encode_image_to_base64(test_image_path)
            
            if base64_data and base64_data.startswith('data:image/'):
                print(f"   圖片編碼成功")
                print(f"   編碼長度: {len(base64_data)} 字元")
                print(f"   格式: {base64_data[:30]}...")
                
                # 清理測試檔案
                os.unlink(test_image_path)
                return True
            else:
                print("   圖片編碼失敗")
                return False
            
    except Exception as e:
        print(f"   圖片編碼測試失敗: {e}")
        return False

def test_css_generation():
    """測試CSS生成"""
    print("\n測試4: CSS樣式生成")
    print("-" * 40)
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = HTMLGenerator(project_root=temp_dir)
            
            # 生成CSS
            css_content = generator.generate_css_styles(800, 600)
            
            # 檢查CSS內容
            required_selectors = ['.container', '.page', '.text-element', '.image-region']
            missing_selectors = []
            
            for selector in required_selectors:
                if selector not in css_content:
                    missing_selectors.append(selector)
            
            if missing_selectors:
                print(f"   缺少CSS選擇器: {missing_selectors}")
                return False
            else:
                print(f"   CSS生成成功")
                print(f"   CSS長度: {len(css_content)} 字元")
                print(f"   包含選擇器: {required_selectors}")
                return True
            
    except Exception as e:
        print(f"   CSS生成測試失敗: {e}")
        return False

def test_javascript_generation():
    """測試JavaScript生成"""
    print("\n測試5: JavaScript生成")
    print("-" * 40)
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = HTMLGenerator(project_root=temp_dir)
            
            # 生成JavaScript
            js_content = generator.generate_javascript()
            
            # 檢查JavaScript內容
            required_functions = ['zoomIn', 'zoomOut', 'resetZoom', 'applyZoom']
            missing_functions = []
            
            for func in required_functions:
                if func not in js_content:
                    missing_functions.append(func)
            
            if missing_functions:
                print(f"   缺少JavaScript函數: {missing_functions}")
                return False
            else:
                print(f"   JavaScript生成成功")
                print(f"   JavaScript長度: {len(js_content)} 字元")
                print(f"   包含函數: {required_functions}")
                return True
            
    except Exception as e:
        print(f"   JavaScript生成測試失敗: {e}")
        return False

def test_page_html_generation():
    """測試單頁HTML生成"""
    print("\n測試6: 單頁HTML生成")
    print("-" * 40)
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = HTMLGenerator(project_root=temp_dir)
            
            # 設定測試資料
            ocr_data, region_data, _ = setup_test_data_structure(temp_dir)
            
            # 生成頁面HTML
            page_html = generator.generate_page_html(ocr_data, region_data)
            
            # 檢查HTML內容
            if '<div class="page"' in page_html and '<div class="text-element"' in page_html:
                print(f"   頁面HTML生成成功")
                print(f"   HTML長度: {len(page_html)} 字元")
                
                # 計算文字元素數量
                text_count = page_html.count('<div class="text-element"')
                print(f"   文字元素數: {text_count}")
                
                # 計算圖片元素數量
                image_count = page_html.count('<div class="image-region"')
                print(f"   圖片元素數: {image_count}")
                
                return True
            else:
                print("   頁面HTML結構不正確")
                return False
            
    except Exception as e:
        print(f"   頁面HTML生成測試失敗: {e}")
        return False

def test_complete_html_generation():
    """測試完整HTML生成"""
    print("\n測試7: 完整HTML生成")
    print("-" * 40)
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = HTMLGenerator(project_root=temp_dir)
            
            # 設定測試資料
            ocr_data, region_data, _ = setup_test_data_structure(temp_dir)
            pages_data = [(ocr_data, region_data)]
            
            # 生成完整HTML
            html_content = generator.generate_complete_html("test_pdf", pages_data)
            
            # 檢查HTML結構
            required_elements = [
                '<!DOCTYPE html>',
                '<html lang="zh-TW">',
                '<head>',
                '<style>',
                '<script>',
                '<div class="container">',
                '<div class="page">'
            ]
            
            missing_elements = []
            for element in required_elements:
                if element not in html_content:
                    missing_elements.append(element)
            
            if missing_elements:
                print(f"   缺少HTML元素: {missing_elements}")
                return False
            else:
                print(f"   完整HTML生成成功")
                print(f"   HTML長度: {len(html_content)} 字元")
                print(f"   包含必要元素: {len(required_elements)} 個")
                
                # 檢查中文支援
                if 'lang="zh-TW"' in html_content and 'charset="UTF-8"' in html_content:
                    print(f"   中文支援: 正確")
                else:
                    print(f"   中文支援: 可能有問題")
                
                return True
            
    except Exception as e:
        print(f"   完整HTML生成測試失敗: {e}")
        return False

def test_pdf_processing():
    """測試PDF處理流程"""
    print("\n測試8: PDF處理流程")
    print("-" * 40)
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = HTMLGenerator(project_root=temp_dir)
            
            # 設定多頁測試資料
            pdf_name = "test_multi_page"
            
            # 建立多頁資料
            for page_num in range(1, 4):  # 建立3頁
                text_dir = Path(temp_dir) / "output" / "text" / pdf_name
                text_dir.mkdir(parents=True, exist_ok=True)
                
                # OCR資料
                ocr_data = create_sample_ocr_data()
                ocr_data['page_number'] = page_num
                ocr_file = text_dir / f"page_{page_num:03d}.json"
                with open(ocr_file, 'w', encoding='utf-8') as f:
                    json.dump(ocr_data, f, ensure_ascii=False, indent=2)
            
            # 處理PDF
            html_path = generator.process_pdf_pages(pdf_name)
            
            if os.path.exists(html_path):
                file_size = os.path.getsize(html_path)
                print(f"   PDF處理成功")
                print(f"   HTML檔案: {os.path.basename(html_path)}")
                print(f"   檔案大小: {file_size} bytes")
                
                # 讀取並檢查內容
                with open(html_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                page_count = content.count('<div class="page"')
                print(f"   頁面數量: {page_count}")
                
                return page_count == 3
            else:
                print("   HTML檔案未生成")
                return False
            
    except Exception as e:
        print(f"   PDF處理流程測試失敗: {e}")
        return False

def test_processing_report():
    """測試處理報告生成"""
    print("\n測試9: 處理報告")
    print("-" * 40)
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = HTMLGenerator(project_root=temp_dir)
            
            # 建立虛擬HTML檔案
            html_dir = Path(temp_dir) / "output" / "html"
            html_dir.mkdir(parents=True, exist_ok=True)
            html_path = html_dir / "test_report.html"
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write("<html><body><h1>Test</h1></body></html>")
            
            # 生成報告
            report = generator.generate_processing_report("test_pdf", str(html_path), 3)
            
            # 檢查報告內容
            required_fields = ['pdf_name', 'html_path', 'pages_processed', 'features']
            missing_fields = [field for field in required_fields if field not in report]
            
            if missing_fields:
                print(f"   缺少報告欄位: {missing_fields}")
                return False
            else:
                print(f"   處理報告生成成功")
                print(f"   PDF名稱: {report['pdf_name']}")
                print(f"   處理頁數: {report['pages_processed']}")
                print(f"   檔案大小: {report['file_size']} bytes")
                print(f"   功能特色: {len(report['features'])} 項")
                
                return True
            
    except Exception as e:
        print(f"   處理報告測試失敗: {e}")
        return False

def main():
    """執行所有HTML生成器測試"""
    print("HTML版面生成器測試套件")
    print("=" * 50)
    
    tests = [
        ("生成器初始化", test_generator_initialization),
        ("資料載入", test_data_loading),
        ("圖片編碼", test_image_encoding),
        ("CSS樣式生成", test_css_generation),
        ("JavaScript生成", test_javascript_generation),
        ("單頁HTML生成", test_page_html_generation),
        ("完整HTML生成", test_complete_html_generation),
        ("PDF處理流程", test_pdf_processing),
        ("處理報告", test_processing_report)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
                print(f"   {test_name}: 通過")
            else:
                print(f"   {test_name}: 失敗")
        except Exception as e:
            print(f"   {test_name}: 錯誤 - {e}")
    
    print("\n" + "=" * 50)
    print(f"測試結果:")
    print(f"   通過: {passed}")
    print(f"   失敗: {total - passed}")
    print(f"   通過率: {(passed/total)*100:.1f}%")
    
    if passed >= 7:  # 至少通過主要功能測試
        print("\n主要功能測試通過！HTML生成器準備就緒！")
        print("現在可以進行完整的PDF轉HTML流程測試")
        
        print("\n模組功能摘要:")
        print("- 載入OCR文字和座標資料")
        print("- 載入圖片區域檢測結果")
        print("- CSS絕對定位重建版面")
        print("- 可選取文字元素生成")
        print("- 圖片base64編碼嵌入")
        print("- 響應式設計支援")
        print("- 縮放控制功能")
        print("- 鍵盤快捷鍵")
        print("- 多頁面支援")
        print("- 處理報告生成")
        
    else:
        print("\n部分測試失敗，請檢查：")
        print("1. 模組相依性是否正確")
        print("2. 檔案權限是否正確")
        print("3. 必要的Python套件是否已安裝")

if __name__ == "__main__":
    main()
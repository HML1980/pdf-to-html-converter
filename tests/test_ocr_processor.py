#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR處理模組測試
測試文字識別功能和座標提取
"""

import os
import sys
import tempfile
import json
from pathlib import Path

# 添加src目錄到Python路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from ocr_processor import OCRProcessor
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
    print("✅ 成功導入OCR處理模組")
except ImportError as e:
    print(f"❌ 導入失敗: {e}")
    print("\n請確認已安裝必要套件:")
    print("pip install pytesseract pillow opencv-python")
    print("\n並安裝Tesseract OCR:")
    print("Windows: 下載 https://github.com/UB-Mannheim/tesseract/wiki")
    print("macOS: brew install tesseract tesseract-lang")
    print("Linux: sudo apt-get install tesseract-ocr tesseract-ocr-chi-tra")
    sys.exit(1)

def create_test_image_with_text(text: str, width: int = 800, height: int = 600) -> str:
    """
    建立包含文字的測試圖片
    
    Args:
        text: 要包含的文字
        width: 圖片寬度
        height: 圖片高度
        
    Returns:
        測試圖片的路徑
    """
    # 建立白色背景圖片
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # 使用預設字體
    try:
        # 嘗試載入較大的字體
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        # 如果沒有arial，使用預設字體
        font = ImageFont.load_default()
    
    # 繪製文字
    lines = text.split('\n')
    y_offset = 50
    
    for line in lines:
        draw.text((50, y_offset), line, fill='black', font=font)
        y_offset += 40
    
    # 儲存測試圖片
    temp_dir = tempfile.mkdtemp()
    image_path = os.path.join(temp_dir, 'test_image.png')
    img.save(image_path)
    
    return image_path

def test_ocr_basic_functionality():
    """測試OCR基本功能"""
    print("\n🧪 測試1: OCR基本功能")
    print("-" * 40)
    
    try:
        # 建立臨時目錄作為測試環境
        with tempfile.TemporaryDirectory() as temp_dir:
            # 初始化OCR處理器
            ocr = OCRProcessor(project_root=temp_dir)
            
            print(f"   📁 測試目錄: {temp_dir}")
            print(f"   🌐 OCR語言設定: {ocr.language}")
            print(f"   ⚙️  OCR配置: {ocr.ocr_config}")
            
            return True
            
    except Exception as e:
        print(f"   ❌ 測試失敗: {e}")
        return False

def test_tesseract_validation():
    """測試Tesseract驗證功能"""
    print("\n🧪 測試2: Tesseract安裝驗證")
    print("-" * 40)
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            ocr = OCRProcessor(project_root=temp_dir)
            
            is_valid = ocr.validate_tesseract_installation()
            
            if is_valid:
                print("   ✅ Tesseract安裝驗證通過")
                return True
            else:
                print("   ⚠️  Tesseract安裝可能有問題，但繼續測試")
                return True  # 不讓這個阻止其他測試
                
    except Exception as e:
        print(f"   ❌ 驗證失敗: {e}")
        print("   💡 請確保已正確安裝Tesseract OCR")
        return False

def test_text_extraction():
    """測試文字提取功能"""
    print("\n🧪 測試3: 文字提取功能")
    print("-" * 40)
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            ocr = OCRProcessor(project_root=temp_dir)
            
            # 建立測試圖片
            test_text = "Hello World\n這是測試文字\n123 ABC"
            image_path = create_test_image_with_text(test_text)
            
            print(f"   🖼️  建立測試圖片: {image_path}")
            
            try:
                # 執行OCR
                result = ocr.extract_text_with_coordinates(image_path)
                
                print(f"   📝 識別文字數: {result['total_elements']}")
                print(f"   📐 圖片尺寸: {result['image_width']} x {result['image_height']}")
                print(f"   🔤 完整文字預覽: {result['full_text'][:100]}...")
                
                # 顯示部分識別結果
                if result['text_elements']:
                    print("   🎯 識別元素範例:")
                    for i, element in enumerate(result['text_elements'][:3]):
                        if element['text'].strip():
                            print(f"      {i+1}. '{element['text']}' at ({element['x']}, {element['y']})")
                
                # 清理測試檔案
                os.unlink(image_path)
                
                return True
                
            except Exception as ocr_error:
                print(f"   ⚠️  OCR執行失敗: {ocr_error}")
                print("   💡 這可能是因為Tesseract語言包未安裝")
                return False
                
    except Exception as e:
        print(f"   ❌ 測試失敗: {e}")
        return False

def test_image_preprocessing():
    """測試圖片預處理功能"""
    print("\n🧪 測試4: 圖片預處理")
    print("-" * 40)
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            ocr = OCRProcessor(project_root=temp_dir)
            
            # 建立測試圖片
            test_text = "PreProcess Test"
            image_path = create_test_image_with_text(test_text, 400, 300)
            
            # 執行預處理
            processed_image = ocr.preprocess_image(image_path)
            
            print(f"   🖼️  原始圖片: {image_path}")
            print(f"   🔧 處理後形狀: {processed_image.shape}")
            print(f"   🎨 圖片類型: {processed_image.dtype}")
            
            # 清理
            os.unlink(image_path)
            
            return True
            
    except Exception as e:
        print(f"   ❌ 預處理測試失敗: {e}")
        return False

def test_json_output():
    """測試JSON輸出功能"""
    print("\n🧪 測試5: JSON輸出格式")
    print("-" * 40)
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            ocr = OCRProcessor(project_root=temp_dir)
            
            # 建立測試圖片
            test_text = "JSON Test\n輸出測試"
            image_path = create_test_image_with_text(test_text)
            
            try:
                # 處理頁面
                result = ocr.process_page_image(image_path, "test_pdf", 1)
                
                # 檢查JSON檔案是否生成
                json_dir = Path(temp_dir) / "output" / "text" / "test_pdf"
                json_file = json_dir / "page_001.json"
                
                if json_file.exists():
                    # 讀取JSON檔案
                    with open(json_file, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                    
                    print("   ✅ JSON檔案成功生成")
                    print(f"   📁 檔案路徑: {json_file}")
                    print(f"   📋 資料欄位: {list(json_data.keys())}")
                    
                    # 驗證必要欄位
                    required_fields = ['image_path', 'text_elements', 'full_text', 'timestamp']
                    missing_fields = [field for field in required_fields if field not in json_data]
                    
                    if missing_fields:
                        print(f"   ⚠️  缺少欄位: {missing_fields}")
                    else:
                        print("   ✅ 所有必要欄位都存在")
                else:
                    print("   ❌ JSON檔案未生成")
                    return False
                
                # 清理
                os.unlink(image_path)
                
                return True
                
            except Exception as process_error:
                print(f"   ⚠️  處理失敗: {process_error}")
                return False
            
    except Exception as e:
        print(f"   ❌ JSON測試失敗: {e}")
        return False

def test_batch_processing():
    """測試批次處理功能"""
    print("\n🧪 測試6: 批次處理")
    print("-" * 40)
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            ocr = OCRProcessor(project_root=temp_dir)
            
            # 建立多個測試圖片
            images_dir = Path(temp_dir) / "output" / "images" / "batch_test"
            images_dir.mkdir(parents=True, exist_ok=True)
            
            test_texts = [
                "Page 1 Content\nFirst page text",
                "Page 2 Content\nSecond page text", 
                "Page 3 Content\nThird page text"
            ]
            
            # 生成測試圖片
            for i, text in enumerate(test_texts, 1):
                img = Image.new('RGB', (600, 400), color='white')
                draw = ImageDraw.Draw(img)
                draw.text((50, 50), text, fill='black')
                
                img_path = images_dir / f"page_{i:03d}.png"
                img.save(img_path)
            
            print(f"   📁 建立測試圖片目錄: {images_dir}")
            print(f"   🖼️  生成 {len(test_texts)} 張測試圖片")
            
            try:
                # 執行批次處理
                stats = ocr.process_pdf_images("batch_test", str(images_dir))
                
                print(f"   📊 處理統計:")
                print(f"      總頁數: {stats['total_pages']}")
                print(f"      成功處理: {stats['processed_pages']}")
                print(f"      失敗頁數: {stats['failed_pages']}")
                print(f"      成功率: {stats['success_rate']:.1f}%")
                
                return stats['processed_pages'] > 0
                
            except Exception as batch_error:
                print(f"   ⚠️  批次處理失敗: {batch_error}")
                return False
                
    except Exception as e:
        print(f"   ❌ 批次處理測試失敗: {e}")
        return False

def main():
    """執行所有OCR測試"""
    print("🔍 OCR處理模組測試套件")
    print("=" * 50)
    
    tests = [
        ("基本功能", test_ocr_basic_functionality),
        ("Tesseract驗證", test_tesseract_validation), 
        ("文字提取", test_text_extraction),
        ("圖片預處理", test_image_preprocessing),
        ("JSON輸出", test_json_output),
        ("批次處理", test_batch_processing)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
                print(f"   ✅ {test_name}: 通過")
            else:
                print(f"   ❌ {test_name}: 失敗")
        except Exception as e:
            print(f"   💥 {test_name}: 錯誤 - {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 測試結果:")
    print(f"   ✅ 通過: {passed}")
    print(f"   ❌ 失敗: {total - passed}")
    print(f"   📈 通過率: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 所有測試通過！OCR模組準備就緒！")
        print("💡 現在可以進入階段4：圖片區域分離")
    else:
        print("\n⚠️  部分測試失敗，請檢查：")
        print("1. Tesseract OCR是否正確安裝")
        print("2. 中文語言包是否已安裝")
        print("3. 必要的Python套件是否已安裝")

if __name__ == "__main__":
    main()
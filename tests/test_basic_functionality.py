"""
PDF處理模組基本功能測試
測試在Codespaces雲端環境中的基本運行情況
"""

import sys
import os
from pathlib import Path
import tempfile
import shutil

# 將src目錄加入Python路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_module_import():
    """測試模組導入"""
    print("🧪 測試1: 模組導入")
    try:
        from pdf_processor import PDFProcessor
        print("   ✅ PDFProcessor 模組導入成功")
        return True
    except ImportError as e:
        print(f"   ❌ 模組導入失敗: {e}")
        return False
    except Exception as e:
        print(f"   ⚠️  導入時發生錯誤: {e}")
        return False

def test_processor_initialization():
    """測試PDF處理器初始化"""
    print("\n🧪 測試2: 處理器初始化")
    try:
        from pdf_processor import PDFProcessor
        
        # 使用臨時目錄進行測試，避免影響D槽
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = os.path.join(temp_dir, "test_pdf_converter")
            
            processor = PDFProcessor(base_path=test_path)
            
            # 檢查屬性設定
            assert processor.dpi == 300
            assert processor.image_format == 'PNG'
            assert Path(test_path) == processor.base_path
            
            print("   ✅ 處理器初始化成功")
            print(f"   📁 測試目錄: {test_path}")
            print(f"   🖼️  DPI設定: {processor.dpi}")
            print(f"   📷 圖片格式: {processor.image_format}")
            return True
            
    except Exception as e:
        print(f"   ❌ 初始化失敗: {e}")
        return False

def test_directory_creation():
    """測試目錄建立功能"""
    print("\n🧪 測試3: 目錄結構建立")
    try:
        from pdf_processor import PDFProcessor
        
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = os.path.join(temp_dir, "test_pdf_converter")
            
            processor = PDFProcessor(base_path=test_path)
            
            # 檢查目錄是否建立
            required_dirs = [
                processor.base_path,
                processor.output_path,
                processor.images_path,
                processor.text_path,
                processor.html_path,
                processor.logs_path
            ]
            
            all_exist = True
            for dir_path in required_dirs:
                if dir_path.exists():
                    print(f"   ✅ {dir_path.name}/ 目錄存在")
                else:
                    print(f"   ❌ {dir_path.name}/ 目錄不存在")
                    all_exist = False
            
            return all_exist
            
    except Exception as e:
        print(f"   ❌ 目錄建立測試失敗: {e}")
        return False

def test_pdf_validation():
    """測試PDF驗證功能"""
    print("\n🧪 測試4: PDF驗證功能")
    try:
        from pdf_processor import PDFProcessor
        
        with tempfile.TemporaryDirectory() as temp_dir:
            processor = PDFProcessor(base_path=temp_dir)
            
            # 測試不存在的檔案
            is_valid, message = processor.validate_pdf("nonexistent.pdf")
            if not is_valid:
                print("   ✅ 正確識別不存在的檔案")
            else:
                print("   ❌ 未能識別不存在的檔案")
                return False
            
            # 測試非PDF檔案
            test_file = os.path.join(temp_dir, "test.txt")
            with open(test_file, 'w') as f:
                f.write("test content")
                
            is_valid, message = processor.validate_pdf(test_file)
            if not is_valid:
                print("   ✅ 正確識別非PDF檔案")
            else:
                print("   ❌ 未能識別非PDF檔案")
                return False
                
            # 測試空檔案
            empty_pdf = os.path.join(temp_dir, "empty.pdf")
            open(empty_pdf, 'w').close()
            
            is_valid, message = processor.validate_pdf(empty_pdf)
            if not is_valid:
                print("   ✅ 正確識別空檔案")
            else:
                print("   ❌ 未能識別空檔案")
                return False
            
            return True
            
    except Exception as e:
        print(f"   ❌ PDF驗證測試失敗: {e}")
        return False

def test_conversion_info():
    """測試轉換資訊功能"""
    print("\n🧪 測試5: 轉換資訊功能")
    try:
        from pdf_processor import PDFProcessor
        
        with tempfile.TemporaryDirectory() as temp_dir:
            processor = PDFProcessor(base_path=temp_dir)
            
            # 建立測試PDF路徑
            test_pdf = os.path.join(temp_dir, "test.pdf")
            
            info = processor.get_conversion_info(test_pdf)
            
            required_keys = ['pdf_path', 'pdf_name', 'output_dir', 'dpi', 'format', 'estimated_time']
            
            for key in required_keys:
                if key in info:
                    print(f"   ✅ {key}: {info[key]}")
                else:
                    print(f"   ❌ 缺少資訊鍵: {key}")
                    return False
            
            return True
            
    except Exception as e:
        print(f"   ❌ 轉換資訊測試失敗: {e}")
        return False

def run_all_tests():
    """執行所有測試"""
    print("🚀 PDF處理器基本功能測試")
    print("=" * 50)
    
    tests = [
        test_module_import,
        test_processor_initialization,
        test_directory_creation,
        test_pdf_validation,
        test_conversion_info
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"   ❌ 測試執行錯誤: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 測試結果：")
    print(f"   ✅ 通過: {passed}")
    print(f"   ❌ 失敗: {failed}")
    print(f"   📈 通過率: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 所有測試通過！PDF處理器基本功能正常！")
        print("💡 現在可以安全地進行下一階段開發")
    else:
        print(f"\n⚠️  有 {failed} 個測試失敗，請檢查程式碼")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
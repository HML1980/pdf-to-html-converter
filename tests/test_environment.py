"""
環境測試 - 驗證雲端開發環境設置
"""

import sys
import subprocess
from pathlib import Path

def test_python_packages():
    """測試必要套件"""
    packages = ['pdf2image', 'PIL', 'cv2', 'pytesseract', 'click', 'tqdm']
    
    for package in packages:
        try:
            __import__(package)
            print(f"✅ {package} 導入成功")
        except ImportError:
            print(f"❌ {package} 導入失敗")
            return False
    return True

def test_system_tools():
    """測試系統工具"""
    try:
        result = subprocess.run(['tesseract', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Tesseract OCR 可用")
        
        result = subprocess.run(['pdftoppm', '-h'], capture_output=True, text=True)
        print("✅ Poppler 工具可用")
        
        return True
    except FileNotFoundError:
        print("❌ 系統工具測試失敗")
        return False

if __name__ == "__main__":
    print("🔍 開始環境測試...")
    print("=" * 40)
    
    if test_python_packages() and test_system_tools():
        print("=" * 40)
        print("🎉 環境測試全部通過！")
    else:
        print("❌ 環境測試失敗")
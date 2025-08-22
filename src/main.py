#!/usr/bin/env python3
"""
PDF轉HTML轉換器 - 雲端版本
主程式入口點
"""

import sys
import json
import click
from pathlib import Path

# 添加src目錄到Python路徑
sys.path.append(str(Path(__file__).parent))

@click.command()
@click.option('--input', '-i', help='輸入PDF檔案路徑')
@click.option('--output', '-o', default='./output', help='輸出目錄路徑')
@click.option('--config', '-c', default='./config/settings.json', help='設定檔路徑')
@click.option('--verbose', '-v', is_flag=True, help='顯示詳細資訊')
def main(input, output, config, verbose):
    """PDF轉HTML轉換工具 - 雲端版本"""
    
    click.echo("PDF轉HTML轉換器 - 雲端版本")
    click.echo("=" * 50)
    
    if not input:
        click.echo("使用方式:")
        click.echo("  python src/main.py -i your_file.pdf")
        click.echo("  python src/main.py --help")
        click.echo("")
        click.echo("環境已準備就緒，等待PDF檔案輸入...")
        return
    
    # 載入設定
    try:
        with open(config, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        click.echo(f"載入設定檔: {config}")
    except FileNotFoundError:
        click.echo(f"找不到設定檔: {config}")
        return
    
    # 顯示設定資訊
    if verbose:
        click.echo(f"輸入檔案: {input}")
        click.echo(f"輸出目錄: {output}")
        click.echo(f"OCR語言: {settings['ocr']['language']}")
        click.echo(f"圖片DPI: {settings['ocr']['dpi']}")
    
    click.echo("轉換功能將在階段2-6中逐步實作")
    click.echo("階段1完成 - 環境設置成功")

if __name__ == "__main__":
    main()
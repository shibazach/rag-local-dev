#!/usr/bin/env python3
# new/utils/update_page_counts.py
# 既存PDFファイルの頁数を更新するスクリプト

import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from new.database import get_db
from new.models import File
from new.config import LOGGER

def update_page_counts():
    """既存のPDFファイルの頁数を更新"""
    print("=== PDF頁数更新スクリプト開始 ===")
    try:
        db = next(get_db())
        
        # PDFファイルのみを取得（小文字統一）
        pdf_files = db.query(File).filter(File.file_type == 'pdf').all()
        
        print(f"PDFファイル数: {len(pdf_files)}")
        LOGGER.info(f"PDFファイル数: {len(pdf_files)}")
        
        updated_count = 0
        
        for file in pdf_files:
            try:
                print(f"処理中: {file.file_name} (タイプ: {file.file_type})")
                file_path = Path(file.file_path)
                if not file_path.exists():
                    print(f"警告: ファイルが存在しません: {file_path}")
                    LOGGER.warning(f"ファイルが存在しません: {file_path}")
                    continue
                
                # 既に頁数が設定されている場合はスキップ
                if file.page_count is not None:
                    print(f"既設定: {file.file_name} - {file.page_count}頁")
                    LOGGER.info(f"頁数既設定: {file.file_name} - {file.page_count}頁")
                    continue
                
                # PyMuPDFで頁数を取得
                try:
                    import fitz
                    doc = fitz.open(file_path)
                    page_count = len(doc)
                    doc.close()
                    
                    # file_metadataを更新
                    if file.file_metadata is None:
                        file.file_metadata = {}
                    
                    file.file_metadata["page_count"] = page_count
                    db.commit()
                    
                    print(f"更新完了: {file.file_name} - {page_count}頁")
                    LOGGER.info(f"頁数更新: {file.file_name} - {page_count}頁")
                    updated_count += 1
                    
                except ImportError:
                    print("エラー: PyMuPDFがインストールされていません")
                    LOGGER.error("PyMuPDFがインストールされていません")
                    break
                except Exception as e:
                    print(f"エラー: 頁数取得失敗 ({file.file_name}): {e}")
                    LOGGER.error(f"頁数取得エラー ({file.file_name}): {e}")
                    
            except Exception as e:
                print(f"エラー: ファイル処理失敗 ({file.file_name}): {e}")
                LOGGER.error(f"ファイル処理エラー ({file.file_name}): {e}")
        
        print(f"更新完了: {updated_count}個のファイルを更新")
        LOGGER.info(f"更新完了: {updated_count}個のファイルを更新")
        
    except Exception as e:
        print(f"スクリプト実行エラー: {e}")
        LOGGER.error(f"スクリプト実行エラー: {e}")
    finally:
        if 'db' in locals():
            db.close()
        print("=== PDF頁数更新スクリプト終了 ===")

if __name__ == "__main__":
    update_page_counts() 
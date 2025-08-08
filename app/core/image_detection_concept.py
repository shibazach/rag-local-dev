"""
PDF画像・グラフ検出機能の設計思想
OLD/db/構想.txt より抜粋・保存

このファイルは将来の実装のための設計思想を記録したものです。
実際の実装時にはこのコードを参考にしてください。
"""

import pdfplumber
from typing import Tuple, List


def detect_page_media(pdf_path: str) -> Tuple[List[int], List[int]]:
    """
    PDFページごとの画像・グラフ有無を検出
    
    将来のマルチモーダルLLM対応のため、PDFに含まれる画像やグラフの
    ページ番号を検出し、優先的に再認識させるためのフラグ立てに使用する。
    
    Args:
        pdf_path: PDFファイルのパス
        
    Returns:
        image_pages: 画像が含まれるページ番号のリスト
        chart_pages: グラフが含まれると推測されるページ番号のリスト
    """
    image_pages, chart_pages = [], []
    
    with pdfplumber.open(pdf_path) as pdf:
        for idx, page in enumerate(pdf.pages, start=1):
            # 画像検出は pdfplumber が抽出した images 配列で判定
            if page.images:
                image_pages.append(idx)
            
            # グラフ判定のヒューリスティック
            # 文字密度が低く、曲線/矩形が多い場合をグラフと推定
            if is_chart_like(page):
                chart_pages.append(idx)
                
    return image_pages, chart_pages


def is_chart_like(page) -> bool:
    """
    ページがグラフらしいかを判定するヒューリスティック
    
    判定基準:
    - 曲線・エッジが多い（20以上）
    - 文字数が少ない（30未満）
    - テーブルではない
    """
    curve_count = len(page.curves) + len(page.edges)
    char_count = len(page.chars)
    
    # グラフの特徴：図形要素が多く、文字が少ない
    if curve_count > 20 and char_count < 30:
        # ただし、テーブルは除外
        if not page.extract_tables():
            return True
            
    return False


# ========== 実装時の利用例 ==========

def process_pdf_with_media_detection(pdf_path: str, file_id: str):
    """
    PDFを処理し、画像・グラフページ情報をデータベースに保存
    
    実装例：
    ```python
    # 画像・グラフページを検出
    image_pages, chart_pages = detect_page_media(pdf_path)
    
    # データベースに保存（将来的にfiles_metaテーブルに追加）
    # ALTER TABLE files_meta
    #   ADD COLUMN image_pages INT[] DEFAULT '{}',
    #   ADD COLUMN chart_pages INT[] DEFAULT '{}';
    
    db.execute(
        "UPDATE files_meta SET image_pages = :image_pages, chart_pages = :chart_pages WHERE blob_id = :blob_id",
        {"image_pages": image_pages, "chart_pages": chart_pages, "blob_id": file_id}
    )
    ```
    """
    pass


# ========== file_imagesテーブルへの画像抽出 ==========

def extract_images_to_table(pdf_path: str, blob_id: str):
    """
    PDFから画像を抽出してfile_imagesテーブルに保存
    
    将来の実装で、PDFから画像を抽出して個別に保存する際の設計思想。
    マルチモーダルLLMでの画像理解や、画像検索機能の実現に使用。
    """
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            for img_idx, img in enumerate(page.images):
                # 画像データを抽出
                # image_data = extract_image_data(img)
                
                # file_imagesテーブルに保存
                # FilesImage(
                #     blob_id=blob_id,
                #     page_number=page_num,
                #     image_index=img_idx,
                #     image_type='image',  # or 'chart', 'diagram'
                #     image_data=image_data,
                #     image_format='png',
                #     width=img.width,
                #     height=img.height
                # )
                pass


# ========== 設計メモ ==========
"""
1. 段階的実装アプローチ:
   Phase 1: files_metaにimage_pages, chart_pagesカラム追加（配列型）
   Phase 2: file_imagesテーブルに実際の画像を抽出・保存
   Phase 3: マルチモーダルLLMでの画像理解・キャプション生成

2. 画像タイプの分類:
   - image: 一般的な画像（写真、イラスト）
   - chart: グラフ（棒グラフ、折れ線グラフ、円グラフ等）
   - diagram: 図表（フローチャート、ネットワーク図等）
   - table: 表（将来的には構造化データとして抽出）

3. 検索・活用シナリオ:
   - 「グラフを含む資料」でフィルタリング
   - 画像キャプションでの全文検索
   - 類似画像検索（将来的にはCLIP等のマルチモーダル埋め込み）
   - マルチモーダルRAG（テキスト+画像を含めた回答生成）
"""
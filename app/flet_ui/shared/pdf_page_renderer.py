#!/usr/bin/env python3
"""
PDF→画像変換エンジン (PyMuPDF使用・V4専用)

主要機能:
- PyMuPDF (fitz) による高速PDF→PNG/WebP変換
- LRUキャッシュによる高速化 (メモリ + ディスク)
- 段階的解像度対応 (720p/1080p/1440p/4K)
- ドキュメントハンドル再利用 (TTL管理)
- 先読み対応 (prefetch API)
- マルチフォーマット (PNG/WebP/JPEG)

パフォーマンス最適化:
- width/dpr段階化でキャッシュヒット率向上
- 非同期レンダリング (ThreadPoolExecutor)
- ドキュメント再利用でopen/close削減
- 適応的品質制御
"""

import io
import os
import fitz  # PyMuPDF
import threading
import logging
import time
import tempfile
import hashlib
from functools import lru_cache
from typing import Dict, Optional, Tuple, Literal
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

logger = logging.getLogger(__name__)

# スレッド安全な処理用ロック
_render_lock = threading.Lock()
_doc_lock = threading.Lock()

# 設定
CACHE_DIR = Path(tempfile.gettempdir()) / "pdf_render_cache_v4"
MAX_DOC_CACHE = 10  # 同時オープンPDF数
DOC_TTL = 300       # ドキュメントキャッシュTTL (秒)
RENDER_WORKERS = max(2, os.cpu_count() // 2)  # レンダリング並列数

# ドキュメントキャッシュ (TTL付き)
_doc_cache: Dict[str, Tuple[fitz.Document, float]] = {}

# 段階的解像度設定
RESOLUTION_TIERS = {
    "low": 720,      # 低解像度 (初回表示用)
    "medium": 1080,  # 中解像度 (通常表示)
    "high": 1440,    # 高解像度 (ズーム用)
    "ultra": 2160    # 超高解像度 (高DPI用)
}

DPR_TIERS = [1.0, 1.5, 2.0, 3.0]  # デバイス解像度倍率

# ThreadPool初期化
_thread_pool = ThreadPoolExecutor(max_workers=RENDER_WORKERS, thread_name_prefix="PDFRender")

def _ensure_cache_dir():
    """キャッシュディレクトリ確保"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR

def _normalize_width(width: int) -> int:
    """width を段階に正規化（キャッシュヒット率向上）"""
    for tier in sorted(RESOLUTION_TIERS.values()):
        if width <= tier:
            return tier
    return RESOLUTION_TIERS["ultra"]

def _normalize_dpr(dpr: float) -> float:
    """DPR を段階に正規化"""
    for tier in DPR_TIERS:
        if dpr <= tier + 0.1:  # 0.1の余裕
            return tier
    return max(DPR_TIERS)

def _get_cache_key(path: str, page: int, width: int, dpr: float, format_type: str, rotation: int = 0) -> str:
    """キャッシュキー生成"""
    # ファイル変更時間も含めてキャッシュ無効化対応
    try:
        mtime = os.path.getmtime(path)
    except:
        mtime = 0
    
    key_str = f"{path}:{page}:{width}:{dpr}:{format_type}:{rotation}:{mtime}"
    return hashlib.md5(key_str.encode()).hexdigest()

def _get_or_open_document(path: str) -> fitz.Document:
    """ドキュメントハンドル取得（TTL付きキャッシュ）"""
    with _doc_lock:
        current_time = time.time()
        
        # 期限切れドキュメント削除
        expired_keys = [
            key for key, (doc, timestamp) in _doc_cache.items()
            if current_time - timestamp > DOC_TTL
        ]
        for key in expired_keys:
            try:
                _doc_cache[key][0].close()
            except:
                pass
            del _doc_cache[key]
            logger.debug(f"[PDFRenderer] Document cache expired: {key}")
        
        # キャッシュから取得または新規オープン
        if path in _doc_cache:
            doc, timestamp = _doc_cache[path]
            _doc_cache[path] = (doc, current_time)  # タイムスタンプ更新
            return doc
        
        # 新規オープン
        if len(_doc_cache) >= MAX_DOC_CACHE:
            # 最古のドキュメントを削除
            oldest_key = min(_doc_cache.keys(), key=lambda k: _doc_cache[k][1])
            try:
                _doc_cache[oldest_key][0].close()
            except:
                pass
            del _doc_cache[oldest_key]
            logger.debug(f"[PDFRenderer] Document cache evicted: {oldest_key}")
        
        # 新規ドキュメントオープン
        try:
            doc = fitz.open(path)
            _doc_cache[path] = (doc, current_time)
            logger.info(f"[PDFRenderer] Document opened: {path} (pages: {len(doc)})")
            return doc
        except Exception as e:
            logger.error(f"[PDFRenderer] Failed to open document {path}: {e}")
            raise

def _render_page_to_bytes(
    path: str, 
    page_index: int, 
    width: int, 
    dpr: float,
    format_type: Literal["png", "webp", "jpeg"] = "png",
    rotation: int = 0
) -> bytes:
    """ページを画像バイトに変換（実際のレンダリング処理）"""
    try:
        # ドキュメント取得
        doc = _get_or_open_document(path)
        
        # ページ範囲チェック
        if page_index < 0 or page_index >= len(doc):
            raise ValueError(f"Page index {page_index} out of range (0-{len(doc)-1})")
        
        # ページロード
        page = doc.load_page(page_index)
        
        # ズーム計算（A4基準595ptから）
        base_width = 595.0  # A4幅 (pt)
        zoom = (width / base_width) * dpr
        zoom = max(0.1, min(zoom, 10.0))  # zoom制限
        
        # 回転行列作成（回転→拡大の順）
        matrix = fitz.Matrix(zoom, zoom)
        if rotation != 0:
            # 回転角度を度からラジアンに変換して回転行列適用
            rotation_matrix = fitz.Matrix(rotation)
            matrix = rotation_matrix * matrix
        
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        
        # フォーマット別バイト変換
        if format_type == "webp":
            # PyMuPDFはWebP直接出力未対応の場合があるのでPNG→WebP変換
            png_bytes = pixmap.tobytes("png")
            try:
                from PIL import Image
                img = Image.open(io.BytesIO(png_bytes))
                webp_buf = io.BytesIO()
                img.save(webp_buf, format="WebP", quality=85, method=6)
                return webp_buf.getvalue()
            except ImportError:
                logger.warning("[PDFRenderer] PIL not available, falling back to PNG")
                return png_bytes
        elif format_type == "jpeg":
            return pixmap.tobytes("jpeg", jpg_quality=90)
        else:  # png (default)
            return pixmap.tobytes("png")
            
    except Exception as e:
        logger.error(f"[PDFRenderer] Render error {path}:{page_index}: {e}")
        raise

# メモリLRUキャッシュ（小さなファイル用）
@lru_cache(maxsize=128)
def _render_cached_memory(
    path: str, page: int, width: int, dpr: float, format_type: str, rotation: int, cache_key: str
) -> bytes:
    """メモリLRUキャッシュ（cache_keyは無視、LRUキー用）"""
    return _render_page_to_bytes(path, page, width, dpr, format_type, rotation)

def _get_disk_cache_path(cache_key: str, format_type: str) -> Path:
    """ディスクキャッシュパス取得"""
    cache_dir = _ensure_cache_dir()
    return cache_dir / f"{cache_key}.{format_type}"

def _load_from_disk_cache(cache_path: Path) -> Optional[bytes]:
    """ディスクキャッシュから読み込み"""
    try:
        if cache_path.exists() and time.time() - cache_path.stat().st_mtime < 3600:  # 1時間TTL
            return cache_path.read_bytes()
    except Exception as e:
        logger.debug(f"[PDFRenderer] Disk cache read error: {e}")
    return None

def _save_to_disk_cache(cache_path: Path, data: bytes):
    """ディスクキャッシュに保存"""
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(data)
        logger.debug(f"[PDFRenderer] Saved to disk cache: {cache_path}")
    except Exception as e:
        logger.debug(f"[PDFRenderer] Disk cache write error: {e}")

def render_page_image(
    path: str,
    page_index: int,
    width: int = 1200,
    dpr: float = 1.0,
    format_type: Literal["png", "webp", "jpeg"] = "png",
    use_cache: bool = True,
    rotation: int = 0
) -> bytes:
    """
    ページ画像レンダリング（メイン関数・同期版）
    
    Args:
        path: PDFファイルパス
        page_index: ページ番号 (0-based)
        width: 画像幅 (px)
        dpr: デバイス解像度倍率
        format_type: 出力画像フォーマット
        use_cache: キャッシュ使用フラグ
        
    Returns:
        画像バイト データ
    """
    with _render_lock:
        # パラメータ正規化
        norm_width = _normalize_width(width)
        norm_dpr = _normalize_dpr(dpr)
        
        if not use_cache:
            return _render_page_to_bytes(path, page_index, norm_width, norm_dpr, format_type, rotation)
        
        # キャッシュキー生成
        cache_key = _get_cache_key(path, page_index, norm_width, norm_dpr, format_type, rotation)
        
        # ディスクキャッシュ確認
        disk_cache_path = _get_disk_cache_path(cache_key, format_type)
        cached_data = _load_from_disk_cache(disk_cache_path)
        if cached_data:
            logger.debug(f"[PDFRenderer] Disk cache hit: {cache_key}")
            return cached_data
        
        # メモリキャッシュ確認＆レンダリング
        try:
            image_data = _render_cached_memory(path, page_index, norm_width, norm_dpr, format_type, rotation, cache_key)
            
            # ディスクキャッシュに保存
            _save_to_disk_cache(disk_cache_path, image_data)
            
            logger.debug(f"[PDFRenderer] Rendered: {path}:{page_index} ({norm_width}x{norm_dpr}) -> {len(image_data)} bytes")
            return image_data
            
        except Exception as e:
            logger.error(f"[PDFRenderer] Render failed: {e}")
            raise

async def render_page_image_async(
    path: str,
    page_index: int,
    width: int = 1200,
    dpr: float = 1.0,
    format_type: Literal["png", "webp", "jpeg"] = "png",
    use_cache: bool = True,
    rotation: int = 0
) -> bytes:
    """ページ画像レンダリング（非同期版）"""
    import asyncio
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        _thread_pool,
        render_page_image,
        path, page_index, width, dpr, format_type, use_cache, rotation
    )

def get_pdf_page_count(path: str) -> int:
    """PDF総ページ数取得"""
    try:
        doc = _get_or_open_document(path)
        return len(doc)
    except Exception as e:
        logger.error(f"[PDFRenderer] Failed to get page count {path}: {e}")
        raise

def prefetch_pages(
    path: str, 
    current_page: int, 
    width: int = 1200, 
    dpr: float = 1.0,
    range_size: int = 2
):
    """ページ先読み（バックグラウンド処理）"""
    def _prefetch():
        try:
            page_count = get_pdf_page_count(path)
            start_page = max(0, current_page - range_size)
            end_page = min(page_count, current_page + range_size + 1)
            
            for page_idx in range(start_page, end_page):
                if page_idx != current_page:  # 現在ページは既にレンダリング済み
                    try:
                        render_page_image(path, page_idx, width, dpr, "png", use_cache=True)
                        logger.debug(f"[PDFRenderer] Prefetched: {path}:{page_idx}")
                    except Exception as e:
                        logger.debug(f"[PDFRenderer] Prefetch failed {path}:{page_idx}: {e}")
        except Exception as e:
            logger.debug(f"[PDFRenderer] Prefetch error: {e}")
    
    _thread_pool.submit(_prefetch)

def clear_document_cache():
    """ドキュメントキャッシュクリア"""
    with _doc_lock:
        for doc, _ in _doc_cache.values():
            try:
                doc.close()
            except:
                pass
        _doc_cache.clear()
        logger.info("[PDFRenderer] Document cache cleared")

def clear_render_cache():
    """レンダリングキャッシュクリア"""
    _render_cached_memory.cache_clear()
    try:
        import shutil
        if CACHE_DIR.exists():
            shutil.rmtree(CACHE_DIR)
        logger.info("[PDFRenderer] Render cache cleared")
    except Exception as e:
        logger.warning(f"[PDFRenderer] Cache clear error: {e}")

def shutdown():
    """レンダラーシャットダウン"""
    clear_document_cache()
    _thread_pool.shutdown(wait=True)
    logger.info("[PDFRenderer] Shutdown complete")

# 使用例とテスト
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python pdf_page_renderer.py <pdf_path> <page_index>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    page_idx = int(sys.argv[2])
    
    try:
        print(f"PDF: {pdf_path}, Page: {page_idx}")
        
        # ページ数確認
        total_pages = get_pdf_page_count(pdf_path)
        print(f"Total pages: {total_pages}")
        
        # レンダリングテスト
        start_time = time.time()
        image_data = render_page_image(pdf_path, page_idx, width=1200, dpr=1.0, format_type="png")
        elapsed = time.time() - start_time
        
        print(f"Rendered: {len(image_data)} bytes in {elapsed:.3f}s")
        
        # ファイル保存
        output_path = f"test_page_{page_idx}.png"
        with open(output_path, "wb") as f:
            f.write(image_data)
        print(f"Saved: {output_path}")
        
        # キャッシュテスト
        start_time = time.time()
        image_data2 = render_page_image(pdf_path, page_idx, width=1200, dpr=1.0, format_type="png")
        elapsed2 = time.time() - start_time
        
        print(f"Cached: {len(image_data2)} bytes in {elapsed2:.3f}s")
        print(f"Speedup: {elapsed / elapsed2:.1f}x")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)
    finally:
        shutdown()


#!/usr/bin/env python3
"""
大容量PDF対応プレビュー - 本番適用版
既存pdf_preview.pyとの置き換え用簡潔版
"""

import flet as ft
from typing import Optional, Dict, Any
import asyncio
from .pdf_large_preview import create_large_pdf_preview

# 既存インターフェース互換のためのシンプルラッパー
def create_pdf_preview(file_path: Optional[str] = None):
    """既存のcreate_pdf_preview関数の代替（大容量対応版）"""
    return create_large_pdf_preview(file_path)

class PDFPreview(ft.Container):
    """既存のPDFPreviewクラスの代替（大容量対応版）"""
    
    def __init__(self, file_path: Optional[str] = None):
        # 大容量対応プレビューをベースにする
        from .pdf_large_preview import LargePDFPreview
        self._large_preview = LargePDFPreview(file_path)
        
        super().__init__()
        self.expand = True
        self.margin = ft.margin.all(4)
        self.content = self._large_preview
        
        # 既存インターフェース互換のプロパティ
        self.file_path = file_path
        self.current_file_info = None
        
    def show_pdf_preview(self, file_info):
        """既存インターフェース互換"""
        self._large_preview.show_pdf_preview(file_info)
        self.current_file_info = file_info
        
    def show_empty_preview(self):
        """既存インターフェース互換"""
        self._large_preview.show_empty_preview()
        self.current_file_info = None
        self.file_path = None
        
    def load_file(self, file_path: str):
        """既存インターフェース互換"""
        self._large_preview.load_file(file_path)
        self.file_path = file_path
        
    async def load_pdf(self, file_info: Dict[str, Any]):
        """既存インターフェース互換"""
        await self._large_preview.load_pdf(file_info)
        self.current_file_info = file_info
        
    def cleanup(self):
        """リソース整理"""
        if hasattr(self._large_preview, 'cleanup'):
            self._large_preview.cleanup()

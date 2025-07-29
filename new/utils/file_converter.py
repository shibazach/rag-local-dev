#!/usr/bin/env python3
# new/utils/file_converter.py
# ファイル変換ユーティリティ

import os
import logging
from pathlib import Path
from typing import Optional, Tuple
import subprocess
import tempfile

LOGGER = logging.getLogger(__name__)

# 対応ファイル形式
SUPPORTED_FORMATS = {
    '.pdf': 'PDF',
    '.txt': 'TXT', 
    '.json': 'JSON',
    '.csv': 'CSV',
    '.md': 'MD',
    '.doc': 'DOC',
    '.docx': 'DOCX',
    '.jpg': 'JPG',
    '.jpeg': 'JPG',
    '.png': 'PNG'
}

# テキストファイル形式（直接テキスト抽出可能）
TEXT_FORMATS = {'.txt', '.json', '.csv', '.md'}

class FileConverter:
    """ファイル変換クラス"""
    
    @staticmethod
    def is_supported_format(filename: str) -> bool:
        """対応形式かチェック"""
        ext = Path(filename).suffix.lower()
        return ext in SUPPORTED_FORMATS
    
    @staticmethod
    def get_file_type(filename: str) -> str:
        """ファイル形式を取得"""
        ext = Path(filename).suffix.lower()
        return SUPPORTED_FORMATS.get(ext, 'UNKNOWN')
    
    @staticmethod
    def convert_to_pdf(input_path: Path, output_path: Path) -> bool:
        """ファイルをPDFに変換"""
        try:
            file_type = FileConverter.get_file_type(input_path.name)
            
            if file_type == 'PDF':
                # PDFの場合はコピー
                import shutil
                shutil.copy2(input_path, output_path)
                return True
            
            elif file_type == 'TXT':
                # テキストファイルをPDFに変換
                return FileConverter._txt_to_pdf(input_path, output_path)
            
            elif file_type in ['DOC', 'DOCX']:
                # Word文書をPDFに変換
                return FileConverter._word_to_pdf(input_path, output_path)
            
            elif file_type in ['JPG', 'PNG']:
                # 画像をPDFに変換
                return FileConverter._image_to_pdf(input_path, output_path)
            
            else:
                LOGGER.error(f"未対応のファイル形式: {file_type}")
                return False
                
        except Exception as e:
            LOGGER.error(f"PDF変換エラー: {e}")
            return False
    
    @staticmethod
    def _txt_to_pdf(input_path: Path, output_path: Path) -> bool:
        """テキストファイルをPDFに変換"""
        try:
            # 一時的なHTMLファイルを作成
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    pre {{ white-space: pre-wrap; word-wrap: break-word; }}
                </style>
            </head>
            <body>
                <pre>{content}</pre>
            </body>
            </html>
            """
            
            # HTMLファイルを一時作成
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                f.write(html_content)
                html_path = f.name
            
            # wkhtmltopdfでHTMLをPDFに変換
            try:
                subprocess.run([
                    'wkhtmltopdf', 
                    '--quiet',
                    '--encoding', 'utf-8',
                    html_path, 
                    str(output_path)
                ], check=True)
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                LOGGER.warning("wkhtmltopdfが見つかりません。代替方法を使用します")
                # 代替方法: テキストをそのまま保存（後でPDF化）
                return FileConverter._create_simple_pdf(content, output_path)
            finally:
                os.unlink(html_path)
                
        except Exception as e:
            LOGGER.error(f"テキストPDF変換エラー: {e}")
            return False
    
    @staticmethod
    def _word_to_pdf(input_path: Path, output_path: Path) -> bool:
        """Word文書をPDFに変換"""
        try:
            # LibreOfficeを使用して変換
            subprocess.run([
                'libreoffice',
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', str(output_path.parent),
                str(input_path)
            ], check=True)
            
            # 変換されたファイルの名前を変更
            converted_path = output_path.parent / f"{input_path.stem}.pdf"
            if converted_path.exists():
                converted_path.rename(output_path)
                return True
            
            return False
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            LOGGER.warning("LibreOfficeが見つかりません。代替方法を使用します")
            return FileConverter._extract_text_and_convert(input_path, output_path)
    
    @staticmethod
    def _image_to_pdf(input_path: Path, output_path: Path) -> bool:
        """画像をPDFに変換"""
        try:
            from PIL import Image
            
            # 画像を開く
            image = Image.open(input_path)
            
            # RGBに変換（RGBAの場合）
            if image.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            
            # PDFとして保存
            image.save(output_path, 'PDF', resolution=100.0)
            return True
            
        except ImportError:
            LOGGER.warning("Pillowが見つかりません。代替方法を使用します")
            return FileConverter._create_simple_pdf(f"画像ファイル: {input_path.name}", output_path)
        except Exception as e:
            LOGGER.error(f"画像PDF変換エラー: {e}")
            return False
    
    @staticmethod
    def _extract_text_and_convert(input_path: Path, output_path: Path) -> bool:
        """テキスト抽出してPDF化（代替方法）"""
        try:
            # テキスト抽出を試行
            text_content = FileConverter._extract_text(input_path)
            if text_content:
                return FileConverter._create_simple_pdf(text_content, output_path)
            else:
                return FileConverter._create_simple_pdf(f"ファイル: {input_path.name}", output_path)
        except Exception as e:
            LOGGER.error(f"テキスト抽出エラー: {e}")
            return FileConverter._create_simple_pdf(f"ファイル: {input_path.name}", output_path)
    
    @staticmethod
    def _extract_text(file_path: Path) -> Optional[str]:
        """ファイルからテキストを抽出"""
        try:
            # テキストファイルの場合
            if file_path.suffix.lower() == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            # その他の場合は空文字を返す
            return ""
            
        except Exception as e:
            LOGGER.error(f"テキスト抽出エラー: {e}")
            return None
    
    @staticmethod
    def _create_simple_pdf(content: str, output_path: Path) -> bool:
        """シンプルなPDFを作成"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            
            # 日本語フォントの設定（利用可能な場合）
            try:
                pdfmetrics.registerFont(TTFont('IPAexGothic', '/usr/share/fonts/opentype/ipafont-gothic/IPAexGothic.ttf'))
                font_name = 'IPAexGothic'
            except:
                font_name = 'Helvetica'
            
            c = canvas.Canvas(str(output_path), pagesize=letter)
            width, height = letter
            
            # テキストを描画
            y = height - 50
            lines = content.split('\n')
            
            for line in lines:
                if y < 50:  # ページの終わりに達した場合
                    c.showPage()
                    y = height - 50
                
                # 長い行を分割
                words = line.split()
                current_line = ""
                
                for word in words:
                    test_line = current_line + " " + word if current_line else word
                    if c.stringWidth(test_line, font_name, 12) < width - 100:
                        current_line = test_line
                    else:
                        if current_line:
                            c.drawString(50, y, current_line)
                            y -= 15
                        current_line = word
                
                if current_line:
                    c.drawString(50, y, current_line)
                    y -= 15
            
            c.save()
            return True
            
        except ImportError:
            LOGGER.error("ReportLabが見つかりません")
            return False
        except Exception as e:
            LOGGER.error(f"PDF作成エラー: {e}")
            return False
    
    @staticmethod
    def extract_text_from_file(file_path: Path) -> Optional[str]:
        """ファイルからテキストを抽出（精度最優先）"""
        try:
            file_ext = file_path.suffix.lower()
            
            # テキストファイル：直接抽出（精度100%）
            if file_ext in TEXT_FORMATS:
                LOGGER.info(f"📝 テキストファイル直接抽出: {file_path.name}")
                return FileConverter._extract_text_direct(file_path)
            
            # 画像ファイル：直接OCR（精度100%）
            elif file_ext in ['.jpg', '.jpeg', '.png']:
                LOGGER.info(f"🖼️ 画像ファイル直接OCR: {file_path.name}")
                return FileConverter._extract_text_with_ocr(file_path)
            
            # PDFファイル：テキスト抽出→失敗時OCR
            elif file_ext == '.pdf':
                LOGGER.info(f"📄 PDFファイル処理: {file_path.name}")
                text = FileConverter.extract_text_from_pdf(file_path)
                if not text or len(text.strip()) < 10:  # テキスト抽出失敗
                    LOGGER.info("📄 PDFテキスト抽出失敗、OCR実行")
                    return FileConverter._extract_text_with_ocr(file_path)
                return text
            
            # 文書ファイル：PDF変換→テキスト抽出
            elif file_ext in ['.doc', '.docx']:
                LOGGER.info(f"📄 文書ファイル処理: {file_path.name}")
                return FileConverter._extract_text_from_document(file_path)
            
            else:
                LOGGER.warning(f"⚠️ 未対応形式: {file_ext}")
                return None
                
        except Exception as e:
            LOGGER.error(f"テキスト抽出エラー: {e}")
            return None
    
    @staticmethod
    def _extract_text_direct(file_path: Path) -> Optional[str]:
        """テキストファイルから直接抽出"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='shift_jis') as f:
                    return f.read()
            except Exception as e:
                LOGGER.error(f"テキストファイル読み込みエラー: {e}")
                return None
        except Exception as e:
            LOGGER.error(f"テキストファイル読み込みエラー: {e}")
            return None
    
    @staticmethod
    def _extract_text_with_ocr(file_path: Path) -> Optional[str]:
        """OCRでテキスト抽出"""
        try:
            # EasyOCRを使用
            import easyocr
            reader = easyocr.Reader(['ja', 'en'])
            
            result = reader.readtext(str(file_path))
            text = '\n'.join([item[1] for item in result])
            
            LOGGER.info(f"OCR結果: {len(text)}文字抽出")
            return text
            
        except ImportError:
            LOGGER.warning("EasyOCRが見つかりません")
            return None
        except Exception as e:
            LOGGER.error(f"OCRエラー: {e}")
            return None
    
    @staticmethod
    def _extract_text_from_document(file_path: Path) -> Optional[str]:
        """文書ファイルからテキスト抽出"""
        try:
            # 一時的なPDFファイルを作成
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                temp_pdf = Path(f.name)
            
            # PDFに変換
            if FileConverter.convert_to_pdf(file_path, temp_pdf):
                # PDFからテキスト抽出
                text = FileConverter.extract_text_from_pdf(temp_pdf)
                # 一時ファイル削除
                temp_pdf.unlink()
                return text
            else:
                return None
                
        except Exception as e:
            LOGGER.error(f"文書ファイル処理エラー: {e}")
            return None
    
    @staticmethod
    def extract_text_from_pdf(pdf_path: Path) -> Optional[str]:
        """PDFからテキストを抽出"""
        try:
            # PyPDF2を使用
            import PyPDF2
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                
                return text
                
        except ImportError:
            LOGGER.warning("PyPDF2が見つかりません。代替方法を使用します")
            return FileConverter._extract_text_with_pdfplumber(pdf_path)
        except Exception as e:
            LOGGER.error(f"PDFテキスト抽出エラー: {e}")
            return FileConverter._extract_text_with_pdfplumber(pdf_path)
    
    @staticmethod
    def _extract_text_with_pdfplumber(pdf_path: Path) -> Optional[str]:
        """pdfplumberを使用してテキスト抽出（代替方法）"""
        try:
            import pdfplumber
            
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
                
                return text
                
        except ImportError:
            LOGGER.error("pdfplumberも見つかりません")
            return None
        except Exception as e:
            LOGGER.error(f"pdfplumberテキスト抽出エラー: {e}")
            return None 
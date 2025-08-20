"""
辞書編集ページ - 専用ページ実装（ui.dialog()制約から解放）
"""
from nicegui import ui
from datetime import datetime
from pathlib import Path
import os
from urllib.parse import unquote

from app.ui.components.layout import RAGHeader, RAGFooter, MainContentArea


class DictEditorPage:
    """辞書編集専用ページ（フルスクリーン）"""
    
    def __init__(self):
        """初期化"""
        self.config_root = Path('app/config/ocr')
        self.dict_root = self.config_root / 'dic'
        self.textarea = None
        self.filename = None
        self.label = None
        self.return_url = None
        self.content = ""
        self.path = None
    
    def render(self, filename: str, label: str = None, return_url: str = None):
        """辞書編集ページをレンダリング"""
        from app.auth.session import SessionManager
        
        current_user = SessionManager.get_current_user()
        if not current_user:
            ui.navigate.to('/login?redirect=/ocr-adjustment')
            return
        
        # パラメータ設定
        self.filename = unquote(filename)
        self.label = unquote(label) if label else filename
        self.return_url = return_url or '/ocr-adjustment'
        
        # ファイル準備
        self._ensure_dict_files()
        self.path = self.dict_root / self.filename
        
        # コンテンツ読み込み
        try:
            self.content = self.path.read_text(encoding='utf-8')
        except Exception:
            self.content = ''
        
        # ページ構築
        RAGHeader(show_site_name=True, current_page="dict-editor")
        
        with MainContentArea():
            self._create_editor_layout()
        
        RAGFooter()
    
    def _create_editor_layout(self):
        """エディタレイアウト作成"""
        # ヘッダーエリア（固定高）
        with ui.element('div').style(
            'width: 100%; padding: 16px 24px; background: #f8f9fa; '
            'border-bottom: 1px solid #e5e7eb; display: flex; '
            'justify-content: space-between; align-items: center;'
        ):
            # タイトルと情報
            with ui.element('div'):
                ui.label(f'✏️ 辞書編集: {self.label}').style('font-size: 20px; font-weight: 600; color: #1f2937; margin-bottom: 4px;')
                ui.label(f'📄 {self.path}').style('font-family: monospace; color: #6b7280; font-size: 13px;')
                ui.label(f'{len(self.content.splitlines())} 行').style('color: #6b7280; font-size: 12px; margin-top: 2px;')
            
            # ボタンエリア
            with ui.element('div').style('display: flex; gap: 12px;'):
                ui.button('🔙 戻る', on_click=self._go_back).props('flat color=primary')
                ui.button('💾 保存', on_click=self._save_content).props('unelevated color=primary')
        
        # メインエディタエリア（フレキシブル）
        with ui.element('div').style(
            'flex: 1; width: 100%; padding: 24px; display: flex; '
            'flex-direction: column; gap: 16px; overflow: hidden;'
        ):
            
            # 説明・ヒント
            with ui.element('div').style(
                'padding: 16px; background: #f0f9ff; border-left: 4px solid #3b82f6; '
                'border-radius: 6px; margin-bottom: 8px;'
            ):
                ui.label('💡 編集のヒント').style('font-weight: 600; color: #1d4ed8; margin-bottom: 8px;')
                with ui.element('div').style('color: #1e40af; font-size: 14px;'):
                    ui.label('• 1行に1つの項目を入力してください')
                    ui.label('• 空行は自動的に無視されます')
                    ui.label('• 保存時に自動でバックアップが作成されます')
                    ui.label('• Ctrl+S でも保存できます')
            
            # テキストエリア（完全フレキシブル - 画面全体に追従）
            self.textarea = ui.textarea(value=self.content).style(
                'flex: 1; width: 100%; min-height: 500px; font-family: "SF Mono", "Monaco", "Inconsolata", "Fira Code", "Fira Mono", "Droid Sans Mono", monospace; '
                'font-size: 14px; line-height: 1.6; box-sizing: border-box; resize: vertical; '
                'border-radius: 8px; border: 2px solid #d1d5db; padding: 16px; '
                'background: #ffffff; tab-size: 4; white-space: pre;'
            ).props('outlined')
            
            # キーボードショートカット（一時無効 - 構文エラー回避）
            # ui.keyboard('ctrl+s', self._save_content)
        
        # ステータスバー（固定高）
        with ui.element('div').style(
            'width: 100%; padding: 12px 24px; background: #f3f4f6; '
            'border-top: 1px solid #e5e7eb; display: flex; '
            'justify-content: space-between; align-items: center; font-size: 12px; color: #6b7280;'
        ):
            ui.label('💾 Ctrl+S で保存 | 📁 バックアップ先: dic/back/')
            ui.label(f'ファイル: {self.filename}')
    
    def _ensure_dict_files(self):
        """辞書ファイルの存在確保"""
        self.dict_root.mkdir(parents=True, exist_ok=True)
        back_dir = self.dict_root / 'back'
        back_dir.mkdir(parents=True, exist_ok=True)
        
        # 旧ファイルからの初期コピー
        old_root = Path('OLD/ocr/dic')
        for fname in ['known_words_common.csv', 'known_words_custom.csv', 'ocr_word_mistakes.csv', 'user_dict.csv', 'word_mistakes.csv']:
            dst = self.dict_root / fname
            if not dst.exists():
                src = old_root / fname
                try:
                    if src.exists():
                        dst.write_bytes(src.read_bytes())
                    else:
                        dst.write_text('', encoding='utf-8')
                except Exception:
                    try:
                        dst.write_text('', encoding='utf-8')
                    except Exception:
                        pass
    
    def _save_content(self):
        """内容を保存"""
        try:
            # バックアップ作成
            back_dir = self.dict_root / 'back'
            back_dir.mkdir(parents=True, exist_ok=True)
            back_path = back_dir / f"{self.filename}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if self.path.exists():
                back_path.write_bytes(self.path.read_bytes())
                ui.notify(f'📁 バックアップ作成: {back_path.name}', type='info')
            
            # メイン保存
            content = self.textarea.value or ''
            self.path.write_text(content, encoding='utf-8')
            
            # 統計情報
            lines = len(content.splitlines())
            non_empty_lines = len([line for line in content.splitlines() if line.strip()])
            
            ui.notify(f'✅ {self.label} を保存しました ({non_empty_lines}/{lines} 行)', type='positive')
            
        except Exception as e:
            ui.notify(f'❌ 保存失敗: {e}', type='negative')
    
    def _go_back(self):
        """元のページに戻る"""
        ui.navigate.to(self.return_url)


# ルート登録関数
def register_dict_editor_routes():
    """辞書編集ページのルートを登録"""
    
    @ui.page('/dict-edit/{filename}')
    def dict_edit_page(filename: str, label: str = None, return_url: str = None):
        """辞書編集ページ"""
        editor = DictEditorPage()
        editor.render(filename, label, return_url)

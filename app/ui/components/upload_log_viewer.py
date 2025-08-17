"""
アップロードログビューアーコンポーネント
"""
from nicegui import ui
from datetime import datetime
import asyncio
from app.services.upload_log_service import upload_log_service
from app.config import logger

class UploadLogViewer:
    """リアルタイムアップロードログビューアー"""
    
    def __init__(self, container, session_id: str | None = None):
        """
        Args:
            container: ログを表示する親コンテナ
        """
        self.container = container
        self.log_service = upload_log_service
        self.logs = []
        self.log_elements = {}
        self.auto_refresh = True
        self.session_id = session_id
        self.setup_ui()
        
    def setup_ui(self):
        """UIをセットアップ"""
        with self.container:
            # ログヘッダー
            with ui.element('div').style(
                'display: flex; justify-content: space-between; align-items: center; '
                'padding: 8px 16px; background: #f3f4f6; border-radius: 8px; margin-bottom: 8px;'
            ):
                ui.label('📋 アップロードログ（リアルタイム）').style('font-weight: 600; font-size: 16px;')
                with ui.element('div').style('display: flex; gap: 8px; align-items: center;'):
                    ui.label('自動更新').style('font-size: 14px; color: #6b7280;')
                    self.auto_refresh_switch = ui.switch(
                        value=True,
                        on_change=lambda e: setattr(self, 'auto_refresh', e.value)
                    ).style('transform: scale(0.8);')
                    ui.button(
                        '🔄',
                        on_click=lambda: self.refresh_logs()
                    ).props('flat dense').style('padding: 4px 8px;').tooltip('手動更新')
            
            # ログコンテナ（スクロール可能）
            self.log_container = ui.element('div').style(
                'flex: 1; overflow-y: auto; background: white; border: 1px solid #e5e7eb; '
                'border-radius: 8px; padding: 8px; max-height: calc(100vh - 200px);'
            )
            
            # 初期メッセージ
            with self.log_container:
                self.empty_message = ui.element('div').style(
                    'text-align: center; color: #9ca3af; padding: 32px;'
                )
                with self.empty_message:
                    ui.icon('history', size='3em').style('margin-bottom: 16px; opacity: 0.5;')
                    ui.label('アップロードログがここに表示されます').style('font-size: 16px;')
            
            # 自動更新タイマー
            self.timer = ui.timer(2.0, self.poll_logs, active=True)
    
    async def poll_logs(self):
        """ログをポーリング"""
        if not self.auto_refresh:
            return
            
        try:
            # 取得ポリシー：現在セッション + 未完了ログ（過去分）
            new_logs = []
            if self.session_id:
                try:
                    new_logs = self.log_service.get_session_logs(self.session_id)
                except Exception:
                    new_logs = []
            try:
                in_progress = self.log_service.get_in_progress_logs(limit=200)
            except Exception:
                in_progress = []
            # 結合（重複除去）: idでユニーク化、最新順（updated_at desc, created_at desc）
            merged = {}
            for item in (new_logs or []):
                merged[item.get('id')] = item
            for item in (in_progress or []):
                merged[item.get('id')] = item
            # 最新順に整列
            def _key(x):
                return (x.get('updated_at') or x.get('created_at') or '')
            combined = list(merged.values())
            combined.sort(key=_key, reverse=True)
            new_logs = combined
            
            if new_logs and new_logs != self.logs:
                self.logs = new_logs
                await self.update_display()
                
        except Exception as e:
            logger.error(f"Failed to poll logs: {e}")
    
    async def refresh_logs(self):
        """手動でログを更新"""
        try:
            # 手動更新も同じポリシー
            base = self.log_service.get_session_logs(self.session_id) if self.session_id else []
            in_progress = self.log_service.get_in_progress_logs(limit=200)
            merged = { (x.get('id')): x for x in base }
            for x in in_progress:
                merged[x.get('id')] = x
            def _key(x):
                return (x.get('updated_at') or x.get('created_at') or '')
            out = list(merged.values())
            out.sort(key=_key, reverse=True)
            self.logs = out
            await self.update_display()
        except Exception as e:
            logger.error(f"Failed to refresh logs: {e}")
    
    async def update_display(self):
        """ログ表示を更新"""
        # 空メッセージを非表示
        if self.logs:
            self.empty_message.style('display: none;')
        else:
            self.empty_message.style('display: block;')
            return
        
        # ログコンテナをクリア
        self.log_container.clear()
        self.log_elements = {}
        
        # ログエントリーを作成（最新が上）
        with self.log_container:
            for log in self.logs:
                self._create_log_entry(log)
    
    def _create_log_entry(self, log):
        """ログエントリーを作成"""
        # ステータスに応じた色とアイコン
        status_config = {
            'pending': ('⏳', '#f59e0b', 'amber'),
            'uploading': ('📤', '#3b82f6', 'blue'),
            'processing': ('⚙️', '#8b5cf6', 'purple'),
            'completed': ('✅', '#10b981', 'green'),
            'failed': ('❌', '#ef4444', 'red'),
            'duplicate': ('📂', '#6b7280', 'gray')
        }
        
        icon, color, color_name = status_config.get(
            log.get('status', 'pending'),
            ('❓', '#9ca3af', 'gray')
        )
        
        # ログエントリーコンテナ
        with ui.element('div').style(
            f'display: flex; align-items: center; padding: 8px 12px; '
            f'border-left: 3px solid {color}; margin-bottom: 8px; '
            f'background: #f9fafb; border-radius: 4px; gap: 12px;'
        ) as entry:
            # ステータスアイコン
            ui.label(icon).style(f'font-size: 20px; color: {color};')
            
            # ファイル情報
            with ui.element('div').style('flex: 1; min-width: 0;'):
                # ファイル名
                ui.label(log.get('file_name', 'Unknown')).style(
                    'font-weight: 600; font-size: 14px; '
                    'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'
                ).tooltip(log.get('file_name', ''))
                
                # メッセージ
                if log.get('message'):
                    ui.label(log.get('message')).style(
                        'font-size: 12px; color: #6b7280; margin-top: 2px;'
                    )
            
            # プログレス（アップロード中の場合）
            if log.get('status') == 'uploading' and log.get('progress') is not None:
                with ui.element('div').style('width: 100px;'):
                    ui.linear_progress(value=log.get('progress', 0) / 100).props(
                        f'color="{color_name}" size="8px"'
                    )
                    ui.label(f"{log.get('progress', 0)}%").style(
                        'font-size: 11px; text-align: center; color: #6b7280;'
                    )
            
            # ファイルサイズ
            if log.get('file_size'):
                size_mb = log.get('file_size', 0) / (1024 * 1024)
                ui.label(f"{size_mb:.1f} MB").style(
                    'font-size: 12px; color: #6b7280; min-width: 60px; text-align: right;'
                )
            
            # タイムスタンプ
            created_at = log.get('created_at')
            if created_at:
                if isinstance(created_at, str):
                    try:
                        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        time_str = dt.strftime('%H:%M:%S')
                    except:
                        time_str = created_at
                else:
                    time_str = created_at.strftime('%H:%M:%S')
                    
                ui.label(time_str).style(
                    'font-size: 11px; color: #9ca3af; min-width: 60px;'
                )
            
            self.log_elements[log.get('id')] = entry



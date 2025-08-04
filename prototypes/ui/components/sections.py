"""
セクション単位の共通UIコンポーネント
ヒーロー、機能リスト、ステータス表示等の再利用可能なセクション
"""
from nicegui import ui
from typing import List, Dict, Any, Optional

class HeroSection:
    """ヒーローセクション - メインタイトルとサブタイトル表示"""
    
    def __init__(self, title: str, subtitle: str, background_color: str = "#334155"):
        self.title = title
        self.subtitle = subtitle
        self.background_color = background_color
        self.render()
    
    def render(self):
        """ヒーローセクション描画（メニューと連続・隙間なし）"""
        with ui.element('div').style(f'background:{self.background_color};padding:40px 0;width:100%;margin:0;margin-left:0;margin-right:0;display:flex;flex-direction:column;align-items:center;justify-content:center;'):
            ui.label(self.title).style('color:white;font-size:48px;font-weight:bold;margin:0 0 16px 0;text-shadow:0 2px 4px rgba(0,0,0,0.3);text-align:center;')
            ui.label(self.subtitle).style('color:rgba(255,255,255,0.9);font-size:18px;margin:0;text-align:center;')

class FeatureSection:
    """機能セクション - 機能一覧表示"""
    
    def __init__(self, title: str = "主な機能", features: List[Dict[str, str]] = None):
        self.title = title
        self.features = features or []
        self.render()
    
    def render(self):
        """機能セクション描画（完全センタリング）"""
        with ui.element('div').style('padding:40px 0;width:100%;margin:0;display:flex;flex-direction:column;align-items:center;justify-content:center;'):
            ui.label(self.title).style('font-size:24px;font-weight:bold;color:#1f2937;margin:0 0 24px 0;text-align:center;')
            
            # 機能リスト（センタリング）
            with ui.element('div').style('display:flex;justify-content:center;align-items:center;width:100%;'):
                with ui.element('div').style('max-width:600px;text-align:left;'):
                    for feature in self.features:
                        self._create_feature_item(
                            feature.get('icon', ''),
                            feature.get('title', ''),
                            feature.get('description', '')
                        )
    
    def _create_feature_item(self, icon: str, title: str, description: str):
        """個別機能アイテム作成"""
        with ui.element('div').style('display:flex;align-items:flex-start;margin:0 0 16px 0;'):
            ui.label(icon).style('font-size:20px;margin:0 12px 0 0;flex-shrink:0;')
            with ui.element('div'):
                ui.html(f'<span style="font-weight:bold;color:#1f2937;">{title}</span> {description}').style('font-size:14px;line-height:1.5;margin:0;')

class StatusSection:
    """ステータスセクション - システム状況表示"""
    
    def __init__(self, title: str = "システム状況", stats: List[Dict[str, Any]] = None):
        self.title = title
        self.stats = stats or []
        self.render()
    
    def render(self):
        """ステータスセクション描画（完全センタリング・下部余白60px）"""
        with ui.element('div').style('padding:40px 0 60px 0;width:100%;margin:0;display:flex;flex-direction:column;align-items:center;justify-content:center;'):
            ui.label(self.title).style('font-size:24px;font-weight:bold;color:#1f2937;margin:0 0 24px 0;text-align:center;')
            
            # ステータスカード群
            with ui.element('div').style('display:flex;gap:24px;justify-content:center;align-items:center;flex-wrap:wrap;'):
                for stat in self.stats:
                    self._create_status_card(
                        stat.get('value', '0'),
                        stat.get('label', ''),
                        stat.get('color', '#3b82f6')
                    )
    
    def _create_status_card(self, value: str, label: str, color: str = "#3b82f6"):
        """個別ステータスカード作成"""
        with ui.element('div').style('background:white;border:1px solid #e5e7eb;border-radius:8px;padding:20px;text-align:center;min-width:120px;box-shadow:0 1px 3px rgba(0,0,0,0.1);'):
            ui.label(str(value)).style(f'font-size:36px;font-weight:bold;color:{color};margin:0 0 8px 0;display:block;')
            ui.label(label).style('font-size:14px;color:#6b7280;margin:0;')

class ContentSection:
    """汎用コンテンツセクション - 任意コンテンツの標準フォーマット"""
    
    def __init__(self, title: Optional[str] = None, padding: str = "40px 0", 
                 center_content: bool = True, max_width: Optional[str] = None):
        self.title = title
        self.padding = padding
        self.center_content = center_content
        self.max_width = max_width
        self.container = None
        self.render()
    
    def render(self):
        """汎用セクション描画"""
        flex_style = 'display:flex;flex-direction:column;align-items:center;justify-content:center;' if self.center_content else ''
        
        with ui.element('div').style(f'padding:{self.padding};width:100%;margin:0;{flex_style}') as container:
            self.container = container
            
            if self.title:
                ui.label(self.title).style('font-size:24px;font-weight:bold;color:#1f2937;margin:0 0 24px 0;text-align:center;')
            
            # コンテンツコンテナ
            if self.max_width:
                with ui.element('div').style(f'max-width:{self.max_width};width:100%;'):
                    pass
    
    def __enter__(self):
        """コンテキストマネージャー - 内部コンテンツ追加用"""
        if self.max_width:
            return ui.element('div').style(f'max-width:{self.max_width};width:100%;').__enter__()
        return self.container.__enter__()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー終了"""
        if self.max_width:
            return None
        return self.container.__exit__(exc_type, exc_val, exc_tb)
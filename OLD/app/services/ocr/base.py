# app/services/ocr/base.py
# OCRエンジンの基底クラス

from typing import Dict, Any, List
from abc import ABC, abstractmethod

class OCREngine(ABC):
    """OCRエンジンの基底クラス"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def process(self, pdf_path: str, page_num: int = 0, **kwargs) -> Dict[str, Any]:
        """PDFの指定ページをOCR処理
        
        Args:
            pdf_path: PDFファイルのパス
            page_num: 処理するページ番号（0から開始）
            **kwargs: エンジン固有のパラメータ
            
        Returns:
            Dict containing:
                - success: bool - 処理成功フラグ
                - text: str - 抽出されたテキスト
                - error: str - エラーメッセージ（失敗時）
                - processing_time: float - 処理時間（秒）
                - confidence: float - 信頼度（利用可能な場合）
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """エンジンが利用可能かチェック"""
        pass
    
    def get_parameters(self) -> List[Dict[str, Any]]:
        """調整可能なパラメータの定義を返す
        
        Returns:
            List of parameter definitions with:
                - name: str - パラメータ名
                - label: str - 表示名
                - type: str - パラメータタイプ（checkbox, number, select等）
                - default: Any - デフォルト値
                - description: str - 説明
                - その他UI用の属性（min, max, options等）
        """
        return []
    
    def validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """パラメータの検証と正規化
        
        Args:
            params: 入力パラメータ
            
        Returns:
            検証・正規化されたパラメータ
        """
        validated = {}
        param_defs = {p['name']: p for p in self.get_parameters()}
        
        for name, value in params.items():
            if name in param_defs:
                param_def = param_defs[name]
                validated[name] = self._validate_single_param(value, param_def)
            else:
                validated[name] = value
                
        # デフォルト値の設定
        for param_def in self.get_parameters():
            if param_def['name'] not in validated:
                validated[param_def['name']] = param_def['default']
                
        return validated
    
    def _validate_single_param(self, value: Any, param_def: Dict[str, Any]) -> Any:
        """単一パラメータの検証"""
        param_type = param_def['type']
        
        if param_type == 'checkbox':
            return bool(value)
        elif param_type == 'number':
            num_val = float(value)
            if 'min' in param_def:
                num_val = max(num_val, param_def['min'])
            if 'max' in param_def:
                num_val = min(num_val, param_def['max'])
            return num_val
        elif param_type == 'select':
            options = param_def.get('options', [])
            if value in [opt['value'] for opt in options]:
                return value
            return param_def['default']
        else:
            return value
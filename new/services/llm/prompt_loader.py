# new/services/llm/prompt_loader.py
# プロンプト管理モジュール

import os
from pathlib import Path
from typing import Dict, Optional
import logging

LOGGER = logging.getLogger(__name__)

class PromptLoader:
    """プロンプトファイルローダー"""
    
    def __init__(self, prompts_dir: Optional[str] = None):
        if prompts_dir is None:
            # new/prompts/ ディレクトリを使用
            current_dir = Path(__file__).parent.parent.parent
            prompts_dir = current_dir / "prompts"
        
        self.prompts_dir = Path(prompts_dir)
        self._prompt_cache = {}
        
        LOGGER.info(f"プロンプトローダー初期化: {self.prompts_dir}")
    
    def load_prompt(self, prompt_name: str, language: str = "ja") -> str:
        """プロンプトファイルから指定言語のプロンプトを読み込み"""
        cache_key = f"{prompt_name}_{language}"
        
        if cache_key in self._prompt_cache:
            return self._prompt_cache[cache_key]
        
        prompt_file = self.prompts_dir / f"{prompt_name}.txt"
        
        if not prompt_file.exists():
            LOGGER.error(f"プロンプトファイルが見つかりません: {prompt_file}")
            return self._get_fallback_prompt(prompt_name, language)
        
        try:
            content = prompt_file.read_text(encoding='utf-8')
            prompt = self._extract_language_section(content, language)
            
            if prompt:
                self._prompt_cache[cache_key] = prompt
                LOGGER.debug(f"プロンプト読み込み成功: {prompt_name} ({language})")
                return prompt
            else:
                LOGGER.warning(f"言語セクションが見つかりません: {language} in {prompt_name}")
                return self._get_fallback_prompt(prompt_name, language)
                
        except Exception as e:
            LOGGER.error(f"プロンプト読み込みエラー [{prompt_file}]: {e}")
            return self._get_fallback_prompt(prompt_name, language)
    
    def _extract_language_section(self, content: str, language: str) -> Optional[str]:
        """プロンプトファイルから指定言語のセクションを抽出"""
        lines = content.split('\n')
        in_target_section = False
        result_lines = []
        
        for line in lines:
            # 言語セクション開始
            if line.strip() == f"{language}:":
                in_target_section = True
                continue
            
            # 別の言語セクション開始（終了）
            if line.strip().endswith(':') and line.strip() != f"{language}:":
                if in_target_section:
                    break
                continue
            
            # コメント行をスキップ
            if line.strip().startswith('#'):
                continue
            
            # 対象セクション内の場合は追加
            if in_target_section:
                result_lines.append(line)
        
        if result_lines:
            return '\n'.join(result_lines).strip()
        
        return None
    
    def _get_fallback_prompt(self, prompt_name: str, language: str) -> str:
        """フォールバックプロンプト"""
        if prompt_name == "refine_prompt_advanced":
            if language == "ja":
                return """以下のテキストを品質向上してください。

原文:
{TEXT}

修正指示:
- OCR誤字・脱字の修正
- 不自然な改行・空白の整理
- 文章構造の改善
- 意味を保持しつつ読みやすく整形

修正後テキスト:"""
            else:
                return """Please improve the quality of the following text.

Original text:
{TEXT}

Correction instructions:
- Fix OCR typos and omissions
- Organize unnatural line breaks and spaces
- Improve sentence structure
- Format for readability while preserving meaning

Corrected text:"""
        
        return "プロンプトが見つかりません。"
    
    def format_prompt(self, template: str, **kwargs) -> str:
        """プロンプトテンプレートをフォーマット"""
        try:
            return template.format(**kwargs)
        except KeyError as e:
            LOGGER.error(f"プロンプトフォーマットエラー: {e}")
            return template

# グローバルインスタンス
_prompt_loader = None

def get_prompt_loader() -> PromptLoader:
    """プロンプトローダーのシングルトンインスタンス取得"""
    global _prompt_loader
    if _prompt_loader is None:
        _prompt_loader = PromptLoader()
    return _prompt_loader
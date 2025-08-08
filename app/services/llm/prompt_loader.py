"""
プロンプト管理サービス - Prototype統合版
言語別プロンプトテンプレートの管理・読み込み
"""

import os
import re
from typing import List, Optional
from pathlib import Path

from app.config import config, logger

class PromptLoader:
    """プロンプト管理サービス"""
    
    def __init__(self, prompt_dir: Optional[str] = None):
        """
        Args:
            prompt_dir: プロンプトファイルディレクトリ（省略時はデフォルト）
        """
        if prompt_dir is None:
            self.prompt_dir = config.PROMPT_DIR
        else:
            self.prompt_dir = Path(prompt_dir)
        
        # プロンプトファイルパス
        self.refine_prompt_file = self.prompt_dir / "refine_prompt_multi.txt"
        self.chat_prompt_file = self.prompt_dir / "chat_prompts.txt"
        
        # キャッシュ
        self._prompt_cache = {}
        self._chat_prompt_cache = {}
    
    def get_prompt_by_lang(self, lang: str = "ja") -> str:
        """
        refine_prompt_multi.txt から "#lang=lang" セクションを抽出し、
        次の "#lang=" またはファイル末尾までの範囲を返却する
        
        Args:
            lang: 言語コード（ja, en等）
            
        Returns:
            プロンプトテンプレート文字列
        """
        # キャッシュチェック
        cache_key = f"refine_{lang}"
        if cache_key in self._prompt_cache:
            return self._prompt_cache[cache_key]
        
        if not self.refine_prompt_file.exists():
            logger.warning(
                f"プロンプトファイルが見つかりません: {self.refine_prompt_file}"
            )
            return self._get_default_prompt(lang)
        
        try:
            content = self.refine_prompt_file.read_text(encoding="utf-8")
            marker = f"#lang={lang}"
            start = content.find(marker)
            
            if start < 0:
                logger.warning(
                    f"{lang} 用プロンプトが見つかりません: "
                    f"{self.refine_prompt_file}"
                )
                return self._get_default_prompt(lang)
            
            # マーカー直後から次の #lang= までを抜き出し
            sub = content[start + len(marker):]
            end = sub.find("#lang=")
            section = sub if end < 0 else sub[:end]
            
            # 行ごとにフィルタリング
            lines = section.splitlines()
            cleaned = []
            
            for ln in lines:
                # 空行はそのまま１行だけ残す
                if not ln.strip():
                    if not cleaned or cleaned[-1].strip():
                        cleaned.append("")
                    continue
                # # で始まるコメント行はスキップ
                if ln.lstrip().startswith("#"):
                    continue
                # "ja:" や "en:" ラベルだけの行はスキップ
                if ln.strip().lower() == f"{lang}:":
                    continue
                cleaned.append(ln)
            
            # 重複する先頭空行を削除
            while cleaned and not cleaned[0].strip():
                cleaned.pop(0)
            # 重複する末尾空行を削除
            while cleaned and not cleaned[-1].strip():
                cleaned.pop()
            
            prompt = "\n".join(cleaned)
            
            # キャッシュに保存
            self._prompt_cache[cache_key] = prompt
            
            return prompt
            
        except Exception as e:
            logger.error(f"プロンプトファイル読み込みエラー: {e}")
            return self._get_default_prompt(lang)
    
    def list_prompt_keys(self) -> List[str]:
        """
        refine_prompt_multi.txt 内の "#lang=キー" を抽出して
        利用可能な言語キー一覧を返却する
        """
        if not self.refine_prompt_file.exists():
            return []
        
        keys: List[str] = []
        try:
            with open(self.refine_prompt_file, encoding="utf-8") as f:
                for line in f:
                    if line.startswith("#lang="):
                        keys.append(line[len("#lang="):].strip())
            return keys
        except Exception as e:
            logger.error(f"プロンプトキー取得エラー: {e}")
            return []
    
    def get_chat_prompt(self, section: str) -> str:
        """
        chat_prompts.txt から指定セクションのプロンプトを取得する。
        セクションは <section_name>...</section_name> 形式で定義される。
        
        Args:
            section: セクション名
            
        Returns:
            プロンプト文字列
        """
        # キャッシュチェック
        cache_key = f"chat_{section}"
        if cache_key in self._chat_prompt_cache:
            return self._chat_prompt_cache[cache_key]
        
        if not self.chat_prompt_file.exists():
            logger.warning(
                f"チャットプロンプトファイルが見つかりません: "
                f"{self.chat_prompt_file}"
            )
            return ""
        
        try:
            with open(self.chat_prompt_file, encoding="utf-8") as f:
                content = f.read()
            
            # <section>...</section> 形式のセクションを抽出
            pattern = f"<{section}>(.*?)</{section}>"
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                prompt = match.group(1).strip()
                # キャッシュに保存
                self._chat_prompt_cache[cache_key] = prompt
                return prompt
            else:
                logger.warning(f"セクション '{section}' が見つかりません")
                return ""
                
        except Exception as e:
            logger.error(f"チャットプロンプト読み込みエラー: {e}")
            return ""
    
    def list_chat_prompt_keys(self) -> List[str]:
        """
        chat_prompts.txt 内の利用可能なセクション名一覧を返却する
        """
        if not self.chat_prompt_file.exists():
            return []
        
        try:
            with open(self.chat_prompt_file, encoding="utf-8") as f:
                content = f.read()
            
            # <section_name> タグを抽出
            sections = re.findall(r'<(\w+)>', content)
            return list(set(sections))  # 重複を除去
            
        except Exception as e:
            logger.error(f"チャットプロンプトキー取得エラー: {e}")
            return []
    
    def _get_default_prompt(self, lang: str) -> str:
        """デフォルトプロンプトを返す"""
        if lang == "ja":
            return """以下のOCR抽出テキストを整形・補正してください：

要件：
1. 明らかな誤字脱字を修正
2. 文章の意味が通るように整形
3. 改行位置を適切に調整
4. 不要な記号や文字化けを除去

{TEXT}"""
        else:
            return """Please format and correct the following OCR-extracted text:

Requirements:
1. Fix obvious typos and errors
2. Format for readability
3. Adjust line breaks appropriately
4. Remove unnecessary symbols and garbled text

{TEXT}"""
    
    def create_default_prompts(self):
        """デフォルトプロンプトファイルを作成（初期セットアップ用）"""
        self.prompt_dir.mkdir(parents=True, exist_ok=True)
        
        # refine_prompt_multi.txt
        if not self.refine_prompt_file.exists():
            content = """#lang=ja
以下のOCR抽出テキストを整形・補正してください。

要件：
- 明らかな誤字脱字を修正する
- 文章として意味が通るように整形する
- 改行位置を適切に調整する
- 不要な記号や文字化けを除去する
- 元の文書の構造をできるだけ保持する

テキスト：
{TEXT}

#lang=en
Please format and correct the following OCR-extracted text.

Requirements:
- Fix obvious typos and errors
- Format the text for better readability
- Adjust line breaks appropriately
- Remove unnecessary symbols and garbled characters
- Preserve the original document structure as much as possible

Text:
{TEXT}
"""
            self.refine_prompt_file.write_text(content, encoding="utf-8")
            logger.info(f"デフォルト整形プロンプトを作成: {self.refine_prompt_file}")
        
        # chat_prompts.txt
        if not self.chat_prompt_file.exists():
            content = """<system>
あなたは親切で知識豊富なアシスタントです。
ユーザーの質問に対して、正確で分かりやすい回答を提供してください。
</system>

<rag_search>
以下の検索結果を参考に、ユーザーの質問に回答してください：

検索結果：
{CONTEXT}

質問：
{QUERY}
</rag_search>

<summarize>
以下のテキストを要約してください：
{TEXT}
</summarize>
"""
            self.chat_prompt_file.write_text(content, encoding="utf-8")
            logger.info(f"デフォルトチャットプロンプトを作成: {self.chat_prompt_file}")

# サービスインスタンス作成ヘルパー
def get_prompt_loader(prompt_dir: Optional[str] = None) -> PromptLoader:
    """プロンプトローダーインスタンス取得"""
    return PromptLoader(prompt_dir)

def get_prompt_by_lang(lang: str = "ja") -> str:
    """
    言語別プロンプト取得（簡易版）
    
    Args:
        lang: 言語コード（ja/en）
        
    Returns:
        プロンプトテキスト
    """
    loader = get_prompt_loader()
    return loader.load_prompt_by_lang(lang)

def get_chat_prompt(section: str = "chat_general") -> str:
    """
    チャットプロンプト取得（簡易版）
    
    Args:
        section: セクション名
        
    Returns:
        チャットプロンプトテキスト
    """
    loader = get_prompt_loader()
    return loader.load_chat_prompt(section)
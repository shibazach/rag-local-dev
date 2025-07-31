# new/services/ocr_comparison/correction_service.py
"""
誤字修正・正規化サービス
旧系のapply_all_corrections機能を移植
"""

import re
import csv
from typing import Dict, List, Tuple
from pathlib import Path

from new.config import LOGGER

class CorrectionService:
    """誤字修正・正規化処理サービス"""
    
    def __init__(self):
        self.logger = LOGGER
        self._correction_dict = None
        self._fullwidth_map = self._create_fullwidth_map()
    
    def _create_fullwidth_map(self) -> Dict[str, str]:
        """全角→半角変換マップを作成"""
        return {
            # 数字
            '０': '0', '１': '1', '２': '2', '３': '3', '４': '4',
            '５': '5', '６': '6', '７': '7', '８': '8', '９': '9',
            # 英字（大文字）
            'Ａ': 'A', 'Ｂ': 'B', 'Ｃ': 'C', 'Ｄ': 'D', 'Ｅ': 'E',
            'Ｆ': 'F', 'Ｇ': 'G', 'Ｈ': 'H', 'Ｉ': 'I', 'Ｊ': 'J',
            'Ｋ': 'K', 'Ｌ': 'L', 'Ｍ': 'M', 'Ｎ': 'N', 'Ｏ': 'O',
            'Ｐ': 'P', 'Ｑ': 'Q', 'Ｒ': 'R', 'Ｓ': 'S', 'Ｔ': 'T',
            'Ｕ': 'U', 'Ｖ': 'V', 'Ｗ': 'W', 'Ｘ': 'X', 'Ｙ': 'Y', 'Ｚ': 'Z',
            # 英字（小文字）
            'ａ': 'a', 'ｂ': 'b', 'ｃ': 'c', 'ｄ': 'd', 'ｅ': 'e',
            'ｆ': 'f', 'ｇ': 'g', 'ｈ': 'h', 'ｉ': 'i', 'ｊ': 'j',
            'ｋ': 'k', 'ｌ': 'l', 'ｍ': 'm', 'ｎ': 'n', 'ｏ': 'o',
            'ｐ': 'p', 'ｑ': 'q', 'ｒ': 'r', 'ｓ': 's', 'ｔ': 't',
            'ｕ': 'u', 'ｖ': 'v', 'ｗ': 'w', 'ｘ': 'x', 'ｙ': 'y', 'ｚ': 'z',
            # 記号
            '．': '.', '，': ',', '：': ':', '；': ';', '？': '?',
            '！': '!', '（': '(', '）': ')', '［': '[', '］': ']',
            '｛': '{', '｝': '}', '＋': '+', '－': '-', '＊': '*',
            '／': '/', '＝': '=', '＜': '<', '＞': '>', '＠': '@',
            '＃': '#', '％': '%', '＆': '&', '｜': '|', '＼': '\\',
            '＾': '^', '＿': '_', '｀': '`', '～': '~', '　': ' ',  # 全角スペース
            # 長音記号・ハイフン類
            '―': '-',  # 全角ダッシュ（em dash）
            '‐': '-',  # ハイフン
            '–': '-',  # en dash
            '—': '-'   # em dash
        }
    
    def load_correction_dict(self) -> Dict[str, str]:
        """誤字修正辞書を読み込み"""
        if self._correction_dict is not None:
            return self._correction_dict
        
        correction_dict = {}
        
        # 新系用辞書パス（旧系パスも試行）
        dict_paths = [
            "new/data/ocr_word_mistakes.csv",
            "OLD/ocr/dic/ocr_word_mistakes.csv",
            "data/ocr_word_mistakes.csv"
        ]
        
        for dict_path in dict_paths:
            if Path(dict_path).exists():
                try:
                    with open(dict_path, 'r', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        # ヘッダー行をスキップ
                        next(reader, None)
                        for row in reader:
                            if len(row) >= 2:
                                wrong, correct = row[0], row[1]
                                # 空の文字列は無視
                                if wrong and correct:
                                    correction_dict[wrong] = correct
                    
                    self.logger.info(f"誤字修正辞書読み込み成功: {dict_path} ({len(correction_dict)}件)")
                    break
                except Exception as e:
                    self.logger.warning(f"誤字修正辞書読み込みエラー [{dict_path}]: {e}")
        
        if not correction_dict:
            self.logger.warning("誤字修正辞書が見つかりません")
        
        self._correction_dict = correction_dict
        return correction_dict
    
    def apply_corrections(self, text: str) -> Tuple[str, List[Dict]]:
        """
        誤字修正と全角→半角変換を統合実行
        
        Returns:
            Tuple[修正後テキスト, 修正情報リスト]
        """
        if not text:
            return text, []
        
        # 誤字修正辞書を取得
        correction_dict = self.load_correction_dict()
        
        # 統合された変換辞書を作成
        combined_dict = {}
        
        # 1. 誤字修正辞書を追加
        for wrong, correct in correction_dict.items():
            combined_dict[wrong] = {"correct": correct, "type": "correction"}
        
        # 2. 全角→半角変換を追加
        for fullwidth, halfwidth in self._fullwidth_map.items():
            combined_dict[fullwidth] = {"correct": halfwidth, "type": "normalization"}
        
        # 修正情報を記録するリスト
        corrections = []
        
        # 置換位置と内容を記録するリスト
        replacements = []
        
        # 各変換対象について処理
        for wrong, info in combined_dict.items():
            correct = info["correct"]
            correction_type = info["type"]
            
            start_pos = 0
            while True:
                # 変換対象の位置を検索
                pos = text.find(wrong, start_pos)
                if pos == -1:
                    break
                
                # 既に変換予定の範囲と重複していないか確認
                overlap = False
                for repl in replacements:
                    repl_start, repl_end = repl['start'], repl['end']
                    if not (pos >= repl_end or pos + len(wrong) <= repl_start):
                        overlap = True
                        break
                
                if not overlap:
                    # 変換情報を記録
                    replacements.append({
                        'start': pos,
                        'end': pos + len(wrong),
                        'wrong': wrong,
                        'correct': correct,
                        'type': correction_type
                    })
                    corrections.append({
                        "wrong": wrong,
                        "correct": correct,
                        "position": pos,
                        "type": correction_type
                    })
                
                start_pos = pos + 1
        
        # カタカナ長音記号「ー」の文脈判定処理
        katakana_dash_replacements = self._process_katakana_dash(text, replacements)
        replacements.extend(katakana_dash_replacements)
        corrections.extend([{
            "wrong": 'ー',
            "correct": '-',
            "position": repl['start'],
            "type": 'normalization'
        } for repl in katakana_dash_replacements])
        
        # 変換位置でソート（後ろから処理することで位置のずれを防ぐ）
        replacements.sort(key=lambda x: x['start'], reverse=True)
        
        # 変換を実行
        result_text = text
        for repl in replacements:
            start, end = repl['start'], repl['end']
            correct = repl['correct']
            result_text = result_text[:start] + correct + result_text[end:]
        
        return result_text, corrections
    
    def _process_katakana_dash(self, text: str, existing_replacements: List[Dict]) -> List[Dict]:
        """カタカナ長音記号「ー」の文脈判定処理"""
        katakana_dash_replacements = []
        start_pos = 0
        
        while True:
            pos = text.find('ー', start_pos)
            if pos == -1:
                break
            
            # 前後の文字をチェック
            prev_char = text[pos - 1] if pos > 0 else ''
            next_char = text[pos + 1] if pos < len(text) - 1 else ''
            
            # 前後の文字の種類を判定
            prev_is_alphanumeric = self._is_alphanumeric(prev_char)
            next_is_alphanumeric = self._is_alphanumeric(next_char)
            prev_is_japanese = self._is_japanese(prev_char)
            next_is_japanese = self._is_japanese(next_char)
            
            # 変換条件：前後のどちらかが英数字で、かつ両方が日本語文字ではない場合のみ変換
            should_convert = ((prev_is_alphanumeric or next_is_alphanumeric) and 
                             not (prev_is_japanese and next_is_japanese))
            
            if should_convert:
                # 既存の置換と重複していないかチェック
                overlap = False
                for repl in existing_replacements:
                    if not (pos >= repl['end'] or pos + 1 <= repl['start']):
                        overlap = True
                        break
                
                if not overlap:
                    katakana_dash_replacements.append({
                        'start': pos,
                        'end': pos + 1,
                        'wrong': 'ー',
                        'correct': '-',
                        'type': 'normalization'
                    })
            
            start_pos = pos + 1
        
        return katakana_dash_replacements
    
    def _is_alphanumeric(self, char: str) -> bool:
        """英数字かどうかを判定"""
        return char.isalnum() or char in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ０１２３４５６７８９'
    
    def _is_katakana(self, char: str) -> bool:
        """カタカナかどうかを判定"""
        return '\u30A0' <= char <= '\u30FF'
    
    def _is_hiragana(self, char: str) -> bool:
        """ひらがなかどうかを判定"""
        return '\u3040' <= char <= '\u309F'
    
    def _is_japanese(self, char: str) -> bool:
        """日本語文字（ひらがな・カタカナ・漢字）かどうかを判定"""
        return (self._is_hiragana(char) or 
                self._is_katakana(char) or 
                '\u4E00' <= char <= '\u9FAF' or  # 漢字
                '\u3400' <= char <= '\u4DBF')    # 漢字拡張A
    
    def highlight_corrections(self, original_text: str, corrections: List[Dict]) -> str:
        """
        置換箇所を色分けハイライトしたHTMLを生成
        """
        if not corrections:
            # 置換がない場合は通常のHTMLエスケープのみ
            html_text = original_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            return html_text.replace("\n", "<br>")
        
        # 置換情報を位置でソート
        sorted_corrections = sorted(corrections, key=lambda x: x.get('position', 0))
        
        # 文字列を分割してHTMLを構築
        result_parts = []
        last_pos = 0
        
        for correction in sorted_corrections:
            wrong = correction['wrong']
            correct = correction['correct']
            position = correction.get('position', 0)
            correction_type = correction.get('type', 'correction')
            
            # 前の部分（置換されない部分）をエスケープして追加
            before_part = original_text[last_pos:position]
            escaped_before = before_part.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            result_parts.append(escaped_before)
            
            # 置換部分を色分けでマークアップ
            escaped_wrong = wrong.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            escaped_correct = correct.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            
            # 正規化（全角→半角）の場合は青色、誤字修正は赤色
            if correction_type == 'normalization':
                marked_part = f'<span style="color:blue; font-weight:bold;" title="全角→半角: {escaped_wrong}">{escaped_correct}</span>'
            else:
                marked_part = f'<span style="color:red; font-weight:bold;" title="修正前: {escaped_wrong}">{escaped_correct}</span>'
            
            result_parts.append(marked_part)
            
            # 次の開始位置を更新
            last_pos = position + len(wrong)
        
        # 残りの部分をエスケープして追加
        remaining_part = original_text[last_pos:]
        escaped_remaining = remaining_part.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        result_parts.append(escaped_remaining)
        
        # 結合してHTMLを生成
        html_text = ''.join(result_parts)
        
        # 改行をHTMLの改行タグに変換
        html_text = html_text.replace("\n", "<br>")
        
        return html_text
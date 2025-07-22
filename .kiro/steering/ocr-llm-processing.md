---
inclusion: always
---

# OCR・LLM処理ガイドライン

## OCR処理の基本方針

### エンジン選択戦略
- **OCRmyPDF**: デフォルト、バランス重視
- **PaddleOCR**: 日本語精度重視、処理速度良好
- **EasyOCR**: 多言語対応、手書き文字対応
- **Tesseract**: 軽量、カスタマイズ性重視

### 処理フロー
1. **PDF抽出**: PyMuPDFによるテキスト層抽出
2. **OCR抽出**: 選択エンジンによる画像OCR
3. **結果統合**: 「【PDF抽出】」「【OCR抽出】」タグ付きで統合
4. **品質評価**: 抽出結果の信頼性スコア算出

### エラーハンドリング
```python
# OCR処理の標準的なエラーハンドリング
try:
    ocr_result = self.ocr_factory.process_with_settings(
        engine_id=ocr_engine_id,
        pdf_path=pdf_path,
        page_num=page_number,
        custom_params=ocr_settings or {}
    )
    if not ocr_result["success"]:
        # OCRエラーでも処理継続、エラー内容を記録
        ocr_text = f"OCRエラー: {ocr_result['error']}"
except Exception as exc:
    LOGGER.warning(f"OCR処理例外: {exc}")
    ocr_text = f"OCR例外: {str(exc)}"
```

## LLM処理ガイドライン

### Ollama統合
- **モデル**: 日本語対応モデルを優先使用
- **タイムアウト**: デフォルト300秒、設定可能
- **プロンプト**: 言語別最適化プロンプト使用

### テキスト整形戦略
1. **前処理**: Unicode正規化（NFKC）、スペルチェック
2. **LLM整形**: 言語検出→適切なプロンプト選択
3. **後処理**: テンプレート応答検出・除去
4. **品質評価**: 整形結果の品質スコア算出

### 不正出力検出
```python
def _is_invalid_llm_output(self, text: str) -> bool:
    """LLM整形後の出力が不正かを判定"""
    # 長さチェック
    if len(text.strip()) < 30:
        return True
    
    # テンプレート応答検出
    lower = text.lower()
    template_patterns = [
        "certainly", "please provide", "reformat", 
        "i will help", "note that this is a translation"
    ]
    if any(p in lower for p in template_patterns):
        return True
    
    # 言語検出（英語応答の除外）
    try:
        if detect(text) == "en":
            return True
    except Exception:
        pass
    
    return False
```

## 特殊ファイル処理

### EMLファイル処理
- **段落分割**: 引用記号除去後、段落単位で処理
- **段落整形**: 各段落を個別にLLM整形
- **結果統合**: 有効な段落のみを統合

### Word文書処理
- **構造抽出**: python-docxによる論理構造抽出
- **OCR抽出**: LibreOffice経由PDF変換→OCR処理
- **統合処理**: 構造情報とOCR結果を統合

## 進捗報告・ログ出力

### リアルタイム進捗
```python
# ページ処理中の定期的な進捗更新
yield {
    "file": file_name, 
    "step": f"ページ {page_number + 1}/{total_pages} 処理中... ({elapsed:.1f}秒経過)",
    "page_id": f"page_{page_number + 1}_{total_pages}",
    "is_progress_update": True
}
```

### 処理時間記録
- OCR処理時間の記録・表示
- LLM処理時間の記録・表示
- 全体処理時間の計測・報告

## 品質管理

### スコア算出
- OCR信頼性スコア
- LLM整形品質スコア
- 総合品質スコア（最小値採用）

### 閾値管理
- 品質閾値による処理スキップ
- 上書き条件の適切な設定
- 品質向上時の自動更新
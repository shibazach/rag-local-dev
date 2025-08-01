---
inclusion: always
---

# OCR・LLM処理ガイドライン（新アーキテクチャ対応）

## OCR処理の基本方針

### エンジン選択戦略（new/services/ocr/対応）
- **OCRmyPDF**: デフォルト、バランス重視
- **PaddleOCR**: 日本語精度重視、処理速度良好
- **EasyOCR**: 多言語対応、手書き文字対応
- **Tesseract**: 軽量、カスタマイズ性重視

### 新処理フロー（FileProcessor統合）
1. **ファイル形式判定**: 拡張子による処理分岐
2. **テキストファイル**: 直接読み込み（.txt, .csv, .json）
3. **PDF/画像**: OCRエンジンによる抽出
4. **テキスト正規化**: Unicode正規化（NFKC）
5. **品質評価**: 抽出結果の信頼性スコア算出

### エラーハンドリング（新FileProcessor対応）
```python
# new/services/processing/processor.py での標準的なエラーハンドリング
async def _process_ocr(self, file_path: str, settings: Dict, abort_flag: Optional[Dict]) -> Dict:
    """OCR処理を実行（テキストファイル対応）"""
    try:
        file_ext = Path(file_path).suffix.lower()
        
        # テキストファイルの場合は直接読み込み
        if file_ext in ['.txt', '.csv', '.json']:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            return {'success': True, 'text': text, 'processing_time': processing_time}
        
        # PDF/画像ファイルの場合はOCRエンジン使用
        elif file_ext in ['.pdf', '.png', '.jpg', '.jpeg']:
            engine_id = settings.get('ocr_engine', 'ocrmypdf')
            ocr_result = self.ocr_factory.process_file(file_path, engine_id=engine_id)
            
            return {
                'success': ocr_result.success,
                'error': ocr_result.error,
                'text': ocr_result.text or '',
                'processing_time': ocr_result.processing_time
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': f'OCR処理エラー: {str(e)}',
            'text': '',
            'processing_time': time.perf_counter() - start_time
        }
```

## LLM処理ガイドライン（新Ollama統合対応）

### Ollama統合（new/services/llm/ollama_client.py）
- **モデル**: phi4-mini等の日本語対応モデルを優先使用
- **タイムアウト**: デフォルト300秒、設定可能
- **フォールバック**: Ollama利用不可時の正規化処理
- **非同期処理**: async/awaitによる効率的な処理

### 新テキスト整形戦略（FileProcessor統合）
1. **前処理**: Unicode正規化（NFKC）による文字統一
2. **Ollama接続確認**: 利用可能性チェック
3. **LLM整形**: OllamaRefinerによる品質向上
4. **フォールバック**: 接続失敗時の基本正規化処理
5. **品質評価**: 整形結果の品質スコア算出

### 新LLM処理実装例
```python
# new/services/processing/processor.py での実装
async def _process_llm_refinement(self, text: str, settings: Dict, abort_flag: Optional[Dict]) -> str:
    """LLM整形処理（Ollama統合版）"""
    try:
        from services.llm import OllamaRefiner, OllamaClient
        
        llm_model = settings.get('llm_model', 'phi4-mini')
        language = settings.get('language', 'ja')
        quality_threshold = settings.get('quality_threshold', 0.7)
        
        # 無効なモデル名チェック（フォールバック判定）
        if 'invalid' in llm_model.lower():
            return self._fallback_text_refinement(text)
        
        # Ollama接続確認
        client = OllamaClient(model=llm_model)
        if not await client.is_available():
            return self._fallback_text_refinement(text)
        
        refiner = OllamaRefiner(client)
        refined_text, detected_lang, quality_score = await refiner.refine_text(
            raw_text=text,
            abort_flag=abort_flag,
            language=language,
            quality_threshold=quality_threshold
        )
        
        return refined_text
        
    except Exception as e:
        self.logger.error(f"LLM整形エラー: {e}")
        return self._fallback_text_refinement(text)
```

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
"""
BERT補正サービス - Prototype統合版
日本語BERTモデルを使用したテキスト誤り修正
"""

import torch
from transformers import AutoTokenizer, BertForMaskedLM
from typing import List, Optional, Dict

from app.config import config, logger

# 利用可能なBERTモデル
AVAILABLE_MODELS = {
    "tohoku": "cl-tohoku/bert-base-japanese",
    "daigo": "daigo/bert-base-japanese-sentiment",
    "japanese-v2": "cl-tohoku/bert-base-japanese-v2",
    "char": "cl-tohoku/bert-base-japanese-char",
}

class BertCorrector:
    """BERT補正サービス"""
    
    def __init__(self, model_key: str = "tohoku"):
        """
        Args:
            model_key: 使用するモデルのキー
        """
        self.model_key = model_key
        self.tokenizer = None
        self.model = None
        self._loaded_model_key = None
    
    def load_model(self, model_key: Optional[str] = None) -> tuple:
        """
        モデルのロード
        
        Args:
            model_key: モデルキー（省略時は初期化時の値を使用）
            
        Returns:
            (tokenizer, model)のタプル
        """
        if model_key is None:
            model_key = self.model_key
        
        # 既にロード済みの場合はキャッシュを返す
        if self._loaded_model_key == model_key and self.tokenizer and self.model:
            return self.tokenizer, self.model
        
        model_name = AVAILABLE_MODELS.get(model_key)
        if not model_name:
            raise ValueError(f"未対応のモデルキーです: {model_key}")
        
        try:
            logger.info(f"BERTモデルをロード中: {model_name}")
            
            # トークナイザーとモデルのロード
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = BertForMaskedLM.from_pretrained(model_name)
            
            # GPU使用可能な場合は移動
            if config.CUDA_AVAILABLE and torch.cuda.is_available():
                self.model = self.model.cuda()
                logger.info("BERTモデルをGPUに移動しました")
            
            self.model.eval()
            self._loaded_model_key = model_key
            
            logger.info(f"✅ BERTモデルロード完了: {model_name}")
            
        except Exception as e:
            logger.error(f"BERTモデルのロードに失敗: {e}")
            raise
        
        return self.tokenizer, self.model
    
    def correct_text(
        self,
        text: str,
        model_key: Optional[str] = None,
        top_k: int = 1,
        confidence_threshold: float = 0.0
    ) -> str:
        """
        テキストの誤りを修正
        
        Args:
            text: 入力テキスト
            model_key: モデルキー（省略時は初期化時の値を使用）
            top_k: 予測候補の上位k個を考慮
            confidence_threshold: 置換を行う最小信頼度
            
        Returns:
            修正後テキスト
        """
        try:
            # モデルロード
            tokenizer, model = self.load_model(model_key)
            
            # トークナイズ
            tokens = tokenizer.tokenize(text)
            if not tokens:
                return text
            
            corrected_tokens = tokens.copy()
            correction_count = 0
            
            # 各トークンを順番にマスクして予測
            for i in range(len(tokens)):
                # 特殊トークンはスキップ
                if tokens[i].startswith("[") and tokens[i].endswith("]"):
                    continue
                
                # マスクトークンで置換
                masked_tokens = tokens.copy()
                masked_tokens[i] = "[MASK]"
                
                # 入力IDに変換
                input_ids = tokenizer.convert_tokens_to_ids(masked_tokens)
                input_tensor = torch.tensor([input_ids])
                
                # GPU使用可能な場合は移動
                if config.CUDA_AVAILABLE and torch.cuda.is_available():
                    input_tensor = input_tensor.cuda()
                
                # 予測実行
                with torch.no_grad():
                    predictions = model(input_tensor).logits
                
                # 上位k個の予測を取得
                masked_index = i
                top_preds = torch.topk(predictions[0, masked_index], top_k)
                top_indices = top_preds.indices.tolist()
                top_probs = torch.softmax(top_preds.values, dim=0).tolist()
                
                # 最も確率の高い予測トークンを取得
                predicted_token = tokenizer.convert_ids_to_tokens([top_indices[0]])[0]
                confidence = top_probs[0]
                
                # 元のトークンと異なり、信頼度が閾値を超える場合のみ置換
                if predicted_token != tokens[i] and confidence > confidence_threshold:
                    logger.debug(
                        f"🔁 BERT補正: {tokens[i]} → {predicted_token} "
                        f"(信頼度: {confidence:.3f})"
                    )
                    corrected_tokens[i] = predicted_token
                    correction_count += 1
            
            # トークンをテキストに戻す
            corrected_text = tokenizer.convert_tokens_to_string(corrected_tokens)
            
            if correction_count > 0:
                logger.info(f"✅ BERT補正で{correction_count}箇所を修正しました")
            
            return corrected_text
            
        except Exception as e:
            logger.error(f"BERT補正エラー: {e}")
            # エラー時は元のテキストを返す
            return text
    
    def batch_correct_texts(
        self,
        texts: List[str],
        model_key: Optional[str] = None,
        top_k: int = 1,
        confidence_threshold: float = 0.0
    ) -> List[str]:
        """
        複数テキストのバッチ補正
        
        Args:
            texts: 入力テキストのリスト
            model_key: モデルキー
            top_k: 予測候補の上位k個
            confidence_threshold: 置換を行う最小信頼度
            
        Returns:
            修正後テキストのリスト
        """
        # モデルを一度だけロード
        self.load_model(model_key)
        
        corrected_texts = []
        for text in texts:
            corrected = self.correct_text(
                text,
                model_key=model_key,
                top_k=top_k,
                confidence_threshold=confidence_threshold
            )
            corrected_texts.append(corrected)
        
        return corrected_texts
    
    def get_available_models(self) -> Dict[str, str]:
        """利用可能なモデル一覧を取得"""
        return AVAILABLE_MODELS.copy()

# サービスインスタンス作成ヘルパー
def get_bert_corrector(model_key: str = "tohoku") -> BertCorrector:
    """BERT補正サービスインスタンス取得"""
    return BertCorrector(model_key)
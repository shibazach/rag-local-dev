# src/ocr_utils/bert_corrector.py
import torch
from transformers import AutoTokenizer, BertForMaskedLM
from src import bootstrap  # ← 実体は何もimportされないが、パスが通る
from src.error_handler import install_global_exception_handler

# REM: 例外発生時のログをグローバルに記録するハンドラを有効化
install_global_exception_handler()

AVAILABLE_MODELS = {
    "tohoku": "cl-tohoku/bert-base-japanese",
    "daigo": "daigo/bert-base-japanese-sentiment"
    # ⚠️ "yasuo": 削除。非公開 or 存在しないため無効
}

def load_model(model_key):
    model_name = AVAILABLE_MODELS.get(model_key)
    if not model_name:
        raise ValueError(f"未対応のモデルキーです: {model_key}")
    tokenizer = AutoTokenizer.from_pretrained(model_name)  # ✅ 自動で最適なトークナイザーを選ぶ
    model = BertForMaskedLM.from_pretrained(model_name)
    model.eval()
    return tokenizer, model

def correct_text_bert(text, model_key="tohoku", top_k=1):
    tokenizer, model = load_model(model_key)
    tokens = tokenizer.tokenize(text)
    corrected_tokens = tokens.copy()

    for i in range(len(tokens)):
        masked_tokens = tokens.copy()
        masked_tokens[i] = "[MASK]"

        input_ids = tokenizer.convert_tokens_to_ids(masked_tokens)
        input_tensor = torch.tensor([input_ids])

        with torch.no_grad():
            predictions = model(input_tensor).logits

        masked_index = i
        top_preds = torch.topk(predictions[0, masked_index], top_k).indices.tolist()
        predicted_token = tokenizer.convert_ids_to_tokens([top_preds[0]])[0]

        if predicted_token != tokens[i]:
            print(f"🔁 [{model_key}] 候補: {tokens[i]} → {predicted_token}")
            corrected_tokens[i] = predicted_token

    corrected_text = tokenizer.convert_tokens_to_string(corrected_tokens)
    return corrected_text

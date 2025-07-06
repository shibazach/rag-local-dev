# scripts/create_rag_data.py
# REM: .eml ファイルや各種文書を OCR→LLM整形→データベース登録するユーティリティ
import os
import glob
import datetime
from email import policy
from email.parser import BytesParser

from src.extractor import extract_text_by_extension
from scripts.llm_text_refiner import refine_text_with_llm
from src.file_embedder import embed_and_insert
from src.config import EMBEDDING_OPTIONS, INPUT_DIR, LOG_DIR, DEVELOPMENT_MODE

from src import bootstrap  # パス確保のみ
from src.error_handler import install_global_exception_handler

# REM: 例外発生時はグローバルにログを記録
install_global_exception_handler()

# REM: 英語誤反映などを判定する典型パターン
TEMPLATE_PATTERNS = [
    "certainly", "please provide", "reformat", "i will help",
    "note that this is a translation", "based on your ocr output"
]

def is_invalid_llm_output(text: str) -> bool:
    from langdetect import detect
    if len(text.strip()) < 30:
        return True
    lower = text.lower()
    if any(p in lower for p in TEMPLATE_PATTERNS):
        return True
    try:
        if detect(text) == "en":
            return True
    except Exception:
        return True
    return False

def extract_text_from_eml(filepath: str) -> list[str]:
    with open(filepath, "rb") as f:
        msg = BytesParser(policy=policy.default).parse(f)
    subject = msg.get("subject", "")
    date = msg.get("date", "")
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    body += part.get_content()
                except Exception:
                    payload = part.get_payload(decode=True) or b""
                    body += payload.decode(errors="ignore")
    else:
        try:
            body = msg.get_content()
        except Exception:
            payload = msg.get_payload(decode=True) or b""
            body = payload.decode(errors="ignore")
    header = f"Subject: {subject}\nDate: {date}\n"
    return [header + "\n" + body]

def log_full_processing(filepath, refined_ja, refined_en,
                        ja_chunks, en_chunks,
                        ja_embeddings, en_embeddings):
    log_dir = LOG_DIR
    os.makedirs(log_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(filepath))[0]
    log_path = os.path.join(log_dir, f"{base}.log")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"📅 実行日時: {now}\n📄 ファイル: {filepath}\n\n")
        f.write(f"🧠 日本語チャンク数: {len(ja_embeddings)}\n")
        f.write(f"🧠 英語チャンク数: {len(en_embeddings)}\n\n")
        f.write("=== 📝 整形済み（日本語） ===\n" + refined_ja + "\n\n")
        f.write("=== ✂️ 日本語チャンク一覧 ===\n" +
                "\n".join(f"[{i+1}] {c}" for i, c in enumerate(ja_chunks)) + "\n\n")
        f.write("=== 🌍 整形済み（英語） ===\n" + refined_en + "\n\n")
        f.write("=== ✂️ 英語チャンク一覧 ===\n" +
                "\n".join(f"[{i+1}] {c}" for i, c in enumerate(en_chunks)))
    print(f"📦 処理ログ出力: {log_path}")

def process_file(filepath: str) -> None:
    print(f"\n📄 処理中: {filepath}")
    try:
        ext = os.path.splitext(filepath)[1].lower()
        texts = extract_text_from_eml(filepath) if ext == ".eml" else extract_text_by_extension(filepath)
        joined = "\n".join(texts).strip()
        if not joined or any(p in joined.lower() for p in TEMPLATE_PATTERNS):
            raise ValueError("無効ファイル（空または英語テンプレート疑い）")

        print("\n🔍 抽出原文プレビュー（最初の20行）:")
        for i, line in enumerate(joined.splitlines()[:20]):
            print(f"{i+1:>2}: {line}")
        if len(joined.splitlines()) > 20:
            print("...（以下省略）")
        print("="*40)

        print("🧠 LLM整形（phi4-mini）実行中…")
        refined_ja, lang, score = refine_text_with_llm(joined, model="phi4-mini")
        if is_invalid_llm_output(refined_ja):
            raise ValueError("整形結果が不正と判断されました")
        print(f"📊 整形品質スコア: {score:.2f}")

        # REM: embed_and_insert 内で insert_file_and_get_id～upsert_content まで実行
        ja_chunks, ja_embeddings = embed_and_insert(
            texts=[joined, refined_ja],
            filepath=filepath,
            model_keys=list(EMBEDDING_OPTIONS.keys()),
            return_data=True,
            quality_score=score,
            ocr_raw_text=joined
        )

        refined_en, en_chunks, en_embeddings = "", [], []

        log_full_processing(
            filepath,
            refined_ja, refined_en,
            ja_chunks, en_chunks,
            ja_embeddings, en_embeddings
        )
        print("✅ 完了")

    except Exception as e:
        print(f"❌ エラー: {e}")

def main(input_folder: str = INPUT_DIR) -> None:
    # REM: 必要に応じて GUI から呼び出す入口として残す
    patterns = ("*.pdf", "*.docx", "*.txt", "*.csv", "*.json", "*.eml")
    files = []
    for pat in patterns:
        files.extend(glob.glob(os.path.join(input_folder, pat)))
    total = len(files)
    for idx, filepath in enumerate(files, start=1):
        process_file(filepath)

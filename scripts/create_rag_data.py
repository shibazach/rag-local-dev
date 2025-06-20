# scripts/create_rag_data.py

import os
import glob
import datetime
from email import policy
from email.parser import BytesParser

from src import bootstrap  # noqa: F401  # インポートパス解決用（定型）
from src.extractor import extract_text_by_extension
from scripts.llm_text_refiner import refine_text_with_llm
from src.embedder import embed_and_insert, insert_file_and_get_id
from src.error_handler import install_global_exception_handler
from src.config import DEVELOPMENT_MODE

# REM: 例外発生時のログをグローバルに記録するハンドラを有効化
install_global_exception_handler()

# REM: 開発時にDBテーブル初期化するかどうかのフラグ
truncate_done_tables: set[str] = set()

# REM: 英語テンプレ誤反映などに該当する典型パターン（lower比較前提）
TEMPLATE_PATTERNS = [
    "certainly", "please provide", "reformat", "i will help",
    "note that this is a translation", "based on your ocr output"
]

# ------------------------------------------------------------------
# REM: LLM整形後の出力がテンプレ・英語・無意味などの不正内容かを判定
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

# ------------------------------------------------------------------
# REM: .emlファイルから本文テキストを抽出する
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

    # REM: ヘッダ情報は本文の先頭に付与
    header = f"Subject: {subject}\nDate: {date}\n"
    return [header + "\n" + body]

# ------------------------------------------------------------------
# REM: 1ファイルの整形・ベクトル化・DB登録のログを保存
def log_full_processing(filepath, refined_ja, refined_en, ja_chunks, en_chunks, ja_embeddings, en_embeddings):
    log_dir = os.path.join("logs", "full_logs")
    os.makedirs(log_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(filepath))[0]
    log_path = os.path.join(log_dir, f"{base_name}.log")
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"📅 実行日時: {now_str}\n📄 ファイル: {filepath}\n")
        f.write(f"🧠 日本語ベクトル数: {len(ja_embeddings)}\n")
        f.write(f"🧠 英語ベクトル数: {len(en_embeddings)}\n")
        f.write("\n=== 📝 整形済み日本語 ===\n" + refined_ja + "\n")
        f.write("\n=== ✂️ 日本語チャンク ===\n" + "\n".join(f"[{i+1}] {c}" for i, c in enumerate(ja_chunks)))
        f.write("\n=== 🌍 翻訳済み英語 ===\n" + refined_en + "\n")
        f.write("\n=== ✂️ 英語チャンク ===\n" + "\n".join(f"[{i+1}] {c}" for i, c in enumerate(en_chunks)))
    print(f"📦 処理ログ出力: {log_path}")

# ------------------------------------------------------------------
# REM: 単一ファイルに対して整形・登録処理を実行
def process_file(filepath: str) -> None:
    print(f"\n📄 処理中: {filepath}")
    try:
        # REM: ファイルのバイナリ読み込み
        with open(filepath, "rb") as f:
            file_blob = f.read()

        ext = os.path.splitext(filepath)[1].lower()

        # REM: テキスト抽出＋整形前チェック
        try:
            texts = extract_text_from_eml(filepath) if ext == ".eml" else extract_text_by_extension(filepath)
            joined = "\n".join(texts)

            # REM: 英語テンプレ誤反映や空テキストなどの無効チェック
            if not joined.strip() or any(p in joined.lower() for p in TEMPLATE_PATTERNS):
                raise ValueError("無効ファイル（空または英語テンプレ）")

        except Exception as extract_error:
            os.makedirs("logs", exist_ok=True)
            with open("logs/invalid_csv_log.txt", "a", encoding="utf-8") as log:
                log.write(f"{filepath}: {extract_error}\n")
            print(f"⚠️ 無効ファイルとしてスキップ: {filepath} ({extract_error})")
            return

        # REM: 原文プレビュー
        print("\n🔍 抽出された原文（20行までプレビュー）:")
        for i, line in enumerate(joined.splitlines()[:20]):
            print(f"{i+1:>2}: {line}")
        if len(joined.splitlines()) > 20:
            print("...（以下省略）")
        print("=" * 40)

        # REM: .eml は段落整形、それ以外は一括整形
        if ext == ".eml":
            texts = extract_text_from_eml(filepath)
            joined = "\n".join(texts)
            print("📧 .emlファイルに対して段落整形モードを適用", flush=True)
            corrected = joined.replace(">>", "").replace("> >", "").replace("> ", "")
            paragraphs = [p.strip() for p in corrected.split("\n\n") if len(p.strip()) > 30]
            refined_parts = []
            for i, para in enumerate(paragraphs):
                print(f"📑 段落 {i+1}/{len(paragraphs)} を整形中...", flush=True)
                try:
                    refined, lang, score = refine_text_with_llm(para, model="phi4-mini")

                    # REM: 各段落に対してテンプレ・英語・短文などの信頼性チェックを実施
                    if is_invalid_llm_output(refined):
                        print(f"⚠️ 不正な段落整形結果（テンプレ等）: スキップ", flush=True)
                        continue

                    refined_parts.append(refined)
                except Exception as e:
                    print(f"⚠️ 整形失敗（段落 {i+1}）: {e}", flush=True)
            refined_ja = "\n\n".join(refined_parts)
        else:
            print("🧠 LLM整形（日本語）...")
            refined_ja, lang, score = refine_text_with_llm(joined, model="phi4-mini")

            # REM: LLM出力の信頼性チェック（テンプレや英語であれば除外）
            if is_invalid_llm_output(refined_ja):
                raise ValueError("整形結果がテンプレ・英語・無意味な可能性あり。ファイルをスキップします")

        print(f"📊 整形品質スコア: {score}")

        # REM: files テーブルへ挿入
        file_id = insert_file_and_get_id(filepath, refined_ja, score)

        # REM: ベクトル化＆DB登録
        ja_chunks, ja_embeddings = embed_and_insert(
            [refined_ja],
            filepath,
            truncate_done_tables if DEVELOPMENT_MODE else set(),
            return_data=True,
            quality_score=score,
        )

        refined_en, en_chunks, en_embeddings = "", [], []

        # REM: logs/full_logs に保存
        log_full_processing(filepath, refined_ja, refined_en, ja_chunks, en_chunks, ja_embeddings, en_embeddings)
        print("✅ 完了")

    except Exception as e:
        print(f"❌ エラー: {filepath}\n{e}")

# ------------------------------------------------------------------
# REM: 対話形式でファイル or フォルダ一括処理を選択する
def main() -> None:
    mode = input("📂 フォルダ全体を処理しますか？（y/n）: ").strip().lower()
    if mode == "y":
        folder = input("📁 フォルダパス: ").strip()
        exts = [".txt", ".pdf", ".docx", ".csv", ".json", ".eml"]
        files = [
            p for p in glob.glob(os.path.join(folder, "*"))
            if os.path.splitext(p)[1].lower() in exts
        ]
        for path in files:
            process_file(path)
    elif mode == "n":
        filepath = input("📄 ファイルパス: ").strip()
        if not os.path.isfile(filepath):
            print("❌ ファイルが存在しません")
            return
        process_file(filepath)
    else:
        print("⚠️ 'y' または 'n' を入力してください")

if __name__ == "__main__":
    main()

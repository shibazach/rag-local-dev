# ocr/ocr_process.py
import os, subprocess
import fitz  # PyMuPDF
from collections import defaultdict

from src import bootstrap
from src.config import INPUT_DIR, OUTPUT_DIR
from src.utils import debug_print

# 出力フォルダの作成
os.makedirs(OUTPUT_DIR, exist_ok=True)

# PDF内にテキストが埋め込まれているか確認
def has_embedded_text(pdf_path):
    doc = fitz.open(pdf_path)
    for page in doc:
        if page.get_text().strip():
            return True
    return False

# PDFからテキストを削除して新しいPDFを作成
def remove_embedded_text(pdf_path):
    doc = fitz.open(pdf_path)
    for page in doc:
        page.clean_contents()
    temp_path = pdf_path.replace(".pdf", "_no_text.pdf")
    doc.save(temp_path)
    return temp_path

# REM: OCRを実行してテキストを埋め込む
def run_ocr(input_pdf, output_pdf):
    subprocess.run(["ocrmypdf", "--force-ocr", "-l", "jpn+eng", input_pdf, output_pdf], check=True)

# REM: PDFページからテキストブロックを抽出
def extract_text_blocks(page):
    blocks = page.get_text("dict")["blocks"]
    text_blocks = []
    for block in blocks:
        if block['type'] == 0:  # テキストブロック
            block_text = ""
            bbox = block['bbox']
            for line in block["lines"]:
                line_text = " ".join(span["text"] for span in line["spans"])
                block_text += line_text + "\n"
            text_blocks.append({"text": block_text.strip(), "bbox": bbox})
    return text_blocks

# REM: X座標で段組み（左本文／右表など）を分ける
def cluster_columns(blocks, x_threshold=100):
    columns = defaultdict(list)
    for block in blocks:
        x0 = block['bbox'][0]
        col_key = int(x0 // x_threshold)
        columns[col_key].append(block)
    return [columns[k] for k in sorted(columns)]

# REM: Y座標で行グループ化
def group_rows_by_y(blocks, y_threshold=15):
    rows = []
    for block in sorted(blocks, key=lambda b: b["bbox"][1]):
        added = False
        for row in rows:
            if abs(row[0]["bbox"][1] - block["bbox"][1]) < y_threshold:
                row.append(block)
                added = True
                break
        if not added:
            rows.append([block])
    return rows

# REM : ラベルと値のペアを抽出
def extract_label_value_pairs_from_rows(rows):
    structured = []
    for i in range(len(rows) - 1):
        label_row = sorted(rows[i], key=lambda b: b["bbox"][0])
        value_row = sorted(rows[i + 1], key=lambda b: b["bbox"][0])
        for j in range(min(len(label_row), len(value_row))):
            label = label_row[j]["text"]
            value = value_row[j]["text"]
            structured.append(f"{label.strip()}: {value.strip()}")
    return structured

# REM: PDFドキュメントからテキストを抽出し、構造化された形式に変換
def extract_and_structure_text(doc):
    structured_text = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        blocks = extract_text_blocks(page)
        columns = cluster_columns(blocks)
        for col_blocks in columns:
            rows = group_rows_by_y(col_blocks)
            structured_text.extend(extract_label_value_pairs_from_rows(rows))
    return structured_text

# REM: 構造化されたテキストをTXTファイルに保存
def save_structured_text_to_txt(structured_text, txt_path):
    with open(txt_path, "w", encoding="utf-8") as f:
        for line in structured_text:
            f.write(line + "\n")

# REM: 構造化されたテキストをPDFに再埋め込み
def embed_text_back_to_pdf(pdf_path, structured_text, output_path):
    doc = fitz.open(pdf_path)
    font_size = 6
    margin = 20
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        if page_num == 0:
            y = margin
            for line in structured_text:
                page.insert_text((margin, y), line, fontsize=font_size, overlay=True)
                y += font_size + 2
    doc.save(output_path)

# REM: メイン処理
def process_pdfs():
    for file_name in os.listdir(INPUT_DIR):
        if file_name.lower().endswith(".pdf"):
            input_path = os.path.join(INPUT_DIR, file_name)
            output_path = os.path.join(OUTPUT_DIR, file_name)

            if has_embedded_text(input_path):
                doc = fitz.open(input_path)
                text = "".join([page.get_text() for page in doc])
                if not text.strip():
                    temp_path = remove_embedded_text(input_path)
                    run_ocr(temp_path, output_path)
                    os.remove(temp_path)
                else:
                    doc.save(output_path)
            else:
                run_ocr(input_path, output_path)

            doc = fitz.open(output_path)
            structured = extract_and_structure_text(doc)
            txt_output = os.path.join(OUTPUT_DIR, file_name.replace(".pdf", "_structured.txt"))
            save_structured_text_to_txt(structured, txt_output)
            debug_print("✅ 構造化テキストを保存しました:", txt_output)

            # PDFに構造化テキストを再埋め込み
            embed_output_pdf = os.path.join(OUTPUT_DIR, file_name.replace(".pdf", "_embedded.pdf"))
            embed_text_back_to_pdf(output_path, structured, embed_output_pdf)
            debug_print("✅ テキストをPDFに再埋め込み:", embed_output_pdf)

if __name__ == "__main__":
    process_pdfs()

import os, subprocess
import fitz  # PyMuPDF
from collections import defaultdict

from src import bootstrap  # ← 実体は何もimportされないが、パスが通る
from src.error_handler import install_global_exception_handler

install_global_exception_handler()

input_folder = "input_pdfs"
output_folder = "output_pdfs"
os.makedirs(output_folder, exist_ok=True)

def has_embedded_text(pdf_path):
    doc = fitz.open(pdf_path)
    for page in doc:
        if page.get_text().strip():
            return True
    return False

def remove_embedded_text(pdf_path):
    doc = fitz.open(pdf_path)
    for page in doc:
        page.clean_contents()
    temp_path = pdf_path.replace(".pdf", "_no_text.pdf")
    doc.save(temp_path)
    return temp_path

def run_ocr(input_pdf, output_pdf):
    subprocess.run(["ocrmypdf", "--force-ocr", "-l", "jpn+eng", input_pdf, output_pdf], check=True)

def extract_text_blocks(page):
    """PDFページからテキストブロックとそのbboxを抽出"""
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

def cluster_columns(blocks, x_threshold=100):
    """X座標で段組み（左本文／右表など）を分ける"""
    columns = defaultdict(list)
    for block in blocks:
        x0 = block['bbox'][0]
        col_key = int(x0 // x_threshold)
        columns[col_key].append(block)
    return [columns[k] for k in sorted(columns)]

def group_rows_by_y(blocks, y_threshold=15):
    """Y座標で行グループ化"""
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

def save_structured_text_to_txt(structured_text, txt_path):
    with open(txt_path, "w", encoding="utf-8") as f:
        for line in structured_text:
            f.write(line + "\n")

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

def process_pdfs():
    for filename in os.listdir(input_folder):
        if filename.lower().endswith(".pdf"):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)

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
            txt_output = os.path.join(output_folder, filename.replace(".pdf", "_structured.txt"))
            save_structured_text_to_txt(structured, txt_output)
            print("✅ 構造化テキストを保存しました:", txt_output)

            # PDFに構造化テキストを再埋め込み
            embed_output_pdf = os.path.join(output_folder, filename.replace(".pdf", "_embedded.pdf"))
            embed_text_back_to_pdf(output_path, structured, embed_output_pdf)
            print("✅ テキストをPDFに再埋め込み:", embed_output_pdf)

if __name__ == "__main__":
    process_pdfs()

# ocr/spellcheck.py
# OCR誤字補正の汎用モジュール
import os, csv
import MeCab

from src import bootstrap
from src.config import MECAB_DICT_PATH
from src.utils import debug_print

 # ✅ このファイルと同じディレクトリ基準
base_dir = os.path.dirname(__file__) 

# --- known_wordsを複数CSVから読み込み ---
def load_known_words(csv_paths):
    words = set()
    for path in csv_paths:
        abs_path = os.path.join(base_dir, path)
        with open(abs_path, encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0].strip():
                    words.add(row[0].strip())
    return words

# --- 誤字辞書をCSVから読み込み ---
def load_kanji_mistakes(csv_path):
    mapping = {}
    abs_path = os.path.join(base_dir, csv_path)

    with open(abs_path, encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if len(row) >= 2:
                wrong, correct = row[0].strip(), row[1].strip()
                if wrong and correct:
                    mapping[wrong] = correct
    return mapping

# --- MeCab分かち書き ---
def tokenize(text):
    try:
        mecab = MeCab.Tagger(f"-d {MECAB_DICT_PATH} -Owakati")
        return mecab.parse(text).strip().split()
    except RuntimeError as e:
        debug_print(f"❌ MeCabの初期化に失敗しました: {e}")
        debug_print(f"👉 config.py の MECAB_DICT_PATH を確認してください（現在: {MECAB_DICT_PATH}）")
        raise

# --- メイン補正関数 ---
def correct_text(text,
                 known_word_paths=["dic/known_words_common.csv", "dic/known_words_custom.csv"],
                 kanji_mistakes_path="dic/ocr_word_mistakes.csv"):
    known_words = load_known_words(known_word_paths)
    kanji_mistakes = load_kanji_mistakes(kanji_mistakes_path)
    for wrong, correct in kanji_mistakes.items():
        if wrong not in known_words:
            text = text.replace(wrong, correct)
    return text

# REM: llm/chunker.py（更新日時: 2025-07-15 18:20 JST）
# REM: 500 字 + 50 字オーバーラップでテキストを分割／結合するユーティリティ

def split_into_chunks(text: str, *, chunk_size: int = 500, overlap: int = 50):
    """
    連続したテキストを chunk_size で切り、前チャンク末尾 overlap 文字を重複させる。
    """
    chunks = []
    start = 0
    end   = len(text)
    while start < end:
        chunk = text[start:start + chunk_size]
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def merge_chunks(chunks):
    """
    現在は単純 join。必要なら重複除去ロジックを追加してください。
    """
    return "".join(chunks)

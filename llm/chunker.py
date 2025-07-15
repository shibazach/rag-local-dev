# REM: llm/chunker.py（更新日時: 2025-07-15 19:40 JST）
"""
テキストを一定長でオーバーラップ付きに分割／結合するユーティリティ
   - split_into_chunks(text, chunk_size=500, overlap=50) -> list[str]
   - merge_chunks(chunks) -> str
"""

from __future__ import annotations

import textwrap
from typing import List


def _normalize(text: str) -> str:
    """前後の空白を削除し、改行を \n に統一"""
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def split_into_chunks(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    文字数ベースで `chunk_size` ごとに切り出し、隣接チャンクと `overlap`
    文字ぶん重なりを持たせる。改行位置は維持するが、行を無理に詰め込む
    ことはしない（textwrap.wrap に任せるシンプル実装）。

    * chunk_size <= overlap の場合は ValueError
    * 空文字列は空リストを返す
    """
    if chunk_size <= overlap:
        raise ValueError("chunk_size は overlap より大きい必要があります")

    text = _normalize(text)
    if not text:
        return []

    # textwrap.wrap は単語境界優先だが、日本語でも句点・改行でほぼ問題ない
    wrapped = textwrap.wrap(text, width=chunk_size - overlap, break_long_words=False, break_on_hyphens=False)

    chunks: list[str] = []
    for idx, segment in enumerate(wrapped):
        # 先頭チャンクはそのまま、以降は直前チャンクの末尾 overlap 文字を付与
        if idx == 0:
            chunks.append(segment)
        else:
            prev_tail = chunks[-1][-overlap:]
            chunks.append(prev_tail + segment)

    return chunks


def merge_chunks(chunks: List[str]) -> str:
    """
    split_into_chunks で分割したチャンク列をほぼロスレスで復元する。
    オーバーラップ部分が重複しているので、後方チャンクから
    前方チャンクと重なる先頭 overlap 文字を削ったものを結合する。
    """
    if not chunks:
        return ""

    merged = chunks[0]
    for prev, cur in zip(chunks[:-1], chunks[1:]):
        # 現在チャンクの前方が直前チャンク末尾と重なっているはずなので削る
        overlap_len = min(len(prev), len(cur))
        overlap = prev[-overlap_len:]
        if cur.startswith(overlap):
            merged += cur[overlap_len:]
        else:
            # 想定外（手動改変など）の場合はそのまま連結
            merged += cur
    return merged

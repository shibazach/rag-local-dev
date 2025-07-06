# scripts/views/result_chunk.py
# =======================================================
# REM: チャンク統合モード（全文検索撤去＋ベクトル検索のみ）
#       - LEFT JOIN 化で file_blobs 欠損レコードもヒット
#       - テキスト全文編集 ＋ 再ベクトル化ボタンを維持
# =======================================================

import streamlit as st
import base64, uuid, time
import numpy as np
from collections import defaultdict
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from langchain_community.embeddings import OllamaEmbeddings
from sentence_transformers import SentenceTransformer

from src.config import DB_ENGINE, EMBEDDING_OPTIONS, OLLAMA_BASE   # REM: 共通設定

# ──────────────────────────────────────────────
# REM: ユーティリティ functions
# ──────────────────────────────────────────────
def to_pgvector_literal(vec: np.ndarray) -> str:
    """numpy→pgvector 文字列に変換"""
    return "[" + ",".join(f"{float(x):.6f}" for x in vec.tolist()) + "]"

def make_unique_key(fid: int, fname: str) -> str:
    """Streamlit キー重複回避用ユニーク文字列"""
    safe = fname.replace(".", "_")
    return f"{fid}_{safe}_{uuid.uuid4().hex[:6]}"

def vector_search(qvec: np.ndarray, table: str, top_k: int = 5) -> list[dict]:
    """ベクトル類似度検索（LEFT JOIN 版）"""
    sql = f"""
      SELECT
        e.content      AS snippet,
        e.file_id,
        f.filename,
        c.refined_text AS full_text,
        b.file_blob
      FROM "{table}" AS e
      JOIN file_contents AS c ON e.file_id = c.file_id
      JOIN files          AS f ON e.file_id = f.file_id
      LEFT JOIN file_blobs AS b ON e.file_id = b.file_id        -- ★ INNER→LEFT に変更
      ORDER BY e.embedding <-> '{to_pgvector_literal(qvec)}'::vector
      LIMIT :k
    """
    with DB_ENGINE.connect() as conn:
        return conn.execute(text(sql), {"k": top_k}).mappings().all()

# ──────────────────────────────────────────────
# REM: メイン描画関数
# ──────────────────────────────────────────────
def render_chunk_mode():
    # 初期化
    if "history" not in st.session_state:
        st.session_state.history = []

    query = st.session_state.get("query_input", "").strip()
    if not query:
        return

    key        = st.session_state["selected_model_key"]
    model_cfg  = EMBEDDING_OPTIONS[key]
    table_name = st.session_state["embedding_tablename"]

    # デバッグ：テーブル件数・クエリ
    try:
        with DB_ENGINE.connect() as conn:
            total = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar()
        st.write(f"🔍 DEBUG — テーブル {table_name} 総チャンク: {total} 件")
        st.write(f"🔍 DEBUG — クエリ: “{query}”")
    except SQLAlchemyError as e:
        st.error(f"❌ 件数取得失敗: {e}")

    # クエリ埋め込み
    if model_cfg["embedder"] == "OllamaEmbeddings":
        emb = OllamaEmbeddings(
            model    = model_cfg["model_name"],
            base_url = OLLAMA_BASE                    # REM: 固定 URL
        )
        qvec = emb.embed_query(query)
    else:
        qvec = SentenceTransformer(model_cfg["model_name"]).encode(
            [query], convert_to_numpy=True
        )[0]

    # ベクトル検索
    docs = vector_search(qvec, table_name, top_k=5)
    st.success(f"🔍 検索結果: {len(docs)} 件")
    if not docs:
        st.warning("⚠️ 0 件ヒット。データ登録またはプロンプトを確認してください。")
        return

    # 結果プレビュー
    grouped = defaultdict(list)
    for d in docs:
        grouped[(d["file_id"], d["filename"])].append(d)

    st.markdown("### 🔍 検索結果プレビュー")
    for (fid, fname), items in grouped.items():
        st.markdown(f"**📄 {fname}**")
        for it in items:
            st.write(f"- {it['snippet']}")

        with st.expander("全文プレビュー"):
            # PDF プレビュー（file_blob が存在する場合のみ）
            if fname.lower().endswith(".pdf") and items[0]["file_blob"]:
                iframe_b64 = base64.b64encode(items[0]["file_blob"]).decode()
                st.components.v1.html(
                    f'<iframe src="data:application/pdf;base64,{iframe_b64}" '
                    'width="100%" height="600" style="border:none;"></iframe>',
                    height=600
                )

            # 全文編集＋再ベクトル化
            uk = make_unique_key(fid, fname)
            edited = st.text_area("全文テキスト（編集可）",
                                  items[0]["full_text"],
                                  height=200,
                                  key=f"edit_{uk}")

            if st.button("再ベクトル化", key=f"save_{uk}"):
                from src.file_embedder import embed_and_insert
                embed_and_insert(
                    texts=[edited],
                    filepath=fname,
                    model_keys=[key],
                    ocr_raw_text=edited
                )
                st.success("✅ 再ベクトル化完了！")

    # 履歴追加
    st.session_state.history.append({
        "query": query,
        "response": "\n".join(d["snippet"] for d in docs),
        "model": key,
        "time": round(time.time(), 2)
    })
    st.session_state.searching = False

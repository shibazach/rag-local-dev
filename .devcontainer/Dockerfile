###############################################################################
# rag-app  Dockerfile   CPU ↔ GPU 両対応 / Python 3.9 ベース / pip 方式
###############################################################################
# build で上書きされない限り python:3.9-slim (=CPU) を使う
ARG BASE_IMAGE=python:3.9-slim
FROM ${BASE_IMAGE}

# ── OS 依存ライブラリ ────────────────────────────────
RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  git build-essential cmake pkg-config \
  libgl1-mesa-glx libglib2.0-0 libsm6 libxrender1 libxext6 \
  poppler-utils tesseract-ocr tesseract-ocr-jpn \
  mecab libmecab-dev mecab-ipadic-utf8 \
  ocrmypdf libreoffice curl iputils-ping && \
  rm -rf /var/lib/apt/lists/*

# ── Python 依存ライブラリ ─────────────────────────────
#   CUDA ランタイムを含むイメージなら GPU Wheel、そうでなければ CPU Wheel
COPY requirements.txt .
RUN pip install --upgrade pip && \
  if echo "${BASE_IMAGE}" | grep -q "cuda"; then \
  pip install torch==2.3.0+cu124 torchvision==0.18.0+cu124 \
  --index-url https://download.pytorch.org/whl/cu124 ; \
  else \
  pip install torch==2.3.0 torchvision==0.18.0 ; \
  fi && \
  pip install -r requirements.txt && \
  pip install "sentence-transformers==2.7.0"

# （任意）モデルを事前キャッシュ
# RUN python - <<'PY'
# from sentence_transformers import SentenceTransformer
# SentenceTransformer('intfloat/e5-large-v2')
# PY

# ── アプリ本体 ────────────────────────────────────────
WORKDIR /workspace
COPY . /workspace

CMD ["bash"]

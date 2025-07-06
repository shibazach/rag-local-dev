# REM_CPU構成（GPUドライバ無しホストでも動く最小構成）
FROM python:3.10-slim

# ---------- 1. Torch バージョンを固定 ARG として宣言 ----------
ARG TorchVer="2.6.0+cpu"
ARG TorchVisionVer="0.21.0+cpu"

# ---------- 2. OS パッケージ ----------
RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --no-install-recommends \
      build-essential git curl ca-certificates \
      tesseract-ocr tesseract-ocr-jpn libreoffice && \
    rm -rf /var/lib/apt/lists/*

# ---------- 3. 作業ディレクトリ ----------
WORKDIR /workspace

# ---------- 4. Python ライブラリ ----------
COPY requirements.txt /tmp/requirements.txt

# pip／setuptools／wheel を最新化
RUN pip install --upgrade pip setuptools wheel

# GitHub の main から huggingface_hub をインストール（1.x 系が手に入る）
RUN pip install --no-cache-dir \
      git+https://github.com/huggingface/huggingface_hub.git@main

# 残りの requirements を一括インストール
RUN pip install --no-cache-dir \
      -r /tmp/requirements.txt && \
    pip install --no-cache-dir streamlit && \
    pip install --no-cache-dir \
      torch=="${TorchVer}" \
      torchvision=="${TorchVisionVer}" \
      --index-url https://download.pytorch.org/whl/cpu && \
    rm /tmp/requirements.txt

# ---------- 5. パッケージ化準備 ----------
RUN mkdir -p src scripts/views && \
    touch src/__init__.py \
          scripts/__init__.py \
          scripts/views/__init__.py

# REM: Streamlit ポート公開（必要に応じてアンコメント）
# EXPOSE 8501

# REM: デフォルト起動コマンド（必要に応じてアンコメント）
# CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

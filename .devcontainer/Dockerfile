# REM_CPU構成（GPUドライバ無しホストでも動く最小構成）
FROM python:3.10-slim

# ---------- 1. Torch バージョンを固定 ARG として宣言 ----------
ARG TorchVer="2.6.0+cpu"
ARG TorchVisionVer="0.21.0+cpu"

# ---------- 2. OS パッケージ ----------
# 対話抑止
ENV DEBIAN_FRONTEND=noninteractive

# システムライブラリ:
#   - build-essential, git, curl: 基本的なビルドツール
#   - tesseract-ocr-*: Tesseract OCRエンジン
#   - libreoffice, ghostscript, ocrmypdf: 文書処理
#   - libgl1-mesa-dev, libxext6, libxrender-dev: OpenGL/X11（PaddleOCR/EasyOCR用）
#   - libglib2.0-0t64, libsm6, libgomp1: ランタイムライブラリ

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
      build-essential git curl ca-certificates \
      tesseract-ocr tesseract-ocr-jpn \
      libreoffice ghostscript ocrmypdf qpdf \
      fonts-noto-cjk \
      libglib2.0-0 libgomp1 libgcc-s1 \
      libgl1-mesa-dev libglib2.0-0t64 libsm6 libxext6 libxrender-dev && \
    rm -rf /var/lib/apt/lists/*

# ---------- 3. 作業ディレクトリ ----------
WORKDIR /workspace

# ---------- 4. Python ライブラリ ----------
COPY requirements.txt /tmp/requirements.txt

# pip／setuptools／wheel を最新化
RUN python3 -m pip install --upgrade pip setuptools wheel

# GitHub の main から huggingface_hub をインストール（1.x 系が手に入る）
RUN python3 -m pip install --no-cache-dir \
      git+https://github.com/huggingface/huggingface_hub.git@main

# 残りの requirements を一括インストール
# ※ OpenCV は opencv-python-headless を requirements.txt 側に入れる想定
RUN python3 -m pip install --no-cache-dir --ignore-installed \
      -r /tmp/requirements.txt && \
    python3 -m pip install --no-cache-dir streamlit && \
    python3 -m pip install --no-cache-dir \
      torch=="${TorchVer}" \
      torchvision=="${TorchVisionVer}" \
      --index-url https://download.pytorch.org/whl/cpu && \
    rm /tmp/requirements.txt

# ---------- 5. パッケージ化準備 ----------
RUN mkdir -p src scripts/views && \
    touch src/__init__.py \
          scripts/__init__.py \
          scripts/views/__init__.py

# REM: デフォルト起動コマンド（必要に応じてアンコメント）
# CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

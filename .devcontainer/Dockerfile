############################################################
# REM: rag-dev devcontainer  (pip 手動 PyTorch 版)
############################################################

ARG BASE_IMAGE=nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04
FROM ${BASE_IMAGE}

# ---------- ① バージョン読み込み ----------
ARG ENV_FILE=.devcontainer/versions.env
COPY ${ENV_FILE} /tmp/versions.env
RUN grep -v '^#' /tmp/versions.env >> /etc/profile.d/versions.sh

# ---------- ② OS パッケージ ----------
ENV DEBIAN_FRONTEND=noninteractive
RUN . /etc/profile.d/versions.sh && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        python${PythonVer} python${PythonVer}-dev python3-pip \
        git curl wget build-essential \
        libgl1-mesa-glx libglib2.0-0 \
        tesseract-ocr tesseract-ocr-jpn tesseract-ocr-eng \
        mecab libmecab-dev mecab-ipadic-utf8 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# ---------- ③ Python 基盤 ----------
RUN . /etc/profile.d/versions.sh && \
    python${PythonVer} -m pip install --upgrade pip wheel setuptools --no-cache-dir

# ---------- ④ Python ライブラリ ----------
COPY requirements.txt /tmp/requirements.txt
RUN . /etc/profile.d/versions.sh && \
    python${PythonVer} -m pip install --no-cache-dir -r /tmp/requirements.txt && \
    # REM: CUDA 専用 index から固定バージョンを取得
    python${PythonVer} -m pip install --no-cache-dir \
        torch==$TorchVer \
        torchvision==$TorchVisionVer \
        --index-url https://download.pytorch.org/whl/cu124 && \
    rm /tmp/requirements.txt
    # cu124 → cu125 など CUDA 世代を替える場合は
    # --index-url のディレクトリも合わせて変える必要があることに注意

# ---------- ⑤ 作業ディレクトリ ----------
WORKDIR /workspace

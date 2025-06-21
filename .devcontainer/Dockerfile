# .devcontainer/Dockerfile
FROM python:3.9-slim

# 作業ディレクトリ
WORKDIR /workspace

# 必要なUbuntuパッケージをまとめてインストール
RUN apt-get update && apt-get install -y \
    git \
    libgl1-mesa-glx \
    tesseract-ocr \
    poppler-utils \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    mecab \
    libmecab-dev \
    mecab-ipadic-utf8 \
    ocrmypdf \
    tesseract-ocr-jpn \
    libreoffice \
    curl \
    build-essential \
    iputils-ping \
  && rm -rf /var/lib/apt/lists/*

# requirements.txt をコピーしてpipインストール
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install -r requirements.txt

# デフォルトコマンド
CMD ["bash"]

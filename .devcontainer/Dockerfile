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

# requirements.txt をコピーして pip インストール
COPY requirements.txt .
RUN pip install --upgrade pip --no-cache-dir \
 && pip install -r requirements.txt --no-cache-dir \
 \
 # Hugging Face の埋め込みモデルを先取り
 && python3 - <<'EOF'
from sentence_transformers import SentenceTransformer
# Sentence-Transformers 側のモデルを事前キャッシュ
SentenceTransformer('intfloat/e5-large-v2')
EOF

# デフォルトコマンド
CMD ["bash"]

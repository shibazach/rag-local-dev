FROM continuumio/miniconda3:latest

COPY environment.yml .

RUN apt-get update && apt-get install -y \
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
    curl && \
    apt-get clean

RUN apt-get update && \
    apt-get install -y libreoffice && \
    apt-get clean

RUN conda env create -f environment.yml

SHELL ["conda", "run", "-n", "rag_env", "/bin/bash", "-c"]

CMD ["sleep", "infinity"]

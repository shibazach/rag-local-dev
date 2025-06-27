#!/usr/bin/env bash
# REM: Ollama install / model preload / systemd 化 / logrotate 設定
# REM: 実行は root 前提 (sudo -i で入ってから叩く想定)
# REM: ragapp など Docker 側は host.docker.internal:11434 で接続

set -euo pipefail

### ---- 共通関数 ---------------------------------------------------------
# REM: コマンド存在チェック
command_exists() { command -v "$1" &>/dev/null; }

### ---- 1. パッケージ前提条件 -------------------------------------------
echo "🧩 [1/5] Installing prerequisite packages…"
apt-get update -qq
apt-get install -yq curl jq logrotate

### ---- 2. Ollama インストール ------------------------------------------
echo "🧠 [2/5] Installing Ollama (if needed)…"
if ! command_exists ollama; then
  curl -fsSL https://ollama.com/install.sh | bash
else
  echo "✅ Ollama already installed."
fi

### ---- 3. ログディレクトリ準備 ----------------------------------------
echo "📁 [3/5] Preparing log directory…"
mkdir -p /var/log/ollama
touch /var/log/ollama/ollama.log
chown root:root /var/log/ollama

### ---- 3.5 モデルディレクトリ準備 -----------------------------------
echo "📁 [3.5/5] Ensuring Ollama model directory exists…"
# Ollama のデフォルト path をそのまま使う
mkdir -p /usr/share/ollama/.ollama/models
chown -R ollama:ollama /usr/share/ollama/.ollama

### ---- 4. モデルあらかじめ取得 ----------------------------------------
echo "📦 [4/5] Pulling required models (may take a while)…"
#export OLLAMA_MODELS=/usr/share/ollama/.ollama/models
#ollama pull phi4-mini        || true
#ollama pull nomic-embed-text || true

sudo -u ollama env \
  HOME=/home/ollama \
  OLLAMA_MODELS=/usr/share/ollama/.ollama/models \
  OLLAMA_DEBUG=1 \
  ollama pull phi4-mini        || true
sudo -u ollama env \
  HOME=/home/ollama \
  OLLAMA_MODELS=/usr/share/ollama/.ollama/models \
  OLLAMA_DEBUG=1 \
  ollama pull nomic-embed-text || true

### ---- 5. systemd ユニット生成 ----------------------------------------
echo "🔧 [5/5] Creating systemd unit /etc/systemd/system/ollama.service"
cat >/etc/systemd/system/ollama.service <<'EOF'
[Unit]
Description=Ollama Service
After=network-online.target
Wants=network-online.target

[Service]
# Environment=HOME=/root
# Environment=OLLAMA_DEBUG=1
# Environment=OLLAMA_MODELS=/usr/share/ollama/.ollama/models
# Environment=OLLAMA_HOST=0.0.0.0:11434
# Environment=OLLAMA_ORIGINS=*

# ここで env を使って確実に環境を渡す
ExecStart=
ExecStart=/usr/bin/env \
  HOME=/root \
  OLLAMA_MODELS=/usr/share/ollama/.ollama/models \
  OLLAMA_HOST=0.0.0.0:11434 \
  OLLAMA_ORIGINS=* \
  /usr/local/bin/ollama serve \
    --host 0.0.0.0 \
    --port 11434 \
    --origins '*'

StandardOutput=append:/var/log/ollama/ollama.log
StandardError=inherit
MemoryMax=16G
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# systemd 再読み込み & 起動
echo "🔄 Reload and start Ollama service…"
systemctl daemon-reload
echo "Enabling Ollama service…"
systemctl enable --now ollama

echo "🎉 Ollama setup complete! 連携先は http://host.docker.internal:11434 です。"

#!/usr/bin/env bash
# REM: Ollama install / model preload / systemd 化 / logrotate 設定
# REM: 実行は root 前提 (sudo -i で入ってから叩く想定)
# REM: ragapp など Docker 側は host.docker.internal:11434 で接続

set -euo pipefail

### ---- 共通関数 ---------------------------------------------------------
# REM: コマンド存在チェック
command_exists() { command -v "$1" &>/dev/null; }

### ---- 1. パッケージ前提条件 -------------------------------------------
echo "🧩 [1/7] Installing prerequisite packages…"
apt-get update -qq
apt-get install -yq curl jq logrotate

### ---- 2. Ollama インストール ------------------------------------------
echo "🧠 [2/7] Installing Ollama (if needed)…"
if ! command_exists ollama; then
  curl -fsSL https://ollama.com/install.sh | bash
else
  echo "✅  Ollama already installed."
fi

### ---- 3. ディレクトリ & 権限整備 --------------------------------------
echo "📁 [3/7] Preparing directories…"
mkdir -p /var/log/ollama
mkdir -p /opt/ollama_models
chown root:root /var/log/ollama /opt/ollama_models
touch /var/log/ollama/ollama.log

### ---- 4. モデルあらかじめ取得 ----------------------------------------
echo "📦 [4/7] Pulling required models (may take a while)…"
ollama pull phi4-mini        || true   # REM: 生成モデル
ollama pull nomic-embed-text || true   # REM: 埋め込みモデル

### ---- 5. systemd ユニット生成 ----------------------------------------
echo "🔧 [5/7] Creating systemd unit /etc/systemd/system/ollama.service"
cat >/etc/systemd/system/ollama.service <<EOF
[Unit]
Description=Ollama Service
After=network-online.target
Wants=network-online.target

[Service]
Environment="HOME=/root"
Environment="OLLAMA_HOST=0.0.0.0"
Environment="OLLAMA_ORIGINS=*"
Environment="OLLAMA_MODELS=/opt/ollama_models"

ExecStart=/usr/local/bin/ollama serve \
  --host ${OLLAMA_HOST} \
  --port 11434 \
  --origins ${OLLAMA_ORIGINS}

StandardOutput=append:/var/log/ollama/ollama.log
StandardError=inherit
MemoryMax=16G
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now ollama

### ---- 6. logrotate 設定 ----------------------------------------------
echo "🗜  [6/7] Setting up logrotate /etc/logrotate.d/ollama"
cat >/etc/logrotate.d/ollama <<'EOF'
/var/log/ollama/ollama.log {
    weekly
    size 100M
    rotate 4
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    create 0644 root root
}
EOF

### ---- 7. Docker–>Host FW ルール設定 -----------------------------------
echo "🛡️  [7/7] Applying firewall rules for Docker bridge…"
# REM: ragnet ネットワークのサブネットを自動取得
DOCKER_NET=$(docker network inspect ragnet \
  --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}' 2>/dev/null || true)

if [[ -n "$DOCKER_NET" ]]; then
  echo "✔️  Detected ragnet subnet: $DOCKER_NET"
  # UFW ルール追加
  if command_exists ufw; then
    ufw allow from "$DOCKER_NET" to any port 11434 proto tcp || true
  fi
  # iptables DOCKER-USER チェーン追加
  if command_exists iptables; then
    iptables -C DOCKER-USER -s "$DOCKER_NET" -p tcp --dport 11434 -j ACCEPT 2>/dev/null \
      || iptables -I DOCKER-USER 1 -s "$DOCKER_NET" -p tcp --dport 11434 -j ACCEPT
  fi
else
  echo "⚠️  ragnet network not found; skipping firewall rules."
fi

### ---- 動作確認 --------------------------------------------------------
echo -e "\n🚀 Verification:"
systemctl --no-pager -l status ollama | head -n 15
ss -tln | grep 11434 || { echo "❌ Port 11434 not listening"; exit 1; }
curl -s http://localhost:11434/api/tags | jq -e '.models[0]' >/dev/null \
  && echo "✅ Ollama REST API is reachable." \
  || { echo "❌ Failed to reach Ollama REST API."; exit 1; }

echo -e "\n🎉 Setup complete!  ragapp からは http://host.docker.internal:11434 で到達できます."

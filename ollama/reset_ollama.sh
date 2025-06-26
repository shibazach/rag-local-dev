#!/usr/bin/env bash
# REM: 完全に Ollama をリセットして痕跡を残さない nuker
# REM: 実行前に「ollama-nuke」とタイプしないと abort する安全装置付き
# REM: root 権限での実行を想定 (sudo -i で入ってから叩く)

set -euo pipefail

### ---- 0. 二重確認 ------------------------------------------------------
read -rp $'\n!!! この操作は Ollama を完全に削除します。\n'\
'    サービス・モデル・ログ・設定ファイル・FW ルールもすべて消えます。\n'\
'    本当に続行する場合は「ollama-nuke」と入力してください > ' CONFIRM
[[ "$CONFIRM" == "ollama-nuke" ]] || { echo "Abort."; exit 1; }

### ---- 1. systemd サービス停止・削除 -----------------------------------
echo "🛑  Stopping & disabling systemd unit…"
systemctl disable --now ollama.service 2>/dev/null || true
rm -f /etc/systemd/system/ollama.service
systemctl daemon-reload

### ---- 2. logrotate 設定削除 -------------------------------------------
echo "🧹  Removing logrotate config…"
rm -f /etc/logrotate.d/ollama

### ---- 3. 実行中プロセス完全 Kill ---------------------------------------
echo "🔪  Killing residual Ollama processes…"
pkill -9 -f 'ollama serve' 2>/dev/null || true

### ---- 4. バイナリ削除 ---------------------------------------------------
echo "💣  Removing Ollama binary…"
rm -f /usr/local/bin/ollama

### ---- 5. モデル & ログ ディレクトリ削除 --------------------------------
echo "📂  Purging model & log directories…"
rm -rf /opt/ollama_models
rm -rf /var/log/ollama
rm -rf /root/.ollama   # 他ユーザー環境なら該当パスを調整

### ---- 6. Docker→Host FW ルール削除 -----------------------------------
echo "🛡️  Cleaning up firewall rules…"
DOCKER_NET=$(docker network inspect rag_ragnet \
  --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}' 2>/dev/null || true)

if [[ -n "$DOCKER_NET" ]]; then
  echo "✔️  Detected rag_ragnet subnet: $DOCKER_NET"
  # UFW ルール削除
  if command -v ufw &>/dev/null; then
    echo "📄 Deleting UFW rule..."
    ufw delete allow from "$DOCKER_NET" to any port 11434 proto tcp || true
  fi
  # iptables DOCKER-USER チェーンルール削除
  if command -v iptables &>/dev/null; then
    echo "📄 Deleting iptables rule..."
    iptables -D DOCKER-USER -s "$DOCKER_NET" -p tcp --dport 11434 -j ACCEPT 2>/dev/null || true
  fi
else
  echo "⚠️  rag_ragnet network not found; skipping FW cleanup."
fi

### ---- 7. ポート確認 ------------------------------------------------------
echo "🔍  Verifying port 11434 is free…"
if ss -tln | grep -q ':11434'; then
  echo "⚠️  Port 11434 is still in use. Please investigate manually."
else
  echo "✅  Port 11434 is now free."
fi

echo -e "\n🎉  Ollama has been completely removed from this system."

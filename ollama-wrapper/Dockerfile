# REM: Ollama のベースイメージを使用
FROM ollama/ollama:latest

# REM: 起動スクリプトをコピーし、実行可能化
COPY start.sh /start.sh
RUN chmod +x /start.sh

# REM: bash 経由で起動（exec format error 回避）
ENTRYPOINT ["/bin/bash", "/start.sh"]

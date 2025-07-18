# REM: app/routes/metrics.py（更新日時: 2025-07-18 日本時間（UTC +9））
# REM: システムモニタリング用ルーター（CPU/GPU 使用率取得）
from fastapi import APIRouter
import psutil
import subprocess
import json

router = APIRouter()

@router.get("/metrics")
def get_metrics():
    # REM: CPU 使用率（直近瞬間値）
    cpu = psutil.cpu_percent(interval=None)
    # REM: GPU 使用率・消費電力（nvidia-smi コマンド）
    gpu_data = {}
    try:
        # JSON 形式で取得
        out = subprocess.check_output([
            "nvidia-smi", 
            "--query-gpu=utilization.gpu,power.draw", 
            "--format=csv,noheader,nounits"
        ])
        util, power = out.decode().strip().split(", ")
        gpu_data = {
            "util": float(util),
            "power": float(power)
        }
    except Exception:
        # GPU がなければ空に
        gpu_data = {}

    return {"cpu": cpu, "gpu": gpu_data}

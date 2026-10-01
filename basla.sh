#!/bin/bash
# Sesli-Yaz (Whisper) sunucusunu baslatir.
cd "$(dirname "$(readlink -f "$0")")" || exit 1

PORT="${VOICE_PORT:-8443}"
IP="$(hostname -I 2>/dev/null | awk '{print $1}')"

# Eski sunucu calisiyorsa kapat (bu portu dinleyen surec)
for p in $(ss -ltnp 2>/dev/null | grep ":$PORT " | grep -o 'pid=[0-9]*' | cut -d= -f2); do
  kill "$p" 2>/dev/null
done

echo "=================================================="
echo "  SESLI YAZ  (Whisper - yerel)"
echo "=================================================="
echo "  Telefondan ac:  https://${IP:-<bilgisayarin-IP>}:$PORT"
echo "  (self-signed uyarisi -> Gelismis -> Devam et)"
echo "  Durdurmak icin:  Ctrl+C"
echo "=================================================="
echo

export DISPLAY="${DISPLAY:-:0}"
# GPU (CUDA) kutuphaneleri venv icindeki nvidia paketlerinden
SP="$(./venv/bin/python -c 'import site;print(site.getsitepackages()[0])')"
export LD_LIBRARY_PATH="$SP/nvidia/cublas/lib:$SP/nvidia/cudnn/lib:$SP/nvidia/cuda_nvrtc/lib:$LD_LIBRARY_PATH"
exec ./venv/bin/python server.py

#!/bin/bash
# Yerel ag icin self-signed HTTPS sertifikasi uretir: cert.pem + key.pem
# (Telefon tarayicisi mikrofona sadece HTTPS uzerinden izin verir.)
# Kullanim:  ./make_cert.sh [IP]     IP verilmezse bu makinenin LAN IP'si kullanilir.
set -e
cd "$(dirname "$(readlink -f "$0")")"
IP="${1:-$(hostname -I | awk '{print $1}')}"
openssl req -x509 -newkey rsa:2048 -nodes -days 3650 \
  -keyout key.pem -out cert.pem -subj "/CN=$IP" \
  -addext "subjectAltName=IP:$IP,DNS:localhost,IP:127.0.0.1"
chmod 600 key.pem
echo "cert.pem + key.pem olusturuldu (IP: $IP). IP degisirse tekrar calistirin."

# SESLI YAZ - Whisper (yerel) - KULLANIM

## Ne yapar

Telefon = kablosuz mikrofon. Telefondan konusursun, masaustundeki Whisper
Turkce'ye cevirir ve o an MASAUSTUNDE ODAKTA olan yere yazar (xdotool).
Boylece not defterine, editore veya terminale sesle yazarsin.

## 1) Sunucuyu baslat (masaustunde)

```bash
./make_cert.sh      # sadece ilk sefer (veya bilgisayarin IP'si degisince)
./basla.sh
```

Ilk acilista model yuklenir (ilk seferde ~/.cache/huggingface altina indirilir).
"Model hazir" + adres yazinca hazirdir. Durdur: `Ctrl+C`

Daha hizli (ama daha az isabetli) istersen:

```bash
VOICE_MODEL=medium ./basla.sh      # veya small
```

## 2) Telefondan ac

- Telefon ve bilgisayar AYNI WiFi'da olmali.
- Tarayicida: `https://<bilgisayarin-IP>:8443` (adres basla.sh ciktisinda yazar)
- Self-signed uyarisi cikar -> "Gelismis" / "Advanced" -> "Devam et / Proceed".
  (Guvenli baglanti sart; mikrofon ancak HTTPS'de calisir.)
- Ilk seferde mikrofon izni ISTER -> IZIN VER.

## 3) Nasil kullanilir

- Masaustunde YAZILMASINI istedigin yere BIR KEZ tikla (odakla):
  not defteri, editor, terminal...
- Telefonda buyuk butonu BASILI TUT, konus, BIRAK.
- Whisper cevirir -> odaktaki yere yazilir. Telefonda da metni gorursun.

Secenekler (telefon sayfasinda):

- **"Masaustunde odaktaki yere yaz"**: xdotool ile yazma (kapatirsan sadece
  telefonda gosterir, Kopyala ile alirsin).
- **"Yazdiktan sonra Enter'a bas"**: sohbet/terminale mesaj gonderirken ac (yazip
  otomatik gonderir). Not alirken KAPALI birak.

## Notlar / dikkat

- xdotool ODAKTAKI pencereye yazar. Once dogru yeri tikla, sonra konus.
- Ag: telefon farkli WiFi'daysa baglanmaz. IP degisirse `./make_cert.sh`'i tekrar
  calistir; sertifika o IP'ye gore uretilir.
- Model dosyalari `~/.cache/huggingface` altinda (bir kere iner).
- Sifre/kimlik dogrulama YOK: ayni agdaki herkes bu porta baglanip masaustune
  yazdirabilir. Sadece guvendigin agda kullan.

## Dosyalar

| Dosya | Ne |
|---|---|
| `server.py` | sunucu (HTTPS + Whisper + xdotool) |
| `basla.sh` | baslatici (eski sunucuyu kapatir, GPU kutuphane yollarini ayarlar) |
| `make_cert.sh` | self-signed sertifika uretir (`cert.pem` / `key.pem`, git'e girmez) |
| `sesli-yaz.desktop` | masaustu kisayolu (Exec yolunu duzenle) |
| `venv/` | izole python (faster-whisper) - git'e girmez |

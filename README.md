# whisper-phone-dictation

**Use your phone as a wireless push-to-talk microphone. A local Whisper model on your Linux desktop turns your speech into text and types it into whichever window has focus.**

## What it does

- `server.py` is a single-file HTTPS server built on the Python standard library
  (`http.server` + `ssl`). It serves a small mobile web page.
- On the phone you **hold the big button, speak and release**. The browser records the clip
  with `MediaRecorder` and posts it to the server.
- The server transcribes it with [faster-whisper](https://github.com/SYSTRAN/faster-whisper).
  The default is `large-v3` on CUDA with float16, and it falls back to CPU with int8 if
  the model cannot be loaded on the GPU. The language is Turkish by default; set `VOICE_LANG=auto` to
  auto-detect, for example for mixed Turkish and English.
- The text comes back to the phone, where you can copy or clear it. Optionally it is also
  **typed into the focused desktop window** with `xdotool`, and Enter can be pressed after
  it.
- Speech recognition runs entirely on your own machine, with no cloud speech API.
  faster-whisper downloads the model from Hugging Face once, on first use.

The web interface is in Turkish ("Sesli Yaz" = "write by voice").

## How it works

```
phone browser ── HTTPS POST /transcribe (webm/opus) ──▶ server.py ──▶ faster-whisper ──▶ text
      ▲                                                                  │
      └──────────────── JSON {text, typed, ms} ◀────────────────────────┤
                                                                         └──▶ xdotool type → focused window
```

- Phone browsers only allow microphone access on a secure origin, so the server uses HTTPS
  with a self-signed certificate for your LAN IP.
- Requests are transcribed one at a time behind a lock. The VAD filter drops silence,
  decoding uses beam size 5, and a Turkish initial prompt nudges the model toward
  punctuation and Turkish characters.

## Requirements

- Linux with an **X11** session. `xdotool` cannot type into native Wayland windows.
- `xdotool` and `openssl`, e.g. `sudo apt install xdotool openssl`.
- Python 3 with `faster-whisper`. An NVIDIA GPU is optional (CUDA 12 libraries from pip,
  see below).
- The phone and the computer on the same network.

## Setup and run

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
# optional, NVIDIA GPU:
./venv/bin/pip install nvidia-cublas-cu12 nvidia-cudnn-cu12 nvidia-cuda-nvrtc-cu12

./make_cert.sh     # creates cert.pem + key.pem for this machine's LAN IP (git-ignored)
./basla.sh         # stops an old instance on the port, sets the CUDA library path, starts server.py
```

Then, on the phone:

1. Open `https://<computer-LAN-IP>:8443`. The address is printed at startup.
2. Accept the self-signed certificate warning (Advanced → Proceed) and allow the microphone.
3. On the desktop, click once into the window where the text should go. Then hold the
   button on the phone, speak and release.

To get a desktop launcher, set the `Exec=` path in `sesli-yaz.desktop` and copy the file to
`~/.local/share/applications/`. A short Turkish usage guide is in
[`docs/KULLANIM.md`](docs/KULLANIM.md).

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `VOICE_MODEL` | `large-v3` | Whisper model (`medium`, `small`, … are faster) |
| `VOICE_LANG` | `tr` | Language code; `auto` = detect |
| `VOICE_PROMPT` | Turkish sentence | Initial prompt (only used when `VOICE_LANG=tr`) |
| `VOICE_DEVICE` | `cuda` | `cuda` or `cpu` (falls back to CPU if loading on CUDA fails) |
| `VOICE_COMPUTE` | `float16` on CUDA, `int8` on CPU | CTranslate2 compute type |
| `VOICE_PORT` | `8443` | HTTPS port |
| `VOICE_DISPLAY` | `$DISPLAY` or `:0` | X display that `xdotool` types into |

## Security notes

- **There is no authentication.** The server listens on all interfaces. Anyone who can
  reach the port can send audio and make your desktop type text. Use it only on a trusted
  network, or firewall the port.
- `key.pem` is your private key. It is git-ignored, so keep it out of commits.
- `basla.sh` stops whatever process is already listening on the configured port.

## Project status

This is a small personal tool written for one Linux (X11) desktop. It is a single script
with no packaging and no automated tests. It was checked end to end (page served,
transcription request answered) on CPU with the `base` model.

## License

[MIT](LICENSE)

---

Built by [Adem Batur](https://github.com/adembtr)

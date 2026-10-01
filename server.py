#!/usr/bin/env python3
"""Yerel Whisper sesli-yazma sunucusu (telefon = kablosuz mikrofon).

Telefondan HTTPS sayfayi ac -> basili tut konus -> birak.
Sunucu (masaustu) Whisper ile Turkce'ye cevirir ve:
  - metni telefona geri gonderir (gormek/kopyalamak icin), VE
  - istege bagli xdotool ile o an MASAUSTUNDE ODAKTA olan yere yazar
    (player notlari, terminal, vs.).

Calistir:  ./basla.sh            (veya: ./venv/bin/python server.py)
Telefon:   https://<bilgisayarin-LAN-IP>:8443   (self-signed uyarisini kabul et)
Sertifika: ./make_cert.sh        (cert.pem + key.pem uretir; mikrofon sadece HTTPS'te calisir)

Ortam degiskenleri:
  VOICE_MODEL  = whisper model (varsayilan: large-v3; daha hizli: medium / small)
  VOICE_LANG   = dil ("tr" varsayilan; "auto"=otomatik algila, TR/EN karisik icin)
  VOICE_PORT   = port (varsayilan 8443)
  VOICE_DISPLAY= X DISPLAY (varsayilan $DISPLAY, yoksa :0)  xdotool bunu kullanir
  VOICE_DEVICE = cuda (varsayilan) / cpu   -- GPU acilmazsa otomatik CPU'ya duser
  VOICE_COMPUTE= float16 (cuda) / int8 (cpu)
  VOICE_PROMPT = Turkce baslangic istemi (sadece VOICE_LANG=tr iken)
"""
import json
import os
import ssl
import subprocess
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from faster_whisper import WhisperModel

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_NAME = os.environ.get("VOICE_MODEL", "large-v3")
PORT = int(os.environ.get("VOICE_PORT", "8443"))
DISPLAY = os.environ.get("VOICE_DISPLAY", os.environ.get("DISPLAY", ":0"))
CERT = os.path.join(HERE, "cert.pem")
KEY = os.path.join(HERE, "key.pem")
if __name__ == "__main__" and not (os.path.isfile(CERT) and os.path.isfile(KEY)):
    raise SystemExit("cert.pem / key.pem bulunamadi -> once ./make_cert.sh calistirin.")

# Dil: varsayilan "tr" (kisa cumlelerde otomatik algilama Turkce'yi sik kacirir);
# TR/EN karisik konusmak icin VOICE_LANG=auto
_lang_env = os.environ.get("VOICE_LANG", "tr").strip().lower()
LANG = None if _lang_env in ("", "auto") else _lang_env
# Turkce'ye yonlendiren baslangic istemi (noktalama + Turkce karakterler icin)
INITIAL_PROMPT = os.environ.get(
    "VOICE_PROMPT",
    "Merhaba, bugün hava çok güzel. Şimdi bu cümleyi yazıya döküyorum, noktalama işaretleriyle birlikte."
) if LANG == "tr" else None

DEVICE = os.environ.get("VOICE_DEVICE", "cuda")   # once GPU dene
COMPUTE = os.environ.get("VOICE_COMPUTE", "float16" if DEVICE == "cuda" else "int8")
print(f"Whisper model yukleniyor: {MODEL_NAME} ({DEVICE}/{COMPUTE}) ...")
try:
    MODEL = WhisperModel(MODEL_NAME, device=DEVICE, compute_type=COMPUTE)
    print(f"Model hazir. ({DEVICE})")
except Exception as e:
    print(f"GPU basarisiz ({e}); CPU'ya donuluyor...")
    DEVICE, COMPUTE = "cpu", "int8"
    MODEL = WhisperModel(MODEL_NAME, device="cpu", compute_type="int8")
    print("Model hazir. (cpu)")
_LOCK = threading.Lock()


def transcribe(audio_path):
    """Ses dosyasini metne cevir (dil otomatik algilanir: TR/EN/...)."""
    with _LOCK:
        segments, _info = MODEL.transcribe(
            audio_path,
            language=LANG,
            vad_filter=True,
            beam_size=5,          # daha isabetli (gurultulu ortam icin)
            best_of=5,
            initial_prompt=INITIAL_PROMPT,
            condition_on_previous_text=False,
        )
        return "".join(s.text for s in segments).strip()


def xdotool_type(text, press_enter=False):
    """Metni o an odakta olan pencereye yaz."""
    env = dict(os.environ, DISPLAY=DISPLAY)
    try:
        subprocess.run(
            ["xdotool", "type", "--clearmodifiers", "--", text],
            env=env, check=True, timeout=15,
        )
        if press_enter:
            subprocess.run(["xdotool", "key", "--clearmodifiers", "Return"],
                           env=env, check=True, timeout=5)
        return True, ""
    except Exception as e:
        return False, str(e)


PAGE = r"""<!doctype html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>Sesli Yaz</title>
<style>
  :root{color-scheme:dark}
  *{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
  body{margin:0;background:#0d0f14;color:#e6e6e6;font:16px system-ui,sans-serif;
       height:100vh;display:flex;flex-direction:column;gap:14px;padding:18px;overflow:hidden}
  h1{font-size:16px;margin:0;color:#8aa;font-weight:600}
  .opt{display:flex;align-items:center;gap:10px;font-size:15px;color:#bcd}
  input[type=checkbox]{width:22px;height:22px}
  #mic{flex:1;border:0;border-radius:22px;background:#1b2540;color:#cfe;
       font-size:26px;font-weight:800;display:flex;align-items:center;justify-content:center;
       user-select:none;touch-action:none;transition:.08s}
  #mic.rec{background:#7d1f2f;color:#fff;transform:scale(.99)}
  #mic small{display:block;font-size:14px;font-weight:500;color:#9ab;margin-top:8px}
  #mic.rec small{color:#ffd0d0}
  #out{min-height:84px;max-height:34vh;overflow:auto;background:#0a0c11;border:1px solid #222;
       border-radius:12px;padding:12px;font-size:16px;line-height:1.5;white-space:pre-wrap}
  #status{font-size:13px;color:#6b7688;min-height:18px}
  .row{display:flex;gap:10px}
  .row button{flex:1;background:#1b1f2b;color:#cfe;border:1px solid #3a4256;border-radius:10px;
       padding:12px;font-size:15px;font-weight:600}
</style></head>
<body>
  <h1>🎤 Sesli Yaz — Whisper (yerel)</h1>
  <label class="opt"><input type="checkbox" id="totype" checked> Masaüstünde odaktaki yere yaz</label>
  <label class="opt"><input type="checkbox" id="enter"> Yazdıktan sonra Enter'a bas</label>
  <button id="mic">BASILI TUT & KONUŞ<small>bırakınca yazar</small></button>
  <div id="out" placeholder=""></div>
  <div class="row">
    <button id="copy">Kopyala</button>
    <button id="clear">Temizle</button>
  </div>
  <div id="status"></div>
<script>
const mic=document.getElementById('mic'), out=document.getElementById('out'),
      status=document.getElementById('status'), totype=document.getElementById('totype'),
      enterBox=document.getElementById('enter');
let rec=null, chunks=[], stream=null, busy=false;

async function ensureStream(){
  if(stream) return stream;
  stream=await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:true,noiseSuppression:true}});
  return stream;
}
async function start(){
  if(busy) return;
  try{
    await ensureStream();
    chunks=[];
    rec=new MediaRecorder(stream);
    rec.ondataavailable=e=>{ if(e.data.size>0) chunks.push(e.data); };
    rec.onstop=send;
    rec.start();
    mic.classList.add('rec'); status.textContent='dinliyorum...';
  }catch(e){ status.textContent='mikrofon HATASI: '+e.message; }
}
function stop(){
  if(rec && rec.state!=='inactive'){ rec.stop(); mic.classList.remove('rec'); status.textContent='cevriliyor...'; }
}
async function send(){
  const blob=new Blob(chunks,{type: rec.mimeType||'audio/webm'});
  if(blob.size<600){ status.textContent='cok kisa'; return; }
  busy=true;
  try{
    const url='/transcribe?type='+(totype.checked?1:0)+'&enter='+(enterBox.checked?1:0);
    const r=await fetch(url,{method:'POST',headers:{'Content-Type':blob.type},body:blob});
    const j=await r.json();
    if(j.error){ status.textContent='hata: '+j.error; }
    else {
      const t=(j.text||'').trim();
      out.textContent=(out.textContent?out.textContent+' ':'')+t;
      out.scrollTop=out.scrollHeight;
      status.textContent=(j.typed? '✓ masaustune yazildi':'✓ cevrildi')+' ('+(j.ms||'?')+'ms)';
    }
  }catch(e){ status.textContent='ag hatasi: '+e.message; }
  busy=false;
}
// bas-konus (dokunma + fare)
mic.addEventListener('pointerdown',e=>{e.preventDefault();start();});
mic.addEventListener('pointerup',e=>{e.preventDefault();stop();});
mic.addEventListener('pointercancel',e=>{stop();});
document.getElementById('copy').onclick=()=>{ navigator.clipboard.writeText(out.textContent).then(()=>status.textContent='kopyalandi'); };
document.getElementById('clear').onclick=()=>{ out.textContent=''; status.textContent=''; };
</script>
</body></html>
"""


def lan_ip():
    """Bu makinenin LAN IP'si (UDP connect paket gondermez; sadece rota secer)."""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, PAGE, "text/html; charset=utf-8")
        else:
            self._send(404, b"{}")

    def do_POST(self):
        if not self.path.startswith("/transcribe"):
            self._send(404, b"{}")
            return
        import time
        from urllib.parse import urlparse, parse_qs
        q = parse_qs(urlparse(self.path).query)
        want_type = (q.get("type") or ["0"])[0] == "1"
        want_enter = (q.get("enter") or ["0"])[0] == "1"
        n = int(self.headers.get("Content-Length", 0))
        data = self.rfile.read(n) if n else b""
        if not data:
            self._send(200, json.dumps({"error": "bos ses"}))
            return
        t0 = time.time()
        tmp = tempfile.NamedTemporaryFile(suffix=".webm", delete=False)
        try:
            tmp.write(data)
            tmp.close()
            text = transcribe(tmp.name)
            typed = False
            if want_type and text:
                ok, err = xdotool_type(text, press_enter=want_enter)
                typed = ok
            ms = int((time.time() - t0) * 1000)
            self._send(200, json.dumps({"text": text, "typed": typed, "ms": ms}))
        except Exception as e:
            self._send(200, json.dumps({"error": str(e)}))
        finally:
            try:
                os.unlink(tmp.name)
            except Exception:
                pass


if __name__ == "__main__":
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(CERT, KEY)
    httpd = ThreadingHTTPServer(("0.0.0.0", PORT), H)
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
    print(f"Sesli-yaz sunucusu -> https://{lan_ip()}:{PORT}")
    print(f"xdotool DISPLAY={DISPLAY}")
    print("Telefonda self-signed uyarisini KABUL ET (Gelismis -> devam).")
    httpd.serve_forever()

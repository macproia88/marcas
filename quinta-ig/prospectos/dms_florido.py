"""Lista las quintas a las que @quintaelflorido les ofreció el servicio de Instagram y si contestaron.
Lee las charlas por la API (IG_TOKEN, nunca se imprime). Solo guarda charlas donde mandamos el mensaje
de prospección. El resultado va CIFRADO con publica.pem del bot (prospectos.enc.json): no queda texto en claro."""
import json, os, base64, urllib.request, urllib.parse
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization

IG = "17841454960836233"; YO = "quintaelflorido"; API = "https://graph.facebook.com/v23.0"
T = os.environ.get("IG_TOKEN", "").strip().strip('"')
AQUI = os.path.dirname(os.path.abspath(__file__))
MARCA = ("Instagram de otras quintas", "demo-quintas", "manejo el Instagram de quintas", "lo probamos una semana",
         "manejo el Instagram", "olvidate del IG", "te olvidás de manejar")

def get(url):
    return json.load(urllib.request.urlopen(url, timeout=40))

url = f"{API}/{IG}/conversations?" + urllib.parse.urlencode({"platform": "instagram", "limit": 25, "access_token": T,
      "fields": "updated_time,participants,messages.limit(25){from,message,created_time}"})
out, vistas, paginas, err = [], 0, 0, ""
try:
    while url and paginas < 40:
        d = get(url); paginas += 1
        for c in d.get("data", []):
            vistas += 1
            msgs = (c.get("messages") or {}).get("data", [])
            nuestros = [m for m in msgs if (m.get("from") or {}).get("username") == YO]
            if not any(any(k in (m.get("message") or "") for k in MARCA) for m in nuestros): continue
            otro = next((p for p in (c.get("participants") or {}).get("data", []) if p.get("username") != YO), {})
            suyos = [m for m in msgs if (m.get("from") or {}).get("username") != YO]
            primero = min((m["created_time"] for m in nuestros if any(k in (m.get("message") or "") for k in MARCA)), default="")
            out.append({"usuario": otro.get("username"), "enviado": primero[:10],
                        "respuestas": [{"t": (m.get("message") or "[adjunto]")[:400], "h": m["created_time"][:16]} for m in reversed(suyos)],
                        "charla": [{"de": "yo" if (m.get("from") or {}).get("username") == YO else "ellos", "t": (m.get("message") or "[adjunto]")[:600], "h": m["created_time"][:16]} for m in reversed(msgs)] if suyos else [], "otro_id": otro.get("id")})
        url = (d.get("paging") or {}).get("next")
except urllib.error.HTTPError as e:
    err = e.read().decode()[:300]

obj = {"charlas_vistas": vistas, "paginas": paginas, "error": err, "prospectos": out}
OAEP = padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
pub = serialization.load_pem_public_key(open(os.path.join(AQUI, "..", "bot", "publica.pem"), "rb").read())
k, iv = AESGCM.generate_key(256), os.urandom(12)
b = lambda x: base64.b64encode(x).decode()
ct = AESGCM(k).encrypt(iv, json.dumps(obj, ensure_ascii=False).encode(), None)
json.dump({"k": b(pub.encrypt(k, OAEP)), "iv": b(iv), "data": b(ct)}, open(os.path.join(AQUI, "florido.enc.json"), "w"))
print("charlas", vistas, "paginas", paginas, "prospectos", len(out), "error" if err else "ok")

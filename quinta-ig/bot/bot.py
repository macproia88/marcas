"""Bot de mensajes y comentarios de Quinta El Florido (Instagram).
leer:   junta DMs y comentarios sin responder -> pendientes.enc.json (cifrado, el repo es público)
enviar: manda las respuestas de responder.enc.json que estén "pendiente" -> las marca enviado/error
pendientes se cifra con publica.pem; solo la tarea programada de Claude tiene la privada (BOT_PRIV).
responder.json va en claro: solo ids opacos y el texto de respuesta (sin nombres). IG_TOKEN nunca se imprime."""
import os, sys, json, base64, datetime, urllib.request, urllib.parse, urllib.error
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization
AQUI = os.path.dirname(os.path.abspath(__file__))
IG = "17841454960836233"; YO = "quintaelflorido"; API = "https://graph.facebook.com/v23.0"
T = os.environ.get("IG_TOKEN", "").strip().strip('"')
AR = datetime.timezone(datetime.timedelta(hours=-3))
ahora = datetime.datetime.now(AR)

OAEP = padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
b64 = lambda x: base64.b64encode(x).decode()
def guardar_cifrado(obj, nombre):
    pub = serialization.load_pem_public_key(open(os.path.join(AQUI, "publica.pem"), "rb").read())
    k, iv = AESGCM.generate_key(256), os.urandom(12)
    ct = AESGCM(k).encrypt(iv, json.dumps(obj, ensure_ascii=False).encode(), None)
    json.dump({"k": b64(pub.encrypt(k, OAEP)), "iv": b64(iv), "data": b64(ct)}, open(os.path.join(AQUI, nombre), "w"))
def abrir_cifrado(nombre):
    priv = serialization.load_pem_private_key(os.environ["BOT_PRIV"].encode(), None)
    d = json.load(open(os.path.join(AQUI, nombre))); u = base64.b64decode
    return json.loads(AESGCM(priv.decrypt(u(d["k"]), OAEP)).decrypt(u(d["iv"]), u(d["data"]), None))
def leer_json(nombre, defecto):
    f = os.path.join(AQUI, nombre)
    return json.load(open(f)) if os.path.exists(f) else defecto
def guardar_json(obj, nombre): json.dump(obj, open(os.path.join(AQUI, nombre), "w"), ensure_ascii=False, indent=1)

def get(path, **p):
    p["access_token"] = T
    return json.load(urllib.request.urlopen(f"{API}/{path}?{urllib.parse.urlencode(p)}", timeout=30))
def post(path, **p):
    p["access_token"] = T
    r = urllib.request.Request(f"{API}/{path}", data=urllib.parse.urlencode(p).encode(), method="POST")
    return json.load(urllib.request.urlopen(r, timeout=30))
def fecha(s): return datetime.datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=datetime.timezone.utc).astimezone(AR)

modo = sys.argv[1] if len(sys.argv) > 1 else "leer"
if modo == "leer":
    out = {"actualizado": ahora.strftime("%Y-%m-%d %H:%M"), "dms": [], "comentarios": [], "errores": []}
    try:
        convs = get(f"{IG}/conversations", platform="instagram", limit=40,
                    fields="id,updated_time,participants,messages.limit(8){id,from,message,created_time}")["data"]
        for c in convs:
            if (ahora - fecha(c["updated_time"])).days > 3: continue
            msgs = (c.get("messages") or {}).get("data", [])
            if not msgs: continue
            ult = msgs[0]
            if (ult.get("from") or {}).get("username") == YO: continue
            cliente = next((p for p in c.get("participants", {}).get("data", []) if p.get("username") != YO), {})
            out["dms"].append({"conv": c["id"], "para_id": cliente.get("id"), "usuario": cliente.get("username"),
                "charla": [{"de": "nosotros" if (m.get("from") or {}).get("username") == YO else "cliente",
                            "texto": m.get("message") or "[adjunto/audio]", "hora": fecha(m["created_time"]).strftime("%d/%m %H:%M")} for m in reversed(msgs)]})
    except urllib.error.HTTPError as e: out["errores"].append("dms: " + e.read().decode()[:200])
    try:
        for m in get(f"{IG}/media", fields="id,caption,timestamp,permalink", limit=10)["data"]:
            for cm in get(f"{m['id']}/comments", fields="id,text,username,timestamp,replies{username}", limit=50).get("data", []):
                if cm.get("username") == YO or (ahora - fecha(cm["timestamp"])).days > 7: continue
                if any(r.get("username") == YO for r in (cm.get("replies") or {}).get("data", [])): continue
                out["comentarios"].append({"comment_id": cm["id"], "usuario": cm.get("username"), "texto": cm.get("text"),
                    "hora": fecha(cm["timestamp"]).strftime("%d/%m %H:%M"), "publicacion": (m.get("caption") or "")[:90]})
    except urllib.error.HTTPError as e: out["errores"].append("comentarios: " + e.read().decode()[:200])
    guardar_cifrado(out, "pendientes.enc.json")
    print("dms", len(out["dms"]), "comentarios", len(out["comentarios"]), "errores", len(out["errores"]))
elif modo == "enviar":
    lista = leer_json("responder.json", [])
    for x in lista:
        if x.get("estado") != "pendiente": continue
        try:
            if x["tipo"] == "dm":
                r = post(f"{IG}/messages", recipient=json.dumps({"id": x["para_id"]}), message=json.dumps({"text": x["texto"]}))
            else:
                r = post(f"{x['comment_id']}/replies", message=x["texto"])
            x["estado"] = "enviado"; x["hora"] = ahora.strftime("%d/%m %H:%M")
        except urllib.error.HTTPError as e:
            x["estado"] = "error"; x["error"] = e.read().decode()[:200]
        except Exception as e:
            x["estado"] = "error"; x["error"] = str(e)[:200]
    guardar_json(lista, "responder.json")
    print([(x.get("tipo"), x["estado"]) for x in lista[-30:]])
elif modo == "precios":
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    e = json.load(open(os.path.join(AQUI, "precios.enc.json"))); u = base64.b64decode
    k = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=u(e["salt"]), iterations=e["iter"]).derive(os.environ["CLAVE"].encode())
    print(json.dumps(json.loads(AESGCM(k).decrypt(u(e["iv"]), u(e["data"]), None)), ensure_ascii=False, indent=1))
elif modo == "ver":
    print(json.dumps(abrir_cifrado("pendientes.enc.json"), ensure_ascii=False, indent=1))

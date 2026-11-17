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
    import hashlib
    h = hashlib.sha256(json.dumps({k: v for k, v in obj.items() if k != "actualizado"}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
    viejo = leer_json(nombre, {})
    if viejo.get("h") == h: return
    pub = serialization.load_pem_public_key(open(os.path.join(AQUI, "publica.pem"), "rb").read())
    k, iv = AESGCM.generate_key(256), os.urandom(12)
    ct = AESGCM(k).encrypt(iv, json.dumps(obj, ensure_ascii=False).encode(), None)
    json.dump({"k": b64(pub.encrypt(k, OAEP)), "iv": b64(iv), "data": b64(ct), "h": h}, open(os.path.join(AQUI, nombre), "w"))
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
AUTO = ("¡Hola! 👋 Gracias por escribir", "¡Hola! 🌙", "¡Hola! 🎄 Gracias por escribir", "📲 Escribinos al WhatsApp",
        "¡Hola! 👋 Gracias por tu comentario", "Estamos en General Rodríguez, a solo", "☀️ Quinta de día", "☀ Quinta de día",
        "¡Pasanos la fecha", "💰 Hasta diciembre", "¡Hola! Gracias por ponerte en contacto")
def mensajes_de(para_id):
    # Últimos mensajes de la charla con ESE cliente (la API no filtra por usuario, así que lo buscamos).
    cs = get(f"{IG}/conversations", platform="instagram", limit=50,
             fields="participants,messages.limit(4){from,message,created_time}").get("data", [])
    for c in cs:
        if any(p.get("id") == para_id for p in (c.get("participants") or {}).get("data", [])):
            return (c.get("messages") or {}).get("data", [])
    raise Exception("charla no encontrada")
def es_auto(t): return (not t.strip()) or t.startswith(AUTO)
def fecha(s): return datetime.datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=datetime.timezone.utc).astimezone(AR)

modo = sys.argv[1] if len(sys.argv) > 1 else "leer"
if modo == "leer":
    out = {"actualizado": ahora.strftime("%Y-%m-%d %H:%M"), "dms": [], "comentarios": [], "errores": []}
    try:
        convs = get(f"{IG}/conversations", platform="instagram", limit=40,
                    fields="id,updated_time,participants,messages.limit(12){id,from,message,created_time}")["data"]
        for c in convs:
            if (ahora - fecha(c["updated_time"])).days > 7: continue
            msgs = (c.get("messages") or {}).get("data", [])
            if not msgs: continue
            # Pendiente si hay un mensaje del cliente más nuevo que nuestra última respuesta real
            # (las automáticas de Meta y la vista previa del link no cuentan como respuesta).
            pend = False
            for m in msgs:
                if (m.get("from") or {}).get("username") != YO: pend = True; break
                if not es_auto(m.get("message") or ""): break
            if not pend: continue
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
    # responder.json lo escribimos nosotros; el reloj solo anota lo mandado en enviados.json
    # (clave = destinatario + texto). Así nunca se manda dos veces lo mismo.
    import hashlib
    lista = leer_json("responder.json", [])
    env = leer_json("enviados.json", {})
    for x in lista:
        if x.get("estado") != "pendiente": continue
        dest = x.get("para_id") or x.get("comment_id")
        clave = hashlib.sha256(f"{x['tipo']}|{dest}|{x['texto']}".encode()).hexdigest()[:16]
        if clave in env: continue
        # Último control justo antes de mandar: si Juan ya contestó a mano, no mandamos nada.
        try:
            if x["tipo"] == "dm" and not x.get("seguimiento"):
                ms = mensajes_de(x["para_id"])
                ult = next((m for m in ms if not ((m.get("from") or {}).get("username") == YO and es_auto(m.get("message") or ""))), None)
                if ult and (ult.get("from") or {}).get("username") == YO:
                    env[clave] = {"estado": "salteado", "motivo": "ya respondió Juan", "hora": ahora.strftime("%d/%m %H:%M")}
                    guardar_json(env, "enviados.json"); continue
            else:
                rs = get(f"{x['comment_id']}", fields="replies{username}").get("replies", {}).get("data", [])
                if any(r.get("username") == YO for r in rs):
                    env[clave] = {"estado": "salteado", "motivo": "comentario ya respondido", "hora": ahora.strftime("%d/%m %H:%M")}
                    guardar_json(env, "enviados.json"); continue
        except Exception as e:
            print("control previo falló, se manda igual:", str(e)[:120])
        try:
            if x["tipo"] == "dm":
                post(f"{IG}/messages", recipient=json.dumps({"id": x["para_id"]}), message=json.dumps({"text": x["texto"]}))
            else:
                post(f"{x['comment_id']}/replies", message=x["texto"])
            env[clave] = {"estado": "enviado", "hora": ahora.strftime("%d/%m %H:%M")}
        except urllib.error.HTTPError as e:
            env[clave] = {"estado": "error", "error": e.read().decode()[:200]}
        except Exception as e:
            env[clave] = {"estado": "error", "error": str(e)[:200]}
        guardar_json(env, "enviados.json")
    print(len(env), "en enviados.json")
elif modo == "limpiar":
    # Saca de responder.json lo ya enviado (según enviados.json). Correr antes de agregar respuestas nuevas.
    import hashlib
    env = leer_json("enviados.json", {})
    lista = leer_json("responder.json", [])
    def k(x): return hashlib.sha256(f"{x['tipo']}|{x.get('para_id') or x.get('comment_id')}|{x['texto']}".encode()).hexdigest()[:16]
    queda = [x for x in lista if x.get("estado") == "pendiente" and k(x) not in env]
    guardar_json(queda, "responder.json")
    print("quedan", len(queda), "sin enviar")
elif modo == "probar_control":
    # Solo lectura: confirma que la consulta de control previo funciona (no imprime textos).
    ms = mensajes_de(sys.argv[2])
    print("CONTROL mensajes:", len(ms), "de:", [("nosotros" if (m.get("from") or {}).get("username") == YO else "cliente") for m in ms])
elif modo == "precios":
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    e = json.load(open(os.path.join(AQUI, "precios.enc.json"))); u = base64.b64decode
    k = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=u(e["salt"]), iterations=e["iter"]).derive(os.environ["CLAVE"].encode())
    print(json.dumps(json.loads(AESGCM(k).decrypt(u(e["iv"]), u(e["data"]), None)), ensure_ascii=False, indent=1))
elif modo == "ver":
    print(json.dumps(abrir_cifrado("pendientes.enc.json"), ensure_ascii=False, indent=1))

"""Conectar cuentas de clientes al robot sin pasar contraseñas.

Flujo:
 1. El cliente abre https://macproia88.github.io/marcas/conectar/?c=<cliente>
    y entra con su Instagram (login oficial de Meta).
 2. La página cifra lo que devuelve Meta con la clave pública (conectar/clave-publica.json)
    y le muestra un "código cifrado" para mandarle a Juan por WhatsApp.
 3. El workflow ig-conectar.yml (accion=conectar) lo descifra acá, lo cambia por una
    llave de 60 días, lo guarda CIFRADO en quinta-ig/publicador/llaves/<usuario>.enc
    y agrega la cuenta a cuentas.json.
 4. accion=renovar (semanal) renueva las llaves antes de que venzan.

Todo se cifra con una clave derivada del secret IG_APP_SECRET (nunca se imprime).
Las llaves nunca se escriben en claro en el repo (que es público).
"""
import base64, datetime, hashlib, json, os, sys, urllib.parse, urllib.request
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(AQUI, "..", ".."))
LLAVES = os.path.join(AQUI, "llaves")
CUENTAS = os.path.join(AQUI, "cuentas.json")
PUBLICA = os.path.join(REPO, "conectar", "clave-publica.json")
PRIVADA = os.path.join(LLAVES, "privada.enc")
APP_ID = os.environ.get("IG_APP_ID", "1441500650864869")
SECRETO = os.environ.get("IG_APP_SECRET", "").strip()
REDIRECT = "https://macproia88.github.io/marcas/conectar/"
FB = "https://graph.facebook.com/v23.0"
IG = "https://graph.instagram.com"
ART = datetime.timezone(datetime.timedelta(hours=-3))


def fernet():
    if not SECRETO:
        sys.exit("Falta el secret IG_APP_SECRET")
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(b"llaves-robot:" + SECRETO.encode()).digest()))


def http(url, params=None, metodo="GET"):
    datos = urllib.parse.urlencode(params or {})
    req = urllib.request.Request(url + ("?" + datos if metodo == "GET" else ""),
                                 data=datos.encode() if metodo == "POST" else None, method=metodo)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        cuerpo = e.read().decode(errors="ignore")
        try:
            msg = json.loads(cuerpo)["error"]
            msg = msg.get("message", str(msg)) if isinstance(msg, dict) else str(msg)
        except Exception:
            msg = cuerpo
        raise RuntimeError(msg[:300])


def claves():
    """Crea el par de claves (una sola vez). La privada queda cifrada; la pública va a la página."""
    if os.path.exists(PRIVADA):
        print("Ya existen las claves")
        return
    os.makedirs(LLAVES, exist_ok=True)
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = priv.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    open(PRIVADA, "wb").write(fernet().encrypt(pem))
    spki = priv.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    os.makedirs(os.path.dirname(PUBLICA), exist_ok=True)
    json.dump({"spki": base64.b64encode(spki).decode(), "creada": datetime.datetime.now(ART).strftime("%Y-%m-%d %H:%M")},
              open(PUBLICA, "w"), indent=1)
    print("Claves creadas")


def descifrar_paquete(paquete):
    """Paquete de la página: base64( clave AES envuelta con RSA-OAEP (256 b) + iv (12 b) + texto cifrado AES-GCM )."""
    crudo = base64.b64decode("".join(paquete.split()) + "===")
    priv = serialization.load_pem_private_key(fernet().decrypt(open(PRIVADA, "rb").read()), password=None)
    k = priv.decrypt(crudo[:256], padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
    return json.loads(AESGCM(k).decrypt(crudo[256:268], crudo[268:], None))


def largo_plazo(tok):
    """Devuelve (llave de ~60 días, api)."""
    if tok.startswith("IG"):
        r = http(f"{IG}/access_token", {"grant_type": "ig_exchange_token", "client_secret": SECRETO, "access_token": tok})
        return r["access_token"], "ig"
    r = http(f"{FB}/oauth/access_token", {"grant_type": "fb_exchange_token", "client_id": APP_ID,
                                         "client_secret": SECRETO, "fb_exchange_token": tok})
    return r["access_token"], "fb"


def cuentas_de(tok, api):
    """Lista de (ig_id, usuario) a las que da acceso la llave."""
    if api == "ig":
        r = http(f"{IG}/v23.0/me", {"fields": "user_id,username", "access_token": tok})
        return [(str(r.get("user_id") or r["id"]), r["username"])]
    r = http(f"{FB}/me/accounts", {"fields": "instagram_business_account{id,username}", "access_token": tok, "limit": 100})
    return [(p["instagram_business_account"]["id"], p["instagram_business_account"]["username"])
            for p in r.get("data", []) if p.get("instagram_business_account")]


def guardar(usuario, ig_id, tok, api, cliente):
    os.makedirs(LLAVES, exist_ok=True)
    nombre = f"llaves/{usuario.lower()}.enc"
    meta = {"llave": tok, "api": api, "renovada": datetime.datetime.now(ART).strftime("%Y-%m-%d %H:%M")}
    open(os.path.join(AQUI, nombre), "wb").write(fernet().encrypt(json.dumps(meta).encode()))
    cs = json.load(open(CUENTAS, encoding="utf-8"))
    fila = next((c for c in cs if c["usuario"].lower() == usuario.lower()), None)
    if fila is None:
        fila = {"nombre": cliente or usuario, "usuario": usuario, "cola": f"clientes/{cliente or usuario}/cola.json", "activa": True}
        cs.append(fila)
    fila.update(ig_id=ig_id, llave=nombre)
    json.dump(cs, open(CUENTAS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def conectar(paquete, cliente):
    d = descifrar_paquete(paquete)
    if d.get("access_token"):
        tok = d["access_token"]
    elif d.get("code"):
        r = http(f"{FB}/oauth/access_token", {"client_id": APP_ID, "client_secret": SECRETO,
                                             "redirect_uri": REDIRECT, "code": d["code"]})
        tok = r["access_token"]
    else:
        sys.exit("El paquete no trae permiso (¿el cliente tocó Cancelar?)")
    cliente = cliente or d.get("state") or ""
    tok, api = largo_plazo(tok)
    cs = cuentas_de(tok, api)
    if not cs:
        sys.exit("La llave no tiene ninguna cuenta de Instagram profesional asociada")
    for ig_id, usuario in cs:
        guardar(usuario, ig_id, tok, api, cliente)
        print(f"CONECTADA: @{usuario} (ig_id {ig_id}), llave de 60 días guardada cifrada")


def llave_de(fila):
    """La usa publicar.py: devuelve la llave en claro (solo en memoria)."""
    meta = json.loads(fernet().decrypt(open(os.path.join(AQUI, fila["llave"]), "rb").read()))
    return meta["llave"]


def renovar():
    for c in json.load(open(CUENTAS, encoding="utf-8")):
        if not c.get("llave"):
            continue
        ruta = os.path.join(AQUI, c["llave"])
        meta = json.loads(fernet().decrypt(open(ruta, "rb").read()))
        try:
            if meta["api"] == "ig":
                r = http(f"{IG}/refresh_access_token", {"grant_type": "ig_refresh_token", "access_token": meta["llave"]})
                meta["llave"] = r["access_token"]
            else:
                meta["llave"], _ = largo_plazo(meta["llave"])
            meta["renovada"] = datetime.datetime.now(ART).strftime("%Y-%m-%d %H:%M")
            open(ruta, "wb").write(fernet().encrypt(json.dumps(meta).encode()))
            print(f"Renovada @{c['usuario']}")
        except Exception as e:
            print(f"NO se pudo renovar @{c['usuario']}: {e}")


if __name__ == "__main__":
    accion = sys.argv[1] if len(sys.argv) > 1 else ""
    if accion == "claves":
        claves()
    elif accion == "conectar":
        conectar(os.environ.get("PAQUETE", ""), os.environ.get("CLIENTE", "").strip())
    elif accion == "renovar":
        renovar()
    else:
        sys.exit("uso: conectar.py claves|conectar|renovar")

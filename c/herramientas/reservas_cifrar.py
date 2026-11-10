"""Guarda las reservas de un cliente cifradas con su clave, para su informe.
Uso: CLAVE=xxxxxx python3 reservas_cifrar.py filas.json c/<carpeta-cliente>/reservas.enc.json
filas.json: lista de filas de la planilla [fecha dd/mm/aaaa, para cuándo, monto, ¿vino por Instagram?]
Solo se guardan las que dicen Sí en Instagram. Nunca imprime la clave.
"""
import json, os, sys, base64, re
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

clave = os.environ["CLAVE"]
filas = json.load(open(sys.argv[1], encoding="utf-8"))
res = []
for f in filas:
    f = [str(x).strip() for x in f] + [""] * 4
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", f[0])
    if not m or not f[3].lower().startswith("s"):
        continue
    monto = int(re.sub(r"[^\d]", "", f[2]) or 0)
    res.append({"registrada": f"{m[3]}-{int(m[2]):02d}-{int(m[1]):02d}", "para": f[1], "monto": monto, "origen": "Instagram"})
salt, iv = os.urandom(16), os.urandom(12)
k = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=200000).derive(clave.encode())
ct = AESGCM(k).encrypt(iv, json.dumps(res, ensure_ascii=False).encode(), None)
b = lambda x: base64.b64encode(x).decode()
json.dump({"salt": b(salt), "iv": b(iv), "data": b(ct), "iter": 200000}, open(sys.argv[2], "w"))
print("ok", len(res), "reservas, total", sum(r["monto"] for r in res))

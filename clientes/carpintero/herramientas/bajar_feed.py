"""Baja todas las fotos del feed de @elcarpintero3f (incluye cada imagen de los carruseles y la portada de los videos)
a clientes/carpintero/fotos/ig/, con un indice.json (fecha, tipo, texto y vistas) para elegir qué reutilizar.
Corre en GitHub Actions (ig-archivo-carpintero.yml) porque necesita la llave cifrada."""
import json, os, sys, urllib.parse, urllib.request
AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "quinta-ig", "publicador"))
import conectar  # noqa: E402

cuentas = json.load(open(os.path.join(REPO, "quinta-ig", "publicador", "cuentas.json"), encoding="utf-8"))
fila = next(c for c in cuentas if c["usuario"] == "elcarpintero3f")
TOKEN = conectar.llave_de(fila)
API = "https://graph.instagram.com/v23.0" if TOKEN.startswith("IG") else "https://graph.facebook.com/v23.0"
DEST = os.path.join(REPO, "clientes", "carpintero", "fotos", "ig")
os.makedirs(DEST, exist_ok=True)


def get(url, **p):
    if p:
        p["access_token"] = TOKEN
        url = url + "?" + urllib.parse.urlencode(p)
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read())


def bajar(url, nombre):
    ruta = os.path.join(DEST, nombre)
    if os.path.exists(ruta):
        return nombre
    with urllib.request.urlopen(url, timeout=120) as r, open(ruta, "wb") as f:
        f.write(r.read())
    return nombre


campos = "id,caption,media_type,media_product_type,timestamp,permalink,media_url,thumbnail_url,children{id,media_type,media_url,thumbnail_url}"
res = get(f"{API}/{fila['ig_id']}/media", fields=campos, limit=50)
items = res.get("data", [])
while res.get("paging", {}).get("next") and len(items) < 200:
    res = get(res["paging"]["next"])
    items += res.get("data", [])

indice = []
for m in items:
    fecha = m["timestamp"][:10]
    hijos = (m.get("children") or {}).get("data") or [m]
    archivos = []
    for k, h in enumerate(hijos):
        url = h.get("media_url") if h.get("media_type") == "IMAGE" else (h.get("thumbnail_url") or h.get("media_url"))
        if not url or h.get("media_type") == "VIDEO" and not h.get("thumbnail_url"):
            continue
        try:
            archivos.append(bajar(url, f"{fecha}-{m['id']}-{k + 1}.jpg"))
        except Exception as e:
            print("No se pudo bajar", m["id"], k, e)
    indice.append({"id": m["id"], "fecha": fecha, "tipo": m.get("media_product_type") or m.get("media_type"),
                   "texto": (m.get("caption") or "")[:300], "permalink": m.get("permalink"), "archivos": archivos})

# Foto de perfil (logo)
try:
    perfil = get(f"{API}/{fila['ig_id']}", fields="profile_picture_url,name,biography")
    os.makedirs(os.path.join(REPO, "clientes", "carpintero", "marca"), exist_ok=True)
    with urllib.request.urlopen(perfil["profile_picture_url"], timeout=60) as r, open(os.path.join(REPO, "clientes", "carpintero", "marca", "perfil-ig.jpg"), "wb") as f:
        f.write(r.read())
    print("Foto de perfil guardada")
except Exception as e:
    print("Sin foto de perfil:", e)

json.dump(indice, open(os.path.join(DEST, "indice.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{len(indice)} posteos, {sum(len(i['archivos']) for i in indice)} imágenes")

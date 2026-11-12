"""Publicador propio de Quinta El Florido (API de Instagram, gratis).
Lee cola.json, publica lo que ya tiene fecha vencida y estado "pendiente",
y anota el resultado. La llave viene del secret IG_TOKEN (nunca se imprime).

Cada item de cola.json:
  {"id": "texto-unico", "tipo": "STORY" | "POST" | "REEL" | "CARRUSEL",
   "media": ["quinta-ig/archivo.jpg", ...]  (ruta del repo o URL https),
   "texto": "caption (no aplica a historias)",
   "fecha": "2026-11-09 21:00"  (hora Argentina),
   "estado": "pendiente"}
"""
import json, os, sys, time, urllib.parse, urllib.request, datetime

API_FB = "https://graph.facebook.com/v23.0"
API_IG = "https://graph.instagram.com/v23.0"  # llaves del login de Instagram (empiezan con "IG")
API = API_FB
RAW = "https://raw.githubusercontent.com/macproia88/marcas/main/"
AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(AQUI, "..", ".."))
CUENTAS = os.path.join(AQUI, "cuentas.json")
IG_ID = TOKEN = COLA = ""  # se cargan por cuenta en main()


def elegir_api(token):
    """Llaves del login de Instagram usan graph.instagram.com; las de Facebook, graph.facebook.com."""
    global API
    API = API_IG if token.startswith("IG") else API_FB
ART = datetime.timezone(datetime.timedelta(hours=-3))


def llamar(metodo, ruta, **params):
    params["access_token"] = TOKEN
    datos = urllib.parse.urlencode(params).encode()
    url = f"{API}/{ruta}"
    if metodo == "GET":
        req = urllib.request.Request(url + "?" + datos.decode())
    else:
        req = urllib.request.Request(url, data=datos, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        cuerpo = e.read().decode(errors="ignore")
        try:
            msg = json.loads(cuerpo)["error"].get("message", cuerpo)
        except Exception:
            msg = cuerpo
        raise RuntimeError(msg[:300])


PAGES = "https://macproia88.github.io/marcas/"


def url_de(m):
    if m.startswith("http"):
        return m
    # Los videos van por GitHub Pages (sirve video/mp4); las fotos por raw.
    return (PAGES if es_video(m) else RAW) + m.lstrip("/")


def es_video(m):
    return m.lower().split("?")[0].endswith((".mp4", ".mov"))


def esperar(cid):
    time.sleep(3)
    for _ in range(40):  # hasta ~10 minutos
        st = llamar("GET", cid, fields="status_code,status")
        if st.get("status_code") == "FINISHED":
            return
        if st.get("status_code") in ("ERROR", "EXPIRED"):
            raise RuntimeError("Instagram no pudo procesar el archivo: " + str(st.get("status")))
        time.sleep(15)
    raise RuntimeError("Tiempo de espera agotado procesando el video")


ETIQUETAS = []  # usuarios a etiquetar en la foto (solo posts de una imagen)


def contenedor(m, tipo, texto=None, en_carrusel=False):
    p = {}
    if es_video(m):
        p["video_url"] = url_de(m)
        p["media_type"] = "STORIES" if tipo == "STORY" else "REELS"
    else:
        p["image_url"] = url_de(m)
        if tipo == "STORY":
            p["media_type"] = "STORIES"
    if en_carrusel:
        p["is_carousel_item"] = "true"
        if es_video(m):
            p["media_type"] = "VIDEO"
        else:
            p.pop("media_type", None)
    if texto and tipo != "STORY" and not en_carrusel:
        p["caption"] = texto
    if ETIQUETAS and tipo == "POST" and not en_carrusel and not es_video(m):
        p["user_tags"] = json.dumps([{"username": u, "x": round(0.2 + 0.6 * i / max(1, len(ETIQUETAS) - 1), 2), "y": 0.9}
                                     for i, u in enumerate(ETIQUETAS)])
    try:
        cid = llamar("POST", f"{IG_ID}/media", **p)["id"]
    except Exception:
        if "user_tags" not in p:
            raise
        p.pop("user_tags")  # si una etiqueta falla, se publica igual sin etiquetas
        cid = llamar("POST", f"{IG_ID}/media", **p)["id"]
    esperar(cid)  # siempre: si se publica antes de que esté listo da "Media ID is not available"
    return cid


def publicar(item):
    global ETIQUETAS
    ETIQUETAS = item.get("etiquetas") or []
    tipo, media = item["tipo"].upper(), item["media"]
    if tipo == "CARRUSEL":
        hijos = [contenedor(m, "POST", en_carrusel=True) for m in media]
        cid = llamar("POST", f"{IG_ID}/media", media_type="CAROUSEL",
                     children=",".join(hijos), caption=item.get("texto", ""))["id"]
        esperar(cid)
    else:
        cid = contenedor(media[0], tipo, item.get("texto"))
    pub = llamar("POST", f"{IG_ID}/media_publish", creation_id=cid)
    return pub["id"]


def main():
    global IG_ID, TOKEN, COLA
    for c in json.load(open(CUENTAS, encoding="utf-8")):
        if not c.get("activa", True):
            continue
        IG_ID, TOKEN = c.get("ig_id", ""), os.environ.get(c["secret"], "")
        elegir_api(TOKEN)
        COLA = os.path.join(REPO, c["cola"])
        print(f"=== {c['nombre']} ===")
        if not TOKEN or not IG_ID:
            print(f"  Falta el secret {c['secret']} o el ig_id: se saltea")
            continue
        if not os.path.exists(COLA):
            print("  Sin cola todavía")
            continue
        # Candado: la llave tiene que ser de la cuenta que dice cuentas.json
        try:
            quien = llamar("GET", IG_ID, fields="username").get("username", "")
        except Exception as e:
            print(f"  No se pudo confirmar la cuenta ({e}): no se publica nada")
            continue
        if quien.lower() != c["usuario"].lower():
            print(f"  CANDADO: la llave es de @{quien} y esta fila es de @{c['usuario']}: no se publica nada")
            continue
        procesar_cuenta()


def procesar_cuenta():
    cola = json.load(open(COLA, encoding="utf-8"))
    ahora = datetime.datetime.now(ART)
    cambios = False
    for item in cola:
        if item.get("estado") != "pendiente":
            continue
        cuando = datetime.datetime.strptime(item["fecha"], "%Y-%m-%d %H:%M").replace(tzinfo=ART)
        if cuando > ahora:
            continue
        print(f"Publicando {item['id']} ({item['tipo']})...")
        try:
            mid = publicar(item)
            item.update(estado="publicado", ig_media_id=mid,
                        publicado_el=datetime.datetime.now(ART).strftime("%Y-%m-%d %H:%M"))
            print("  OK", mid)
        except Exception as e:
            item.update(estado="error", error=str(e)[:300],
                        intento=datetime.datetime.now(ART).strftime("%Y-%m-%d %H:%M"))
            print("  ERROR", e)
        cambios = True
    try:
        lim = llamar("GET", f"{IG_ID}/content_publishing_limit", fields="quota_usage,config")
        print("Cupo usado en 24 h:", json.dumps(lim.get("data", lim)))
    except Exception as e:
        print("No se pudo leer el cupo:", e)
    if cambios:
        json.dump(cola, open(COLA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def probar():
    """Crea los contenedores de los videos pendientes (sin publicar) para ver si Instagram los acepta."""
    global IG_ID, TOKEN, COLA
    for c in json.load(open(CUENTAS, encoding="utf-8")):
        IG_ID, TOKEN = c.get("ig_id", ""), os.environ.get(c["secret"], "")
        elegir_api(TOKEN)
        COLA = os.path.join(REPO, c["cola"])
        if not (IG_ID and TOKEN and os.path.exists(COLA)):
            continue
        for item in json.load(open(COLA, encoding="utf-8")):
            if item.get("estado") == "pendiente" and any(es_video(m) for m in item["media"]):
                try:
                    contenedor(item["media"][0], item["tipo"].upper(), item.get("texto"))
                    print(f"PRUEBA OK {item['id']}")
                except Exception as e:
                    print(f"PRUEBA ERROR {item['id']}: {e}")


if __name__ == "__main__":
    probar() if "--probar" in sys.argv else main()

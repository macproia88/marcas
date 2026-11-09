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

IG_ID = "17841454960836233"
API = "https://graph.facebook.com/v23.0"
RAW = "https://raw.githubusercontent.com/macproia88/marcas/main/"
TOKEN = os.environ.get("IG_TOKEN", "")
COLA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cola.json")
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


def url_de(m):
    return m if m.startswith("http") else RAW + m.lstrip("/")


def es_video(m):
    return m.lower().split("?")[0].endswith((".mp4", ".mov"))


def esperar(cid):
    for _ in range(40):  # hasta ~10 minutos
        st = llamar("GET", cid, fields="status_code,status")
        if st.get("status_code") == "FINISHED":
            return
        if st.get("status_code") in ("ERROR", "EXPIRED"):
            raise RuntimeError("Instagram no pudo procesar el archivo: " + str(st.get("status")))
        time.sleep(15)
    raise RuntimeError("Tiempo de espera agotado procesando el video")


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
    cid = llamar("POST", f"{IG_ID}/media", **p)["id"]
    if es_video(m) or tipo == "STORY":
        esperar(cid)
    return cid


def publicar(item):
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
    if not TOKEN:
        sys.exit("Falta el secret IG_TOKEN")
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


if __name__ == "__main__":
    main()

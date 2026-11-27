"""Busca un posteo propio por su código (el de la URL /reel/XXXX/) y baja el video/fotos al repo.
Uso (en Actions): METRICAS_USUARIO=... METRICAS_IG=... python3 bajar_post.py CODIGO carpeta_destino"""
import json, os, sys, urllib.request
sys.argv += []
codigo, destino = sys.argv[1], sys.argv[2]
import metricas as m
os.makedirs(destino, exist_ok=True)
url = f"{m.IG}/media"; p = {"fields": "id,shortcode,permalink,media_type,media_url,thumbnail_url,timestamp,caption,children{media_type,media_url}", "limit": 50}
encontrado = None; pag = 0
while url and pag < 40 and not encontrado:
    r = m.get(url, **p) if pag == 0 else json.loads(urllib.request.urlopen(url, timeout=60).read())
    for it in r.get("data", []):
        if it.get("shortcode") == codigo or codigo in (it.get("permalink") or ""):
            encontrado = it; break
    url = (r.get("paging") or {}).get("next"); pag += 1
if not encontrado:
    sys.exit(f"No encontré {codigo} en {pag} páginas")
info = {k: v for k, v in encontrado.items() if k not in ("media_url", "thumbnail_url", "children")}
json.dump(info, open(os.path.join(destino, "info.json"), "w"), ensure_ascii=False, indent=1)
print(info["timestamp"], info["media_type"], (info.get("caption") or "")[:200])
archivos = [encontrado] + [c for c in (encontrado.get("children") or {}).get("data", [])]
for i, a in enumerate(archivos):
    u = a.get("media_url")
    if not u: continue
    ext = "mp4" if a.get("media_type") == "VIDEO" else "jpg"
    urllib.request.urlretrieve(u, os.path.join(destino, f"{i}.{ext}"))
    print("bajado", i, ext)

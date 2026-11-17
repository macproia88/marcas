"""Baja las fotos de Mercado Libre del catálogo y las guarda dentro del repo (catalogo/p/), así la página
no depende de Mercado Libre y carga bien en cualquier celular. Reescribe las rutas en catalogo/index.html.
Corre en GitHub Actions (ig-fotos-catalogo.yml) porque desde acá no hay salida a mlstatic."""
import hashlib, io, json, os, re, urllib.request
from PIL import Image
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "catalogo")
HTML = os.path.join(BASE, "index.html")
s = open(HTML, encoding="utf-8").read()
urls = sorted(set(re.findall(r'https://http2\.mlstatic\.com/[^"\\]+', s)))
os.makedirs(os.path.join(BASE, "p"), exist_ok=True)
ok = 0
for u in urls:
    nombre = hashlib.md5(u.encode()).hexdigest()[:12] + ".jpg"
    ruta = os.path.join(BASE, "p", nombre)
    if not os.path.exists(ruta):
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
            im = Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=60).read())).convert("RGB")
            im.thumbnail((700, 700))
            im.save(ruta, quality=82, optimize=True, progressive=True)
        except Exception as e:
            print("falló", u, e); continue
    s = s.replace(u, "p/" + nombre); ok += 1
open(HTML, "w", encoding="utf-8").write(s)
print(ok, "de", len(urls), "fotos guardadas")

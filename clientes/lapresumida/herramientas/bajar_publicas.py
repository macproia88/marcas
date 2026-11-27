"""Baja la foto de portada de publicaciones públicas de @lapresumidapastas (para armar la propuesta).
Lee los códigos de posteo de ids.txt y guarda fotos/ig/<codigo>.jpg + indice.json con el título."""
import os, re, json, html, urllib.request
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "fotos", "ig"); os.makedirs(OUT, exist_ok=True)
ids = open(os.path.join(BASE, "herramientas", "ids.txt")).read().split()
UAS = ["facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
       "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"]
idx = {}
for c in ids:
    ok = False
    for ua in UAS:
        try:
            req = urllib.request.Request(f"https://www.instagram.com/p/{c}/", headers={"User-Agent": ua, "Accept-Language": "es-AR"})
            h = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")
            m = re.search(r'<meta property="og:image" content="([^"]+)"', h)
            t = re.search(r'<meta property="og:description" content="([^"]*)"', h) or re.search(r'<meta property="og:title" content="([^"]*)"', h)
            if not m: continue
            u = html.unescape(m.group(1))
            img = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": ua}), timeout=30).read()
            open(os.path.join(OUT, c + ".jpg"), "wb").write(img)
            idx[c] = {"texto": html.unescape(t.group(1)) if t else "", "bytes": len(img)}
            ok = True; break
        except Exception as e:
            print(c, ua[:12], e)
    print(c, "ok" if ok else "FALLO")
json.dump(idx, open(os.path.join(OUT, "indice.json"), "w"), ensure_ascii=False, indent=1)
print(len(idx), "bajadas")

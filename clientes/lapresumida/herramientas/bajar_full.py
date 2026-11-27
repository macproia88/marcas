"""Baja en 1080 las fotos de urls_full.json (URLs tomadas del embed público) a fotos/full/."""
import os, json, urllib.request
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
O = os.path.join(B, "fotos", "full"); os.makedirs(O, exist_ok=True)
for k, u in json.load(open(os.path.join(B, "herramientas", "urls_full.json"))).items():
    try:
        d = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read()
        open(os.path.join(O, k + ".jpg"), "wb").write(d); print(k, len(d))
    except Exception as e:
        print(k, "FALLO", e)

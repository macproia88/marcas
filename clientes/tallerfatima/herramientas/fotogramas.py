"""Saca fotos fijas en alta calidad de un video, en los momentos pedidos.
Para cada momento prueba 5 fotogramas (±2 s) y se queda con el más nítido.
Uso: python3 fotogramas.py video.mp4 carpeta_salida factor  t1 t2 ...
(t = segundos en la versión acelerada; se multiplican por el factor para ir al original)
"""
import sys, subprocess, os
import numpy as np
from PIL import Image, ImageFilter
v, out, fac = sys.argv[1], sys.argv[2], float(sys.argv[3])
os.makedirs(out, exist_ok=True)
for t in sys.argv[4:]:
    base = float(t) * fac; mejor = None
    for d in (-2, -1, 0, 1, 2):
        tmp = f"/tmp/fg_{d}.png"
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", str(max(0, base + d)), "-i", v, "-frames:v", "1", tmp], check=False)
        if not os.path.exists(tmp): continue
        im = Image.open(tmp).convert("L")
        nit = np.asarray(im.filter(ImageFilter.FIND_EDGES), dtype=float).var()
        if mejor is None or nit > mejor[0]: mejor = (nit, Image.open(tmp).convert("RGB"))
    if mejor:
        nombre = f"{out}/cuadro-{float(t):05.1f}.jpg"
        mejor[1].save(nombre, quality=88); print(nombre, mejor[1].size)

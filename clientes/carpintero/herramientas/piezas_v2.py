"""Estilo 2 de El carpintero3 (pedido del cliente el 17/11/2026, con referencias tipo @justwoodd).
- La foto del mueble limpia y entera: sin recuadros, sin franjas negras ni amarillas, sin texto encima.
- Solo una firma chica "EL CARPINTERO3" en una esquina, en blanco con sombra suave.
- Toda la información va en el texto del posteo (sin "24 hs").
Uso: python3 piezas_v2.py
"""
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageEnhance

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = os.path.join(BASE, "fotos")
OUT = os.path.join(BASE, "img", "v2")
os.makedirs(OUT, exist_ok=True)
FUENTE = os.path.join(BASE, "herramientas", "fuentes", "Inter-SemiBold.otf")
# Recortes fijos para sacar marcas de agua de IA y botones de capturas de pantalla
RECORTE = {"banquetas-soga-cocina.jpg": (0, 140, 1206, 1561), "banqueta-tapizada-ia.jpg": (0, 0, 1024, 1265),
           "frente-local-ia.jpg": (0, 0, 1024, 1262), "sillon-soga-mesita-showroom-ia.jpg": (0, 0, 896, 1135),
           "comedor-varillas-ia.jpg": (0, 0, 1192, 845), "silla-curva-alfombra.jpg": (0, 0, 1206, 1322)}


def gradar(im):
    """Look premium y parejo: tonos cálidos suaves, negros apenas levantados, color un poco más sobrio y viñeta leve."""
    import numpy as np
    a = np.asarray(im).astype("float32") / 255.0
    a = 0.035 + a * 0.95                      # negros levantados, luces sin quemar
    a = np.clip((a - 0.5) * 1.06 + 0.5, 0, 1)  # un toque de contraste
    g = a.mean(axis=2, keepdims=True)
    a = g + (a - g) * 0.90                     # saturación más sobria
    a[..., 0] *= 1.025; a[..., 2] *= 0.975     # calidez de madera
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    r = ((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2
    a *= (1 - 0.07 * np.clip(r - 0.35, 0, 1))[..., None]
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype("uint8"))


def preparar(nombre, w, h, centro=(0.5, 0.5), caja=None):
    im = ImageOps.exif_transpose(Image.open(os.path.join(F, nombre))).convert("RGB")
    caja = caja or RECORTE.get(nombre)
    if caja:
        im = im.crop(caja)
    im = ImageOps.fit(im, (w, h), Image.LANCZOS, centering=centro)
    im = gradar(im)
    return im.filter(ImageFilter.UnsharpMask(radius=1.6, percent=40, threshold=3))


def firma(im):
    """Firma premium: EL CARPINTERO 3 en letra fina y espaciada, blanca con sombra difusa, sin caja."""
    w, h = im.size
    f = ImageFont.truetype(os.path.join(BASE, "herramientas", "fuentes", "Inter-Light.otf"), 22)
    letras = list("EL CARPINTERO 3")
    esp = 5
    d0 = ImageDraw.Draw(im)
    tw = sum(d0.textlength(c, font=f) for c in letras) + esp * (len(letras) - 1)
    x0, y = w - tw - 44, h - 62
    capa = Image.new("L", im.size, 0); dc = ImageDraw.Draw(capa)
    x = x0
    for c in letras:
        dc.text((x, y), c, font=f, fill=255); x += d0.textlength(c, font=f) + esp
    dc.line([(x0, y - 12), (x0 + 34, y - 12)], fill=255, width=1)
    sombra = capa.filter(ImageFilter.GaussianBlur(7)).point(lambda v: int(v * 0.55))
    im.paste((0, 0, 0), (0, 0), sombra)
    im.paste((255, 255, 255), (0, 0), capa)
    return im


def pieza(nombre, salida, w=1080, h=1350, centro=(0.5, 0.5), caja=None):
    firma(preparar(nombre, w, h, centro, caja)).save(os.path.join(OUT, salida), quality=93)


def historia(nombre, salida, caja=None):
    """Historia 1080x1920 sin recortar el mueble: la foto entera al medio y, arriba y abajo,
    la misma foto ampliada y desenfocada (no hay franjas ni recuadros de color)."""
    im = ImageOps.exif_transpose(Image.open(os.path.join(F, nombre))).convert("RGB")
    caja = caja or RECORTE.get(nombre)
    if caja:
        im = im.crop(caja)
    fondo = ImageOps.fit(im, (1080, 1920), Image.LANCZOS).filter(ImageFilter.GaussianBlur(40))
    fondo = ImageEnhance.Brightness(fondo).enhance(0.92)
    frente = im.copy(); frente.thumbnail((1080, 1920), Image.LANCZOS)
    frente = frente.resize((1080, int(frente.height * 1080 / frente.width)), Image.LANCZOS)
    fondo.paste(frente, (0, (1920 - frente.height) // 2))
    fondo = gradar(fondo)
    firma(fondo).save(os.path.join(OUT, salida), quality=93)


if __name__ == "__main__":
    # Prueba 1: carrusel de mesas con base de varillas (fotos en casas de clientes)
    pieza("mesa-ovalada-varillas-casa.jpg", "prueba-mesas-1.jpg", centro=(0.5, 0.6))
    pieza("mesa-rectangular-varillas-casa.jpg", "prueba-mesas-2.jpg", centro=(0.5, 0.55))
    # Prueba 2: posteo de la silla de brazos curvos
    pieza("silla-curva-alfombra.jpg", "prueba-silla.jpg", centro=(0.5, 0.5), caja=(0, 0, 1206, 1322))
    # Prueba 3: historia vertical del sillón de soga
    historia("sillon-soga-ia.jpg", "prueba-historia-sillon.jpg")
    print("Listo")


def reel(fotos, salida, seg=3.0):
    """Reel 1080x1920 con las fotos enteras (fondo desenfocado de la misma foto), zoom lento, firma chica y música.
    Sin títulos ni placas de color."""
    import subprocess, sys, tempfile
    tmp = tempfile.mkdtemp()
    partes = []
    for k, (nombre, caja) in enumerate(fotos):
        historia(nombre, f"_reel_{k}.jpg", caja)
        src = os.path.join(OUT, f"_reel_{k}.jpg")
        n = int(seg * 30)
        dst = f"{tmp}/p{k}.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", src, "-vf",
                        f"scale=2160:3840,zoompan=z='1+0.0008*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s=1080x1920:fps=30,format=yuv420p,setsar=1",
                        "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", dst], check=True)
        os.remove(src)
        partes.append(dst)
    ent = sum((["-i", p] for p in partes), [])
    cad = "".join(f"[{i}:v]" for i in range(len(partes))) + f"concat=n={len(partes)}:v=1[v]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ent, "-filter_complex", cad, "-map", "[v]", "-c:v", "libx264",
                    "-preset", "veryfast", "-crf", "20", f"{tmp}/c.mp4"], check=True)
    dur = len(fotos) * seg
    musica = os.path.join(BASE, "..", "tallerfatima", "herramientas", "musica.py")
    subprocess.run([sys.executable, musica, f"{tmp}/m.wav", str(dur + 0.5)], check=True)
    os.makedirs(os.path.join(BASE, "videos", "v2"), exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{tmp}/c.mp4", "-i", f"{tmp}/m.wav", "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-af", f"afade=t=out:st={dur - 1.5}:d=1.5", "-shortest",
                    "-movflags", "+faststart", os.path.join(BASE, "videos", "v2", salida)], check=True)


def semana():
    S = (0, 0, 1206, 1322)  # silla: sin el ícono de sonido de la captura
    # Feed (4:5)
    pieza("mesa-ovalada-varillas-casa.jpg", "1117-mesas-1.jpg", centro=(0.5, 0.6))
    pieza("mesa-rectangular-varillas-casa.jpg", "1117-mesas-2.jpg", centro=(0.5, 0.55))
    pieza("silla-curva-alfombra.jpg", "1118-silla.jpg", caja=S)
    pieza("banquetas-soga-cocina.jpg", "1119-banquetas-1.jpg", centro=(0.5, 0.55))
    pieza("banqueta-tapizada-ia.jpg", "1119-banquetas-2.jpg", centro=(0.5, 0.6))
    pieza("sillon-soga-ia.jpg", "1120-soga-1.jpg", centro=(0.5, 0.55))
    pieza("sillon-soga-mesita-showroom-ia.jpg", "1120-soga-2.jpg", centro=(0.5, 0.65))
    pieza("comedor-varillas-ia.jpg", "1121-comedor.jpg", w=1080, h=810)
    # Historias (mueble entero)
    for dia, foto, caja in (("1117", "mesa-ovalada-varillas-casa.jpg", None), ("1118", "silla-curva-alfombra.jpg", S),
                            ("1119", "banquetas-soga-cocina.jpg", None), ("1120", "sillon-soga-mesita-showroom-ia.jpg", None),
                            ("1121", "banqueta-tapizada-ia.jpg", None), ("1122", "sillon-soga-ia.jpg", None),
                            ("1123", "mesa-rectangular-varillas-casa.jpg", None)):
        historia(foto, f"{dia}-historia.jpg", caja)
    # Reels
    reel([("mesa-ovalada-varillas-casa.jpg", None), ("comedor-varillas-ia.jpg", None), ("mesa-rectangular-varillas-casa.jpg", None)], "1119-reel-mesas.mp4")
    reel([("sillon-soga-ia.jpg", None), ("sillon-soga-mesita-showroom-ia.jpg", None), ("banquetas-soga-cocina.jpg", None), ("silla-curva-alfombra.jpg", S)], "1121-reel-madera.mp4")


if __name__ == "__main__":
    import sys
    if "--semana" in sys.argv:
        semana()
        print("Semana lista")

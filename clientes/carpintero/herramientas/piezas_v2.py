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


def preparar(nombre, w, h, centro=(0.5, 0.5), caja=None):
    im = ImageOps.exif_transpose(Image.open(os.path.join(F, nombre))).convert("RGB")
    caja = caja or RECORTE.get(nombre)
    if caja:
        im = im.crop(caja)
    im = ImageOps.fit(im, (w, h), Image.LANCZOS, centering=centro)
    im = ImageEnhance.Contrast(im).enhance(1.03)
    return im.filter(ImageFilter.UnsharpMask(radius=1.6, percent=45, threshold=3))


def firma(im):
    """Firma chica abajo a la derecha, blanca con sombra difusa (sin caja)."""
    w, h = im.size
    f = ImageFont.truetype(FUENTE, 26)
    t = "EL CARPINTERO3"
    d0 = ImageDraw.Draw(im)
    tw = d0.textlength(t, font=f)
    x, y = w - tw - 40, h - 64
    sombra = Image.new("L", im.size, 0)
    ImageDraw.Draw(sombra).text((x, y + 2), t, font=f, fill=150)
    sombra = sombra.filter(ImageFilter.GaussianBlur(6))
    im.paste((0, 0, 0), (0, 0), sombra)
    ImageDraw.Draw(im).text((x, y), t, font=f, fill=(255, 255, 255))
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
    pieza("frente-local-ia.jpg", "1122-showroom.jpg", centro=(0.5, 0.6))
    # Historias (mueble entero)
    for dia, foto, caja in (("1117", "mesa-ovalada-varillas-casa.jpg", None), ("1118", "silla-curva-alfombra.jpg", S),
                            ("1119", "banquetas-soga-cocina.jpg", None), ("1120", "sillon-soga-mesita-showroom-ia.jpg", None),
                            ("1121", "frente-local-ia.jpg", None), ("1122", "comedor-varillas-ia.jpg", None),
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

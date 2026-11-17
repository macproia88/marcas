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
RECORTE = {"mesa-redonda-cruz-captura.jpg": (0, 245, 720, 1205), "banquetas-soga-cocina.jpg": (0, 140, 1206, 1561), "banqueta-tapizada-ia.jpg": (0, 0, 1024, 1265),
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


def dibujar_sello(im, x0, base, vidrio=True):
    """Dos pastillas apiladas abajo a la izquierda: verde WhatsApp grande y blanca con la dirección."""
    fb = ImageFont.truetype(os.path.join(BASE, "herramientas", "fuentes", "Inter-Bold.otf"), 40)
    fr = ImageFont.truetype(os.path.join(BASE, "herramientas", "fuentes", "Inter-Medium.otf"), 27)
    t1, t2 = "WhatsApp 11 4194-3328", "Román Gómez 1893, José Ingenieros"
    d = ImageDraw.Draw(im)
    w1 = d.textlength(t1, font=fb) + 108; h1 = 74
    w2 = d.textlength(t2, font=fr) + 88; h2 = 54
    y2 = base - h2; y1 = y2 - 12 - h1
    if vidrio and im.mode == "RGB":
        zona = im.crop((x0, y2, int(x0 + w2), base)).filter(ImageFilter.GaussianBlur(14))
        zona = Image.blend(zona, Image.new("RGB", zona.size, (255, 255, 255)), 0.85)
        m = Image.new("L", zona.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, zona.width - 1, zona.height - 1], 27, fill=255)
        im.paste(zona, (x0, y2), m)
    else:
        d.rounded_rectangle([x0, y2, x0 + w2, base], 27, fill=(255, 255, 255, 235))
    px, py = x0 + 33, y2 + 29
    d.ellipse([px - 11, py - 17, px + 11, py + 5], fill=(28, 26, 25))
    d.polygon([(px - 10, py - 3), (px + 10, py - 3), (px, py + 13)], fill=(28, 26, 25))
    d.ellipse([px - 4, py - 10, px + 4, py - 2], fill=(255, 255, 255))
    d.text((x0 + 58, y2 + 12), t2, font=fr, fill=(40, 36, 33))
    d.rounded_rectangle([x0, y1, x0 + w1, y1 + h1], 37, fill=(37, 211, 102))
    cx, cy = x0 + 46, y1 + h1 // 2
    d.ellipse([cx - 20, cy - 20, cx + 20, cy + 20], outline=(255, 255, 255), width=4)
    d.polygon([(cx - 17, cy + 11), (cx - 23, cy + 24), (cx - 6, cy + 18)], fill=(255, 255, 255))
    d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=(255, 255, 255))
    d.text((x0 + 84, y1 + 14), t1, font=fb, fill=(255, 255, 255))
    return im


def sello(im, k=1.0):
    if k == 1.0:
        return dibujar_sello(im, 34, im.size[1] - 36)
    # Historias: el mismo sello, más grande (dibujado chico y ampliado)
    w, h = im.size
    capa = Image.new("RGBA", (int(w / k), int(h / k)), (0, 0, 0, 0))
    dibujar_sello(capa, 30, capa.size[1] - 150, vidrio=False)
    capa = capa.resize((w, h), Image.LANCZOS)
    base = im.convert("RGBA"); base.alpha_composite(capa)
    return base.convert("RGB")


def reel_video(origen, salida):
    """Reel con el video real del cliente: 1080x1920, sello y firma superpuestos, música."""
    import subprocess, sys, tempfile
    tmp = tempfile.mkdtemp()
    capa = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    dibujar_sello(capa, 34, 1920 - 150, vidrio=False)
    f = ImageFont.truetype(os.path.join(BASE, "herramientas", "fuentes", "Inter-Light.otf"), 24)
    ImageDraw.Draw(capa).text((1080 - 360, 1920 - 200), "E L   C A R P I N T E R O   3", font=f, fill=(255, 255, 255, 230))
    capa.save(f"{tmp}/capa.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", origen, "-i", f"{tmp}/capa.png", "-filter_complex",
                    "[0:v]scale=1080:1920:flags=lanczos,setsar=1,fps=30,eq=saturation=0.92:contrast=1.04[v];[v][1:v]overlay=0:0,format=yuv420p",
                    "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", f"{tmp}/a.mp4"], check=True)
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{tmp}/a.mp4"]))
    musica = os.path.join(BASE, "..", "tallerfatima", "herramientas", "musica.py")
    subprocess.run([sys.executable, musica, f"{tmp}/m.wav", str(dur + 0.5)], check=True)
    os.makedirs(os.path.join(BASE, "videos", "v2"), exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{tmp}/a.mp4", "-i", f"{tmp}/m.wav", "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-af", f"afade=t=out:st={dur - 1.5}:d=1.5", "-shortest",
                    "-movflags", "+faststart", os.path.join(BASE, "videos", "v2", salida)], check=True)


def pieza(nombre, salida, w=1080, h=1350, centro=(0.5, 0.5), caja=None):
    sello(firma(preparar(nombre, w, h, centro, caja))).save(os.path.join(OUT, salida), quality=93)


def historia(nombre, salida, caja=None, titulo=None):
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
    if titulo:
        d = ImageDraw.Draw(fondo)
        ft = ImageFont.truetype(os.path.join(BASE, "herramientas", "fuentes", "Inter-Light.otf"), 78)
        capa = Image.new("L", fondo.size, 0); ImageDraw.Draw(capa).text((70, 150), titulo, font=ft, fill=255)
        fondo.paste((0, 0, 0), (0, 0), capa.filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.5)))
        d.text((70, 150), titulo, font=ft, fill=(255, 255, 255))
    sello(firma(fondo), k=1.45).save(os.path.join(OUT, salida), quality=93)


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
    """Semana del 17 al 23/11: ninguna foto se repite y se alternan mesas, sillones, pino, banquetas y sillas."""
    pieza("mesa-ovalada-varillas-casa.jpg", "1117-mesas-1.jpg", centro=(0.5, 0.6))
    pieza("mesa-rectangular-varillas-casa.jpg", "1117-mesas-2.jpg", centro=(0.5, 0.55))
    pieza("alacena-pino-vereda.jpg", "1118-pino.jpg", centro=(0.5, 0.55))
    pieza("sillon-soga-ia.jpg", "1119-sillones-1.jpg", centro=(0.5, 0.55))
    pieza("sillon-1c-gris.jpg", "1119-sillones-2.jpg", centro=(0.5, 0.55))
    pieza("sillones-colores.jpg", "1119-sillones-3.jpg", centro=(0.5, 0.5))
    pieza("silla-curva-alfombra.jpg", "1120-silla.jpg")
    pieza("living-negro.jpg", "1121-living-1.jpg", centro=(0.5, 0.6))
    pieza("sillon-beige-mesita.jpg", "1121-living-2.jpg", centro=(0.3, 0.5))
    pieza("sillon-soga-mesita-showroom-ia.jpg", "1121-living-3.jpg", centro=(0.5, 0.65))
    pieza("comedor-varillas-4-sillas.jpg", "1123-comedores-1.jpg", centro=(0.5, 0.55))
    pieza("comedor-varillas-6-sillas.jpg", "1123-comedores-2.jpg", centro=(0.5, 0.6))
    for dia, foto, tit in (("1117", "banquetas-soga-cocina.jpg", None), ("1118", "sillon-2c-azul.jpg", None),
                           ("1119", "mesa-varillas.jpg", None), ("1120", "silla-soga.jpg", None),
                           ("1121", "mesa-ratona-estante.jpg", None), ("1122", "banqueta-tapizada-ia.jpg", None),
                           ("1123", "mesa-redonda-cruz-captura.jpg", "Buen lunes")):
        historia(foto, f"{dia}-historia.jpg", titulo=tit)
    reel_video(os.path.join(F, "video-1.mp4"), "1122-reel-banqueta.mp4")


if __name__ == "__main__":
    import sys
    if "--semana" in sys.argv:
        semana()
        print("Semana lista")

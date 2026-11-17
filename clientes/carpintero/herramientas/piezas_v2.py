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


def preparar(nombre, w, h, centro=(0.5, 0.5), caja=None):
    im = ImageOps.exif_transpose(Image.open(os.path.join(F, nombre))).convert("RGB")
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

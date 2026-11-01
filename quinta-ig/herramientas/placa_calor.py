"""Placa de calor para Quinta El Florido.
Uso: python3 -I placa_calor.py FOTO TEMPERATURA "TITULO" SALIDA_FEED SALIDA_HISTORIA
  FOTO: foto de la pileta (cualquier tamaño, idealmente ya mejorada)
  TEMPERATURA: número, ej 34
  TITULO: ej "MAÑANA" o "SÁBADO" (se muestra arriba de la temperatura)
Genera feed 1080x1350 y historia 1080x1920. Sin emojis (las fuentes no los dibujan).
"""
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SANS_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
VERDE = (37, 211, 102)
NARANJA = (255, 122, 26)


def cubrir(img, W, H):
    r = max(W / img.width, H / img.height)
    img = img.resize((round(img.width * r), round(img.height * r)), Image.LANCZOS)
    x, y = (img.width - W) // 2, (img.height - H) // 2
    return img.crop((x, y, x + W, y + H))


def degradado(W, H, alto, desde_arriba=True, alfa=200):
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    for i in range(alto):
        a = int(alfa * (1 - i / alto) ** 1.4)
        y = i if desde_arriba else H - 1 - i
        d.line([(0, y), (W, y)], fill=(0, 0, 0, a))
    return capa


def centrado(d, W, y, texto, fuente, color, sombra=True):
    w = d.textlength(texto, font=fuente)
    if sombra:
        d.text(((W - w) / 2 + 3, y + 3), texto, font=fuente, fill=(0, 0, 0, 160))
    d.text(((W - w) / 2, y), texto, font=fuente, fill=color)


def pastilla(d, W, y, texto, fuente, fondo, color=(255, 255, 255), pad=(44, 22)):
    w = d.textlength(texto, font=fuente)
    b = fuente.getbbox(texto)
    h = b[3] - b[1]
    x0 = (W - w) / 2 - pad[0]
    d.rounded_rectangle([x0, y, x0 + w + 2 * pad[0], y + h + 2 * pad[1]], radius=(h + 2 * pad[1]) // 2, fill=fondo)
    d.text(((W - w) / 2, y + pad[1] - b[1]), texto, font=fuente, fill=color)
    return y + h + 2 * pad[1]


def placa(foto, temp, titulo, W, H):
    img = cubrir(Image.open(foto).convert("RGB"), W, H).convert("RGBA")
    img.alpha_composite(degradado(W, H, int(H * 0.50), True, 215))
    img.alpha_composite(degradado(W, H, int(H * 0.38), False, 225))
    d = ImageDraw.Draw(img)
    esc = W / 1080
    top = int(H * (0.05 if H < 1600 else 0.09))
    centrado(d, W, top, "Quinta El Florido", ImageFont.truetype(SERIF, int(46 * esc)), (255, 255, 255))
    centrado(d, W, top + int(95 * esc), titulo.upper(), ImageFont.truetype(SANS, int(78 * esc)), (255, 255, 255))
    centrado(d, W, top + int(175 * esc), f"{temp}°", ImageFont.truetype(SANS, int(250 * esc)), NARANJA)
    centrado(d, W, top + int(455 * esc), "¿Ya tenés pileta?", ImageFont.truetype(SERIF, int(70 * esc)), (255, 255, 255))
    y = H - int((330 if H < 1600 else 420) * esc)
    y = pastilla(d, W, y, "Pileta · Quincho · Parrilla", ImageFont.truetype(SANS_R, int(40 * esc)), (0, 0, 0, 150), pad=(36, 16))
    y = pastilla(d, W, y + int(22 * esc), "Desde $140.000 el día", ImageFont.truetype(SANS, int(54 * esc)), NARANJA)
    pastilla(d, W, y + int(22 * esc), "WhatsApp 11 3877-7015", ImageFont.truetype(SANS, int(50 * esc)), VERDE)
    return img.convert("RGB")


if __name__ == "__main__":
    foto, temp, titulo, feed, hist = sys.argv[1:6]
    placa(foto, temp, titulo, 1080, 1350).save(feed, quality=93)
    placa(foto, temp, titulo, 1080, 1920).save(hist, quality=93)
    print("ok", feed, hist)

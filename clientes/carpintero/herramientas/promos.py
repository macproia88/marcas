"""Piezas de promoción (historias 1080x1920 y post 1080x1350): fondo cálido de estudio, la foto entera
en una tarjeta con sombra (sin tapar el mueble), nombre grande, precio grande y sello de WhatsApp + dirección."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
import piezas_v2 as pv

FU = os.path.join(pv.BASE, "herramientas", "fuentes")
def f(n, s): return ImageFont.truetype(os.path.join(FU, n), s)
TX, MU, TERRA = (31, 27, 22), (122, 113, 104), (168, 67, 42)
OUT = os.path.join(pv.BASE, "img", "promos"); os.makedirs(OUT, exist_ok=True)


def tarjeta(im, w, h, radio=34):
    im = im.copy(); im.thumbnail((w, h), Image.LANCZOS)
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, *im.size), radio, fill=255)
    return im, m


def pieza(foto, salida, etiqueta, nombre, detalle, precio, previo=None, desde=False, ancho=1080, alto=1920, caja=None, ml=None, estudio=False):
    lienzo = pv.fondo_estudio(ancho, alto, piso=0.999).convert("RGB")
    d = ImageDraw.Draw(lienzo)
    k = ancho / 1080
    x0, y = int(70 * k), int((150 if alto > 1500 else 70) * k)
    # Etiqueta
    fe = f("Inter-Bold.otf", int(30 * k)); tw = d.textlength(etiqueta, font=fe)
    d.rounded_rectangle((x0, y, x0 + tw + 44 * k, y + 56 * k), 28 * k, fill=TERRA)
    d.text((x0 + 22 * k, y + 28 * k), etiqueta, font=fe, fill="white", anchor="lm")
    y += int(86 * k)
    fn = f("Inter-SemiBold.otf", int(70 * k))
    for linea in nombre.split("\n"):
        d.text((x0, y), linea, font=fn, fill=TX); y += int(82 * k)
    d.text((x0, y + 6 * k), detalle, font=f("Inter-Regular.otf", int(33 * k)), fill=MU); y += int(70 * k)
    # Precio
    if desde:
        d.text((x0, y + 8 * k), "desde", font=f("Inter-Medium.otf", int(34 * k)), fill=TX); px = x0 + 118 * k
    else:
        px = x0
    fp = f("Inter-Bold.otf", int(104 * k))
    d.text((px, y - 30 * k), precio, font=fp, fill=TERRA)
    if previo:
        pw = d.textlength(precio, font=fp); fa = f("Inter-Medium.otf", int(36 * k))
        ax = px + pw + 26 * k; ay = y + 22 * k
        d.text((ax, ay), previo, font=fa, fill=MU)
        aw = d.textlength(previo, font=fa); d.line((ax, ay + 22 * k, ax + aw, ay + 22 * k), fill=MU, width=max(2, int(3 * k)))
    y += int(120 * k)
    if ml:
        fm = f("Inter-Medium.otf", int(32 * k))
        t1 = "En Mercado Libre "; d.text((x0, y - 8 * k), t1, font=fm, fill=MU)
        ax = x0 + d.textlength(t1, font=fm); d.text((ax, y - 8 * k), ml, font=fm, fill=MU)
        aw = d.textlength(ml, font=fm); d.line((ax, y + 12 * k, ax + aw, y + 12 * k), fill=MU, width=3)
        y += int(56 * k)
        d.text((x0, y), "Precio showroom · efectivo o transferencia", font=f("Inter-SemiBold.otf", int(30 * k)), fill=(47, 125, 79))
        y += int(52 * k)
    d.text((x0, y), "Stock disponible · Vení a verlo al showroom", font=f("Inter-Medium.otf", int(30 * k)), fill=TX)
    y += int(70 * k)
    # Foto entera en tarjeta
    if estudio:
        foto = pv.a_estudio(foto, "ml-" + os.path.basename(foto), alto=0.72)
    im = ImageOps.exif_transpose(Image.open(os.path.join(pv.F, foto))).convert("RGB")
    if caja: im = im.crop(caja)
    im = pv.gradar(im).filter(ImageFilter.UnsharpMask(radius=1.6, percent=45, threshold=3))
    base = alto - int((470 if alto > 1500 else 250) * k)
    t, m = tarjeta(im, ancho - 2 * x0, base - y)
    tx = (ancho - t.width) // 2
    sombra = Image.new("L", lienzo.size, 0); sombra.paste(m, (tx + int(8 * k), y + int(18 * k)))
    sombra = sombra.filter(ImageFilter.GaussianBlur(28 * k)).point(lambda v: int(v * 0.35))
    lienzo.paste((90, 70, 50), (0, 0), sombra)
    lienzo.paste(t, (tx, y), m)
    lienzo = pv.firma(lienzo)
    lienzo = pv.sello(lienzo, k=1.45 if alto > 1500 else 1.0)
    lienzo.save(os.path.join(OUT, salida), quality=93)
    return salida


def ronda2():
    """Ronda extra (más frecuencia los primeros días): precio del showroom vs. Mercado Libre."""
    pieza("wa-1117/foto-1.jpg", "r2-banquetas-x2.jpg", "AHORRÁS 27%", "2 banquetas de\npetiribí tejidas", "Para barra o desayunador · el par", "$270.000", ml="$369.550", caja=(0, 70, 1206, 1561))
    pieza("ml/2f2355cbb2c1.jpg", "r2-combo-120.jpg", "AHORRÁS 24%", "Combo de cocina\nen pino 1,20 m", "Bajo mesada + alacena · pino macizo", "$135.900", ml="$179.900", estudio=True)
    pieza("ml/a275c2319fab.jpg", "r2-ropero-120.jpg", "AHORRÁS 35%", "Ropero de pino\nmacizo 1,20 m", "Con cajonera · el más vendido", "$149.000", ml="$229.900", estudio=True)
    pieza("ml/723110675bd4.jpg", "r2-alacena-120.jpg", "AHORRÁS 46%", "Alacena de pino\n1,20 m", "Para colgar · 120x60x29 · estante interior", "$69.900", ml="$129.900", estudio=True)
    pieza("ml/ca71442b3e7e.jpg", "r2-mesa-varillada.jpg", "AHORRÁS 29%", "Mesa redonda\nvarillada 120 cm", "Pino · base central varillada · para 6", "$169.000", ml="$239.000", estudio=True)
    pieza("ml/5cb7250724d4.jpg", "r2-banqueta-tapizada.jpg", "AHORRÁS 54%", "Banqueta alta\nde paraíso tapizada", "Pana gris · para barra o desayunador", "$125.000", ml="$269.000", estudio=True)


if __name__ == "__main__":
    import sys
    if "--ronda2" in sys.argv:
        ronda2(); print("ok"); raise SystemExit
    ypf = pv.a_estudio("sillon-1c-gris.jpg", "sillon-ypf-gris.jpg", alto=0.66)
    pieza(pv.a_estudio(pv.ig("17997719087698301-1"), "combo-pino-frente.jpg"), "promo-1-combo-pino.jpg",
          "EL MÁS VENDIDO", "Combo de cocina\nen pino macizo", "Bajo mesada + alacena · 1,20 m a 2 m", "$179.900", desde=True)
    pieza(ypf, "promo-2-sillon-ypf.jpg", "OFERTA", "Sillón YPF\nen paraíso", "Tapizado en pana, chenille o ecocuero", "$160.550", previo="$169.000")
    pieza("wa-1117/foto-4.jpg", "promo-3-banquetas.jpg", "COMBO X2", "Banquetas de\npetiribí tejidas", "Para barra o desayunador · el par", "$369.550", previo="$389.000", caja=(0, 70, 1206, 1558))
    pieza("wa-1117/foto-13.jpg", "promo-4-bano-historia.jpg", "PARA TU BAÑO", "Botiquín\ncon espejo", "Laqueado blanco, con luz · mini tolva $189.000", "$149.000", desde=True)
    pieza("wa-1117/foto-13.jpg", "promo-4-bano.jpg", "PARA TU BAÑO", "Botiquín con espejo", "Laqueado blanco, con luz · mini tolva $189.000", "$149.000", desde=True, alto=1350)
    print("ok")


def feed(foto, salida, etiqueta, nombre, precio, ml, estudio=True):
    """Post 1080x1350: foto grande arriba, precio grande abajo, sello de WhatsApp + dirección."""
    W, H = 1080, 1350
    lienzo = pv.fondo_estudio(W, H, piso=0.999).convert("RGB")
    if estudio:
        from rembg import remove, new_session
        cut = remove(Image.open(os.path.join(pv.F, foto)).convert("RGB"), session=new_session("isnet-general-use"))
        im = pv.gradar(pv.estudio(cut, w=1000, h=760, alto=0.80, piso=0.86))
    else:
        im = pv.gradar(ImageOps.exif_transpose(Image.open(os.path.join(pv.F, foto))).convert("RGB"))
        im.thumbnail((1000, 760))
    t, m = tarjeta(im, 1000, 760, radio=30)
    sombra = Image.new("L", lienzo.size, 0); sombra.paste(m, (48, 58))
    lienzo.paste((90, 70, 50), (0, 0), sombra.filter(ImageFilter.GaussianBlur(22)).point(lambda v: int(v * 0.3)))
    lienzo.paste(t, (40, 40), m)
    d = ImageDraw.Draw(lienzo)
    fe = f("Inter-Bold.otf", 28); tw = d.textlength(etiqueta, font=fe)
    d.rounded_rectangle((64, 64, 64 + tw + 40, 116), 26, fill=TERRA)
    d.text((84, 90), etiqueta, font=fe, fill="white", anchor="lm")
    y = 830
    d.text((60, y), nombre, font=f("Inter-SemiBold.otf", 50), fill=TX)
    fp = f("Inter-Bold.otf", 92); d.text((60, y + 62), precio, font=fp, fill=TERRA)
    px = 60 + d.textlength(precio, font=fp) + 28
    fm = f("Inter-Medium.otf", 28)
    d.text((px, y + 82), "en el showroom", font=fm, fill=TX)
    t1 = "Mercado Libre "; d.text((px, y + 120), t1, font=fm, fill=MU)
    ax = px + d.textlength(t1, font=fm); d.text((ax, y + 120), ml, font=fm, fill=MU)
    d.line((ax, y + 138, ax + d.textlength(ml, font=fm), y + 138), fill=MU, width=3)
    lienzo = pv.firma(lienzo)
    lienzo = pv.sello(lienzo, k=1.0)
    lienzo.save(os.path.join(OUT, salida), quality=93)

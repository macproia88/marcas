"""Tapas con identidad propia para cada carrusel (misma marca, distinto diseño).
Pedido 19/11: que no salgan todas con el mismo molde.
Uso: python3 tapas_variadas.py <carpeta_fuentes>
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import armar_piezas as a
from PIL import Image, ImageDraw, ImageOps, ImageFilter

W, H = 1080, 1350
E = a.F + "/expo-2026"; O = a.OUT
a.TURQUESA = "#17919C"

def flecha(d, x, y, color, txt="Deslizá"):
    tx = x - d.textlength(txt, font=a.LATOB(34))
    d.text((tx, y), txt, font=a.LATOB(34), fill=color)
    d.polygon([(x + 15, y + 5), (x + 48, y + 21), (x + 15, y + 37)], fill=color)

def resaltado(d, lineas, fnt, x, y, fondo, color, pad=16, alto=None):
    alto = alto or int(fnt.size * 1.18)
    for l in lineas:
        w = d.textlength(l, font=fnt)
        d.rectangle([x - pad, y - 6, x + w + pad, y + alto - 10], fill=fondo)
        d.text((x, y), l, font=fnt, fill=color)
        y += alto
    return y

def degradado(c, desde, color=(0, 0, 0), maxa=200):
    g = Image.new("L", (1, H))
    for yy in range(H):
        g.putpixel((0, yy), 0 if yy < desde else int(maxa * min(1, (yy - desde) / (H - desde) * 1.4)))
    capa = Image.new("RGB", (W, H), color)
    c.paste(capa, (0, 0), g.resize((W, H)))

# 1) Trabajos: foto completa + frase en bloques verdes resaltados (como "La profe siempre está…")
def tapa_resaltada(foto, chico, titulo, salida, centro=(0.5, 0.45)):
    c = a.recortar(foto, W, H, centro); d = ImageDraw.Draw(c)
    degradado(c, 700, maxa=120); d = ImageDraw.Draw(c)
    d.rectangle([70, 760, 70 + d.textlength(chico, font=a.LATOB(32)) + 36, 812], fill=a.AMARILLO)
    d.text((88, 769), chico, font=a.LATOB(32), fill=a.MARRON)
    resaltado(d, a.partir(d, titulo, a.SP(96), W - 200), a.SP(96), 90, 850, a.VERDE, "white", alto=112)
    flecha(d, W - 120, H - 95, "white")
    c.save(salida, quality=92)

# 2) Comunidad: tarjeta crema, foto redondeada arriba, título centrado verde (como "¡Gracias Acción Social…!")
def tapa_tarjeta(foto, chico, titulo, sub, salida, centro=(0.5, 0.45)):
    c = Image.new("RGB", (W, H), a.CREMA); d = ImageDraw.Draw(c)
    ph = a.recortar(foto, 940, 760, centro)
    m = Image.new("L", ph.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, *ph.size], 44, fill=255)
    c.paste(ph, (70, 70), m)
    for i, col in enumerate([a.VERDE, a.AMARILLO, a.TURQUESA]):
        d.ellipse([W // 2 - 70 + i * 50, 870, W // 2 - 50 + i * 50, 890], fill=col)
    tw = d.textlength(chico, font=a.LATOB(32)); d.text(((W - tw) / 2, 915), chico, font=a.LATOB(32), fill=a.TURQUESA)
    y = 965
    for l in a.partir(d, titulo.upper(), a.SP(84), W - 160):
        d.text(((W - d.textlength(l, font=a.SP(84))) / 2, y), l, font=a.SP(84), fill=a.VERDE); y += 88
    for l in a.partir(d, sub, a.LATO(36), W - 220):
        d.text(((W - d.textlength(l, font=a.LATO(36))) / 2, y + 14), l, font=a.LATO(36), fill=a.MARRON); y += 46
    flecha(d, W - 120, H - 80, a.VERDE)
    c.save(salida, quality=92)

# 3) Gracias: foto en blanco y negro, "¡Gracias!" grande en amarillo, sin flecha de deslizar
def tapa_bn(foto, titulo, sub, salida, centro=(0.5, 0.45)):
    c = ImageOps.grayscale(a.recortar(foto, W, H, centro)).convert("RGB")
    degradado(c, 600, color=(0, 40, 22), maxa=235); d = ImageDraw.Draw(c)
    d.text((70, 900), titulo, font=a.SP(190), fill=a.AMARILLO)
    a.texto_lineas(d, a.partir(d, sub, a.LATOB(42), W - 160), a.LATOB(42), 76, 1110, "white", 1.25)
    a.logo(c, a.LOGO_B, 300, W - 370, 70)
    c.save(salida, quality=92)

# 4) Carpintería: foto completa, etiqueta verde arriba tipo "Hola, mi nombre es…", título blanco abajo
def tapa_etiqueta(foto, chico, titulo, salida, centro=(0.5, 0.45)):
    c = a.recortar(foto, W, H, centro); degradado(c, 750, maxa=215); d = ImageDraw.Draw(c)
    l = a.partir(d, chico, a.LATOB(36), 500)
    y = resaltado(d, l, a.LATOB(36), 90, 90, a.VERDE, "white", pad=20, alto=52)
    a.texto_lineas(d, a.partir(d, titulo, a.SP(100), W - 160), a.SP(100), 70, 1000, "white", 1.0)
    d.rectangle([70, 960, 200, 970], fill=a.AMARILLO)
    flecha(d, W - 120, H - 95, a.AMARILLO)
    c.save(salida, quality=92)

# 5) Costura: collage de 3 fotos con banda amarilla en el medio
def tapa_collage(fotos, chico, titulo, salida):
    c = Image.new("RGB", (W, H), a.VERDE)
    c.paste(a.recortar(fotos[0], W, 640), (0, 0))
    c.paste(a.recortar(fotos[1], 534, 420), (0, 930))
    c.paste(a.recortar(fotos[2], 534, 420), (546, 930))
    d = ImageDraw.Draw(c)
    d.rectangle([0, 640, W, 930], fill=a.AMARILLO)
    d.text((70, 670), chico, font=a.LATOB(32), fill=a.VERDE)
    a.texto_lineas(d, a.partir(d, titulo, a.SP(92), W - 140), a.SP(92), 70, 725, a.MARRON, 1.0)
    d.rectangle([534, 930, 546, H], fill=a.VERDE)
    d.rounded_rectangle([W - 290, H - 95, W - 40, H - 35], 30, fill=a.VERDE)
    flecha(d, W - 110, H - 85, "white")
    c.save(salida, quality=92)

if __name__ == "__main__":
  tapa_resaltada(f"{E}/muebles-alumnos.jpg", "EXPO FÁTIMA 2026", "Lo que hicieron los alumnos", f"{O}/expo-trabajos-1.jpg", (0.5, 0.5))
  tapa_tarjeta(f"{E}/stand-grupo-sonriendo.jpg", "EXPO FÁTIMA 2026", "Una Expo para toda la comunidad",
             "Stands, emprendimientos, historia y mucha gente compartiendo el día.", f"{O}/expo-comunidad-1.jpg", (0.5, 0.4))
  tapa_bn(f"{E}/foto-grupal-carpinteria.jpg", "¡Gracias!",
        "A todos los que trabajaron y colaboraron para que este día sea posible.", f"{O}/expo-gracias-1.jpg", (0.5, 0.4))
  tapa_etiqueta(f"{a.F}/carpinteria/grupo-1.jpg", "TALLER DE CARPINTERÍA PARA ADULTOS", "Aprender un oficio con las manos", f"{O}/1117-carpinteria-1.jpg", (0.5, 0.35))
  tapa_collage([f"{a.F}/costura/grupo-sonriendo.jpg", f"{a.F}/costura/regla-fatima.jpg", f"{a.F}/costura/moldes-1.jpg"],
             "TALLER DE COSTURA", "Del molde a la prenda", f"{O}/1121-costura-1.jpg")
  print("listo")

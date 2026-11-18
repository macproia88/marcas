"""Arma las piezas gráficas de Escuela Taller Fátima con la identidad del manual de marca 2023.
Colores: verde #00894C, crema #F5FBF6, marrón #52453B, turquesa #17919C, verde claro #78B02A, amarillo #FFCB33.
Tipografías: League Spartan Bold (títulos) y Lato (textos).
Uso: python3 armar_piezas.py <carpeta_fuentes>   (carpeta con los .woff de Lato y League Spartan)
"""
import sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = os.path.join(BASE, "fotos")
OUT = os.path.join(BASE, "img")
os.makedirs(OUT, exist_ok=True)
FUENTES = sys.argv[1]
VERDE, CREMA, MARRON, AMARILLO = "#00894C", "#F5FBF6", "#52453B", "#FFCB33"

def fuente(nombre, tam):
    return ImageFont.truetype(os.path.join(FUENTES, nombre), tam)

SP = lambda t: fuente("league-spartan-latin-700-normal.woff", t)
LATO = lambda t: fuente("lato-latin-400-normal.woff", t)
LATOB = lambda t: fuente("lato-latin-700-normal.woff", t)
LOGO_B = Image.open(os.path.join(BASE, "marca", "logo-blanco.png")).convert("RGBA")
LOGO_V = Image.open(os.path.join(BASE, "marca", "logo-verde.png")).convert("RGBA")

def recortar(ruta, w, h, centro=(0.5, 0.45)):
    im = ImageOps.exif_transpose(Image.open(ruta)).convert("RGB")
    return ImageOps.fit(im, (w, h), Image.LANCZOS, centering=centro)

def logo(lienzo, cual, ancho, x, y):
    l = cual.copy(); l.thumbnail((ancho, ancho))
    bb = l.getbbox(); l = l.crop(bb)
    lienzo.paste(l, (x, y), l)

def texto_lineas(d, lineas, fnt, x, y, color, inter=1.12):
    for ln in lineas:
        d.text((x, y), ln, font=fnt, fill=color)
        y += int(fnt.size * inter)
    return y

def partir(d, texto, fnt, ancho):
    pal, lineas, act = texto.split(), [], ""
    for p in pal:
        prueba = (act + " " + p).strip()
        if d.textlength(prueba, font=fnt) <= ancho: act = prueba
        else: lineas.append(act); act = p
    if act: lineas.append(act)
    return lineas

def portada(foto, etiqueta, titulo, sub, salida, deslizar=True):
    W, H = 1080, 1350
    c = Image.new("RGB", (W, H), CREMA)
    c.paste(recortar(foto, W, 830), (0, 0))
    d = ImageDraw.Draw(c)
    d.rectangle([0, 830, W, H], fill=VERDE)
    d.rounded_rectangle([70, 785, 70 + d.textlength(etiqueta, font=LATOB(34)) + 56, 860], 38, fill=AMARILLO)
    d.text((98, 800), etiqueta, font=LATOB(34), fill=MARRON)
    y = texto_lineas(d, partir(d, titulo, SP(92), W - 140), SP(92), 70, 905, "white", 1.02)
    texto_lineas(d, partir(d, sub, LATO(40), W - 140), LATO(40), 70, y + 18, CREMA, 1.3)
    logo(c, LOGO_B, 330, 70, H - 120)
    if not deslizar:
        c.save(salida, quality=92); return
    tx = W - 120 - d.textlength("Deslizá", font=LATOB(36))
    d.text((tx, H - 100), "Deslizá", font=LATOB(36), fill=AMARILLO)
    d.polygon([(W - 105, H - 95), (W - 70, H - 78), (W - 105, H - 61)], fill=AMARILLO)
    c.save(salida, quality=92)

def foto_con_texto(foto, frase, salida, n=None, centro=(0.5, 0.45)):
    W, H = 1080, 1350
    c = recortar(foto, W, H, centro)
    grad = Image.new("L", (1, 256))
    for i in range(256): grad.putpixel((0, i), int(max(0, i - 90) * 1.35))
    sombra = Image.new("RGB", (W, H), "#0b3d26"); mask = grad.resize((W, H))
    c = Image.composite(sombra, c, mask)
    d = ImageDraw.Draw(c)
    lineas = partir(d, frase, SP(66), W - 160)
    y0 = H - 140 - len(lineas) * 70
    d.rectangle([70, y0 - 6, 82, y0 + len(lineas) * 70 - 14], fill=AMARILLO)
    texto_lineas(d, lineas, SP(66), 110, y0, "white", 1.06)
    logo(c, LOGO_B, 250, 70, H - 95)
    if n: d.text((W - 150, H - 88), n, font=LATOB(34), fill=CREMA)
    c.save(salida, quality=92)

def cierre(titulo, texto, salida):
    W, H = 1080, 1350
    c = Image.new("RGB", (W, H), VERDE); d = ImageDraw.Draw(c)
    hoja = Image.open(os.path.join(BASE, "marca", "hoja-verde.png")).convert("RGBA").resize((520, 520))
    r, g, b, a = hoja.split(); hoja = Image.merge("RGBA", (r.point(lambda v: 0), g.point(lambda v: 160), b.point(lambda v: 90), a.point(lambda v: v * 0.35)))
    c.paste(hoja, (W - 430, -120), hoja)
    y = texto_lineas(d, partir(d, titulo, SP(88), W - 160), SP(88), 80, 330, "white", 1.02)
    texto_lineas(d, partir(d, texto, LATO(44), W - 160), LATO(44), 80, y + 40, CREMA, 1.35)
    d.rounded_rectangle([80, 1010, 80 + d.textlength("Escribinos por mensaje", font=LATOB(42)) + 70, 1100], 45, fill=AMARILLO)
    d.text((115, 1030), "Escribinos por mensaje", font=LATOB(42), fill=MARRON)
    logo(c, LOGO_B, 360, 80, H - 140)
    c.save(salida, quality=92)

def historia(foto, arriba, grande, abajo, salida):
    W, H = 1080, 1920
    fondo = recortar(foto, W, H).filter(ImageFilter.GaussianBlur(28))
    fondo = Image.blend(fondo, Image.new("RGB", (W, H), "#0b3d26"), 0.45)
    ph = recortar(foto, 920, 1100)
    m = Image.new("L", ph.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, *ph.size], 40, fill=255)
    fondo.paste(ph, (80, 330), m)
    d = ImageDraw.Draw(fondo)
    logo(fondo, LOGO_B, 330, 80, 150)
    d.rounded_rectangle([80, 230, 80 + d.textlength(arriba, font=LATOB(38)) + 50, 300], 35, fill=AMARILLO)
    d.text((105, 243), arriba, font=LATOB(38), fill=MARRON)
    y = texto_lineas(d, partir(d, grande, SP(76), W - 160), SP(76), 80, 1470, "white", 1.04)
    if abajo: texto_lineas(d, partir(d, abajo, LATO(40), W - 160), LATO(40), 80, y + 10, CREMA)
    fondo.save(salida, quality=92)

if __name__ == "__main__":
    # Carrusel 1: Carpintería (martes 17/11)
    portada(f"{F}/carpinteria/grupo-1.jpg", "TALLER DE CARPINTERÍA", "Aprender un oficio con las manos",
            "Así se vivió la capacitación de carpintería para adultos.", f"{OUT}/1117-carpinteria-1.jpg")
    foto_con_texto(f"{F}/carpinteria/profe-ensenando.jpg", "Se aprende mirando, preguntando y haciendo.", f"{OUT}/1117-carpinteria-2.jpg", "2/5")
    foto_con_texto(f"{F}/carpinteria/manos-lijando.jpg", "Cada pieza empieza con un buen lijado.", f"{OUT}/1117-carpinteria-3.jpg", "3/5", (0.5, 0.75))
    foto_con_texto(f"{F}/carpinteria/demostracion.jpg", "Herramientas reales y seguridad desde el primer día.", f"{OUT}/1117-carpinteria-4.jpg", "4/5")
    cierre("Un oficio abre puertas", "Aprender carpintería es ganar herramientas para trabajar y emprender.", f"{OUT}/1117-carpinteria-5.jpg")
    # Carrusel 2: Costura (sábado 21/11)
    portada(f"{F}/costura/grupo-sonriendo.jpg", "TALLER DE COSTURA", "Del molde a la prenda",
            "Moldería, medidas y mucho compañerismo en el taller de costura.", f"{OUT}/1121-costura-1.jpg")
    foto_con_texto(f"{F}/costura/regla-fatima.jpg", "Todo empieza con un buen molde.", f"{OUT}/1121-costura-2.jpg", "2/5")
    foto_con_texto(f"{F}/costura/pizarron.jpg", "Medir, trazar, cortar: paso a paso.", f"{OUT}/1121-costura-3.jpg", "3/5")
    foto_con_texto(f"{F}/costura/moldes-2.jpg", "Aprendemos juntas y juntos.", f"{OUT}/1121-costura-4.jpg", "4/5")
    cierre("Coser también es emprender", "Con un oficio en las manos se abren nuevas oportunidades.", f"{OUT}/1121-costura-5.jpg")
    # Historias diarias
    H = [
        ("1117", f"{F}/carpinteria/grupo-2.jpg", "HOY EN EL FEED", "Así fue la capacitación de carpintería", "Mirá el posteo completo"),
        ("1118", f"{F}/soldadura/chispas-grupo.jpg", "¿SABÍAS QUE…?", "En Fátima también se aprende soldadura", "Primeras prácticas del año"),
        ("1119", f"{F}/manicuria/clase.jpg", "TALLER DE MANICURÍA", "Manos que aprenden un oficio", "Una salida laboral real"),
        ("1120", f"{F}/soldadura/profe-y-alumnos.jpg", "LOS PROFES", "Gracias por enseñar con tanta paciencia", ""),
        ("1121", f"{F}/costura/moldes-1.jpg", "HOY EN EL FEED", "Del molde a la prenda", "Mirá el posteo completo"),
        ("1122", f"{F}/carpinteria/charla-tecnica.jpg", "COMUNIDAD FÁTIMA", "Aprender un oficio es abrir una puerta", "Mirá el testimonio de Corina en el feed"),
        ("1123", f"{F}/costura/grupo.jpg", "¿QUERÉS SUMARTE?", "Escribinos por mensaje y te contamos", "Talleres de oficios en Escuela Taller Fátima"),
    ]
    for dia, foto, a, g, b in H:
        historia(foto, a, g, b, f"{OUT}/{dia}-historia.jpg")
    print("listo")

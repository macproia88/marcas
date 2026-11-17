"""Arma las piezas gráficas de El carpintero3 (@elcarpintero3f) con los colores del cartel del local.
Colores: negro #1C1A19, rojo del "3" #C4243A, verde agua de "amoblamientos" #2FB592, amarillo #F2C230, crema #F6EEE2.
Tipografía: Inter Display Black (títulos) e Inter (textos), en herramientas/fuentes.
Uso: python3 armar_piezas.py        (lee fotos/ y escribe img/ y videos/)
"""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = os.path.join(BASE, "fotos")
OUT = os.path.join(BASE, "img")
VID = os.path.join(BASE, "videos")
TMP = "/tmp/carpintero"
FUENTES = os.path.join(BASE, "herramientas", "fuentes")
for d in (OUT, VID, TMP):
    os.makedirs(d, exist_ok=True)

NEGRO, ROJO, VERDE, AMARILLO, CREMA = "#1C1A19", "#C4243A", "#2FB592", "#F2C230", "#F6EEE2"
TIT = lambda t: ImageFont.truetype(os.path.join(FUENTES, "InterDisplay-Black.otf"), t)
TXT = lambda t: ImageFont.truetype(os.path.join(FUENTES, "Inter-Regular.otf"), t)
TXTB = lambda t: ImageFont.truetype(os.path.join(FUENTES, "Inter-Bold.otf"), t)
DIRECCION = "Román Gómez 1893 · José Ingenieros"
WHATSAPP = "WhatsApp 24 hs · 11 4194-3328"


def foto(nombre):
    return os.path.join(F, nombre)


def mejorar(im):
    """Retoque de foto de celular: niveles, balance de blanco, color cálido de madera, contraste y nitidez."""
    from PIL import ImageEnhance, ImageStat
    im = ImageOps.autocontrast(im, cutoff=(1, 0.6))
    r, g, b = ImageStat.Stat(im).mean
    gris = (r + g + b) / 3
    fac = [min(max(gris / max(v, 1), 0.9), 1.1) for v in (r, g, b)]   # balance de blanco suave (gray world)
    fac[0] *= 1.03; fac[2] *= 0.96                                      # un toque cálido para la madera
    canales = [c.point(lambda x, f=f: min(255, int(x * f))) for c, f in zip(im.split(), fac)]
    im = Image.merge("RGB", canales)
    # levantar sombras sin quemar luces
    im = im.point(lambda x: int(255 * ((x / 255) ** 0.9)))
    im = ImageEnhance.Color(im).enhance(1.15)
    im = ImageEnhance.Contrast(im).enhance(1.06)
    im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=70, threshold=3))
    return im


def recortar(ruta, w, h, centro=(0.5, 0.5), caja=None, zoom=1.0):
    im = ImageOps.exif_transpose(Image.open(ruta)).convert("RGB")
    if caja:
        im = im.crop(caja)
    if zoom > 1:
        W0, H0 = im.size
        cw, ch = W0 / zoom, H0 / zoom
        x0 = (W0 - cw) * centro[0]; y0 = (H0 - ch) * centro[1]
        im = im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch)))
    return mejorar(ImageOps.fit(im, (w, h), Image.LANCZOS, centering=centro))


def partir(d, texto, fnt, ancho):
    lineas, act = [], ""
    for p in texto.split():
        prueba = (act + " " + p).strip()
        if d.textlength(prueba, font=fnt) <= ancho:
            act = prueba
        else:
            lineas.append(act)
            act = p
    if act:
        lineas.append(act)
    return lineas


def lineas(d, ls, fnt, x, y, color, inter=1.1):
    for ln in ls:
        d.text((x, y), ln, font=fnt, fill=color)
        y += int(fnt.size * inter)
    return y


def marca(d, x, y, tam=44, color=NEGRO):
    """Logotipo de texto: EL CARPINTERO + 3 en rojo, como en el cartel."""
    f = TIT(tam)
    d.text((x, y), "EL CARPINTERO", font=f, fill=color)
    d.text((x + d.textlength("EL CARPINTERO", font=f) + 2, y), "3", font=f, fill=ROJO)


def etiqueta(d, texto, x, y, fondo=AMARILLO, color=NEGRO, tam=32):
    f = TXTB(tam)
    w = d.textlength(texto, font=f)
    d.rounded_rectangle([x, y, x + w + 52, y + tam + 34], (tam + 34) // 2, fill=fondo)
    d.text((x + 26, y + 15), texto, font=f, fill=color)


def portada(nombre, etq, titulo, sub, salida, centro=(0.5, 0.5), caja=None):
    W, H = 1080, 1350
    c = Image.new("RGB", (W, H), CREMA)
    c.paste(recortar(foto(nombre), W, 900, centro, caja), (0, 0))
    d = ImageDraw.Draw(c)
    d.rectangle([0, 900, W, H], fill=NEGRO)
    d.rectangle([0, 900, W, 912], fill=AMARILLO)
    etiqueta(d, etq, 64, 845)
    y = lineas(d, partir(d, titulo, TIT(84), W - 128), TIT(84), 64, 950, "white", 1.02)
    lineas(d, partir(d, sub, TXT(38), W - 128), TXT(38), 64, y + 14, CREMA, 1.3)
    marca(d, 64, H - 92, 40, "white")
    f = TXTB(32)
    d.text((W - 64 - d.textlength("Deslizá →", font=f), H - 86), "Deslizá →", font=f, fill=AMARILLO)
    c.save(os.path.join(OUT, salida), quality=92)


def interna(nombre, frase, salida, n, centro=(0.5, 0.5), caja=None):
    W, H = 1080, 1350
    c = recortar(foto(nombre), W, H, centro, caja)
    d = ImageDraw.Draw(c, "RGBA")
    f = TIT(58)
    ls = partir(d, frase, f, W - 200)
    alto = len(ls) * int(f.size * 1.08) + 70
    d.rounded_rectangle([50, H - 70 - alto, W - 50, H - 70], 28, fill=(28, 26, 25, 235))
    lineas(d, ls, f, 92, H - 70 - alto + 34, "white", 1.08)
    d.ellipse([W - 130, 50, W - 50, 130], fill=AMARILLO)
    t = str(n)
    d.text((W - 90 - d.textlength(t, font=TIT(44)) / 2, 62), t, font=TIT(44), fill=NEGRO)
    c.save(os.path.join(OUT, salida), quality=92)


def cierre(titulo, texto, salida):
    W, H = 1080, 1350
    c = Image.new("RGB", (W, H), AMARILLO)
    d = ImageDraw.Draw(c)
    marca(d, 80, 110, 64)
    d.rectangle([80, 205, 260, 217], fill=ROJO)
    y = lineas(d, partir(d, titulo, TIT(96), W - 160), TIT(96), 80, 300, NEGRO, 1.02)
    y = lineas(d, partir(d, texto, TXT(42), W - 160), TXT(42), 80, y + 30, NEGRO, 1.35)
    y = max(y + 60, 860)
    for ic, t in (("Showroom", DIRECCION), ("Horario", "Lun a Vie 11 a 18:30 · Sáb 11 a 16"), ("Consultas", WHATSAPP)):
        d.text((80, y), ic.upper(), font=TXTB(28), fill=ROJO)
        d.text((80, y + 38), t, font=TXTB(40), fill=NEGRO)
        y += 120
    c.save(os.path.join(OUT, salida), quality=92)


def historia(nombre, arriba, grande, abajo, salida, centro=(0.5, 0.5), caja=None):
    W, H = 1080, 1920
    c = recortar(foto(nombre), W, H, centro, caja)
    d = ImageDraw.Draw(c, "RGBA")
    d.rectangle([0, 0, W, 300], fill=(28, 26, 25, 225))
    marca(d, 70, 120, 46, "white")
    f = TIT(86)
    ls = partir(d, grande, f, W - 180)
    alto = len(ls) * int(f.size * 1.04) + 230
    y0 = H - 300 - alto
    d.rounded_rectangle([50, y0, W - 50, H - 300], 34, fill=(242, 194, 48, 245))
    d.text((90, y0 + 40), arriba.upper(), font=TXTB(32), fill=ROJO)
    y = lineas(d, ls, f, 90, y0 + 92, NEGRO, 1.04)
    d.text((90, y + 14), abajo, font=TXTB(36), fill=NEGRO)
    d.rectangle([0, H - 210, W, H], fill=(28, 26, 25, 225))
    t = WHATSAPP
    d.text(((W - d.textlength(t, font=TXTB(40))) / 2, H - 150), t, font=TXTB(40), fill="white")
    c.save(os.path.join(OUT, salida), quality=92)


def placa_video(texto_arriba, salida, w=1080, h=1920):
    """Capa PNG transparente con título arriba y pie de marca abajo, para superponer al video."""
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    f = TIT(76)
    ls = partir(d, texto_arriba, f, w - 180)
    alto = len(ls) * int(f.size * 1.05) + 80
    d.rounded_rectangle([50, 150, w - 50, 150 + alto], 30, fill=(28, 26, 25, 225))
    lineas(d, ls, f, 90, 190, "white", 1.05)
    d.rectangle([0, h - 230, w, h], fill=(28, 26, 25, 215))
    marca(d, 70, h - 200, 44, "white")
    d.text((70, h - 130), DIRECCION, font=TXTB(36), fill=AMARILLO)
    c.save(salida)


def placa_final(salida, w=1080, h=1920):
    c = Image.new("RGB", (w, h), AMARILLO)
    d = ImageDraw.Draw(c)
    marca(d, 80, 520, 84)
    d.rectangle([80, 640, 300, 654], fill=ROJO)
    y = lineas(d, ["Somos", "fabricantes."], TIT(120), 80, 720, NEGRO, 1.0)
    for t in (DIRECCION, "Lun a Vie 11 a 18:30 · Sáb 11 a 16", WHATSAPP):
        d.text((80, y + 50), t, font=TXTB(42), fill=NEGRO)
        y += 70
    c.save(salida)


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def musica(segundos, salida):
    script = os.path.join(BASE, "..", "tallerfatima", "herramientas", "musica.py")
    subprocess.run([sys.executable, script, salida, str(segundos)], check=True)


def reel_video(origen, titulo, salida):
    placa_video(titulo, f"{TMP}/capa.png")
    placa_final(f"{TMP}/final.png")
    ff("-i", origen, "-i", f"{TMP}/capa.png",
       "-filter_complex", "[0:v]scale=1080:1920:flags=lanczos,setsar=1,fps=30[v];[v][1:v]overlay=0:0,format=yuv420p",
       "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", f"{TMP}/a.mp4")
    ff("-loop", "1", "-t", "3", "-i", f"{TMP}/final.png", "-vf", "fps=30,format=yuv420p,setsar=1",
       "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", f"{TMP}/b.mp4")
    ff("-i", f"{TMP}/a.mp4", "-i", f"{TMP}/b.mp4", "-filter_complex", "[0:v][1:v]concat=n=2:v=1[v]", "-map", "[v]",
       "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", f"{TMP}/c.mp4")
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{TMP}/c.mp4"]))
    musica(dur + 0.5, f"{TMP}/m.wav")
    ff("-i", f"{TMP}/c.mp4", "-i", f"{TMP}/m.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
       "-af", f"afade=t=out:st={dur - 1.5}:d=1.5", "-shortest", "-movflags", "+faststart", os.path.join(VID, salida))


def reel_fotos(fotos, titulo, salida, seg=2.4):
    """Reel de fotos con zoom lento, título arriba y placa final."""
    placa_video(titulo, f"{TMP}/capa.png")
    placa_final(f"{TMP}/final.png")
    partes = []
    for i, (nombre, centro) in enumerate(fotos):
        recortar(foto(nombre), 1080, 1920, centro).save(f"{TMP}/f{i}.jpg", quality=95)
        n = int(seg * 30)
        ff("-loop", "1", "-i", f"{TMP}/f{i}.jpg", "-i", f"{TMP}/capa.png", "-filter_complex",
           f"[0:v]scale=2160:3840,zoompan=z='1+0.0012*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s=1080x1920:fps=30[z];[z][1:v]overlay=0:0,format=yuv420p,setsar=1",
           "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", f"{TMP}/p{i}.mp4")
        partes.append(f"{TMP}/p{i}.mp4")
    ff("-loop", "1", "-t", "3", "-i", f"{TMP}/final.png", "-vf", "fps=30,format=yuv420p,setsar=1",
       "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", f"{TMP}/fin.mp4")
    partes.append(f"{TMP}/fin.mp4")
    entradas = sum((["-i", p] for p in partes), [])
    cad = "".join(f"[{i}:v]" for i in range(len(partes))) + f"concat=n={len(partes)}:v=1[v]"
    ff(*entradas, "-filter_complex", cad, "-map", "[v]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", f"{TMP}/c.mp4")
    dur = len(fotos) * seg + 3
    musica(dur + 0.5, f"{TMP}/m.wav")
    ff("-i", f"{TMP}/c.mp4", "-i", f"{TMP}/m.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
       "-af", f"afade=t=out:st={dur - 1.5}:d=1.5", "-shortest", "-movflags", "+faststart", os.path.join(VID, salida))


CAPTURA = (0, 245, 720, 1205)  # recorte de la captura de pantalla de la mesa con patas en cruz

if __name__ == "__main__":
    # Martes 17: carrusel "Somos fabricantes"
    portada("frente-local.jpg", "Volvimos", "Somos fabricantes", "Muebles hechos por nosotros, en nuestro showroom de José Ingenieros.",
            "1117-fabricantes-1.jpg", centro=(0.5, 0.35))
    interna("living-negro.jpg", "Juegos de living: sillón, butacas y mesita", "1117-fabricantes-2.jpg", 2, (0.5, 0.6))
    interna("comedor-varillas-6-sillas.jpg", "Comedores con mesa redonda y sillas tapizadas", "1117-fabricantes-3.jpg", 3, (0.5, 0.6))
    interna("sillones-colores.jpg", "Sillones en varios colores de tapizado", "1117-fabricantes-4.jpg", 4, (0.5, 0.5))
    cierre("Vení a conocernos", "Tenemos los muebles en exhibición. Consultanos medidas, colores y precio.", "1117-fabricantes-5.jpg")
    # Jueves 19: carrusel mesa con base de varillas
    portada("mesa-varillas.jpg", "Comedor", "Mesa redonda con base de varillas", "Para 4 o 6 sillas. Consultanos medidas y terminaciones.",
            "1119-mesa-varillas-1.jpg", centro=(0.5, 0.55))
    interna("comedor-varillas-4-sillas.jpg", "Con 4 sillas de respaldo curvo", "1119-mesa-varillas-2.jpg", 2, (0.5, 0.55))
    interna("comedor-varillas-6-sillas.jpg", "O con 6 sillones tapizados", "1119-mesa-varillas-3.jpg", 3, (0.5, 0.6))
    interna("mesa-varillas.jpg", "La base, una por una, hecha en el taller", "1119-mesa-varillas-4.jpg", 4, (0.5, 0.75))
    cierre("¿Te la imaginás en tu casa?", "Escribinos y te pasamos medidas, colores y precio.", "1119-mesa-varillas-5.jpg")
    # Sábado 21: carrusel madera y soga
    portada("silla-soga.jpg", "Living", "Madera y soga", "Sillones bajos de soga tejida, mesitas y mesas ratonas.", "1121-soga-1.jpg", centro=(0.5, 0.6))
    interna("mesitas-y-sillas-soga.jpg", "Mesitas redondas y sillones de soga", "1121-soga-2.jpg", 2, (0.5, 0.6))
    interna("mesa-ratona-estante.jpg", "Mesa ratona con estante abajo", "1121-soga-3.jpg", 3, (0.5, 0.5))
    interna("mesa-redonda-cruz-captura.jpg", "Mesa redonda con patas en cruz", "1121-soga-4.jpg", 4, (0.5, 0.5), CAPTURA)
    cierre("Armá tu rincón", "Combiná sillón, mesita y mesa ratona. Consultanos por WhatsApp.", "1121-soga-5.jpg")
    # Sábado 21: carrusel "Elegí tu sillón"
    portada("sillon-2c-azul.jpg", "Sillones", "Elegí tu sillón", "De 1 o 2 cuerpos, con el tapizado y el color que quieras.", "1121-sillones-1.jpg", centro=(0.5, 0.6))
    interna("sillon-1c-gris.jpg", "Sillón de 1 cuerpo en gris", "1121-sillones-2.jpg", 2, (0.5, 0.55))
    interna("sillon-beige-mesita.jpg", "En crudo, con mesita bicolor", "1121-sillones-3.jpg", 3, (0.3, 0.5))
    interna("sillones-colores.jpg", "Naranja, mostaza, gris... ¿cuál va con tu casa?", "1121-sillones-4.jpg", 4, (0.5, 0.5))
    cierre("Pedí el tuyo", "Contanos qué color y qué medida necesitás y te pasamos el precio.", "1121-sillones-5.jpg")
    # Domingo 22: posteo del comedor
    portada("comedor-varillas-6-sillas.jpg", "Domingo en familia", "La mesa donde entran todos", "Mesa redonda con 6 sillones tapizados. Hecha en nuestro taller.", "1122-comedor.jpg", centro=(0.5, 0.6))
    # Historias de las 13:00
    historia("frente-local.jpg", "Martes", "Volvimos con todo", "Lun a Vie 11 a 18:30 · Sáb 11 a 16", "1117-historia.jpg", (0.55, 0.5))
    historia("sillon-2c-azul.jpg", "Miércoles", "¿Qué color elegís?", "Sillones con tapizado a elección", "1118-historia.jpg", (0.5, 0.55))
    historia("comedor-varillas-4-sillas.jpg", "Jueves", "Mesa + 4 sillas", "Esta noche te la mostramos", "1119-historia.jpg", (0.5, 0.6))
    historia("living-negro.jpg", "Viernes", "Vení a verlo", DIRECCION, "1120-historia.jpg", (0.45, 0.6))
    historia("silla-soga.jpg", "Sábado", "Hoy abrimos hasta las 16 h", DIRECCION, "1121-historia.jpg", (0.5, 0.6))
    historia("sillon-1c-gris.jpg", "Domingo", "Te respondemos hoy también", "Escribinos y te pasamos precio", "1122-historia.jpg", (0.5, 0.55))
    historia("mesa-ratona-estante.jpg", "Lunes", "Nueva semana en el showroom", "Lun a Vie 11 a 18:30", "1123-historia.jpg", (0.5, 0.5))
    # Reels
    if "--sin-video" not in sys.argv:
        reel_video(foto("video-1.mp4"), "Banqueta alta tapizada", "1118-reel-banqueta.mp4")
        reel_fotos([("sillon-2c-azul.jpg", (0.5, 0.6)), ("sillon-1c-gris.jpg", (0.5, 0.55)), ("sillon-beige-mesita.jpg", (0.35, 0.5)),
                    ("living-negro.jpg", (0.5, 0.6)), ("sillones-colores.jpg", (0.5, 0.5))],
                   "Sillones en el color que elijas", "1120-reel-sillones.mp4")
    print("Listo")

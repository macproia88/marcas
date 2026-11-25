"""Piezas para generar interacción (pedido de Juan 22/11/2026: "algo viral tenemos que armar").
1) Reel "Adiviná el precio": pregunta con cuenta regresiva y después revela precio Mercado Libre vs showroom.
2) Carrusel "¿Cuál va en tu quincho? 1, 2 o 3" para que comenten el número.
Fotos: las de las publicaciones de Mercado Libre del cliente (catalogo/p), muebles que no salieron en el feed.
Uso: python3 viral.py
"""
import os, sys, subprocess, tempfile
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import piezas_v2 as pv

FU = os.path.join(pv.BASE, "herramientas", "fuentes")
P = os.path.join(pv.BASE, "catalogo", "p")
def f(n, s): return ImageFont.truetype(os.path.join(FU, n), s)
TX, MU, TERRA, VERDE = (31, 27, 22), (122, 113, 104), (168, 67, 42), (47, 125, 79)

ADIVINA = [  # (foto, nombre, detalle, showroom, mercado libre)
    ("a275c2319fab", "Ropero de pino 1,20 m", "Pino macizo · con cajonera", "$149.000", "$229.900"),
    ("902155c188ba", "4 sillas hindú", "Pino macizo · las 4", "$87.560", "$179.000"),
    ("68332efc5efe", "Mesa ratona Restoration", "Línea francesa · 80x80", "$189.900", "$299.000"),
    ("9a787b45ce0f", "Mesa de quincho 3 m\n+ 14 sillas", "Pino · para toda la familia", "$529.000", "$974.025"),
]


def pct(a, b):
    n = lambda s: int(s.replace("$", "").replace(".", ""))
    return round(100 * (1 - n(a) / n(b)))


def centrado(d, y, t, fuente, color):
    d.text((540, y), t, font=fuente, fill=color, anchor="ma")


def foto_tarjeta(lienzo, foto, y, lado=940):
    im = Image.open(os.path.join(P, foto + ".jpg")).convert("RGB")
    im = im.resize((lado, lado), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.4, percent=60, threshold=2))
    im = pv.gradar(im)
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, lado, lado), 36, fill=255)
    x = (1080 - lado) // 2
    s = Image.new("L", lienzo.size, 0); s.paste(m, (x + 8, y + 18))
    lienzo.paste((90, 70, 50), (0, 0), s.filter(ImageFilter.GaussianBlur(26)).point(lambda v: int(v * 0.35)))
    lienzo.paste(im, (x, y), m)


def placa(texto, y, d, fuente, fondo, color="white", pad=34):
    w = d.textlength(texto, font=fuente)
    d.rounded_rectangle((540 - w / 2 - pad, y, 540 + w / 2 + pad, y + fuente.size + 40), 30, fill=fondo)
    d.text((540, y + 20), texto, font=fuente, fill=color, anchor="ma")


def cuadro_tapa():
    L = pv.fondo_estudio(1080, 1920, piso=0.999).convert("RGB"); d = ImageDraw.Draw(L)
    centrado(d, 200, "ADIVINÁ", f("InterDisplay-Black.otf", 170), TERRA)
    centrado(d, 380, "EL PRECIO", f("InterDisplay-Black.otf", 170), TX)
    centrado(d, 600, "4 muebles de fábrica", f("Inter-Medium.otf", 54), TX)
    centrado(d, 676, "¿Cuántos acertás?", f("Inter-Medium.otf", 54), TX)
    placa("Comentá tus respuestas", 790, d, f("Inter-Bold.otf", 50), TERRA)
    mini = [Image.open(os.path.join(P, a[0] + ".jpg")).convert("RGB").resize((400, 400), Image.LANCZOS) for a in ADIVINA]
    # dos fotos chicas con signo de pregunta
    for k in range(2):
        im = mini[k]; m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, 400, 400), 28, fill=255)
        im = pv.gradar(im).filter(ImageFilter.GaussianBlur(3))
        x = 100 + k * 480; L.paste(im, (x, 960), m)
        dd = ImageDraw.Draw(L); dd.text((x + 200, 1160), "?", font=f("InterDisplay-Black.otf", 230), fill="white", anchor="mm")
    return pv.sello(pv.firma(L), k=1.45)


def cuadro_pregunta(a, n, cuenta):
    L = pv.fondo_estudio(1080, 1920, piso=0.999).convert("RGB"); d = ImageDraw.Draw(L)
    placa(f"{n} / 4", 150, d, f("Inter-Bold.otf", 34), TX)
    y = 250
    for linea in a[1].split("\n"):
        centrado(d, y, linea, f("Inter-SemiBold.otf", 70), TX); y += 84
    centrado(d, y + 4, a[2], f("Inter-Regular.otf", 36), MU)
    lado = 1330 - (y + 80) - 40
    foto_tarjeta(L, a[0], y + 80, lado)
    cx, cy = 540 + lado // 2 - 90, y + 80 + 90
    d.ellipse((cx - 75, cy - 75, cx + 75, cy + 75), fill=TERRA)
    d.text((cx, cy), str(cuenta), font=f("InterDisplay-Black.otf", 100), fill="white", anchor="mm")
    centrado(d, 1335, "¿Cuánto sale?", f("InterDisplay-Black.otf", 100), TERRA)
    return pv.sello(pv.firma(L), k=1.45)


def cuadro_respuesta(a, n):
    L = pv.fondo_estudio(1080, 1920, piso=0.999).convert("RGB"); d = ImageDraw.Draw(L)
    placa(f"{n} / 4", 150, d, f("Inter-Bold.otf", 34), TX)
    y = 250
    for linea in a[1].split("\n"):
        centrado(d, y, linea, f("Inter-SemiBold.otf", 70), TX); y += 84
    centrado(d, y + 4, a[2], f("Inter-Regular.otf", 36), MU)
    lado = 1035 - (y + 70)
    foto_tarjeta(L, a[0], y + 70, lado)
    yb = 1060
    fm = f("Inter-Medium.otf", 44); t = "En Mercado Libre " + a[4]
    w = d.textlength(t, font=fm); x0 = 540 - w / 2
    d.text((x0, yb), t, font=fm, fill=MU)
    xa = x0 + d.textlength("En Mercado Libre ", font=fm)
    d.line((xa, yb + 28, x0 + w, yb + 28), fill=(190, 40, 40), width=6)
    centrado(d, yb + 66, "En el showroom", f("Inter-SemiBold.otf", 44), VERDE)
    centrado(d, yb + 116, a[3], f("InterDisplay-Black.otf", 130), TERRA)
    placa(f"AHORRÁS {pct(a[3], a[4])}%", yb + 270, d, f("Inter-Bold.otf", 50), VERDE)
    return pv.sello(pv.firma(L), k=1.45)


def cuadro_cierre():
    L = pv.fondo_estudio(1080, 1920, piso=0.999).convert("RGB"); d = ImageDraw.Draw(L)
    centrado(d, 420, "¿Cuántos", f("InterDisplay-Black.otf", 150), TX)
    centrado(d, 590, "acertaste?", f("InterDisplay-Black.otf", 150), TERRA)
    placa("Contanos en los comentarios", 840, d, f("Inter-Bold.otf", 48), TERRA)
    for k, t in enumerate(["Precio de fábrica · efectivo o transferencia",
                           "Stock disponible en el showroom",
                           "Román Gómez 1893 · José Ingenieros"]):
        centrado(d, 1040 + k * 76, t, f("Inter-Medium.otf", 42), TX)
    centrado(d, 1330, "Seguinos para la próxima", f("Inter-SemiBold.otf", 46), MU)
    return pv.sello(pv.firma(L), k=1.45)


def clip(im, seg, dst, zoom=True):
    tmp = dst + ".png"; im.save(tmp)
    n = int(seg * 30)
    vf = (f"scale=2160:3840,zoompan=z='1+0.0006*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s=1080x1920:fps=30,format=yuv420p,setsar=1"
          if zoom else "scale=1080:1920,fps=30,format=yuv420p,setsar=1")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", tmp, "-vf", vf, "-frames:v", str(n),
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", dst], check=True)
    os.remove(tmp)


def reel_adivina(salida="1123-reel-adivina-precio.mp4"):
    tmp = tempfile.mkdtemp(); partes = []
    def add(im, seg, zoom=True):
        p = f"{tmp}/{len(partes):02d}.mp4"; clip(im, seg, p, zoom); partes.append(p)
    add(cuadro_tapa(), 2.5)
    for n, a in enumerate(ADIVINA, 1):
        for c in (3, 2, 1):
            add(cuadro_pregunta(a, n, c), 1.0, zoom=False)
        add(cuadro_respuesta(a, n), 2.8)
    add(cuadro_cierre(), 3.0)
    lista = f"{tmp}/l.txt"; open(lista, "w").write("".join(f"file '{p}'\n" for p in partes))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lista, "-c", "copy", f"{tmp}/c.mp4"], check=True)
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{tmp}/c.mp4"]))
    musica = os.path.join(pv.BASE, "..", "tallerfatima", "herramientas", "musica.py")
    subprocess.run([sys.executable, musica, f"{tmp}/m.wav", str(dur + 0.5)], check=True)
    out = os.path.join(pv.BASE, "videos", "v2", salida)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{tmp}/c.mp4", "-i", f"{tmp}/m.wav", "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-af", f"afade=t=out:st={dur - 1.5}:d=1.5", "-shortest",
                    "-movflags", "+faststart", out], check=True)
    # cuadros sueltos para revisar
    os.makedirs(os.path.join(pv.BASE, "img", "viral"), exist_ok=True)
    cuadro_tapa().save(os.path.join(pv.BASE, "img", "viral", salida[:4] + "-adivina-tapa.jpg"), quality=90)
    cuadro_pregunta(ADIVINA[3], 4, 3).save(os.path.join(pv.BASE, "img", "viral", salida[:4] + "-adivina-pregunta.jpg"), quality=90)
    cuadro_respuesta(ADIVINA[3], 4).save(os.path.join(pv.BASE, "img", "viral", salida[:4] + "-adivina-respuesta.jpg"), quality=90)
    cuadro_cierre().save(os.path.join(pv.BASE, "img", "viral", salida[:4] + "-adivina-cierre.jpg"), quality=90)
    return out


QUINCHO = [  # (foto, nombre, detalle, precio showroom)
    ("20ff7ddca5b7", "Mesa plegable + 2 bancos", "Pino · 1,80 m · se guarda en cualquier lado", "$119.000"),
    ("3dd3dc79ac5a", "Mesa 2,40 m + 12 sillas", "Pino macizo al natural", "$465.000"),
    ("e66fed63ce82", "Mesa 2,40 m + 10 sillas", "Pino macizo de campo", "$439.000"),
]


def carrusel_quincho():
    out = os.path.join(pv.BASE, "img", "viral"); os.makedirs(out, exist_ok=True)
    W, H = 1080, 1350
    # Tapa
    L = pv.fondo_estudio(W, H, piso=0.999).convert("RGB"); d = ImageDraw.Draw(L)
    d.text((540, 150), "¿Cuál va en", font=f("InterDisplay-Black.otf", 120), fill=TX, anchor="ma")
    d.text((540, 290), "tu quincho?", font=f("InterDisplay-Black.otf", 120), fill=TERRA, anchor="ma")
    for k, q in enumerate(QUINCHO):
        im = pv.gradar(Image.open(os.path.join(P, q[0] + ".jpg")).convert("RGB").resize((300, 300), Image.LANCZOS))
        m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, 300, 300), 24, fill=255)
        x = 60 + k * 330; L.paste(im, (x, 500), m)
        d.ellipse((x + 110, 830, x + 190, 910), fill=TERRA)
        d.text((x + 150, 870), str(k + 1), font=f("Inter-Bold.otf", 48), fill="white", anchor="mm")
    d.text((540, 990), "Comentá 1, 2 o 3", font=f("Inter-Bold.otf", 64), fill=TX, anchor="ma")
    d.text((540, 1080), "Deslizá para ver cada uno →", font=f("Inter-Medium.otf", 40), fill=MU, anchor="ma")
    pv.sello(pv.firma(L)).save(os.path.join(out, "quincho-0.jpg"), quality=93)
    archivos = [os.path.join(out, "quincho-0.jpg")]
    for k, q in enumerate(QUINCHO, 1):
        L = pv.fondo_estudio(W, H, piso=0.999).convert("RGB"); d = ImageDraw.Draw(L)
        im = pv.gradar(Image.open(os.path.join(P, q[0] + ".jpg")).convert("RGB").resize((820, 820), Image.LANCZOS)
                       .filter(ImageFilter.UnsharpMask(radius=1.4, percent=60, threshold=2)))
        m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, 820, 820), 32, fill=255)
        s = Image.new("L", L.size, 0); s.paste(m, (138, 68))
        L.paste((90, 70, 50), (0, 0), s.filter(ImageFilter.GaussianBlur(24)).point(lambda v: int(v * 0.3)))
        L.paste(im, (130, 50), m)
        d.ellipse((160, 80, 270, 190), fill=TERRA)
        d.text((215, 135), str(k), font=f("InterDisplay-Black.otf", 72), fill="white", anchor="mm")
        d.text((90, 895), q[1], font=f("Inter-SemiBold.otf", 56), fill=TX)
        d.text((90, 965), q[2], font=f("Inter-Regular.otf", 34), fill=MU)
        d.text((90, 1010), q[3], font=f("InterDisplay-Black.otf", 80), fill=TERRA)
        pw = d.textlength(q[3], font=f("InterDisplay-Black.otf", 80))
        d.text((110 + pw, 1045), "en el showroom", font=f("Inter-Medium.otf", 32), fill=TX)
        p = os.path.join(out, f"quincho-{k}.jpg"); pv.sello(pv.firma(L)).save(p, quality=93); archivos.append(p)
    return archivos


ADIVINA2 = [
    ("18ac856e299b", "Mesa ratona Asia", "Pino macizo · 1,20 x 0,70", "$76.900", "$119.000"),
    ("390c2e3a3fd8", "Bahiut de pino 1,20 m", "Cajones y puertas", "$99.900", "$139.500"),
    ("0ebd6924f5f7", "Sillón nórdico matero", "Madera de paraíso", "$150.000", "$232.092"),
    ("a877114c9ffa", "Ropero 2 m + alzada", "Pino macizo · placard vestidor", "$339.900", "$489.000"),
]


def historia_producto(foto, nombre, detalle, show, ml, arriba, abajo, salida):
    L = pv.fondo_estudio(1080, 1920, piso=0.999).convert("RGB"); d = ImageDraw.Draw(L)
    placa(arriba, 150, d, f("Inter-Bold.otf", 44), TERRA)
    centrado(d, 295, nombre, f("Inter-SemiBold.otf", 62), TX)
    centrado(d, 380, detalle, f("Inter-Regular.otf", 38), MU)
    foto_tarjeta(L, foto, 450, 600)
    yb = 1090
    fm = f("Inter-Medium.otf", 44); t = "En Mercado Libre " + ml
    w = d.textlength(t, font=fm); x0 = 540 - w / 2
    d.text((x0, yb), t, font=fm, fill=MU)
    xa = x0 + d.textlength("En Mercado Libre ", font=fm)
    d.line((xa, yb + 28, x0 + w, yb + 28), fill=(190, 40, 40), width=6)
    centrado(d, yb + 66, "En el showroom", f("Inter-SemiBold.otf", 44), VERDE)
    centrado(d, yb + 116, show, f("InterDisplay-Black.otf", 130), TERRA)
    placa(abajo, yb + 270, d, f("Inter-Bold.otf", 44), VERDE)
    out = os.path.join(pv.BASE, "img", "viral", salida)
    pv.sello(pv.firma(L), k=1.45).save(out, quality=92); return out


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "semana1126":
    print(historia_producto("273c4058a4da", "Despensero porta microondas", "Pino macizo · 60 cm", "$95.900", "$159.900",
                            "STOCK DISPONIBLE", "Efectivo o transferencia", "1126-historia-despensero.jpg"))
    print(historia_producto("94a98b272182", "Cómoda chifonier 6 cajones", "Pino macizo", "$85.000", "$119.000",
                            "HOY SÁBADO ABRIMOS DE 11 A 16", "Vení a verla al showroom", "1128-historia-sabado.jpg"))
    ADIVINA[:] = ADIVINA2
    print(reel_adivina("1129-reel-adivina-precio-2.mp4"))
    sys.exit()

if __name__ == "__main__":
    print(reel_adivina())
    print(carrusel_quincho())

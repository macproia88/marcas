"""Semana de ejemplo para la propuesta de Instagram de La Presumida (pedido de Juan, 27/11/2026).
Usa solo fotos ya publicadas en @lapresumidapastas (fotos/full) y el logo de la tienda.
Estética de marca: crema, dorado, bordó / rosa viejo, poco negro.
Uso: python3 semana.py  -> propuesta/img/*.jpg y propuesta/img/reel-amasado.mp4
"""
import os, sys, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = os.path.join(B, "fotos", "full")
OUT = os.path.join(B, "propuesta", "img"); os.makedirs(OUT, exist_ok=True)
FU = os.path.join(B, "herramientas", "fuentes")
LOGO = os.path.join(B, "..", "..", "tienda", "img", "logo-lp.jpg")

CREMA, CREMA2 = (246, 239, 228), (236, 225, 208)
BORDO, ROSA, DORADO, TX, MU = (122, 40, 46), (196, 140, 135), (176, 138, 72), (58, 36, 32), (125, 104, 96)


def serif(s, w=500, it=False):
    f = ImageFont.truetype(os.path.join(FU, "Cormorant-Italic.ttf" if it else "Cormorant.ttf"), s)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f


def sans(s, n="Medium"): return ImageFont.truetype(os.path.join(FU, f"Inter-{n}.otf"), s)


def foto(nombre, w, h, fx=0.5, fy=0.5, zoom=1.0):
    im = Image.open(os.path.join(F, nombre + ".jpg")).convert("RGB")
    r = max(w / im.width, h / im.height) * zoom
    im = im.resize((int(im.width * r + 1), int(im.height * r + 1)), Image.LANCZOS)
    x = int((im.width - w) * fx); y = int((im.height - h) * fy)
    im = im.crop((x, y, x + w, y + h))
    im = ImageEnhance.Color(im).enhance(1.06); im = ImageEnhance.Contrast(im).enhance(1.04)
    return im.filter(ImageFilter.UnsharpMask(radius=1.2, percent=50, threshold=2))


def medallon(L, cx, cy, r=70):
    lg = Image.open(LOGO).convert("RGB").resize((int(r * 1.7), int(r * 1.55)), Image.LANCZOS)
    m = Image.new("L", (2 * r, 2 * r), 0); ImageDraw.Draw(m).ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=255)
    disco = Image.new("RGB", (2 * r, 2 * r), (255, 255, 255)); disco.paste(lg, ((2 * r - lg.width) // 2, (2 * r - lg.height) // 2 + 4))
    L.paste(disco, (cx - r, cy - r), m)
    ImageDraw.Draw(L).ellipse((cx - r, cy - r, cx + r, cy + r), outline=DORADO, width=3)


def degradado(L, y0, y1, color, a0=0, a1=230):
    g = Image.new("L", (1, y1 - y0))
    for i in range(y1 - y0): g.putpixel((0, i), int(a0 + (a1 - a0) * (i / (y1 - y0)) ** 1.4))
    g = g.resize((L.width, y1 - y0))
    L.paste(Image.new("RGB", (L.width, y1 - y0), color), (0, y0), g)


def centrado(d, y, t, f, c, W=1080): d.text((W // 2, y), t, font=f, fill=c, anchor="ma")


def pie(d, W, H, texto="WhatsApp Florida 11 6546-4546 · Beccar 11 4401-0033"):
    centrado(d, H - 70, texto, sans(26), CREMA, W)


def guardar(L, n): p = os.path.join(OUT, n); L.save(p, quality=92); return p


# ---------- piezas ----------
def portada_texto(fotoname, titulo, sub, n, fx=0.5, fy=0.5, W=1080, H=1350, zoom=1.0, chico=None):
    L = foto(fotoname, W, H, fx, fy, zoom); degradado(L, int(H * 0.45), H, BORDO, 0, 235)
    d = ImageDraw.Draw(L); medallon(L, W // 2, 110, 66)
    y = H - 420
    for linea in titulo.split("\n"):
        centrado(d, y, linea, serif(96, 600), CREMA, W); y += 100
    if chico: centrado(d, y + 6, chico, serif(44, 500, True), (240, 215, 200), W); y += 56
    centrado(d, y + 24, sub, sans(30), CREMA, W)
    return guardar(L, n)


def slide_producto(fotoname, num, nombre, linea, n, fx=0.5, fy=0.5):
    W, H = 1080, 1350
    L = Image.new("RGB", (W, H), CREMA); d = ImageDraw.Draw(L)
    im = foto(fotoname, 960, 960, fx, fy)
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, 960, 960), 40, fill=255)
    L.paste(im, (60, 60), m)
    d.ellipse((90, 90, 190, 190), fill=BORDO); d.text((140, 140), num, font=serif(64, 700), fill=CREMA, anchor="mm")
    centrado(d, 1060, nombre, serif(76, 600), BORDO)
    centrado(d, 1160, linea, sans(32, "Regular"), MU)
    d.line((440, 1230, 640, 1230), fill=DORADO, width=3)
    centrado(d, 1250, "La Presumida · Rica, fresca y casera", serif(34, 500, True), DORADO)
    return guardar(L, n)


def historia(fotoname, arriba, grande, abajo, n, fx=0.5, fy=0.5, opciones=None):
    W, H = 1080, 1920
    L = foto(fotoname, W, H, fx, fy); degradado(L, 0, 520, CREMA, 230, 0) if False else None
    degradado(L, 900, H, BORDO, 0, 240)
    d = ImageDraw.Draw(L); medallon(L, W // 2, 170, 80)
    y = 1180
    centrado(d, y, arriba, sans(34, "SemiBold"), (240, 215, 200)); y += 70
    for linea in grande.split("\n"):
        centrado(d, y, linea, serif(104, 600), CREMA); y += 108
    if opciones:
        y += 30
        for k, o in enumerate(opciones):
            d.rounded_rectangle((180, y, 900, y + 92), 46, fill=CREMA)
            d.text((540, y + 46), o, font=sans(38, "SemiBold"), fill=BORDO, anchor="mm"); y += 112
    if abajo: centrado(d, H - 150, abajo, sans(30), CREMA)
    return guardar(L, n)


def club(n):
    W, H = 1080, 1350
    L = Image.new("RGB", (W, H), (245, 226, 170)); d = ImageDraw.Draw(L)
    for x in range(-H, W, 60):  # rayas mostaza suaves
        d.line((x, 0, x + H, H), fill=(238, 214, 150), width=22)
    d.rounded_rectangle((60, 60, W - 60, H - 60), 40, fill=CREMA)
    medallon(L, W // 2, 190, 84)
    centrado(d, 310, "La Presumida", serif(80, 600), BORDO)
    centrado(d, 395, "CLUB", sans(40, "Bold"), DORADO)
    im = foto("DfcjDmJIU2H", 820, 420, 0.5, 0.5)
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, 820, 420), 30, fill=255); L.paste(im, (130, 480), m)
    centrado(d, 940, "1 kg de fideos de regalo", serif(78, 650), BORDO)
    centrado(d, 1035, "en tu primera compra de más de $10.000", sans(34, "Regular"), TX)
    centrado(d, 1100, "Sumate con tu DNI en el local o con el QR", sans(30, "Regular"), MU)
    d.rounded_rectangle((300, 1170, 780, 1250), 40, fill=BORDO)
    d.text((540, 1210), "Link en la bio", font=sans(34, "SemiBold"), fill=CREMA, anchor="mm")
    return guardar(L, n)


def reel_amasado(n="reel-amasado.mp4"):
    tmp = tempfile.mkdtemp(); partes = []
    escenas = [("DdpObzpDbvx", "Todo empieza acá.", 0.5, 0.5), ("DfcjDmJIU2H", "Amasado y cortado\nesta mañana.", 0.5, 0.5),
               ("DeP2Y5mDfyN", "Al huevo, verde\ny con tinta.", 0.5, 0.5), ("Dd_plwyjZWs", "Diez minutos en la olla.", 0.5, 0.6),
               ("Dd37KlojSB3", "Y la mesa\nestá lista.", 0.5, 0.6)]
    for k, (fo, t, fx, fy) in enumerate(escenas):
        L = foto(fo, 1080, 1920, fx, fy); degradado(L, 1000, 1360, BORDO, 0, 200); L.paste(Image.new('RGB', (1080, 560), BORDO), (0, 1360), Image.new('L', (1080, 560), 200)); d = ImageDraw.Draw(L)
        if k == 0: medallon(L, 540, 200, 80)
        y = 1420
        for linea in t.split("\n"):
            centrado(d, y, linea, serif(92, 600), CREMA); y += 96
        if k == len(escenas) - 1:
            centrado(d, y + 30, "Florida · Beccar · Rica, fresca y casera", sans(32), CREMA)
        p = f"{tmp}/{k}.png"; L.save(p); q = f"{tmp}/{k}.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", p, "-vf",
                        "scale=2160:3840,zoompan=z='1+0.0008*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=75:s=1080x1920:fps=25,format=yuv420p",
                        "-frames:v", "75", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", q], check=True)
        partes.append(q)
    open(f"{tmp}/l.txt", "w").write("".join(f"file '{p}'\n" for p in partes))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{tmp}/l.txt", "-c", "copy", f"{tmp}/c.mp4"], check=True)
    musica = os.path.join(B, "..", "tallerfatima", "herramientas", "musica.py")
    subprocess.run([sys.executable, musica, f"{tmp}/m.wav", "15.5"], check=True)
    out = os.path.join(OUT, n)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{tmp}/c.mp4", "-i", f"{tmp}/m.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-af", "afade=t=out:st=13.5:d=1.5", "-shortest", "-movflags", "+faststart", out], check=True)
    Image.open(partes and f"{tmp}/1.png").convert("RGB").save(os.path.join(OUT, "reel-amasado-tapa.jpg"), quality=88)
    return out


if __name__ == "__main__":
    # Lunes: carrusel "5 cenas resueltas"
    portada_texto("DeP2Y5mDfyN", "Tu semana,\nresuelta", "Deslizá y elegí tus 4 cenas →", "lun-0.jpg", chico="4 pastas para 4 noches")
    slide_producto("DfcjDmJIU2H", "1", "Cintas al huevo", "Diez minutos en la olla y a la mesa", "lun-1.jpg")
    slide_producto("De631ijgWBM", "2", "Ravioles tricolor", "Porque a veces no podés elegir un solo gusto", "lun-2.jpg")
    slide_producto("DfFK_35j_z4", "3", "Ñoquis de papa", "Con tuco, fileto o pesto", "lun-3.jpg", fy=0.45)
    slide_producto("DdwM3KKjLVI", "4", "Lasaña de la casa", "Entra al horno y sale humeante", "lun-4.jpg")
    historia("DfFK_35j_z4", "ENCUESTA", "¿Con qué salsa\nlos comés?", "", "lun-historia.jpg", opciones=["Tuco", "Fileto", "Pesto"])
    # Martes: reel
    reel_amasado()
    historia("DdpObzpDbvx", "HOY EN EL TALLER", "Masa recién\nhecha", "Lu a Sá 9 a 20 h · Do 9 a 14 h", "mar-historia.jpg")
    # Miércoles: adiviná
    portada_texto("DfPeKkeDEjc", "¿Adivinás\nel relleno?", "Comentá tu respuesta · mañana lo contamos", "mie-post.jpg", fx=0.5, chico="Masa negra de tinta de calamar")
    historia("DfPeKkeDEjc", "PISTA", "Viene del mar", "Respondé esta historia", "mie-historia.jpg")
    # Jueves: club
    club("jue-club.jpg")
    historia("DdgwJ92j6rk", "LA PRESUMIDA CLUB", "Tu primer kilo\nva de regalo", "Link en la bio", "jue-historia.jpg")
    # Viernes: lasaña + pedidos
    portada_texto("DexUs4WiHiq", "Viernes de\nlasaña", "Pedí por WhatsApp y pasá a buscarla", "vie-post.jpg", fy=0.6)
    historia("DdwM3KKjLVI", "PEDÍ POR WHATSAPP", "Florida\n11 6546-4546", "Beccar · 11 4401-0033", "vie-historia.jpg")
    # Sábado: Fiestas
    portada_texto("Deb-Q3Gj6A_", "Las Fiestas\nse amasan antes", "Encargá tus pastas con tiempo", "sab-0.jpg", chico="Arrollados, lasañas y rellenas")
    slide_producto("Deb-Q3Gj6A_", "1", "Arrollado de la casa", "Para la mesa de Navidad", "sab-1.jpg")
    slide_producto("DdwM3KKjLVI", "2", "Lasaña para compartir", "Se calienta y se sirve", "sab-2.jpg")
    slide_producto("DeP2Y5mDfyN", "3", "Raviolones especiales", "Al huevo, verdes y de tinta", "sab-3.jpg")
    historia("DexUs4WiHiq", "HOY SÁBADO", "Abrimos de\n9 a 20 h", "Florida · Beccar", "sab-historia.jpg")
    # Domingo
    portada_texto("Dd37KlojSB3", "Domingo de\nñoquis", "Abrimos de 9 a 14 h · Florida y Beccar", "dom-post.jpg", fy=0.6)
    historia("Dd_plwyjZWs", "DOMINGO", "Abrimos de\n9 a 14 h", "Florida · Beccar", "dom-historia.jpg", fy=0.6)
    print("listo")

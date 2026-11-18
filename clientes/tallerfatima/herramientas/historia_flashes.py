"""Historia animada estilo "flashes": las fotos aparecen una por una como fotos instantáneas,
con un destello blanco de cámara en cada una, y al final un llamado a ver el posteo.
Uso: python3 historia_flashes.py <carpeta_fuentes> <carpeta_frames> foto1 foto2 ...
"""
import sys, os, math, random
from PIL import Image, ImageDraw, ImageOps, ImageFilter
sys.argv, ARGS = sys.argv[:2], sys.argv[2:]
import armar_piezas as a

FR = ARGS[0]; FOTOS = ARGS[1:]
os.makedirs(FR, exist_ok=True)
W, H, FPS = 1080, 1920, 30
POR_FOTO = 1.35          # segundos entre flashes
FINAL = 3.2              # segundos con el texto final
random.seed(4)

fondo = Image.new("RGB", (W, H), a.VERDE)
hoja = Image.open(os.path.join(a.BASE, "marca", "hoja-verde.png")).convert("RGBA").resize((900, 650))
r, g, b, al = hoja.split()
hoja = Image.merge("RGBA", (r.point(lambda v: 0), g.point(lambda v: 160), b.point(lambda v: 90), al.point(lambda v: int(v * 0.35))))
fondo.paste(hoja, (380, 1350), hoja)
d = ImageDraw.Draw(fondo)
a.logo(fondo, a.LOGO_B, 380, 80, 110)
d.rounded_rectangle([80, 230, 80 + d.textlength("EXPO FÁTIMA 2026", font=a.LATOB(40)) + 56, 305], 37, fill=a.AMARILLO)
d.text((108, 244), "EXPO FÁTIMA 2026", font=a.LATOB(40), fill=a.MARRON)

def polaroid(ruta, ang):
    foto = a.recortar(ruta, 640, 640)
    marco = Image.new("RGB", (700, 820), "white")
    marco.paste(foto, (30, 30))
    sombra = Image.new("RGBA", (740, 860), (0, 0, 0, 0))
    ImageDraw.Draw(sombra).rectangle([20, 24, 720, 844], fill=(0, 0, 0, 110))
    sombra = sombra.filter(ImageFilter.GaussianBlur(14))
    sombra.paste(marco, (20, 20))
    return sombra.rotate(ang, resample=Image.BICUBIC, expand=True)

POS = [(-7, 170, 380), (6, 260, 470), (-3, 120, 560), (8, 290, 640), (-9, 150, 700), (4, 230, 600)]
piezas = []
for k, f in enumerate(FOTOS):
    ang, x, y = POS[k % len(POS)]
    piezas.append((polaroid(f, ang), x + random.randint(-20, 20), y + random.randint(-20, 20)))

total = int((len(piezas) * POR_FOTO + FINAL) * FPS)
n = 0
for i in range(total):
    t = i / FPS
    k = min(int(t // POR_FOTO), len(piezas) - 1)
    lienzo = fondo.copy()
    for j in range(k + 1):
        p, x, y = piezas[j]
        dt = t - j * POR_FOTO
        esc = 1.0 if j < k or dt > 0.25 else 1.12 - 0.12 * (dt / 0.25)   # pequeño "golpe" al aparecer
        pp = p if esc == 1.0 else p.resize((int(p.width * esc), int(p.height * esc)))
        lienzo.paste(pp, (x - (pp.width - p.width) // 2, y - (pp.height - p.height) // 2), pp)
    fin = t > len(piezas) * POR_FOTO
    if fin:
        dd = ImageDraw.Draw(lienzo)
        alpha = min(1, (t - len(piezas) * POR_FOTO) / 0.4)
        caja = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dc = ImageDraw.Draw(caja)
        dc.rounded_rectangle([70, 1500, W - 70, 1800], 40, fill=(255, 203, 51, int(250 * alpha)))
        a.texto_lineas(dc, ["Mirá el posteo", "completo"], a.SP(84), 120, 1535, (82, 69, 59, int(255 * alpha)), 1.02)
        cx, cy = W - 210, 1650 + int(12 * math.sin(t * 7))
        dc.polygon([(cx, cy - 70), (cx - 55, cy), (cx - 20, cy), (cx - 20, cy + 60), (cx + 20, cy + 60), (cx + 20, cy), (cx + 55, cy)], fill=(82, 69, 59, int(255 * alpha)))
        lienzo.paste(caja, (0, 0), caja)
    # destello de flash al aparecer cada foto
    dt = t - k * POR_FOTO
    if not fin and dt < 0.22:
        lienzo = Image.blend(lienzo, Image.new("RGB", (W, H), "white"), 0.85 * (1 - dt / 0.22))
    lienzo.save(os.path.join(FR, f"f{n:04d}.jpg"), quality=90); n += 1
print(n, "frames", round(n / FPS, 1), "s")

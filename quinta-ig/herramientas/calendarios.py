"""Calendarios de disponibilidad (diseño verde/rojo), 2 meses por hoja, uno por quinta.
Uso: python3 quinta-ig/herramientas/calendarios.py   (desde la raíz del repo)
Lee quinta-ig/bot/quinta.json y genera quinta-ig/calendarios/{dia,casa}-{1,2,3}.jpg
(los próximos 6 meses desde el mes actual). Correr cada vez que se carga una reserva."""
import json, calendar, datetime, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
BASE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(BASE))
q = json.load(open(os.path.join(RAIZ, "quinta-ig/bot/quinta.json"), encoding="utf-8"))
alq = {(c["fecha"], c["quinta"]) for c in q["calendario"]}
FU = os.path.join(BASE, "fuentes") + "/"
PB, PM, PR, LI = FU + "Poppins-Bold.ttf", FU + "Poppins-Medium.ttf", FU + "Poppins-Regular.ttf", FU + "Lora-Italic-Variable.ttf"
F = lambda p, s: ImageFont.truetype(p, s)
VERDE, VERDE2, ROJO, ROSA, ORO, BLANCO = (28, 62, 38), (46, 96, 58), (178, 30, 36), (246, 208, 210), (232, 190, 90), (255, 255, 255)
MESES = ['', 'ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
DIAS = ['LUN', 'MAR', 'MIÉ', 'JUE', 'VIE', 'SÁB', 'DOM']
AHORA = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3)))
HOY = AHORA.date()
NOMBRE = {'dia': 'Quinta de día', 'casa': 'Quinta con casa'}
W, H, RH = 1080, 1920, 92

def cubrir(im):
    im = ImageOps.exif_transpose(im).convert('RGB'); r = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS); x = (im.width - W) // 2; y = (im.height - H) // 2
    return im.crop((x, y, x + W, y + H))

def cen(d, y, t, f, c, x0=0, x1=W, sombra=False):
    w = d.textlength(t, font=f); x = x0 + (x1 - x0 - w) / 2
    if sombra: d.text((x + 4, y + 4), t, font=f, fill=(0, 0, 0, 170))
    d.text((x, y), t, font=f, fill=c); return x + w

def corazon(d, x, y, s, c):
    d.ellipse((x, y, x + s * .55, y + s * .55), fill=c); d.ellipse((x + s * .45, y, x + s, y + s * .55), fill=c)
    d.polygon([(x + s * .03, y + s * .38), (x + s * .97, y + s * .38), (x + s * .5, y + s * .95)], fill=c)

def alto(a, m): return 110 + len(calendar.Calendar(0).monthdayscalendar(a, m)) * RH + 12

def mes(d, x0, y0, x1, a, m, qq):
    sem = calendar.Calendar(0).monthdayscalendar(a, m); h = alto(a, m)
    d.rounded_rectangle((x0, y0, x1, y0 + h), radius=26, fill=BLANCO)
    d.rounded_rectangle((x0, y0, x1, y0 + 66), radius=26, fill=VERDE); d.rectangle((x0, y0 + 40, x1, y0 + 66), fill=VERDE)
    cen(d, y0 + 8, f'{MESES[m]} {a}', F(PB, 38), BLANCO, x0, x1)
    cw = (x1 - x0) / 7; yh = y0 + 66
    d.rectangle((x0, yh, x1, yh + 44), fill=VERDE2)
    for i, t in enumerate(DIAS): cen(d, yh + 8, t, F(PM, 22), BLANCO, x0 + i * cw, x0 + (i + 1) * cw)
    for r, s in enumerate(sem):
        for c, dd in enumerate(s):
            cx0 = x0 + c * cw; cy0 = yh + 44 + r * RH; cx1 = cx0 + cw; cy1 = cy0 + RH
            if r < len(sem) - 1: d.line((cx0, cy1, cx1, cy1), fill=(225, 225, 225), width=2)
            if c: d.line((cx0, cy0, cx0, cy1), fill=(225, 225, 225), width=2)
            if not dd: continue
            fe = datetime.date(a, m, dd); oc = (fe.isoformat(), qq) in alq
            if oc:
                d.rectangle((cx0 + 2, cy0 + 2, cx1 - 2, cy1 - 2), fill=ROSA)
                cen(d, cy0 + 8, str(dd), F(PB, 34), ROJO, cx0, cx1)
                ft = F(PB, 15); t = 'ALQUILADA'; tw = d.textlength(t, font=ft)
                d.rounded_rectangle(((cx0 + cx1 - tw) / 2 - 7, cy1 - 30, (cx0 + cx1 + tw) / 2 + 7, cy1 - 8), radius=4, fill=ROJO)
                d.text(((cx0 + cx1 - tw) / 2, cy1 - 29), t, font=ft, fill=BLANCO)
            else:
                cen(d, cy0 + (RH - 46) / 2, str(dd), F(PB, 34), (190, 190, 190) if fe < HOY else VERDE, cx0, cx1)
    return y0 + h

def hoja(qq, meses, sal):
    im = cubrir(Image.open(os.path.join(BASE, 'fondos', qq + '.jpg'))).filter(ImageFilter.GaussianBlur(1.2)).convert('RGBA')
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for y in range(H): od.line((0, y, W, y), fill=(10, 25, 15, int(110 + 70 * abs(y / H - 0.5))))
    im = Image.alpha_composite(im, ov); d = ImageDraw.Draw(im)
    cen(d, 40, NOMBRE[qq], F(LI, 72), ORO, sombra=True)
    cen(d, 135, 'CALENDARIO', F(PB, 128), BLANCO, sombra=True)
    ft = F(PB, 40); t = '— DISPONIBILIDAD —'; tw = d.textlength(t, font=ft)
    d.polygon([((W - tw) / 2 - 60, 300), ((W + tw) / 2 + 60, 300), ((W + tw) / 2 + 40, 330), ((W + tw) / 2 + 60, 360), ((W - tw) / 2 - 60, 360), ((W - tw) / 2 - 40, 330)], fill=VERDE2)
    cen(d, 303, t, ft, BLANCO)
    tot = alto(*meses[0]) + alto(*meses[1]) + 24; y0 = 390 + (1330 - tot) // 2
    y1 = mes(d, 60, y0, W - 60, *meses[0], qq); mes(d, 60, y1 + 24, W - 60, *meses[1], qq)
    y = 1735
    d.ellipse((90, y + 8, 118, y + 36), fill=ROJO); d.text((130, y + 2), 'ALQUILADA', font=F(PM, 28), fill=BLANCO)
    d.ellipse((330, y + 8, 358, y + 36), fill=BLANCO); d.text((370, y + 2), 'DISPONIBLE', font=F(PM, 28), fill=BLANCO)
    cen(d, y - 6, 'QUINTA', F(LI, 30), ORO, 600, 1020); cen(d, y + 24, 'EL FLORIDO', F(PB, 40), BLANCO, 600, 1020)
    d.rounded_rectangle((60, 1810, W - 60, 1880), radius=18, fill=VERDE)
    xe = cen(d, 1818, 'Planificá ahora, disfrutá después  ', F(LI, 40), ORO); corazon(d, xe - 14, 1832, 30, ORO)
    d.text((W - 330, 1888), 'Actualizado ' + AHORA.strftime('%d/%m/%Y %H:%M'), font=F(PR, 20), fill=(220, 220, 220))
    im.convert('RGB').save(sal, quality=90)

if __name__ == '__main__':
    a, m = HOY.year, HOY.month; meses = []
    for _ in range(6): meses.append((a, m)); m += 1; a, m = (a + 1, 1) if m == 13 else (a, m)
    out = os.path.join(RAIZ, 'quinta-ig/calendarios'); os.makedirs(out, exist_ok=True)
    for qq in ('dia', 'casa'):
        for i in range(3):
            hoja(qq, meses[2 * i:2 * i + 2], os.path.join(out, f'{qq}-{i + 1}.jpg'))
    print('calendarios OK', AHORA.strftime('%d/%m %H:%M'))

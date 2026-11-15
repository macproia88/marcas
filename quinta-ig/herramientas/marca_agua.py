"""Uso: python3 marca_agua.py entrada.jpg salida.jpg  -> foto con marca de agua @quintaelflorido"""
import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def marcar(ent, sal):
    im = ImageOps.exif_transpose(Image.open(ent)).convert('RGB'); im.thumbnail((1440, 1440))
    W, H = im.size; capa = Image.new('RGBA', (W*2, H*2), (0, 0, 0, 0)); d = ImageDraw.Draw(capa)
    f = ImageFont.truetype(F, max(28, W//18)); t = '@quintaelflorido'; tw = d.textlength(t, font=f)
    for y in range(0, H*2, int(W/3.2)):
        for x in range(-int(tw), W*2, int(tw*1.6)):
            d.text((x + (y//int(W/3.2) % 2)*tw*0.8, y), t, font=f, fill=(255, 255, 255, 45))
    capa = capa.rotate(30, resample=Image.BICUBIC).crop((W//2, H//2, W//2+W, H//2+H))
    im = Image.alpha_composite(im.convert('RGBA'), capa); d = ImageDraw.Draw(im)
    f2 = ImageFont.truetype(F, max(24, W//24)); t2 = 'Quinta El Florido · @quintaelflorido'
    w2 = d.textlength(t2, font=f2); p = 14
    d.rounded_rectangle((W-w2-3*p, H-f2.size-3*p, W-p, H-p), radius=12, fill=(0, 0, 0, 150))
    d.text((W-w2-2*p, H-f2.size-2*p-3), t2, font=f2, fill='white')
    im.convert('RGB').save(sal, quality=88)
if __name__ == '__main__': marcar(sys.argv[1], sys.argv[2])

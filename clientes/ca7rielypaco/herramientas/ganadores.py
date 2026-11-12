# Genera los 7 diseños '¡GANARON!' (foto arriba, texto abajo: el texto nunca tapa caras).
# Uso: python3 clientes/ca7rielypaco/herramientas/ganadores.py  -> deja PNG en herramientas/fuentes/ (copiar a img/ y plan/img/)
import sys, pathlib
from playwright.sync_api import sync_playwright
REPO = pathlib.Path(__file__).resolve().parent.parent
HERE = pathlib.Path(__file__).resolve().parent / 'fuentes'
P = [  # foto, posición vertical del recorte (%), categoría, obra  (fotos nuevas de la clienta, 11/11)
 ('16-show-guitarra.jpg', 50, 'Grabación del Año', '“HA HA”'),
 ('17-alfombra-grammy-gris.jpg', 8, 'Álbum del Año', 'FREE SPIRITS'),
 ('19-smoking-negro.jpg', 23, 'Canción del Año', '“HASTA JESÚS TUVO UN MAL DÍA” FT. STING'),
 ('18-azul-gris-anteojos.jpg', 17, 'Mejor Interpretación de Música Electrónica', '“BETO’S HORNS” (FRED AGAIN.. REMIX)'),
 ('21-trajes-blancos-rosa.jpg', 3, 'Mejor Canción Pop/Rock', '“HASTA JESÚS TUVO UN MAL DÍA” FT. STING'),
 ('22-trajes-blancos-pose.jpg', 12, 'Mejor Álbum de Música Alternativa', 'FREE SPIRITS'),
 ('20-brindis-azul.jpg', 23, 'Mejor Video Musical Versión Larga', 'FREE SPIRITS (THE FILM)'),
]
CSS = f'''
@font-face{{font-family:Anton;src:url({HERE}/anton-latin-400-normal.woff2)}}
@font-face{{font-family:Oswald;font-weight:500;src:url({HERE}/oswald-latin-500-normal.woff2)}}
@font-face{{font-family:Oswald;font-weight:700;src:url({HERE}/oswald-latin-700-normal.woff2)}}
@font-face{{font-family:Playfair;font-style:italic;font-weight:700;src:url({HERE}/playfair-display-latin-700-italic.woff2)}}
*{{box-sizing:border-box;margin:0}}
body{{width:1080px;height:1350px;background:#ece3da;color:#1c1716;font-family:Oswald;overflow:hidden}}
.p{{position:absolute;inset:0;padding:48px 56px 44px;display:flex;flex-direction:column}}
.mast{{display:flex;justify-content:space-between;align-items:flex-end;border-bottom:2px solid #1c1716;padding-bottom:14px}}
.logo{{font-family:Anton;font-size:58px;line-height:1}} .logo b{{color:#a8706a;font-weight:400}}
.iss{{text-align:right;font-weight:500;letter-spacing:.2em;font-size:19px;line-height:1.35}}
.foto{{margin-top:26px;height:735px;overflow:hidden;background:#d8cdc3}}
.foto img{{width:104%;margin-left:-2%;height:100%;object-fit:cover;display:block}}
.txt{{flex:1;display:flex;flex-direction:column;justify-content:flex-end}}
.chip{{margin-top:22px;align-self:flex-start;background:#1c1716;color:#ece3da;font-weight:700;letter-spacing:.2em;font-size:22px;padding:8px 18px}}
h1{{font-family:Anton;font-weight:400;font-size:140px;line-height:1;margin-top:8px}}
.cat{{font-family:Playfair;font-style:italic;font-weight:700;color:#a8706a;line-height:1.1;margin-top:2px}}
.rule{{border-top:2px solid #1c1716;margin:18px 0 14px}}
.obra{{font-weight:700;letter-spacing:.06em;font-size:30px}}
.ed{{font-family:Playfair;font-style:italic;font-weight:700;font-size:28px;margin-top:4px}}
.foot{{display:flex;justify-content:space-between;margin-top:22px;font-weight:500;letter-spacing:.2em;font-size:17px;color:#8a7f78}}
'''
def html(f, y, cat, obra):
    cs = 50 if len(cat) < 24 else (42 if len(cat) < 36 else 38)
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body><div class="p">
<div class="mast"><div class="logo">CA7RIEL <b>&amp;</b> PACO</div><div class="iss">EDICIÓN ESPECIAL<br>LATIN GRAMMY 2026</div></div>
<div class="foto"><img src="{REPO}/fotos-hd/{f}" style="object-position:50% {y}%"></div>
<div class="txt"><div class="chip">GANADORES · LATIN GRAMMY 2026</div><h1>¡GANARON!</h1>
<div class="cat" style="font-size:{cs}px">{cat}</div><div class="rule"></div>
<div class="obra">{obra}</div><div class="ed">27.ª edición de los Latin Grammy · Las Vegas</div>
<div class="foot"><span>@CA7RIELYPACOAMOROSOARG</span><span>FAN CLUB ARGENTINA</span></div></div></div></body></html>'''
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width':1080,'height':1350})
    for i, row in enumerate(P, 1):
        h = HERE / f'g{i}.html'; h.write_text(html(*row))
        pg.goto(h.as_uri()); pg.wait_for_timeout(400)
        over = pg.evaluate("document.querySelector('.txt').scrollHeight > document.querySelector('.txt').clientHeight + 1")
        pg.screenshot(path=str(HERE / f'g{i}.png'))
        print(i, 'DESBORDA' if over else 'ok')
    b.close()

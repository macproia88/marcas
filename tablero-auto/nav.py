"""Pone (o actualiza) abajo de cada página del negocio los links a todas las demás.

Uso:  python3 tablero-auto/nav.py            -> todas las páginas de PAGINAS que existan en el repo
Regla: si se agrega una página nueva del negocio, sumarla a PAGINAS y correr este script.
actualizar.py y reconocimiento.py ya lo corren solos.
"""
import pathlib, re

RAIZ = pathlib.Path(__file__).resolve().parent.parent
BASE = 'https://macproia88.github.io/marcas/'
# (archivo en este repo o URL externa, nombre)
PAGINAS = [
    ('tablero-presumida-v2.html', 'Tablero La Presumida'),
    ('mostrador.html', 'Tablero de mostrador'),
    ('apps.html', 'Tablero de apps'),
    ('tablero-club.html', 'Tablero del club'),
    ('reconocimiento.html', 'Agenda de reconocimiento'),
    ('ranking-anual.html', 'Ranking del año'),
    ('ranking-mostrador.html', 'Ranking de mostrador'),
    ('https://macproia88.github.io/sel-oct26-presumida/', 'Selección de personal (CVs)'),
]
MARCA = re.compile(r'<nav id="lp-nav".*?</nav>\s*', re.S)
ESTILO = ('font:13px/1.6 system-ui,-apple-system,Segoe UI,sans-serif;max-width:1180px;margin:24px auto 16px;'
          'padding:12px 16px;border-top:1px solid rgba(128,128,128,.35);color:#6b6b6b')


def nav(actual):
    links = []
    for href, nombre in PAGINAS:
        if href == actual:
            links.append(f'<b style="color:inherit">{nombre}</b>')
        else:
            links.append(f'<a href="{href}" style="color:#b85042;text-decoration:none;white-space:nowrap">{nombre}</a>')
    return (f'<nav id="lp-nav" style="{ESTILO}"><div style="font-weight:600;margin-bottom:4px">Páginas del negocio</div>'
            + ' · '.join(links) + '</nav>\n')


def poner(path):
    h = path.read_text(encoding='utf-8')
    h = MARCA.sub('', h)
    i = h.lower().rfind('</body>')
    h = (h[:i] + nav(path.name) + h[i:]) if i >= 0 else h + nav(path.name)
    path.write_text(h, encoding='utf-8')


def main():
    for href, _ in PAGINAS:
        p = RAIZ / href
        if not href.startswith('http') and p.exists():
            poner(p)
            print('links:', href)


if __name__ == '__main__':
    main()

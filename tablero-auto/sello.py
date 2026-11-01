"""Pone (o actualiza) la línea "Última actualización" en las páginas de la web.

Uso:
  python3 tablero-auto/sello.py archivo.html [archivo2.html ...]          -> fecha y hora de ahora
  python3 tablero-auto/sello.py --git archivo.html [...]                  -> fecha y hora del último cambio en git

Regla: toda página que se suba a la web lleva esta línea. Se corre cada vez que se cambia una página.
El tablero principal (tablero-presumida-v2.html) ya la pone solo con actualizar.py.
"""
import re, sys, subprocess, datetime as dt, pathlib

AR = dt.timezone(dt.timedelta(hours=-3))
MARCA = re.compile(r'<div id="lp-upd"[^>]*>.*?</div>\s*', re.S)


def cuando_git(path):
    out = subprocess.run(['git', 'log', '-1', '--format=%cI', '--', path.name], cwd=path.parent,
                         capture_output=True, text=True).stdout.strip()
    return dt.datetime.fromisoformat(out).astimezone(AR) if out else dt.datetime.now(AR)


def sellar(path, cuando):
    h = path.read_text(encoding='utf-8')
    div = (f'<div id="lp-upd" style="font:12px/1.4 system-ui,-apple-system,Segoe UI,sans-serif;color:#6b6b6b;'
           f'text-align:right;padding:6px 16px">Última actualización: {cuando:%d/%m/%Y} a las {cuando:%H:%M} (hora Argentina)</div>\n')
    h = MARCA.sub('', h)
    m = re.search(r'<body[^>]*>', h, re.I)
    h = h[:m.end()] + '\n' + div + h[m.end():] if m else div + h
    path.write_text(h, encoding='utf-8')
    print(f'{path.name}: {cuando:%d/%m/%Y %H:%M}')


if __name__ == '__main__':
    args = sys.argv[1:]
    usar_git = '--git' in args
    for a in [x for x in args if x != '--git']:
        p = pathlib.Path(a).resolve()
        sellar(p, cuando_git(p) if usar_git else dt.datetime.now(AR))

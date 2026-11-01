"""Arma ../reconocimiento.html (Agenda de reconocimiento) para la web, con los mismos datos y reglas
que el tablero de reconocimiento de Claude. Datos: data/recon_locales.json y data/recon_vendedoras.json.
Uso: python3 tablero-auto/reconocimiento.py
"""
import json, pathlib, datetime as dt
AQUI = pathlib.Path(__file__).resolve().parent
SRC, DATA = AQUI / 'src', AQUI / 'data'
SALIDA = AQUI.parent / 'reconocimiento.html'
AR = dt.timezone(dt.timedelta(hours=-3))

SHIM = """(function(){
  const RAW = window.__REC__, CALC = {}, CACHE = {}, DRAW = {};
  const data = (id) => {
    if (RAW[id]) return {status: 'ok', data: RAW[id]};
    if (CALC[id]) { if (!CACHE[id]) CACHE[id] = CALC[id].fn(...CALC[id].inputs.map((i) => data(i).data)); return {status: 'ok', data: CACHE[id]}; }
    return {status: 'missing', data: []};
  };
  const run = (id) => { const f = DRAW[id]; if (!f) return; document.querySelectorAll('[data-draw="' + id + '"]').forEach((el) => { try { f(el); } catch (e) { console.error(e); } }); };
  window.dash = {
    calc: (id, o) => { CALC[id] = o; },
    data,
    onData: (f) => { document.addEventListener('DOMContentLoaded', f); },
    draw: (id, f) => { if (f) DRAW[id] = f; if (document.readyState !== 'loading') run(id); },
    colors: ['#c2410c', '#94a3b8', '#0f766e', '#7c3aed']
  };
  document.addEventListener('DOMContentLoaded', () => Object.keys(DRAW).forEach(run));
})();"""

def main():
    D = {'locales': json.loads((DATA / 'recon_locales.json').read_text(encoding='utf-8')),
         'vendedoras': json.loads((DATA / 'recon_vendedoras.json').read_text(encoding='utf-8'))}
    css = (SRC / 'standalone.css').read_text(encoding='utf-8')
    d3 = (SRC / 'd3.min.js').read_text(encoding='utf-8')
    page = (SRC / 'reconocimiento_page.html').read_text(encoding='utf-8').replace('<meta name="dash-one-writer">', '')
    out = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Reconocimiento Octubre</title>
<style>{css}</style>
<script>{d3}</script>
<script>window.__REC__={json.dumps(D, ensure_ascii=False, separators=(',', ':'))};</script>
<script>{SHIM}</script>
</head><body><div class="wrap"><div id="dash-root">
{page}
</div></div></body></html>"""
    SALIDA.write_text(out, encoding='utf-8')
    print('armado', SALIDA.name)
    import nav; nav.main()

if __name__ == '__main__':
    main()

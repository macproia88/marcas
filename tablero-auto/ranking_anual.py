"""Ranking del año: qué local fue el mejor en cada KPI, mes a mes (enero a último mes completo).

Uso: python3 tablero-auto/ranking_anual.py   (actualizar.py lo corre solo)
Fuentes:
  - data/ventas_diarias.json (venta, tickets de mostrador, venta y pedidos de apps por día y local), sumado por mes.
  - data/apps_cierres.json vía canales.cierres_apps (lo facturado y lo que llega al local de PedidosYa y Rappi).
Solo entran los meses con al menos 25 días cargados en los 3 locales.
"""
import json, pathlib, html, datetime as dt
import canales

RAIZ = pathlib.Path(__file__).resolve().parent.parent
LOC = ['Florida', 'Beccar', 'Paz']
MESN = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
COL = {'Florida': '#b85042', 'Beccar': '#3b2e2a', 'Paz': '#8c6b3f'}


def mfmt(v): return f'${v/1e6:,.1f}M'.replace(',', 'X').replace('.', ',').replace('X', '.')
def nfmt(v, d=0): return f'{v:,.{d}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
def pfmt(v): return ('+' if v > 0 else '') + nfmt(v * 100, 1) + '%'


def datos():
    V = canales.cargar('ventas_diarias.json')
    ult = max(x['fecha'] for x in V)
    M = canales.mensual(V, ult[:7])
    m = {(r['mes'], r['local']): r for r in M if r['local'] in LOC and r['mes'] >= '2026-01'}
    meses = sorted({k[0] for k in m if all((k[0], L) in m and m[(k[0], L)]['dias'] >= 25 for L in LOC)})
    cier = canales.cierres_apps(canales.cargar('apps_det.json'))
    llega = {}
    for r in cier:
        if r['deposito'] is None or not r['venta']: continue
        a = llega.setdefault((r['mes'], r['local']), [0, 0]); a[0] += r['deposito']; a[1] += r['venta']
    K = {}  # kpi -> mes -> local -> valor
    def put(k, mes, L, v):
        if v is not None: K.setdefault(k, {}).setdefault(mes, {})[L] = v
    for i, mes in enumerate(meses):
        for L in LOC:
            r = m[(mes, L)]; d = r['dias']
            put('venta', mes, L, r['venta_mostrador'] + r['venta_app'])
            put('clientes', mes, L, r['tickets'] / d)
            put('ticket', mes, L, r['venta_mostrador'] / r['tickets'])
            put('pedidos', mes, L, r['pedidos'] / d)
            x = llega.get((mes, L)); put('llega', mes, L, x[0] / x[1] if x else None)
            if i:
                p = m[(meses[i - 1], L)]; pd_ = p['dias']
                put('crec_venta', mes, L, ((r['venta_mostrador'] + r['venta_app']) / d) / ((p['venta_mostrador'] + p['venta_app']) / pd_) - 1)
                put('crec_clientes', mes, L, (r['tickets'] / d) / (p['tickets'] / pd_) - 1)
                put('crec_pedidos', mes, L, (r['pedidos'] / d) / (p['pedidos'] / pd_) - 1 if p['pedidos'] else None)
    return meses, K


KPIS = [  # clave, nombre, formato, tipo, explicación
    ('venta', 'Venta total', mfmt, 'tamaño', 'Mostrador más apps, en pesos.'),
    ('clientes', 'Clientes de mostrador por día', lambda v: nfmt(v), 'tamaño', 'Tickets de mostrador ÷ días con venta.'),
    ('pedidos', 'Pedidos de apps por día', lambda v: nfmt(v), 'tamaño', 'PedidosYa + Rappi ÷ días con venta.'),
    ('ticket', 'Ticket promedio de mostrador', lambda v: '$' + nfmt(v), 'gestión', 'Venta de mostrador ÷ tickets.'),
    ('crec_venta', 'Crecimiento de la venta', pfmt, 'gestión', 'Venta por día contra el mes anterior del mismo local.'),
    ('crec_clientes', 'Crecimiento de clientes de mostrador', pfmt, 'gestión', 'Clientes por día contra el mes anterior del mismo local.'),
    ('crec_pedidos', 'Crecimiento de pedidos de apps', pfmt, 'gestión', 'Pedidos por día contra el mes anterior del mismo local.'),
    ('llega', 'Lo que llega al local de las apps', lambda v: nfmt(v * 100) + '%', 'gestión', 'De cada $100 facturados en PedidosYa y Rappi, cuánto llega al local (liquidaciones; enero a abril incluye lo cobrado en efectivo).'),
]


def armar():
    meses, K = datos()
    gan = {}  # kpi -> mes -> local ganador
    for k, *_ in KPIS:
        for mes, vals in K.get(k, {}).items():
            if len(vals) == 3: gan.setdefault(k, {})[mes] = max(vals, key=vals.get)
    tot = {L: 0 for L in LOC}; totg = {L: 0 for L in LOC}
    for k, _, _, tipo, _ in KPIS:
        for L in gan.get(k, {}).values():
            tot[L] += 1
            if tipo == 'gestión': totg[L] += 1
    ahora = dt.datetime.now(dt.timezone(dt.timedelta(hours=-3)))
    chip = lambda L: f'<span class="chip" style="background:{COL[L]}">{L}</span>'
    # medallero
    med = ''.join(f'<tr><td>{chip(L)}</td><td class="n">{tot[L]}</td><td class="n">{totg[L]}</td><td class="n">{tot[L]-totg[L]}</td></tr>'
                  for L in sorted(LOC, key=lambda L: (-totg[L], -tot[L])))
    secs = ''
    for k, nombre, fmt, tipo, expl in KPIS:
        g = gan.get(k, {})
        if not g: continue
        cnt = {L: sum(1 for x in g.values() if x == L) for L in LOC}
        filas = ''
        for mes in meses:
            vals = K.get(k, {}).get(mes)
            if not vals or len(vals) < 3: continue
            w = g[mes]
            filas += f'<tr><td>{MESN[int(mes[5:]) - 1]}</td>' + ''.join(
                f'<td class="n{" win" if L == w else ""}">{fmt(vals[L])}</td>' for L in LOC) + f'<td>{chip(w)}</td></tr>'
        resumen = ' · '.join(f'{L} {cnt[L]}' for L in sorted(LOC, key=lambda L: -cnt[L]))
        secs += (f'<section class="card"><h2>{html.escape(nombre)} <span class="tag {tipo}">{tipo}</span></h2>'
                 f'<p class="note">{html.escape(expl)} Meses ganados: <b>{resumen}</b>.</p>'
                 f'<div class="tw"><table><thead><tr><th>Mes</th>' + ''.join(f'<th class="n">{L}</th>' for L in LOC) +
                 f'<th>Mejor</th></tr></thead><tbody>{filas}</tbody></table></div></section>')
    desde, hasta = MESN[int(meses[0][5:]) - 1], MESN[int(meses[-1][5:]) - 1]
    css = """:root{--bg:#f7f3ed;--panel:#fff;--fg:#2b211d;--muted:#6b625c;--line:#e7dfd6;--win:#e6f2ea;--ok:#2f6b4f}
@media (prefers-color-scheme:dark){:root{--bg:#1c1917;--panel:#26211e;--fg:#f2ece6;--muted:#b3a89f;--line:#3a332e;--win:#20382b;--ok:#6fbf8f}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1000px;margin:0 auto;padding:8px 16px 30px}h1{font:400 30px/1.15 Georgia,serif;margin:6px 0 4px}h2{font-size:17px;margin:0 0 4px}
.sub,.note{color:var(--muted)}.note{font-size:13px;margin:0 0 10px}.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:14px}
table{width:100%;border-collapse:collapse;font-size:14px}th,td{padding:7px 8px;border-bottom:1px solid var(--line);text-align:left}th{font-size:12px;color:var(--muted)}
.n{text-align:right;font-variant-numeric:tabular-nums}td.win{background:var(--win);font-weight:700;color:var(--ok)}.tw{overflow-x:auto}
.chip{color:#fff;border-radius:999px;padding:2px 9px;font-size:12px;white-space:nowrap}.tag{font-size:11px;font-weight:600;border-radius:4px;padding:1px 6px;vertical-align:2px;border:1px solid var(--line);color:var(--muted)}
.tag.gestión{color:var(--ok);border-color:var(--ok)}
@media (max-width:640px){h1{font-size:23px}.card{padding:12px}table{font-size:12.5px}th,td{padding:6px 5px}}"""
    out = f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ranking del año</title><style>{css}</style></head><body>
<div class="wrap"><h1>Ranking del año</h1>
<p class="sub">Qué local fue el mejor en cada indicador, mes a mes · {desde} a {hasta} 2026 · los 3 locales. En verde, el mejor de cada mes.</p>
<section class="card"><h2>Meses ganados en el año</h2><p class="note">Cuántas veces salió primero cada local, sumando todos los indicadores y meses. <b>Gestión</b> = indicadores que no dependen del tamaño del local (ticket, crecimiento contra el mes anterior y lo que llega de las apps): es la comparación más justa. <b>Tamaño</b> = venta, clientes y pedidos totales, que suele ganar el local más grande.</p>
<div class="tw"><table><thead><tr><th>Local</th><th class="n">Total</th><th class="n">Gestión</th><th class="n">Tamaño</th></tr></thead><tbody>{med}</tbody></table></div></section>
{secs}
<p class="note">Fuentes: venta, tickets y pedidos por día del tablero La Presumida (venta detallada de Maxi Rest y cierres de caja); apps: estados de cuenta de PedidosYa y liquidaciones de Rappi (octubre de PedidosYa con el detalle de pedidos; octubre de Rappi estimado). Los crecimientos arrancan en febrero porque no hay diciembre 2025 cargado.</p>
</div></body></html>"""
    (RAIZ / 'ranking-anual.html').write_text(out, encoding='utf-8')
    print('armado ranking-anual.html', meses[0], meses[-1], tot, totg)


if __name__ == '__main__':
    armar()

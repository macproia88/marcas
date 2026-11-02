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


MENOS = {'chicos'}
FALTA = {'grandes': 'no está la venta detallada de septiembre en el cerebro', 'chicos': 'no está la venta detallada de septiembre en el cerebro'}  # indicadores donde menos es mejor


def armar():
    meses, K = datos()
    pagina('ranking-anual.html', 'Ranking del año', 'los 3 locales, mostrador y apps', KPIS, meses, K,
           'Fuentes: venta, tickets y pedidos por día del tablero La Presumida (venta detallada de Maxi Rest y cierres de caja); apps: estados de cuenta de PedidosYa y liquidaciones de Rappi (octubre de PedidosYa con el detalle de pedidos; octubre de Rappi estimado). Los crecimientos arrancan en febrero porque no hay diciembre 2025 cargado.')
    mm, KM = datos_mostrador()
    pagina('ranking-mostrador.html', 'Ranking de mostrador', 'solo mostrador (sin apps)', KPIS_M, mm, KM,
           'Fuentes: venta y tickets de mostrador por día del tablero La Presumida (venta detallada de Maxi Rest y cierres de caja; mostrador = venta total menos el código 202 de apps). Tamaño de los tickets: venta detallada de Maxi Rest (enero a agosto y 1 al 25 de octubre; septiembre no está en el cerebro). Sugestivas, unidades y kilos: venta por artículo de Maxi Rest (desde octubre; desde noviembre se carga sola con los cierres de caja). Sugestivas, unidades y kilos de septiembre: informe de unidades por artículo de Maxi Rest (Septiembre_completo, solo cantidades). Club: reporte de ventas de ALAX desde julio (cuánto más gasta el socio y altas: octubre). Los crecimientos arrancan en febrero porque no hay diciembre 2025 cargado.')


def pagina(archivo, titulo, alcance, KPIS, meses, K, fuentes):
    gan = {}  # kpi -> mes -> local ganador
    for k, *_ in KPIS:
        for mes, vals in K.get(k, {}).items():
            if len(vals) == 3: gan.setdefault(k, {})[mes] = (min if k in MENOS else max)(vals, key=vals.get)
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
        con = sorted(g); rango = [x for x in meses if con and con[0] <= x <= con[-1]]
        for mes in rango:
            vals = K.get(k, {}).get(mes)
            if mes not in g or not vals or len(vals) < 3:
                filas += f'<tr><td>{MESN[int(mes[5:]) - 1]}</td><td colspan="4" class="sd">Sin dato: {html.escape(FALTA.get(k, "no está el archivo de ese mes en el cerebro"))}</td></tr>'
                continue
            w = g[mes]
            filas += f'<tr><td>{MESN[int(mes[5:]) - 1]}</td>' + ''.join(
                f'<td class="n{" win" if L == w else ""}">{fmt(vals[L])}</td>' for L in LOC) + f'<td>{chip(w)}</td></tr>'
        resumen = ' · '.join(f'{L} {cnt[L]}' for L in sorted(LOC, key=lambda L: -cnt[L]))
        secs += (f'<section class="card"><h2>{html.escape(nombre)} <span class="tag {tipo}">{tipo}</span></h2>'
                 f'<p class="note">{html.escape(expl)} Meses ganados: <b>{resumen}</b>.</p>'
                 f'<div class="tw"><table><thead><tr><th>Mes</th>' + ''.join(f'<th class="n">{L}</th>' for L in LOC) +
                 f'<th>Mejor</th></tr></thead><tbody>{filas}</tbody></table></div></section>')
    meses = sorted({m for k in K.values() for m in k}); desde, hasta = MESN[int(meses[0][5:]) - 1], MESN[int(meses[-1][5:]) - 1]
    css = """:root{--bg:#f7f3ed;--panel:#fff;--fg:#2b211d;--muted:#6b625c;--line:#e7dfd6;--win:#e6f2ea;--ok:#2f6b4f}
@media (prefers-color-scheme:dark){:root{--bg:#1c1917;--panel:#26211e;--fg:#f2ece6;--muted:#b3a89f;--line:#3a332e;--win:#20382b;--ok:#6fbf8f}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1000px;margin:0 auto;padding:8px 16px 30px}h1{font:400 30px/1.15 Georgia,serif;margin:6px 0 4px}h2{font-size:17px;margin:0 0 4px}
.sub,.note{color:var(--muted)}.note{font-size:13px;margin:0 0 10px}.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:14px}
table{width:100%;border-collapse:collapse;font-size:14px}th,td{padding:7px 8px;border-bottom:1px solid var(--line);text-align:left}th{font-size:12px;color:var(--muted)}
.n{text-align:right;font-variant-numeric:tabular-nums}td.win{background:var(--win);font-weight:700;color:var(--ok)}.tw{overflow-x:auto}
.chip{color:#fff;border-radius:999px;padding:2px 9px;font-size:12px;white-space:nowrap}.tag{font-size:11px;font-weight:600;border-radius:4px;padding:1px 6px;vertical-align:2px;border:1px solid var(--line);color:var(--muted)}
.sd{color:var(--muted);font-style:italic}.tag.gestión{color:var(--ok);border-color:var(--ok)}
@media (max-width:640px){h1{font-size:23px}.card{padding:12px}table{font-size:12.5px}th,td{padding:6px 5px}}"""
    out = f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{titulo}</title><style>{css}</style></head><body>
<div class="wrap"><h1>{titulo}</h1>
<p class="sub">Qué local fue el mejor en cada indicador, mes a mes · {desde} a {hasta} 2026 · {alcance}. En verde, el mejor de cada mes.</p>
<section class="card"><h2>Meses ganados en el año</h2><p class="note">Cuántas veces salió primero cada local, sumando todos los indicadores y meses. <b>Gestión</b> = indicadores que no dependen del tamaño del local (por ticket, por cliente, crecimiento contra el mes anterior): es la comparación más justa. <b>Tamaño</b> = totales de venta, clientes o pedidos, que suele ganar el local más grande.</p>
<div class="tw"><table><thead><tr><th>Local</th><th class="n">Total</th><th class="n">Gestión</th><th class="n">Tamaño</th></tr></thead><tbody>{med}</tbody></table></div></section>
{secs}
<p class="note">{fuentes}</p>
</div></body></html>"""
    (RAIZ / archivo).write_text(out, encoding='utf-8')
    print('armado', archivo, meses[0], meses[-1], tot, totg)




def datos_mostrador():
    import collections, articulos
    V = canales.cargar('ventas_diarias.json')
    ult = max(x['fecha'] for x in V)
    M = canales.mensual(V, ult[:7])
    m = {(r['mes'], r['local']): r for r in M if r['local'] in LOC and r['mes'] >= '2026-01'}
    meses = sorted({k[0] for k in m if all((k[0], L) in m and m[(k[0], L)]['dias'] >= 25 for L in LOC)})
    DM = canales.cargar('mostrador_det.json'); ART = articulos.armar()
    CL = {'2026-10': canales.cargar('club_local.json')}
    CM = canales.cargar('club_mensual.json')
    KGB = canales.cargar('kg_bienvenida.json')  # kilos de fideos de regalo de bienvenida del club (cupones usados en ALAX), se descuentan de los kilos vendidos
    UNID = {}
    for f in (canales.DATA).glob('unid_*.json'):
        UNID[f.stem[5:]] = json.loads(f.read_text(encoding='utf-8'))
    C = canales.cargar('cierres.json'); B = canales.cargar('art_base.json') if (canales.DATA / 'art_base.json').exists() else {}
    PK = articulos.por_kilo(B, C)
    RUB = {f['codigo']: f['rubro'] for a in ART.values() for f in a['filas']}
    K = {}
    def put(k, mes, L, v):
        if v is not None: K.setdefault(k, {}).setdefault(mes, {})[L] = v
    for i, mes in enumerate(meses):
        for L in LOC:
            r = m[(mes, L)]; d = r['dias']; tk = r['tickets']; vm = r['venta_mostrador']
            put('venta_m', mes, L, vm); put('clientes', mes, L, tk / d); put('ticket', mes, L, vm / tk)
            if i:
                p = m[(meses[i - 1], L)]; pd_ = p['dias']
                put('crec_venta', mes, L, (vm / d) / (p['venta_mostrador'] / pd_) - 1)
                put('crec_clientes', mes, L, (tk / d) / (p['tickets'] / pd_) - 1)
                put('crec_ticket', mes, L, (vm / tk) / (p['venta_mostrador'] / p['tickets']) - 1)
            if mes in DM:
                b = [x for x in DM[mes]['bandas'] if x['local'] == L]; t = sum(x['tickets'] for x in b)
                if t:
                    put('grandes', mes, L, sum(x['tickets'] for x in b if x['orden'] >= 3) / t)
                    put('chicos', mes, L, sum(x['tickets'] for x in b if x['orden'] == 0) / t)
            a = ART.get(mes)
            if a and a['desde'] == mes + '-01' and a['hasta'][8:] >= '28':
                F = [f for f in a['filas'] if f['local'] == L and f['codigo'] not in (202, 4000, 1) and f['venta'] > 0]
                dd = sum(x['tickets_mostrador'] for x in V if x['local'] == L and a['desde'] <= x['fecha'] <= a['hasta'])
                if dd:
                    un = [f for f in F if not f['kg']]
                    put('sug100', mes, L, sum(f['cantidad'] for f in un if f['rubro'] in ('Salsas', 'Quesos', 'Postre', 'Freddo', 'Bebidas')) / dd * 100)
                    put('uni100', mes, L, sum(f['cantidad'] for f in un) / dd); put('unidades', mes, L, sum(f['cantidad'] for f in un)); put('kilos', mes, L, sum(f['cantidad'] for f in F if f['kg']) - KGB.get(mes, {}).get(L, 0))
                    put('kg100', mes, L, (sum(f['cantidad'] for f in F if f['kg']) - KGB.get(mes, {}).get(L, 0)) / dd)
                    put('precio_u', mes, L, sum(f['venta'] for f in un) / sum(f['cantidad'] for f in un))
            elif mes in UNID and L in UNID[mes]:  # meses con informe de unidades por artículo (solo cantidades)
                dd = r['tickets']; filas = [f for f in UNID[mes][L] if f[0] not in (202, 4000, 1, 22) and f[2] > 0]
                kgs = lambda cod, u: cod in PK or (cod not in RUB and abs(u - round(u)) > 1e-6)
                un = [f for f in filas if not kgs(f[0], f[2])]
                put('sug100', mes, L, sum(f[2] for f in un if RUB.get(f[0], f[3]) in ('Salsas', 'Quesos', 'Postre', 'Freddo', 'Bebidas')) / dd * 100)
                put('uni100', mes, L, sum(f[2] for f in un) / dd); put('unidades', mes, L, sum(f[2] for f in un)); put('kilos', mes, L, sum(f[2] for f in filas if kgs(f[0], f[2])) - KGB.get(mes, {}).get(L, 0))
                put('kg100', mes, L, (sum(f[2] for f in filas if kgs(f[0], f[2])) - KGB.get(mes, {}).get(L, 0)) / dd)
            for c in CM:  # club: compras con DNI y venta de socios (reporte de ventas de ALAX), desde julio
                if c['mes'] == mes and c['local'] == L:
                    put('club', mes, L, c['pct_venta']); put('dni100', mes, L, c['pct_clientes'] * 100)
            for c in (CL.get(mes) or []):
                if c['local'] == L:
                    put('socio', mes, L, c['ticket_socio'] / c['ticket_no_socio'] - 1)
                    put('altas100', mes, L, c['altas'] / c['tickets'] * 100)
    return meses, K


KPIS_M = [
    ('venta_m', 'Venta de mostrador', mfmt, 'tamaño', 'Venta del mes sin apps, en pesos.'),
    ('clientes', 'Clientes por día', lambda v: nfmt(v), 'tamaño', 'Tickets de mostrador ÷ días con venta.'),
    ('ticket', 'Ticket promedio', lambda v: '$' + nfmt(v), 'gestión', 'Venta de mostrador ÷ tickets.'),
    ('crec_venta', 'Crecimiento de la venta', pfmt, 'gestión', 'Venta de mostrador por día contra el mes anterior del mismo local.'),
    ('crec_clientes', 'Crecimiento de clientes', pfmt, 'gestión', 'Clientes por día contra el mes anterior del mismo local.'),
    ('crec_ticket', 'Crecimiento del ticket', pfmt, 'gestión', 'Ticket promedio contra el mes anterior del mismo local.'),
    ('grandes', 'Tickets de más de $30.000', lambda v: nfmt(v * 100, 1) + '%', 'gestión', 'De cada 100 tickets, cuántos son de más de $30.000.'),
    ('chicos', 'Tickets de hasta $10.000 (menos es mejor)', lambda v: nfmt(v * 100, 1) + '%', 'gestión', 'De cada 100 tickets, cuántos son de hasta $10.000: ahí está la venta sugestiva que falta. Gana el que tiene menos.'),
    ('sug100', 'Sugestivas cada 100 clientes', lambda v: nfmt(v, 1), 'gestión', 'Salsas, quesos, postres, Freddo y bebidas vendidos cada 100 tickets (son productos por unidad).'),
    ('unidades', 'Unidades vendidas', lambda v: nfmt(v), 'tamaño', 'Total de productos por unidad vendidos en el mes en mostrador (sin los de peso, que van en kilos).'),
    ('uni100', 'Unidades por ticket', lambda v: nfmt(v, 2), 'gestión', 'Productos por unidad que se lleva cada cliente en promedio (unidades ÷ tickets).'),
    ('kilos', 'Kilos vendidos', lambda v: nfmt(v) + ' kg', 'tamaño', 'Total de kilos de productos por peso (fideos, ñoquis, sorrentinos, comida al peso) vendidos en el mes en mostrador, sin los kilos de regalo del club (bienvenida, 6 compras, 4 cajas de ravioles, compra mayor y promos 2x1 de fideos o ñoquis: cupones usados en ALAX), porque no son venta.'),
    ('kg100', 'Kilos por ticket', lambda v: nfmt(v, 2) + ' kg', 'gestión', 'Kilos de productos por peso que se lleva cada cliente en promedio (kilos ÷ tickets), sin los kilos de regalo del club.'),
    ('club', 'Venta del club', lambda v: nfmt(v * 100, 1) + '%', 'gestión', 'De cada $100 de venta de mostrador, cuántos son de socios (compras con DNI en el reporte de ventas de ALAX). Desde julio, cuando arrancó el club.'),
    ('dni100', 'Clientes del club', lambda v: nfmt(v, 1) + '%', 'gestión', 'De cada 100 clientes de mostrador, cuántos compraron con DNI (socios del club, reporte de ventas de ALAX). Desde julio.'),
    ('altas100', 'Altas al club cada 100 tickets', lambda v: nfmt(v, 1), 'gestión', 'Kilos de bienvenida entregados (socios nuevos) cada 100 tickets de mostrador.'),
    ('socio', 'Cuánto más gasta el socio', pfmt, 'gestión', 'Ticket del socio contra el ticket del que no es socio.'),
]


if __name__ == '__main__':
    armar()

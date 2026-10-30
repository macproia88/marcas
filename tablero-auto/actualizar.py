"""Actualiza el tablero con los cierres de turno de Maxi Rest y arma tablero-presumida-v2.html.

Uso:  python3 tablero-auto/actualizar.py

1. Lee data/cierres.json (un objeto por mail "MaxiREST - Fin de turno", ver INSTRUCCIONES.md).
2. Suma los turnos de cada día y local y reemplaza ese día en data/ventas_diarias.json.
   Los días que vinieron de la venta detallada (sin "fuente") no se tocan.
3. Arma ../tablero-presumida-v2.html con todos los datos de data/.
"""
import json, re, datetime as dt, pathlib

AQUI = pathlib.Path(__file__).resolve().parent
DATA = AQUI / 'data'
SRC = AQUI / 'src'
SALIDA = AQUI.parent / 'tablero-presumida-v2.html'

SUCURSALES = {'fpastas': 'Florida', 'beccar': 'Beccar', 'paz': 'Paz', 'pastas paz': 'Paz', 'olivos': 'Paz'}
APPS = re.compile(r'^(PEDIDOS YA|RAPPI|MP DELIVERY|PAGO ONLINE)', re.I)
DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
# Venta del código 202 en los cierres ÷ pedidos reales (PedidosYa + Rappi), 26 al 29/10: para estimar pedidos hasta que llegan los archivos de las apps
TICKET_APP = {'Florida': 20675.0, 'Beccar': 18620.0, 'Paz': 18057.0}
# Ticket promedio de apps oct-2025, para clientes 2025 (mismo criterio que el tablero)
TK25 = {'Florida': 18142, 'Beccar': 16025}


def cargar(nombre):
    return json.loads((DATA / nombre).read_text(encoding='utf-8'))


def actualizar_ventas():
    V = cargar('ventas_diarias.json')
    C = cargar('cierres.json')
    ref = {(r['fecha'], r['local']): r for r in cargar('ref_2025.json')}
    # pedidos reales de apps (archivos de PedidosYa + Rappi), si existen, en lugar del estimado
    try:
        reales = cargar('pedidos_reales.json')
    except FileNotFoundError:
        reales = {}
    dias = {}
    avisos = []
    for c in C:
        L = SUCURSALES.get(str(c.get('sucursal', '')).strip().lower())
        if not L:
            avisos.append(f"Sucursal sin asignar: {c.get('sucursal')} ({c.get('subject')})")
            continue
        a = dias.setdefault((c['fecha'], L), dict(total=0.0, tickets=0, app_cant=0, c202=0.0, turnos=[]))
        a['total'] += float(c['total'])
        a['tickets'] += int(c['tickets'])
        a['c202'] += float(c.get('cod202_importe') or 0)
        a['app_cant'] += sum(int(v[1]) for f, v in (c.get('formas') or {}).items() if APPS.match(f.strip()))
        a['turnos'].append(c.get('turno'))
    fijos = {(x['fecha'], x['local']) for x in V if not x.get('fuente')}
    V = [x for x in V if not x.get('fuente') or (x['fecha'], x['local']) not in dias]
    nuevos = []
    for (f, L), a in sorted(dias.items()):
        if (f, L) in fijos:
            continue
        d = dt.date.fromisoformat(f)
        va = round(a['c202'], 2)
        x = dict(fecha=f, mes=f[:7], local=L, dia=DIAS[d.weekday()], venta=round(a['total'], 2),
                 venta_mostrador=round(a['total'] - va, 2), venta_app=va,
                 tickets_mostrador=float(a['tickets'] - a['app_cant']),
                 venta_2025=None, tickets_mostrador_2025=None, venta_mostrador_2025=None, venta_app_2025=None,
                 pedidos_app=reales.get(f'{f}|{L}', round(va / TICKET_APP[L])), clientes_2025=None, fuente='cierre')
        r = ref.get((f, L))
        if r:
            x.update(venta_2025=r['venta_2025'], tickets_mostrador_2025=r['tickets_mostrador_2025'],
                     venta_mostrador_2025=r['venta_mostrador_2025'], venta_app_2025=r['venta_app_2025'])
            if r['tickets_mostrador_2025'] and L in TK25:
                x['clientes_2025'] = round(r['tickets_mostrador_2025'] + (r['venta_app_2025'] or 0) / TK25[L])
            elif r['tickets_mostrador_2025'] and L == 'Paz':
                x['clientes_2025'] = round(r['tickets_mostrador_2025'] + 285 / 31)  # Paz: ~285 pedidos de apps en oct-2025
        else:
            avisos.append(f"Sin referencia 2025 para {L} {f}")
        nuevos.append(x)
        print(f"{f} {L}: ${x['venta']:,.0f} ({len(a['turnos'])} turnos: {', '.join(map(str, a['turnos']))})")
    V += nuevos
    V.sort(key=lambda x: (x['fecha'], x['local']))
    (DATA / 'ventas_diarias.json').write_text(json.dumps(V, ensure_ascii=False), encoding='utf-8')
    for a in avisos:
        print('AVISO:', a)
    return V


def venta_mensual(V):
    """Enero-agosto de la venta detallada (data/venta_mensual_hist.json); desde septiembre, suma de ventas_diarias."""
    H = cargar('venta_mensual_hist.json')
    meses_hist = {r['mes'] for r in H}
    acc = {}
    for x in V:
        if x['mes'] in meses_hist:
            continue
        a = acc.setdefault((x['mes'], x['local']), dict(mes=x['mes'], local=x['local'], venta=0.0, venta_app=0.0, venta_mostrador=0.0,
                                                         tickets_mostrador=0, dias=0, hasta=x['fecha']))
        a['venta'] += x['venta'] or 0
        a['venta_app'] += x['venta_app'] or 0
        a['venta_mostrador'] += x['venta_mostrador'] or 0
        a['tickets_mostrador'] += int(x['tickets_mostrador'] or 0)
        a['dias'] += 1
        a['hasta'] = max(a['hasta'], x['fecha'])
    R = H + [dict(v, venta=round(v['venta'], 2), venta_app=round(v['venta_app'], 2), venta_mostrador=round(v['venta_mostrador'], 2))
             for v in acc.values()]
    R.sort(key=lambda r: (r['mes'], r['local']))
    (DATA / 'venta_mensual.json').write_text(json.dumps(R, ensure_ascii=False), encoding='utf-8')
    return R


def armar_html(V):
    fmax = max(x['fecha'] for x in V)
    flor = max(x['fecha'] for x in V if x['local'] == 'Florida')
    paz = max(x['fecha'] for x in V if x['local'] == 'Paz')
    d = dt.date.fromisoformat(fmax)
    u7 = (d - dt.timedelta(days=6)).isoformat()
    h = (SRC / 'index_v2.html').read_text(encoding='utf-8')
    h = h.replace('max="2026-10-29"', f'max="{fmax}"')
    h = h.replace("const FMAX = '2026-10-29';", f"const FMAX = '{fmax}';")
    h = h.replace("ult7:['2026-10-23','2026-10-29']", f"ult7:['{u7}','{fmax}']")
    h = h.replace("anio:['2026-01-02','2026-10-29']", f"anio:['2026-01-02','{fmax}']")
    if fmax[:7] == '2026-10':
        h = h.replace("oct_s5:['2026-10-26','2026-10-29']", f"oct_s5:['2026-10-26','{fmax}']")
        h = h.replace('Oct semana 5 (26 al 29)', f'Oct semana 5 (26 al {d.day})')
    else:
        h = h.replace("oct_s5:['2026-10-26','2026-10-29']", "oct_s5:['2026-10-26','2026-10-31']")
        h = h.replace('Oct semana 5 (26 al 29)', 'Oct semana 5 (26 al 31)')
    h = h.replace("Barras: 2026. Línea: mismo día de la semana de 2025.", "Barras naranjas: 2026. Línea gris: mismo día de la semana de 2025.")
    h = h.replace("Abajo: tickets de mostrador. Arriba: pedidos de apps (PedidosYa + Rappi).",
                  "Naranja: tickets de mostrador. Gris: pedidos de apps (PedidosYa + Rappi). Línea: clientes del mismo día de la semana de 2025.")
    D = {}
    for k in ['ventas_diarias', 'clientes_hora', 'club_local', 'vendedoras', 'compras_mes', 'compras_proveedor', 'arca', 'canasta',
              'apps_resultado', 'top_mostrador', 'py_articulos', 'club_compra', 'club_frec', 'fichadas', 'fich_hora', 'club_ind',
              'club_sem', 'apps_liq', 'recetas', 'recetas_cob', 'compras_rubro', 'precios_var', 'eerr_res', 'vend_v2',
              'resumen_kpis', 'resumen_avance', 'resumen_alertas', 'venta_mensual']:
        rows = cargar(k + '.json')
        keys = [c for c in rows[0].keys() if c != 'fuente']
        D[k] = [keys, [[round(x.get(c), 2) if isinstance(x.get(c), float) else x.get(c) for c in keys] for x in rows]]
    D['vend_prod'] = [['personas', 'sin_fichada', 'resumen'], [list(cargar('vend_prod.json').values())]]
    d3 = (SRC / 'd3.min.js').read_text(encoding='utf-8')
    css = (SRC / 'standalone.css').read_text(encoding='utf-8')
    shim = (SRC / 'shim.js').read_text(encoding='utf-8').replace(
        'const RAW = window.__LP_DATA__,',
        'const RAW = Object.fromEntries(Object.entries(window.__LP_DATA__).map(([k,[c,rs]])=>[k,rs.map(r=>Object.fromEntries(c.map((n,i)=>[n,r[i]])))])),')
    fm = lambda s: f"{s[8:10]}/{s[5:7]}"
    pie_venta = f"venta hasta el {fm(flor)}/2026" + (f" (Paz hasta el {fm(paz)})" if paz < flor else '')
    out = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tablero La Presumida</title>
<style>{css}</style>
<script>{d3}</script>
<script>window.__LP_DATA__={json.dumps(D, ensure_ascii=False, separators=(',', ':'))};</script>
<script>{shim}</script>
</head><body><div class="wrap">
{h}
<p class="pie">Datos: {pie_venta}, compras hasta el 17/10/2026. Fichadas del 05/10 al 18/10. Estado de resultados hasta septiembre. Fuentes: Maxi Rest, PedidosYa, Rappi, ALAX, SmartPSS y sistema de compras.</p>
</div></body></html>"""
    SALIDA.write_text(out, encoding='utf-8')
    print(f'Tablero armado: {SALIDA.name} · venta hasta {fmax}')


if __name__ == '__main__':
    V = actualizar_ventas()
    venta_mensual(V)
    armar_html(V)

"""Arma los tableros por canal: ../apps.html (PedidosYa + Rappi) y ../mostrador.html.
Uso: python3 tablero-auto/canales.py [AAAA-MM]
Datos: data/apps_mes_<mes>.json (apps_agregar.py), data/mostrador_mes_<mes>.json (mostrador_agregar.py),
data/ventas_diarias.json, data/top_mostrador.json, data/club_local.json.
"""
import json, sys, pathlib, datetime as dt, collections

AQUI = pathlib.Path(__file__).resolve().parent
DATA, SRC = AQUI / 'data', AQUI / 'src'
AR = dt.timezone(dt.timedelta(hours=-3))
LOC = ['Florida', 'Beccar', 'Paz']
MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
DIAS = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']


def cargar(n):
    return json.loads((DATA / n).read_text(encoding='utf-8'))


def N(x): return f'{x:,.0f}'.replace(',', '.')
def M(x): return ('$' + f'{x/1e6:,.1f}'.replace(',', 'X').replace('.', ',').replace('X', '.') + 'M')
def P(x, d=0): return f'{x*100:.{d}f}%'.replace('.', ',')
def PS(x, d=0): return ('+' if x >= 0 else '') + P(x, d)


def mensual(V, mes):
    acc = collections.defaultdict(lambda: dict(pedidos=0, venta_app=0.0, tickets=0, venta_mostrador=0.0, dias=0, tickets_2025=0, dias_2025=0))
    for x in V:
        if x['mes'] > mes: continue
        for L in (x['local'], 'Todos'):
            a = acc[(x['mes'], L)]
            a['pedidos'] += x.get('pedidos_app') or 0; a['venta_app'] += x.get('venta_app') or 0
            a['tickets'] += x.get('tickets_mostrador') or 0; a['venta_mostrador'] += x.get('venta_mostrador') or 0
            a['dias'] += 1 if L != 'Todos' else 0
    out = []
    for (m, L), a in sorted(acc.items()):
        if L == 'Todos': a['dias'] = acc[(m, 'Florida')]['dias']
        out.append(dict(mes=m, local=L, **{k: round(v) for k, v in a.items()}))
    return out


def picos(horas, campo, L):
    tot = collections.Counter()
    for h in horas:
        if L == 'Todos' or h['local'] == L: tot[h['hora']] += h[campo]
    top = sorted(tot, key=lambda k: -tot[k])[:3]
    return sorted(top)


def rango_horas(hs):
    hs = sorted(hs); grupos = []
    for h in hs:
        if grupos and h == grupos[-1][-1] + 1: grupos[-1].append(h)
        else: grupos.append([h])
    return ' y '.join(f'{g[0]} a {g[-1] + 1} h' for g in grupos)


def textos_apps(A, MEN, mes):
    out = {}
    prev = (dt.date.fromisoformat(mes + '-01') - dt.timedelta(days=1)).strftime('%Y-%m')
    for L in ['Todos'] + LOC:
        sel = (lambda r: True) if L == 'Todos' else (lambda r, L=L: r['local'] == L)
        t = []
        prods = collections.Counter()
        for r in A['productos']:
            if sel(r): prods[r['producto']] += r['unidades']
        top = prods.most_common(3)
        if top: t.append('Lo que más sale: ' + ', '.join(f"{p.lower()} ({N(u)})" for p, u in top) + '. Casi todo es comida lista: porciones con salsa y pasta caliente.')
        pk = picos(A['horas'], 'pedidos', L)
        dia = collections.Counter()
        for r in A['horas']:
            if sel(r): dia[r['dia']] += r['pedidos']
        t.append(f"Horas pico: {rango_horas(pk)}. El día más fuerte es el {DIAS[max(dia, key=dia.get)]}.")
        py = [r for r in A['plata'] if r['app'] == 'PedidosYa' and sel(r)]
        vta = sum(r['venta'] for r in py); neto = sum(r['neto'] for r in py); ped_py = sum(r['pedidos'] for r in py)
        ban = [r for r in A['bandas'] if sel(r)]
        alto = sum(r['pedidos'] for r in ban if r['orden'] >= 3); alto_v = sum(r['venta'] for r in ban if r['orden'] >= 3)
        tp = sum(r['pedidos'] for r in ban); tv = sum(r['venta'] for r in ban)
        if tp: t.append(f"Ticket promedio de PedidosYa {('$' + N(vta / ped_py)) if ped_py else '—'}. Los pedidos de más de $40.000 son {P(alto/tp)} de los pedidos pero {P(alto_v/tv)} de la plata.")
        q = sum(r['unidades'] for r in A['agregados'] if sel(r) and r['agregado'].lower() == 'queso rallado')
        if ped_py: t.append(f"Queso rallado: se agregan {q/ped_py*100:.0f} quesos cada 100 pedidos de PedidosYa. Es la venta sugestiva de la app y ya funciona.")
        if vta: t.append(f"De cada $100 que se venden en PedidosYa vuelven ${neto/vta*100:.0f} al local; el resto es comisión, descuentos que paga el local y otros cargos.")
        rec = [r for r in A['reclamos'] if sel(r)]
        nr = sum(r['reclamos'] for r in rec); arm = sum(r.get('Producto faltante', 0) + r.get('Producto incorrecto', 0) + r.get('Orden equivocada', 0) for r in rec)
        if nr: t.append(f"Reclamos: {nr/sum(r['pedidos'] for r in rec)*100:.1f} cada 100 pedidos.".replace('.', ',', 1) + f" {P(arm/nr)} son de armado (faltante, incorrecto u orden equivocada): se arreglan controlando el pedido antes de entregarlo.")
        out[L] = t
    return out


def textos_mostrador(Mo, MEN, TOP, CL, mes):
    out = {}
    for L in ['Todos'] + LOC:
        sel = (lambda r: True) if L == 'Todos' else (lambda r, L=L: r['local'] == L)
        t = []
        pk = picos(Mo['horas'], 'tickets', L)
        t.append(f"Horas pico: {rango_horas(pk)}. El mediodía concentra la mayor parte de los clientes.")
        co = collections.Counter(); tt = 0
        for r in Mo['cobro']:
            if sel(r): co[r['forma']] += r['tickets']; tt += r['tickets']
        t.append('Cómo paga: ' + ', '.join(f"{k.lower() if k not in ('MODO', 'Mercado Pago') else k} {P(v/tt)}" for k, v in co.most_common(4)) + '.')
        ban = [r for r in Mo['bandas'] if sel(r)]
        tp = sum(r['tickets'] for r in ban); tv = sum(r['venta'] for r in ban)
        alto = [r for r in ban if r['orden'] >= 3]
        chico = [r for r in ban if r['orden'] == 0]
        t.append(f"Los tickets de más de $30.000 son {P(sum(r['tickets'] for r in alto)/tp)} de los clientes pero {P(sum(r['venta'] for r in alto)/tv)} de la venta. Los de hasta $10.000 son {P(sum(r['tickets'] for r in chico)/tp)}: ahí está la venta sugestiva.")
        top = collections.Counter()
        for r in TOP:
            if sel(r): top[r['articulo'].strip()] += r['venta']
        t.append('Lo que más se vende en pesos: ' + ', '.join(p.lower() for p, _ in top.most_common(4)) + ' (fideos incluye el kilo de regalo del club).')
        cl = [r for r in CL if sel(r)]
        if cl:
            vc = sum(r['venta_club'] for r in cl); vm = sum(r['venta_mostrador'] for r in cl)
            nc = sum(r['tickets_club'] for r in cl); tk = sum(r['tickets'] for r in cl)
            ts = vc / nc; tn = (vm - vc) / (tk - nc)
            t.append(f"Club: {P(vc/vm)} de la venta de mostrador es de socios, y el socio gasta {P(ts/tn-1)} más por ticket que el que no es socio.")
        out[L] = t
    return out




def armar(nombre, titulo, sub, datos, js):
    css = (SRC / 'canales.css').read_text(encoding='utf-8')
    d3 = (SRC / 'd3.min.js').read_text(encoding='utf-8')
    ahora = dt.datetime.now(AR)
    html = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{titulo}</title><style>{css}</style><script>{d3}</script>
<script>window.D={json.dumps(datos, ensure_ascii=False, separators=(',', ':'))};</script></head>
<body>
<div id="lp-upd" style="font:12px/1.4 system-ui,-apple-system,Segoe UI,sans-serif;color:#6b6b6b;text-align:right;padding:6px 16px">Última actualización: {ahora:%d/%m/%Y} a las {ahora:%H:%M} (hora Argentina)</div>
<main class="wrap">
<header><h1>{titulo}</h1><p class="sub">{sub}</p>
<div class="ctl"><label>Mes <select id="mes"></select></label></div>
<nav class="loc" id="loc"><button data-l="Todos" aria-pressed="true">Los 3 locales</button><button data-l="Florida">Florida</button><button data-l="Beccar">Beccar</button><button data-l="Paz">Paz</button></nav></header>
<section class="card"><h2>Lo que dicen los números</h2><ul id="txt" class="txt"></ul></section>
<section class="kpis" id="kpis"></section>
<div id="secs"></div>
<p class="pie" id="pie"></p>
<p class="pie"><a href="tablero-presumida-v2.html">Tablero La Presumida</a> · <a href="apps.html">Tablero de apps</a> · <a href="mostrador.html">Tablero de mostrador</a></p>
</main>
<script>{(SRC / 'canales.js').read_text(encoding='utf-8')}</script>
<script>{js}</script>
</body></html>"""
    (AQUI.parent / nombre).write_text(html, encoding='utf-8')
    print('armado', nombre)


MESN = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']


def textos_base(MEN, mes, canal):
    prev = (dt.date.fromisoformat(mes + '-01') - dt.timedelta(days=1)).strftime('%Y-%m')
    out = {}
    for L in ['Todos'] + LOC:
        m0 = next((r for r in MEN if r['mes'] == mes and r['local'] == L), None); m1 = next((r for r in MEN if r['mes'] == prev and r['local'] == L), None)
        if not m0 or not m0['dias']: out[L] = []; continue
        cant, vta = (m0['pedidos'], m0['venta_app']) if canal == 'apps' else (m0['tickets'], m0['venta_mostrador'])
        nom = 'pedidos' if canal == 'apps' else 'clientes'
        t = f"{N(cant)} {nom} en {MESN[int(mes[5:])-1]}" + (f" ({m0['dias']} días cargados)" if m0['dias'] < 28 else '') + f", {cant/m0['dias']:.0f} por día, con ticket promedio de ${N(vta/cant) if cant else 0}"
        if m1 and m1['dias']:
            c1, v1 = (m1['pedidos'], m1['venta_app']) if canal == 'apps' else (m1['tickets'], m1['venta_mostrador'])
            if c1: t += f". Contra {MESN[int(prev[5:])-1]}: {PS((cant/m0['dias'])/(c1/m1['dias'])-1)} {nom} por día y {PS((vta/cant)/(v1/c1)-1)} en el ticket"
        out[L] = [t + '.']
    return out


def main():
    V = cargar('ventas_diarias.json')
    ult = max(x['fecha'] for x in V); mes_max = ult[:7]
    MEN = mensual(V, mes_max)
    meses = sorted({r['mes'] for r in MEN if r['mes'] >= '2026-01'})
    dias_mes = {r['local']: r['dias'] for r in MEN if r['mes'] == mes_max}
    defecto = mes_max if min(dias_mes.values() or [0]) >= 7 else meses[-2]
    DA = cargar('apps_det.json'); DM = cargar('mostrador_det.json')
    TOP = cargar('top_mostrador.json'); CL = cargar('club_local.json')
    dias = [dict(fecha=x['fecha'], local=x['local'], tickets=x['tickets_mostrador'], tickets_2025=x.get('tickets_mostrador_2025'),
                 venta=x['venta_mostrador'], pedidos=x.get('pedidos_app'), venta_app=x['venta_app']) for x in V if x['fecha'] >= '2026-01-01']
    ta, tm = {}, {}
    for m in meses:
        ba, bm = textos_base(MEN, m, 'apps'), textos_base(MEN, m, 'mostrador')
        da = textos_apps(DA[m], MEN, m) if m in DA else {}
        dm = textos_mostrador(DM[m], MEN, TOP, CL, m) if m in DM else {}
        ta[m] = {L: ba.get(L, []) + da.get(L, []) for L in ['Todos'] + LOC}
        tm[m] = {L: bm.get(L, []) + dm.get(L, []) for L in ['Todos'] + LOC}
    top = {'2026-10': [dict(local=r['local'], articulo=r['articulo'].strip(), rubro=r['rubro'], venta=r['venta'], cantidad=r['cantidad']) for r in TOP]}
    armar('apps.html', 'Tablero de apps', 'PedidosYa y Rappi · los 3 locales',
          dict(meses=meses, mes=defecto, men=MEN, dias=dias, det=DA, textos=ta), 'paginaApps();')
    armar('mostrador.html', 'Tablero de mostrador', 'Clientes que compran en el local · los 3 locales',
          dict(meses=meses, mes=defecto, men=MEN, dias=dias, det=DM, top=top, club={'2026-10': CL}, textos=tm), 'paginaMostrador();')


if __name__ == '__main__':
    main()

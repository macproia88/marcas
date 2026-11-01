"""Resume un mes de pedidos de apps (PedidosYa orderDetails .csv + Rappi orders .xlsx) en data/apps_mes_<AAAA-MM>.json.
Uso: python3 tablero-auto/apps_agregar.py <orderDetails.csv> <rappi.xlsx> <AAAA-MM>
No guarda datos de clientes: solo totales por local, día, hora, motivo y producto.
"""
import sys, json, re, collections, pathlib
import pandas as pd

AQUI = pathlib.Path(__file__).resolve().parent
MP = {'La Presumida Pastas - Florida': 'Florida', 'Pastas Frescas La Presumida - Vicente López': 'Florida',
      'La Presumida Pastas - Beccar': 'Beccar', 'Pastas Frescas La Presumida - San Isidro': 'Beccar', 'Pastas Paz': 'Paz'}
LOC = ['Florida', 'Beccar', 'Paz']


def num(x):
    if pd.isna(x): return 0.0
    s = str(x).strip().replace('.', '').replace(',', '.')
    try: return float(s)
    except ValueError: return 0.0


def main(py_csv, rappi_xlsx, mes):
    d = pd.read_csv(py_csv, sep=None, engine='python'); d.columns = [c.replace('﻿', '') for c in d.columns]
    d['f'] = pd.to_datetime(d['Fecha del pedido']); d = d[d.f.dt.strftime('%Y-%m') == mes].copy()
    d['L'] = d['Nombre del local'].map(MP)
    for c in ['Total parcial', 'Comisión', 'Total de costes de marketing', 'Costes de publicidad', 'Descuento financiado por usted',
              'Vale financiado por usted', 'Comisión por pago en línea', 'Gastos operativos', 'Tarifa por espera', 'Ingreso estimado',
              'Reembolsos a la tienda', 'Tarifa de cancelación evitable']:
        d[c] = d[c].map(num)
    e = d[d['Estado del pedido'] == 'Entregado'].copy()
    r = pd.read_excel(rappi_xlsx, header=1).iloc[:, 1:]
    r.columns = ['orden', 'cliente', 'suc', 'f', 'pago', 'total', 'estado'] + list(r.columns[7:])
    r['f'] = pd.to_datetime(r.f, errors='coerce'); r = r[r.f.dt.strftime('%Y-%m') == mes]
    r['L'] = r.suc.astype(str).map(lambda s: 'Florida' if 'Florida' in s else 'Beccar')
    rt = r[r.estado.astype(str).str.strip() == 'Terminada'].copy(); rt['total'] = pd.to_numeric(rt.total, errors='coerce').fillna(0)

    out = {'mes': mes, 'dias': [], 'plata': [], 'reclamos': [], 'cancelados': [], 'tiempos': [], 'horas': [], 'productos': [], 'resumen': []}
    # pedidos por día y app
    dias = pd.date_range(d.f.min().normalize(), d.f.max().normalize())
    for L in LOC:
        for dd in dias:
            py = int(((e.L == L) & (e.f.dt.normalize() == dd)).sum()); ra = int(((rt.L == L) & (rt.f.dt.normalize() == dd)).sum())
            out['dias'].append(dict(fecha=dd.strftime('%Y-%m-%d'), local=L, pedidosya=py, rappi=ra, pedidos=py + ra))
    # plata
    for L in LOC:
        x = e[e.L == L]; y = rt[rt.L == L]
        venta = x['Total parcial'].sum()
        mkt = x['Total de costes de marketing'].sum()
        desc = x['Descuento financiado por usted'].sum() + x['Vale financiado por usted'].sum()
        com = x['Comisión'].sum() + x['Comisión por pago en línea'].sum()
        neto = x['Ingreso estimado'].sum()
        out['plata'].append(dict(local=L, app='PedidosYa', pedidos=int(len(x)), venta=round(venta), comision=round(com), publicidad=round(mkt),
                                 descuentos=round(desc), otros=round(venta - com - mkt - desc - neto), neto=round(neto),
                                 ticket=round(venta / len(x)) if len(x) else 0))
        out['plata'].append(dict(local=L, app='Rappi', pedidos=int(len(y)), venta=round(y.total.sum()), comision=None, publicidad=None,
                                 descuentos=None, otros=None, neto=None, ticket=round(y.total.sum() / len(y)) if len(y) else 0))
    # reclamos y cancelados (PedidosYa)
    for L in LOC:
        x = d[d.L == L]; ent = int((x['Estado del pedido'] == 'Entregado').sum())
        rec = x[x['¿Tiene algún reclamo?'] == 'Sí']
        mot = rec['Motivo del reclamo'].fillna('Sin motivo').value_counts().to_dict()
        out['reclamos'].append(dict(local=L, pedidos=ent, reclamos=int(len(rec)), **{k: int(v) for k, v in mot.items()}))
        c = x[x['Estado del pedido'] != 'Entregado']
        out['cancelados'].append(dict(local=L, cancelados=int(len(c)), por_local=int(c['Responsable del rechazo'].astype(str).str.contains('Local').sum()),
                                      rappi_cancelados=int(((r.L == L) & (r.estado.astype(str).str.strip() != 'Terminada')).sum())))
    # tiempos (minutos, mediana)
    for L in LOC:
        x = e[e.L == L]
        prep = (pd.to_datetime(x['Lista para retiro'], errors='coerce') - pd.to_datetime(x['Aceptado en'], errors='coerce')).dt.total_seconds() / 60
        tot = (pd.to_datetime(x['Entregado el'], errors='coerce') - x.f).dt.total_seconds() / 60
        out['tiempos'].append(dict(local=L, preparacion=round(float(prep[(prep >= 0) & (prep < 240)].median()), 1),
                                   total=round(float(tot[(tot >= 0) & (tot < 300)].median()), 1),
                                   prep_mas_20=round(float((prep[(prep >= 0) & (prep < 240)] > 20).mean()), 3)))
    # horas x día de la semana (PedidosYa + Rappi)
    both = pd.concat([e[['L', 'f']], rt[['L', 'f']]])
    for L in LOC:
        x = both[both.L == L]
        g = x.groupby([x.f.dt.dayofweek, x.f.dt.hour]).size()
        for (dw, h), n in g.items():
            out['horas'].append(dict(local=L, dia=int(dw), hora=int(h), pedidos=int(n)))
    # productos (PedidosYa): producto principal y agregados (lo que va entre corchetes: salsa, queso, guarnición)
    def partes(txt):
        res, prof, cur = [], 0, ''
        for ch in txt:
            if ch == '[': prof += 1
            if ch == ']': prof -= 1
            if ch == ',' and prof == 0: res.append(cur.strip()); cur = ''
            else: cur += ch
        if cur.strip(): res.append(cur.strip())
        out_ = []
        for r_ in res:  # '1,5 lt' no es un producto nuevo: se une al anterior
            if out_ and (not re.match(r'\d+\s+\D', r_) or re.search(r'\d$', out_[-1])): out_[-1] += ',' + r_
            else: out_.append(r_)
        return out_
    cnt = collections.Counter(); ext = collections.Counter(); unid = []
    for L, s in zip(e.L, e['Artículos del pedido'].fillna('')):
        n_ped = 0
        for it in partes(s):
            m = re.match(r'(\d+)\s+([^\[]*)(\[(.*)\])?', it)
            if not m: continue
            q = int(m.group(1)); n_ped += q
            cnt[(L, m.group(2).strip().rstrip(']').strip())] += q
            for sub in (m.group(4) or '').split(','):
                mm = re.match(r'\s*(\d+)\s+(.*)', sub)
                if mm: ext[(L, mm.group(2).strip())] += int(mm.group(1)) * q
        unid.append((L, n_ped))
    for L in LOC:
        top = sorted([(k[1], v) for k, v in cnt.items() if k[0] == L], key=lambda t: -t[1])[:25]
        out['productos'] += [dict(local=L, producto=p, unidades=u) for p, u in top]
        tope = sorted([(k[1], v) for k, v in ext.items() if k[0] == L], key=lambda t: -t[1])[:12]
        out.setdefault('agregados', []).extend(dict(local=L, agregado=p, unidades=u) for p, u in tope)
    # canasta: tamaño del pedido (pesos) y unidades por pedido
    BANDAS = [(0, 15000, 'Hasta $15.000'), (15000, 25000, '$15.000 a $25.000'), (25000, 40000, '$25.000 a $40.000'), (40000, 60000, '$40.000 a $60.000'), (60000, 1e12, 'Más de $60.000')]
    for L in LOC:
        x = e[e.L == L]['Total parcial']
        for i, (a_, b_, n_) in enumerate(BANDAS):
            sel = x[(x >= a_) & (x < b_)]
            out.setdefault('bandas', []).append(dict(local=L, orden=i, banda=n_, pedidos=int(len(sel)), venta=round(sel.sum())))
        u = [n for l_, n in unid if l_ == L]
        out.setdefault('canasta', []).append(dict(local=L, unidades_pedido=round(sum(u) / len(u), 2) if u else 0, ticket=round(x.mean()) if len(x) else 0))
    for L in LOC:
        out['resumen'].append(dict(local=L, pedidosya=int((e.L == L).sum()), rappi=int((rt.L == L).sum())))
    p = AQUI / 'data' / f'apps_mes_{mes}.json'
    p.write_text(json.dumps(out, ensure_ascii=False), encoding='utf-8')
    print('ok', p.name, {k: len(v) for k, v in out.items() if isinstance(v, list)})


if __name__ == '__main__':
    main(*sys.argv[1:4])

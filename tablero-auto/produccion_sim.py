"""Control de producción hacia atrás: para cada día desde que hay cierres con detalle de los 3 locales (30/09/2026),
calcula el sugerido que se hubiera mandado esa mañana (solo con los cierres anteriores a ese día, igual que produccion.py)
y lo compara con lo vendido en mostrador. Guarda data/sugerido_sim.json (lo usa produccion.html en el control, marcado
"simulado") y arma un Excel con la evaluación: qué tan cerca estuvo el sugerido, por local, rubro y producto, y si
conviene el promedio o la mediana.

Uso: python3 tablero-auto/produccion_sim.py [carpeta_salida]
"""
import collections, datetime as dt, json, math, pathlib, statistics, sys
import produccion as P
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

DATA = P.DATA
DESDE = dt.date(2026, 10, 1)          # primer día con los 3 locales con cierre del día anterior
HASTA_REAL = '2026-11-02'             # desde acá están los sugeridos que se mandaron de verdad (sugerido_hist.json)


def cargar():
    c = json.load(open(DATA / 'cierres.json')); mae = json.load(open(DATA / 'productos_maestro.json'))
    por = collections.defaultdict(lambda: collections.defaultdict(float)); con = collections.defaultdict(set); meta = {}
    for x in c:
        if 'articulos' not in x: continue
        L = P.LOC.get(x['sucursal'], x['sucursal']); con[L].add(x['fecha'])
        for cod, nom, rub, q, imp in x['articulos']:
            if cod in P.EXCLUIR: continue
            m = mae.get(str(cod), {}); r = m.get('rubro') or rub
            if r in P.REVENTA: continue
            n = m.get('nombre') or nom
            por[(L, x['fecha'])][n] += q
            if n not in meta: meta[n] = (r, m.get('kg'))
    for n, (r, kg) in list(meta.items()):
        if kg is None:
            vals = [d[n] for d in por.values() if n in d]
            meta[n] = (r, any(abs(v - round(v)) > 1e-6 for v in vals))
    return por, con, meta


def redondeo(v, kg): return (math.ceil(v * 2 - 1e-9) / 2) if kg else math.ceil(v - 1e-9)


def dias_previos(con, L, t):
    f0 = t.isoformat()
    if t.day == 29:
        return sorted([f for f in con[L] if f < f0 and f.endswith('-29')], reverse=True)[:4]
    return sorted([f for f in con[L] if f < f0 and f not in P.FERIADOS and not f.endswith('-29')
                   and dt.date.fromisoformat(f).weekday() == t.weekday()], reverse=True)[:4]


def main():
    out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path('.')
    por, con, meta = cargar()
    sim, filas = {}, []
    t = DESDE; fin = dt.date.fromisoformat(HASTA_REAL)
    while t < fin:
        f = t.isoformat(); sim[f] = {}
        for L in P.LOCS:
            if f not in con[L]: continue                       # local sin cierre ese día: no se compara
            prev = dias_previos(con, L, t)
            if not prev: continue
            prods = set().union(*[set(por[(L, d)]) for d in prev]) | set(por[(L, f)])
            for n in prods:
                rub, kg = meta.get(n, ('', False)); vals = [por[(L, d)].get(n, 0.0) for d in prev]
                prom, med, mx = sum(vals) / len(vals), statistics.median(vals), max(vals)
                s_prom, s_med = redondeo(prom, kg), redondeo(med, kg)
                v = round(por[(L, f)].get(n, 0.0), 2)
                if s_prom > 0: sim[f][f'{L}|{n}'] = s_prom
                if s_prom == 0 and v == 0: continue
                filas.append(dict(fecha=f, local=L, rubro=rub, nombre=n, kg=kg, semanas=len(prev), sug=s_prom, sug_med=s_med,
                                  mx=mx, vend=v, feriado=f in P.FERIADOS, dia29=t.day == 29))
        t += dt.timedelta(days=1)
    json.dump(sim, open(DATA / 'sugerido_sim.json', 'w'), ensure_ascii=False, sort_keys=True)

    def estado(x, s):
        tol = max(0.5 if x['kg'] else 1.0, 0.2 * s); d = x['vend'] - s
        if x['vend'] <= 0 and s >= (1.0 if x['kg'] else 3.0): return 'cero'
        return 'ok' if abs(d) <= tol else ('mas' if d > 0 else 'menos')
    for x in filas:
        x['estado'] = estado(x, x['sug']); x['estado_med'] = estado(x, x['sug_med'])
        x['dif'] = round(x['vend'] - x['sug'], 2)
    comp = [x for x in filas if not x['feriado']]          # los feriados se muestran pero no entran en la evaluación

    # ---------------- Excel
    AR = Font(name='Arial', size=10); B = Font(name='Arial', size=10, bold=True); WF = Font(name='Arial', bold=True, color='FFFFFF')
    H = PatternFill('solid', fgColor='7A3E2B'); thin = Border(bottom=Side(style='thin', color='D9C3B0'))
    RED = PatternFill('solid', fgColor='F2D4CE'); GRN = PatternFill('solid', fgColor='D4E6D0'); YEL = PatternFill('solid', fgColor='FFF2CC')
    TX = {'ok': 'Dentro del sugerido', 'mas': 'Vendió más', 'menos': 'Vendió menos (posible sobrante)', 'cero': 'No se vendió nada: ¿faltó?'}
    FILL = {'mas': RED, 'menos': GRN, 'cero': YEL}

    def hoja(ws, enc, anchos):
        ws.append(enc)
        for i, w in enumerate(anchos, 1):
            c = ws.cell(1, i); c.font = WF; c.fill = H; c.alignment = Alignment(wrap_text=True, vertical='center')
            ws.column_dimensions[c.column_letter].width = w
        ws.freeze_panes = 'A2'; ws.row_dimensions[1].height = 34

    wb = Workbook(); ws = wb.active; ws.title = 'Resumen'
    hoja(ws, ['Local', 'Días comparados', 'Productos-día', 'Dentro del sugerido', 'Vendió más', 'Vendió menos (posible sobrante)', 'No se vendió nada (¿faltó?)',
              '% dentro (promedio)', '% dentro si se usara la mediana', 'Unidades sugeridas', 'Unidades vendidas', 'Kg sugeridos', 'Kg vendidos'],
         [10, 11, 11, 12, 11, 14, 14, 12, 14, 12, 12, 11, 11])
    res = {}
    for L in P.LOCS + ['Los 3']:
        xs = [x for x in comp if L == 'Los 3' or x['local'] == L]
        if not xs: continue
        n = len(xs); cnt = collections.Counter(x['estado'] for x in xs); cm = collections.Counter(x['estado_med'] for x in xs)
        u = [x for x in xs if not x['kg']]; k = [x for x in xs if x['kg']]
        res[L] = (cnt['ok'] / n, cm['ok'] / n)
        ws.append([L, len({x['fecha'] for x in xs}), n, cnt['ok'], cnt['mas'], cnt['menos'], cnt['cero'], cnt['ok'] / n, cm['ok'] / n,
                   sum(x['sug'] for x in u), sum(x['vend'] for x in u), sum(x['sug'] for x in k), round(sum(x['vend'] for x in k), 1)])
        r = ws.max_row
        for c in range(1, 14):
            ws.cell(r, c).font = B if L == 'Los 3' else AR; ws.cell(r, c).border = thin
        for c in (8, 9): ws.cell(r, c).number_format = '0%'
        for c in (10, 11): ws.cell(r, c).number_format = '#,##0'
        for c in (12, 13): ws.cell(r, c).number_format = '#,##0.0'
    ws.auto_filter.ref = f'A1:M{ws.max_row}'
    ws.append([])
    for t_ in ['Cómo leerlo: para cada día desde el 01/10 se calculó el sugerido que se hubiera mandado esa mañana, con el mismo método del mensaje diario '
               '(promedio de los últimos 4 días iguales de la semana, por local, redondeado para arriba; sin feriados; el 29 con los 29). Solo se usan cierres anteriores a ese día.',
               'Dentro = diferencia de hasta 20% del sugerido (mínimo 1 unidad o 0,5 kg). Vendió más = se vendió más de lo sugerido (o se produjo más). Vendió menos = posible sobrante. '
               'Cero = sugerido de 3 u o 1 kg o más y no se vendió nada: revisar si faltó.',
               'Ojo: en las primeras semanas de octubre el sugerido sale de 1 a 3 semanas de historia (no 4), y los cierres de Florida y Beccar con detalle empiezan el 29-30/09. '
               'Los feriados (12/10) se muestran en el detalle pero no entran en estos porcentajes.',
               'Mediana: en vez del promedio de los 4 días, el del medio. Un día muy fuerte (fin de semana largo, ñoquis) pesa menos.']:
        ws.append([t_]); ws.cell(ws.max_row, 1).font = Font(name='Arial', size=9, italic=True, color='555555')

    # por rubro
    ws2 = wb.create_sheet('Por rubro')
    hoja(ws2, ['Local', 'Rubro', 'Unidad', 'Productos-día', '% dentro', 'Sugerido total', 'Vendido total', 'Diferencia', 'Diferencia %', 'Días con algún cero (¿faltó?)'],
         [10, 18, 8, 11, 10, 12, 12, 12, 11, 14])
    g = collections.defaultdict(list)
    for x in comp: g[(x['local'], x['rubro'], x['kg'])].append(x)
    for (L, rub, kg), xs in sorted(g.items(), key=lambda z: (P.LOCS.index(z[0][0]), -sum(x['vend'] for x in z[1]))):
        s = sum(x['sug'] for x in xs); v = sum(x['vend'] for x in xs)
        ws2.append([L, rub, 'kg' if kg else 'u', len(xs), sum(x['estado'] == 'ok' for x in xs) / len(xs), s, round(v, 1), round(v - s, 1), (v - s) / s if s else None,
                    len({x['fecha'] for x in xs if x['estado'] == 'cero'})])
        r = ws2.max_row
        for c in range(1, 11): ws2.cell(r, c).font = AR; ws2.cell(r, c).border = thin
        ws2.cell(r, 5).number_format = '0%'; ws2.cell(r, 9).number_format = '+0%;-0%;0%'
        for c in (6, 7, 8): ws2.cell(r, c).number_format = '#,##0.0' if kg else '#,##0'
    ws2.auto_filter.ref = f'A1:J{ws2.max_row}'

    # por producto
    ws3 = wb.create_sheet('Por producto')
    hoja(ws3, ['Local', 'Rubro', 'Producto', 'Unidad', 'Días', '% dentro', 'Veces vendió más', 'Veces vendió menos', 'Veces cero (¿faltó?)',
               'Sugerido promedio por día', 'Vendido promedio por día', 'Diferencia promedio', 'Qué conviene'],
         [10, 16, 34, 8, 7, 9, 10, 10, 10, 12, 12, 12, 46])
    g = collections.defaultdict(list)
    for x in comp: g[(x['local'], x['rubro'], x['nombre'], x['kg'])].append(x)
    for (L, rub, n, kg), xs in sorted(g.items(), key=lambda z: (P.LOCS.index(z[0][0]), z[0][1], -sum(x['vend'] for x in z[1]))):
        c = collections.Counter(x['estado'] for x in xs); d = len(xs)
        sp = sum(x['sug'] for x in xs) / d; vp = sum(x['vend'] for x in xs) / d; dif = vp - sp
        if c['cero'] >= 2: q = 'Varios días sin venta con sugerido: revisar si faltó producto'
        elif c['mas'] >= d / 2: q = 'Se queda corto seguido: producir un poco más que el sugerido'
        elif c['menos'] >= d / 2: q = 'Sobra seguido: producir un poco menos que el sugerido'
        else: q = 'El sugerido anda bien'
        ws3.append([L, rub, n, 'kg' if kg else 'u', d, c['ok'] / d, c['mas'], c['menos'], c['cero'], round(sp, 1), round(vp, 1), round(dif, 1), q])
        r = ws3.max_row
        for cc in range(1, 14): ws3.cell(r, cc).font = AR; ws3.cell(r, cc).border = thin
        ws3.cell(r, 6).number_format = '0%'
        if q.startswith('Se queda'): ws3.cell(r, 13).fill = RED
        elif q.startswith('Sobra'): ws3.cell(r, 13).fill = GRN
        elif q.startswith('Varios'): ws3.cell(r, 13).fill = YEL
    ws3.auto_filter.ref = f'A1:M{ws3.max_row}'

    # detalle día por día
    ws4 = wb.create_sheet('Día por día')
    hoja(ws4, ['Fecha', 'Día', 'Local', 'Rubro', 'Producto', 'Unidad', 'Semanas de historia', 'Sugerido', 'Máximo de esos días', 'Vendido', 'Diferencia', 'Qué pasó', 'Nota'],
         [11, 7, 10, 16, 34, 8, 10, 10, 10, 10, 10, 30, 14])
    for x in sorted(filas, key=lambda z: (z['fecha'], P.LOCS.index(z['local']), z['rubro'], z['nombre'])):
        d = dt.date.fromisoformat(x['fecha'])
        ws4.append([d, P.DIAS[d.weekday()][:3], x['local'], x['rubro'], x['nombre'], 'kg' if x['kg'] else 'u', x['semanas'], x['sug'], round(x['mx'], 1), x['vend'], x['dif'],
                    TX[x['estado']], 'feriado' if x['feriado'] else ('día 29' if x['dia29'] else '')])
        r = ws4.max_row; ws4.cell(r, 1).number_format = 'dd/mm/yyyy'
        for cc in range(1, 14): ws4.cell(r, cc).font = AR
        for cc in (8, 9, 10, 11): ws4.cell(r, cc).number_format = '#,##0.0' if x['kg'] else '#,##0'
        if x['estado'] in FILL: ws4.cell(r, 12).fill = FILL[x['estado']]
    ws4.auto_filter.ref = f'A1:M{ws4.max_row}'

    fn = out / 'Produccion_Control_Octubre_2026.xlsx'; wb.save(fn)
    print('ARCHIVO', fn)
    for L, (a, b) in res.items(): print(f'RES {L}: dentro {a:.0%} (mediana {b:.0%})')
    print('SIM dias', len(sim), 'filas', len(filas))


if __name__ == '__main__':
    main()

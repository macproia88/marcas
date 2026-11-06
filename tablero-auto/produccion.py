"""Listado de productos vendidos en MOSTRADOR el día anterior (o la fecha que se pase), por local, en unidades o kg.

Uso:  python3 tablero-auto/produccion.py [AAAA-MM-DD] [carpeta_salida]
Fuente: data/cierres.json (cierres de turno de Maxi Rest que llegan por mail, sección VENTAS POR ARTICULO, todos los turnos).
- Mostrador = todo menos el código 202 (carga de apps) y el 4000 (descuento del club ALAX).
- kg o unidades: data/productos_maestro.json (de la venta por artículo por vendedor de Maxi Rest). Si un código no está, se
  toma kg cuando la cantidad tiene decimales.
- Guarda el día en data/produccion_hist.json para comparar con el mismo día de la semana anterior y el promedio de 4 semanas.
Imprime un resumen para el mensaje y deja Produccion_<dd-mm-aaaa>.xlsx en la carpeta de salida.
"""
import json, sys, datetime as dt, pathlib, collections
from zoneinfo import ZoneInfo
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

DATA = pathlib.Path(__file__).resolve().parent / 'data'
LOC = {'fpastas': 'Florida', 'Beccar': 'Beccar', 'Pastas Paz': 'Paz'}
LOCS = ['Florida', 'Beccar', 'Paz']
TURNOS = {'Florida': 'Mañana, Intermedio y Noche', 'Beccar': 'Mañana y Noche', 'Paz': 'Mañana e Intermedio'}
REVENTA = {'Bebidas', 'Lacteo', 'Arcor', 'Dankon', 'DIBBLE', 'Isla', 'Santa', 'Nestle', 'Reventa', 'El Aljibe - La Fontana',
           'Panaderia', 'Pan F', 'Freddo', 'Otros', 'Sin rubro', ''}
EXCLUIR = {0, 1, 202, 4000}
DIAS = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']


def cargar(fecha):
    c = json.load(open(DATA / 'cierres.json'))
    mae = json.load(open(DATA / 'productos_maestro.json'))
    turnos = collections.defaultdict(list)
    filas = {}   # (local, cod) -> dict
    for x in c:
        if x['fecha'] != fecha or 'articulos' not in x:
            continue
        L = LOC.get(x['sucursal'], x['sucursal'])
        turnos[L].append(x['turno'])
        for cod, nom, rub, q, imp in x['articulos']:
            if cod in EXCLUIR:
                continue
            m = mae.get(str(cod), {})
            k = (L, cod)
            f = filas.setdefault(k, dict(local=L, cod=cod, nombre=m.get('nombre') or nom, rubro=m.get('rubro') or rub,
                                         kg=m.get('kg'), q=0.0, imp=0.0, turnos=collections.Counter()))
            f['q'] += q; f['imp'] += imp; f['turnos'][x['turno']] += q
    for f in filas.values():
        if f['kg'] is None:
            f['kg'] = abs(f['q'] - round(f['q'])) > 1e-6
    return filas, turnos


def historial(fecha, filas, turnos):
    """Guarda el día y devuelve, por local|código, la cantidad de los 4 mismos días de semana anteriores
    (None si ese local no tenía cierres guardados ese día: no se cuenta como cero)."""
    p = DATA / 'produccion_hist.json'
    h = json.load(open(p)) if p.exists() else {}
    h[fecha] = {'_locales': sorted(turnos)} | {f"{f['local']}|{f['cod']}": round(f['q'], 3) for f in filas.values()}
    json.dump(h, open(p, 'w'), ensure_ascii=False, sort_keys=True)
    d = dt.date.fromisoformat(fecha)
    prev = [(d - dt.timedelta(days=7 * i)).isoformat() for i in range(1, 5)]
    out = {}
    for f in filas.values():
        k = f"{f['local']}|{f['cod']}"
        out[k] = [(h[x].get(k, 0.0) if f['local'] in h[x].get('_locales', []) else None) if x in h else None for x in prev]
    return out


FERIADOS = {'2026-10-12', '2026-11-09', '2026-11-11', '2026-11-23', '2026-12-08', '2026-12-25'}


ATIPICOS = {'2026-10-17': 'víspera del Día de la Madre', '2026-10-18': 'Día de la Madre'}   # días especiales que no sirven de referencia


def _cargar_base():
    c = json.load(open(DATA / 'cierres.json')); mae = json.load(open(DATA / 'productos_maestro.json'))
    por_dia = collections.defaultdict(lambda: collections.defaultdict(float)); turnos = collections.defaultdict(set)
    for x in c:
        if 'articulos' not in x: continue
        L = LOC.get(x['sucursal'], x['sucursal']); turnos[(L, x['fecha'])].add(x['turno'])
        for cod, nom, rub, q, imp in x['articulos']:
            if cod in EXCLUIR: continue
            por_dia[(L, x['fecha'])][cod] += q
    return c, mae, por_dia, turnos


def _unid_prod(por_dia, mae, c, L, f):
    """Unidades de producción (sin reventa ni kg) vendidas ese día: sirve para detectar días fuera de lo normal."""
    t = 0.0
    for cod, q in por_dia[(L, f)].items():
        m = mae.get(str(cod), {})
        if (m.get('rubro') or '') in REVENTA or m.get('kg') or abs(q - round(q)) > 1e-6: continue
        t += q
    return t


def motivo_atipico(L, f, por_dia, turnos, mae, c, con):
    """Por qué un día NO se usa como referencia (o None si sirve):
    - día especial cargado a mano (ATIPICOS), feriado o día 29 (se trata aparte);
    - falta un turno (sin el cierre de la mañana, o un solo turno en un día que no es domingo);
    - vendió mucho más (más de 35% arriba) o mucho menos (40% abajo) que la mediana de ese mismo día de la semana
      en las 6 semanas alrededor: fin de semana largo, lluvia fuerte, corte de luz, cierre que no llegó completo."""
    if f in ATIPICOS: return ATIPICOS[f]
    d = dt.date.fromisoformat(f); ts = turnos[(L, f)]
    if d.weekday() != 6 and f not in FERIADOS and ('Mañana' not in ts or len(ts) < 2):
        return 'faltan turnos (' + ', '.join(sorted(ts)) + ')'
    ref = [g for g in con[L] if g != f and g not in FERIADOS and g not in ATIPICOS and not g.endswith('-29')
           and dt.date.fromisoformat(g).weekday() == d.weekday() and abs((dt.date.fromisoformat(g) - d).days) <= 42]
    if len(ref) >= 3:
        import statistics
        m = statistics.median(_unid_prod(por_dia, mae, c, L, g) for g in ref); u = _unid_prod(por_dia, mae, c, L, f)
        if m and u > 1.35 * m: return f'vendió {u / m - 1:.0%} más que un {DIAS[d.weekday()]} normal'
        if m and u < 0.60 * m: return f'vendió {1 - u / m:.0%} menos que un {DIAS[d.weekday()]} normal'
    return None


def sugerido(target, detalle=False):
    """Sugerido para producir el día target (AAAA-MM-DD), solo mostrador.
    Toma los últimos 4 días iguales de la semana que sirven de referencia (mismo local; sin feriados, sin días especiales,
    sin días con turnos faltantes y sin días muy fuera de lo normal) y usa la MEDIANA (el valor del medio), que no se
    deja arrastrar por un día muy fuerte o muy flojo. Unidades redondeadas para arriba; kg al medio kilo para arriba.
    Probado contra la venta real del 20/10 al 05/11: el promedio anterior sugería 13% de más; así queda en -2%.
    Devuelve filas y los días usados por local (con detalle=True también los días dejados afuera y por qué)."""
    import math, statistics
    c, mae, por_dia, turnos = _cargar_base()
    con_cierre = collections.defaultdict(set)
    for (L, f) in por_dia: con_cierre[L].add(f)
    t = dt.date.fromisoformat(target)
    dias, afuera = {}, {}
    for L in LOCS:
        if t.day == 29:   # día de ñoquis: se compara con los 29 anteriores
            cand = sorted([f for f in con_cierre[L] if f < target and f.endswith('-29')], reverse=True)
        else:
            cand = sorted([f for f in con_cierre[L] if f < target and f not in FERIADOS and not f.endswith('-29')
                           and dt.date.fromisoformat(f).weekday() == t.weekday()], reverse=True)
        ok, fuera = [], []
        for f in cand:
            if len(ok) == 4: break
            if t.day == 29:   # entre días 29 solo se deja afuera el que tiene turnos faltantes
                ts = turnos[(L, f)]; d29 = dt.date.fromisoformat(f)
                mot = ('faltan turnos (' + ', '.join(sorted(ts)) + ')') if d29.weekday() != 6 and ('Mañana' not in ts or len(ts) < 2) else None
            else:
                mot = motivo_atipico(L, f, por_dia, turnos, mae, c, con_cierre)
            (fuera.append((f, mot)) if mot else ok.append(f))
        if t.day == 29 and not ok:   # todavía no hay 2 días 29 con cierre: se usa el mismo día de la semana
            ok, fuera = [], [(f, 'día 29 con poca historia: se usa el mismo día de la semana') for f in ok]
            for f in sorted([f for f in con_cierre[L] if f < target and f not in FERIADOS and not f.endswith('-29')
                             and dt.date.fromisoformat(f).weekday() == t.weekday()], reverse=True):
                if len(ok) == 4: break
                mot = motivo_atipico(L, f, por_dia, turnos, mae, c, con_cierre)
                (fuera.append((f, mot)) if mot else ok.append(f))
        dias[L] = ok; afuera[L] = fuera
    nombres = {}
    for x in c:
        for a in x.get('articulos', []): nombres.setdefault(a[0], (a[1], a[2]))
    P = collections.OrderedDict()
    for L in LOCS:
        if not dias[L]: continue
        cods = set()
        for f in dias[L]: cods |= set(por_dia[(L, f)])
        for cod in cods:
            m = mae.get(str(cod), {}); rub = m.get('rubro') or nombres.get(cod, ('', ''))[1]
            nombre = m.get('nombre') or nombres.get(cod, (str(cod), ''))[0]
            if rub in REVENTA: continue
            vals = [por_dia[(L, f)].get(cod, 0.0) for f in dias[L]]
            kg = m.get('kg', any(abs(v - round(v)) > 1e-6 for v in vals))
            base = statistics.median(vals)
            sug = (math.ceil(base * 2 - 1e-9) / 2) if kg else math.ceil(base - 1e-9)
            k = (rub, nombre, kg)
            r = P.setdefault(k, dict(rubro=rub, nombre=nombre, kg=kg, cods=set(), sug={X: 0.0 for X in LOCS}, mx={X: 0.0 for X in LOCS}))
            r['cods'].add(cod); r['sug'][L] += sug; r['mx'][L] += max(vals)
    filas = sorted(P.values(), key=lambda r: (r['rubro'], -sum(r['sug'].values())))
    filas = [r for r in filas if sum(r['sug'].values()) > 0]
    return (filas, dias, afuera) if detalle else (filas, dias)


def num(q, kg): return f'{q:.1f}'.replace('.', ',') if kg else f'{q:.0f}'


def main():
    hoy = dt.datetime.now(ZoneInfo('America/Argentina/Buenos_Aires')).date()
    fecha = sys.argv[1] if len(sys.argv) > 1 else (hoy - dt.timedelta(days=1)).isoformat()
    out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path('.')
    filas, turnos = cargar(fecha)
    d = dt.date.fromisoformat(fecha)
    if not filas:
        print(f'SIN CIERRES para el {d:%d/%m/%Y}'); return
    comp = historial(fecha, filas, turnos)

    # producto = nombre completo + rubro + unidad (Paz usa otros códigos: si el nombre coincide, se suma en la misma fila)
    P = collections.OrderedDict()
    for f in sorted(filas.values(), key=lambda f: (f['rubro'] in REVENTA, f['rubro'], f['nombre'])):
        k = (f['rubro'], f['nombre'], f['kg'])
        p = P.setdefault(k, dict(rubro=f['rubro'], nombre=f['nombre'], kg=f['kg'], tipo='Reventa' if f['rubro'] in REVENTA else 'Producción',
                                 cods=set(), q={L: 0.0 for L in LOCS}, imp=0.0, sem=None, prom=None, sem_falta=False, prom_falta=False))
        p['cods'].add(f['cod']); p['q'][f['local']] += f['q']; p['imp'] += f['imp']; p['tot'] = sum(p['q'].values())
        c = comp.get(f"{f['local']}|{f['cod']}", [None] * 4)
        # si a algún local que vendió le falta el dato, la comparación queda en "Sin dato" (no se compara parcial)
        if c[0] is None: p['sem_falta'] = True
        else: p['sem'] = (p['sem'] or 0) + c[0]
        v = [x for x in c if x is not None]
        if not v: p['prom_falta'] = True
        else: p['prom'] = (p['prom'] or 0) + sum(v) / len(v)

    for p in P.values():
        if p['sem_falta']: p['sem'] = None
        if p['prom_falta']: p['prom'] = None

    # ---------- Excel
    wb = Workbook(); H = PatternFill('solid', fgColor='7A3E2B'); WF = Font(name='Arial', bold=True, color='FFFFFF'); AR = Font(name='Arial')
    B = Font(name='Arial', bold=True); CR = PatternFill('solid', fgColor='F7EFE6'); thin = Side(style='thin', color='D9C3B0')

    def hoja(ws, enc, anchos):
        ws.append(enc)
        for i, w in enumerate(anchos, 1):
            ws.column_dimensions[get_column_letter(i)].width = w
            c = ws.cell(1, i); c.fill = H; c.font = WF; c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        ws.freeze_panes = 'A2'; ws.row_dimensions[1].height = 32

    ws = wb.active; ws.title = 'Detalle'
    hoja(ws, ['Tipo', 'Rubro', 'Producto', 'Código Maxi', 'Unidad', 'Florida', 'Beccar', 'Paz', 'Total', 'Mismo día semana anterior', 'Promedio últimas 4 semanas', 'Venta $ (mostrador)'],
         [11, 14, 34, 12, 8, 10, 10, 10, 10, 14, 14, 15])
    for p in P.values():
        ws.append([p['tipo'], p['rubro'], p['nombre'], ', '.join(str(c) for c in sorted(p['cods'])), 'kg' if p['kg'] else 'u',
                   *[round(p['q'][L], 2) for L in LOCS], None, round(p['sem'], 2) if p['sem'] is not None else 'Sin dato',
                   round(p['prom'], 2) if p['prom'] is not None else 'Sin dato', round(p['imp'])])
        r = ws.max_row; ws.cell(r, 9).value = round(p['tot'], 2)
        fmt = '#,##0.0' if p['kg'] else '#,##0'
        for col in range(1, 13):
            c = ws.cell(r, col); c.font = AR; c.border = Border(bottom=thin)
            if 6 <= col <= 11: c.number_format = fmt
        ws.cell(r, 12).number_format = '"$"#,##0'; ws.cell(r, 9).font = B
        if p['tipo'] == 'Reventa':
            for col in range(1, 13): ws.cell(r, col).fill = CR
    ws.auto_filter.ref = f'A1:L{ws.max_row}'

    ws2 = wb.create_sheet('Resumen por rubro')
    hoja(ws2, ['Tipo', 'Rubro', 'Unidad', 'Florida', 'Beccar', 'Paz', 'Total'], [11, 16, 8, 11, 11, 11, 11])
    R = collections.OrderedDict()
    for p in P.values():
        k = (p['tipo'], p['rubro'], p['kg']); R.setdefault(k, {L: 0.0 for L in LOCS})
        for L in LOCS: R[k][L] += p['q'][L]
    for (t, rub, kg), q in R.items():
        ws2.append([t, rub, 'kg' if kg else 'u', *[round(q[L], 2) for L in LOCS], None]); r = ws2.max_row
        ws2.cell(r, 7).value = round(sum(q.values()), 2)
        for col in range(1, 8):
            ws2.cell(r, col).font = AR
            if col >= 4: ws2.cell(r, col).number_format = '#,##0.0' if kg else '#,##0'
    ws2.auto_filter.ref = f'A1:G{ws2.max_row}'

    ws3 = wb.create_sheet('Por turno')
    hoja(ws3, ['Local', 'Turno', 'Rubro', 'Producto', 'Unidad', 'Cantidad'], [10, 12, 14, 34, 8, 10])
    for f in sorted(filas.values(), key=lambda f: (LOCS.index(f['local']) if f['local'] in LOCS else 9, f['rubro'] in REVENTA, f['rubro'], f['nombre'])):
        for t, q in f['turnos'].items():
            ws3.append([f['local'], t, f['rubro'], f['nombre'], 'kg' if f['kg'] else 'u', round(q, 2)])
            for col in range(1, 7): ws3.cell(ws3.max_row, col).font = AR
    ws3.auto_filter.ref = f'A1:F{ws3.max_row}'

    # ---------- sugerido para hoy (el día siguiente al informado)
    tgt = (d + dt.timedelta(days=1)).isoformat(); tg = dt.date.fromisoformat(tgt)
    SUG, sdias, safuera = sugerido(tgt, detalle=True)
    hp = DATA / 'sugerido_hist.json'
    SH = json.load(open(hp)) if hp.exists() else {}
    SH[tgt] = {f"{L}|{r['nombre']}": r['sug'][L] for r in SUG for L in LOCS if r['sug'][L] > 0}
    json.dump(SH, open(hp, 'w'), ensure_ascii=False, sort_keys=True)

    # ---------- ayer: vendido contra el sugerido que se mandó para ese día (desde el martes 03/11)
    VS = []
    parcial = {L for L in turnos if d.weekday() != 6 and fecha not in FERIADOS and ('Mañana' not in turnos[L] or len(turnos[L]) < 2)}
    if fecha in SH:
        vend = collections.defaultdict(float); meta = {}
        for f in filas.values():
            if f['rubro'] in REVENTA: continue
            vend[f"{f['local']}|{f['nombre']}"] += f['q']; meta[f['nombre']] = (f['rubro'], f['kg'])
        for k in set(SH[fecha]) | set(vend):
            L, nom = k.split('|', 1)
            if L not in turnos: continue          # local sin cierre ayer: no se compara
            if L in parcial: continue             # faltan turnos de ayer: la comparación no sirve
            sg = SH[fecha].get(k, 0.0); v = vend.get(k, 0.0)
            rub, kg = meta.get(nom, (None, None))
            if rub is None:
                rr = next((r for r in SUG if r['nombre'] == nom), None)
                rub, kg = (rr['rubro'], rr['kg']) if rr else ('', False)
            VS.append(dict(local=L, nombre=nom, rubro=rub, kg=kg, sug=sg, vend=round(v, 2), dif=round(v - sg, 2)))
        VS.sort(key=lambda x: (LOCS.index(x['local']), x['rubro'], x['nombre']))
        ws6 = wb.create_sheet(f'Ayer vendido vs sugerido', 1)
        hoja(ws6, ['Local', 'Rubro', 'Producto', 'Unidad', 'Sugerido', 'Vendido', 'Diferencia', 'Qué pasó'], [10, 14, 34, 8, 11, 11, 11, 30])
        RED = PatternFill('solid', fgColor='F2D4CE'); GRN = PatternFill('solid', fgColor='D4E6D0')
        for x in VS:
            tol = max(1.0 if not x['kg'] else 0.5, 0.2 * x['sug'])
            if x['dif'] > tol: txt, fill = 'Vendió más que el sugerido', RED
            elif x['dif'] < -tol: txt, fill = 'Vendió menos que el sugerido (posible sobrante)', GRN
            else: txt, fill = 'Dentro del sugerido', None
            if x['vend'] <= 0 and x['sug'] >= (1.0 if x['kg'] else 3.0):
                txt, fill = 'No se vendió nada: ¿faltó? Revisar con el local', PatternFill('solid', fgColor='FFF2CC')
            x['estado'] = txt
            ws6.append([x['local'], x['rubro'], x['nombre'], 'kg' if x['kg'] else 'u', x['sug'], x['vend'], x['dif'], txt]); rr = ws6.max_row
            for col in range(1, 9):
                c = ws6.cell(rr, col); c.font = AR; c.border = Border(bottom=thin)
                if 5 <= col <= 7: c.number_format = '#,##0.0' if x['kg'] else '#,##0'
            if fill:
                for col in (7, 8): ws6.cell(rr, col).fill = fill
        ws6.append([]); ws6.append(['Más/menos = la venta de mostrador se pasó o quedó corta en más de 20% del sugerido (mínimo 1 unidad o 0,5 kg). Vendido más puede ser que se produjo más de lo sugerido; vendido menos es posible sobrante; cero con sugerido de 3 u o 1 kg o más = no se vendió nada, revisar si faltó. Usá la flecha de cada título para ordenar de mayor a menor.'])
        ws6.cell(ws6.max_row, 1).font = Font(name='Arial', italic=True, color='555555')
        ws6.auto_filter.ref = f'A1:H{len(VS) + 1}'
    ws5 = wb.create_sheet(f'Sugerido {DIAS[tg.weekday()]} {tg:%d-%m}', 0)
    hoja(ws5, ['Rubro', 'Producto', 'Unidad', 'Florida sugerido', 'Florida máx.', 'Beccar sugerido', 'Beccar máx.', 'Paz sugerido', 'Paz máx.', 'Total sugerido'],
         [14, 34, 8, 11, 10, 11, 10, 11, 10, 12])
    for r in SUG:
        ws5.append([r['rubro'], r['nombre'], 'kg' if r['kg'] else 'u', r['sug']['Florida'], round(r['mx']['Florida'], 1), r['sug']['Beccar'], round(r['mx']['Beccar'], 1),
                    r['sug']['Paz'], round(r['mx']['Paz'], 1), sum(r['sug'].values())])
        rr = ws5.max_row
        for col in range(1, 11):
            c = ws5.cell(rr, col); c.font = B if col in (4, 6, 8, 10) else AR; c.border = Border(bottom=thin)
            if col >= 4: c.number_format = '#,##0.0' if r['kg'] else '#,##0'
    ws5.append([]); ws5.append(['Cómo se calcula: MEDIANA (el valor del medio) de lo vendido en MOSTRADOR los últimos 4 ' + DIAS[tg.weekday()] + ' que sirven de referencia, por local, redondeado para arriba (unidades enteras; kg al medio kilo). Se dejan afuera feriados, días especiales (Día de la Madre), días con turnos faltantes y días que vendieron 35% más o 40% menos que un ' + DIAS[tg.weekday()] + ' normal. El 29 se compara con los 29 anteriores. Máx. = el mejor de esos días. Solo mostrador.'])
    ws5.append(['Días usados: ' + ' · '.join(f"{L}: {', '.join(dt.date.fromisoformat(x).strftime('%d/%m') for x in sdias[L]) or 'sin datos'}" for L in LOCS)])
    ws5.append(['Días dejados afuera: ' + (' · '.join(f"{L} {dt.date.fromisoformat(f):%d/%m} ({m})" for L in LOCS for f, m in safuera[L]) or 'ninguno')])
    for rr in (ws5.max_row - 2, ws5.max_row - 1, ws5.max_row): ws5.cell(rr, 1).font = Font(name='Arial', italic=True, color='555555')
    # sugerido por rubro: lo que amasa el pastero
    wsr = wb.create_sheet(f'Sugerido por rubro', 1)
    hoja(wsr, ['Rubro', 'Unidad', 'Florida', 'Beccar', 'Paz', 'Total', 'Productos'], [16, 8, 11, 11, 11, 11, 70])
    RR = collections.OrderedDict()
    for r in SUG:
        g = RR.setdefault((r['rubro'], r['kg']), dict(q={L: 0.0 for L in LOCS}, p=[]))
        for L in LOCS: g['q'][L] += r['sug'][L]
        g['p'].append(f"{r['nombre']} {num(sum(r['sug'].values()), r['kg'])}")
    for (rub, kg), g in RR.items():
        wsr.append([rub, 'kg' if kg else 'u', *[g['q'][L] for L in LOCS], sum(g['q'].values()), ' · '.join(g['p'])]); rr = wsr.max_row
        for col in range(1, 8):
            cc = wsr.cell(rr, col); cc.font = B if col in (1, 6) else AR; cc.border = Border(bottom=thin)
            if 3 <= col <= 6: cc.number_format = '#,##0.0' if kg else '#,##0'
        wsr.cell(rr, 7).alignment = Alignment(wrap_text=True, vertical='top')
    wsr.append([]); wsr.append(['Suma de los sugeridos por producto de cada rubro. Es el número para planificar la masa y el relleno del día; el detalle por producto está en la primera hoja.'])
    wsr.cell(wsr.max_row, 1).font = Font(name='Arial', italic=True, color='555555')
    ws5.auto_filter.ref = f'A1:J{len(SUG) + 1}'
    wb.active = 0

    ws4 = wb.create_sheet('Cómo se calculó')
    txt = [f'Venta de mostrador del {DIAS[d.weekday()]} {d:%d/%m/%Y}, los 3 locales.',
           'Fuente: mails "Fin de turno" de Maxi Rest de cada turno, sección VENTAS POR ARTICULO (columna de cantidad).',
           'Turnos leídos: ' + ' · '.join(f'{L}: {", ".join(turnos.get(L, [])) or "SIN CIERRE"} (normal: {TURNOS[L]})' for L in LOCS),
           'Mostrador = todo menos el código 202 (PedidosYa y Rappi se cargan juntos en ese código, sin detalle de producto) y el 4000 (descuento del club).',
           'Unidad: kg o unidades según la venta por artículo por vendedor de Maxi Rest; sin dato, kg si la cantidad tiene decimales.',
           'Paz usa códigos propios para algunos productos (por ejemplo Ravioles Pollo y Jamón): si el nombre es igual se suman en la misma fila; si no, quedan en filas separadas.',
           'Fideos incluye el kilo de regalo de bienvenida del club (se carga como venta y se descuenta con el cupón).',
           'Comparaciones: mismo día de la semana anterior y promedio de los últimos 4 días iguales. Hay cierres guardados de Florida y Beccar desde el 29/10 y de Paz desde el 24/10: si a algún local que vendió el producto le falta ese día, la comparación queda en "Sin dato".',
           'Reventa (bebidas, lácteos, panadería, Arcor, Dankon, etc.) va al final, en crema.']
    for t in txt: ws4.append([t]); ws4.cell(ws4.max_row, 1).font = AR
    ws4.column_dimensions['A'].width = 140
    out.mkdir(parents=True, exist_ok=True)
    fn = out / f'Produccion_{d:%d-%m-%Y}.xlsx'; wb.save(fn)

    # ---------- resumen para el mensaje
    print(f'ARCHIVO {fn}')
    print(f'Venta de mostrador del {DIAS[d.weekday()]} {d:%d/%m}')
    for L in LOCS:
        print(f'TURNOS {L}: {", ".join(turnos.get(L, [])) or "SIN CIERRE"}')
    for (t, rub, kg), q in R.items():
        if t != 'Producción': continue
        tot = sum(q.values())
        print(f"RUBRO {rub} ({'kg' if kg else 'u'}): Florida {num(q['Florida'], kg)} · Beccar {num(q['Beccar'], kg)} · Paz {num(q['Paz'], kg)} · Total {num(tot, kg)}")
    for p in sorted([p for p in P.values() if p['tipo'] == 'Producción'], key=lambda p: -p['imp'])[:15]:
        extra = ''
        if p['sem'] is not None: extra += f" · semana anterior {num(p['sem'], p['kg'])}"
        print(f"TOP {p['nombre']}: {num(p['tot'], p['kg'])} {'kg' if p['kg'] else 'u'} (F {num(p['q']['Florida'], p['kg'])} · B {num(p['q']['Beccar'], p['kg'])} · P {num(p['q']['Paz'], p['kg'])}){extra}")

    for L in sorted(parcial):
        print(f"VSPARCIAL {L}: ayer llegaron solo los turnos {', '.join(turnos[L])}; no se compara contra el sugerido")
    if VS:
        for L in LOCS:
            xs = [x for x in VS if x['local'] == L]
            if not xs: continue
            n_ok = sum(x['estado'] == 'Dentro del sugerido' for x in xs); n_mas = sum(x['estado'].startswith('Vendió más') for x in xs)
            n_cer = sum(x['estado'].startswith('No se vendió') for x in xs); n_men = len(xs) - n_ok - n_mas - n_cer
            print(f'VSLOCAL {L}: {len(xs)} productos · dentro del sugerido {n_ok} · vendió más {n_mas} · vendió menos {n_men} · no se vendió nada {n_cer}')
        for L in LOCS:   # por rubro: lo que de verdad planifica el pastero (producto por producto siempre hay ruido de 1 o 2 unidades)
            g = collections.OrderedDict()
            for x in VS:
                if x['local'] != L or not x['rubro']: continue
                k = (x['rubro'], x['kg']); g.setdefault(k, [0.0, 0.0]); g[k][0] += x['sug']; g[k][1] += x['vend']
            for (rub, kg), (sg, vd) in sorted(g.items(), key=lambda z: -z[1][1] / (2 if z[0][1] else 1))[:8]:
                if sg <= 0: continue
                print(f"VSRUBRO {L} {rub}: sugerido {num(sg, kg)} · vendido {num(vd, kg)} {'kg' if kg else 'u'} ({(vd - sg) / sg:+.0%})")
        for x in sorted([x for x in VS if x['estado'].startswith('No se vendió')], key=lambda x: -x['sug']):
            print(f"VSCERO {x['local']} {x['nombre']}: sugerido {num(x['sug'], x['kg'])} {'kg' if x['kg'] else 'u'}, vendido 0 (¿faltó? revisar con el local)")
        big = sorted([x for x in VS if x['estado'] != 'Dentro del sugerido'], key=lambda x: -abs(x['dif']) / (2 if x['kg'] else 1))[:12]
        for x in big:
            print(f"VS {x['local']} {x['nombre']}: sugerido {num(x['sug'], x['kg'])} · vendido {num(x['vend'], x['kg'])} {'kg' if x['kg'] else 'u'} ({'+' if x['dif'] > 0 else ''}{num(x['dif'], x['kg'])})")
    else:
        print(f'VSNO no hay sugerido guardado para el {d:%d/%m} (la comparación arranca con el lunes 02/11)')
    print(f'SUGERIDO para el {DIAS[tg.weekday()]} {tg:%d/%m} (mediana de los últimos 4 {DIAS[tg.weekday()]} que sirven de referencia): ' + ' · '.join(f"{L} {len(sdias[L])} días ({', '.join(dt.date.fromisoformat(x).strftime('%d/%m') for x in sdias[L])})" for L in LOCS))
    for L in LOCS:
        for f, m in safuera[L]:
            print(f"AFUERA {L} {dt.date.fromisoformat(f):%d/%m}: {m}")
    RS = collections.OrderedDict()
    for r in SUG:
        k = (r['rubro'], r['kg']); RS.setdefault(k, {L: 0.0 for L in LOCS})
        for L in LOCS: RS[k][L] += r['sug'][L]
    for (rub, kg), q in RS.items():
        print(f"SUGRUBRO {rub} ({'kg' if kg else 'u'}): Florida {num(q['Florida'], kg)} · Beccar {num(q['Beccar'], kg)} · Paz {num(q['Paz'], kg)} · Total {num(sum(q.values()), kg)}")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Planilla Z automatica con el formato EXACTO de la planilla de Fermin.

Uso:
  python3 tablero-auto/zetas_fermin.py <xlsx_fermin> <AAAA-MM> <salida.xlsx> [--cruce <salida_cruce.xlsx>]

- <xlsx_fermin>: la planilla Z del mes de Fermin (su xlsx tal cual, vacio o ya cargado).
- Toma los cierres de Maxi Rest de data/cierres.json y completa, en las hojas
  FLORIDA, BECCAR y OLIVOS, por cada dia que tenga cierres:
    I  PLANILLA CAJA        = venta total del dia de Maxi (suma de todos los turnos)
    J  MEDIOS ELECTRONICOS  = venta total - EFECTIVO - CTA. CTE.
  D, E y F (el Z fiscal) NO estan en Maxi: se dejan como estan (los carga Fermin).
- No toca nada mas: mismas hojas, estilos, formulas y tablas dinamicas. Se edita el
  XML del xlsx directamente (sin openpyxl ni LibreOffice sobre el archivo final) y se
  vuelven a poner los valores calculados de las formulas para que se vean en el celular.
- --cruce: arma un Excel aparte comparando dia por dia lo que cargo Fermin (I y J de su
  planilla) contra Maxi.
Imprime un JSON con los dias cargados, turnos por dia y avisos.
"""
import sys, os, re, json, zipfile, shutil, subprocess, tempfile, datetime as dt, collections
import openpyxl

AQUI = os.path.dirname(os.path.abspath(__file__))
CIERRES = os.path.join(AQUI, 'data', 'cierres.json')
RECALC = '/mnt/skills/public/xlsx/scripts/recalc.py'
SUC = {'fpastas': 'FLORIDA', 'Beccar': 'BECCAR', 'Pastas Paz': 'OLIVOS'}
HOJAS = ['RESUMEN', 'FLORIDA', 'BECCAR', 'OLIVOS']
NO_ELECTRONICO = {'EFECTIVO', 'CTA. CTE.'}


def datos_maxi(mes):
    d = json.load(open(CIERRES))
    dias = collections.defaultdict(lambda: {'caja': 0.0, 'medios': 0.0, 'turnos': []})
    vistos = set()
    for x in d:
        if not x['fecha'].startswith(mes) or x['sucursal'] not in SUC:
            continue
        k = (x['sucursal'], x['fecha'], x['turno'])
        if k in vistos:
            continue
        vistos.add(k)
        r = dias[(SUC[x['sucursal']], x['fecha'])]
        r['caja'] += x['total']
        r['medios'] += x['total'] - sum(v[0] for f, v in x['formas'].items() if f.upper() in NO_ELECTRONICO)
        r['turnos'].append(x['turno'])
    return dias


def hojas_xml(z):
    wb = z.read('xl/workbook.xml').decode()
    rels = z.read('xl/_rels/workbook.xml.rels').decode()
    tgt = {m.group(1): m.group(2) for m in re.finditer(r'<Relationship Id="([^"]+)"[^>]*Target="([^"]+)"', rels)}
    out = {}
    for m in re.finditer(r'<sheet [^>]*name="([^"]+)"[^>]*r:id="([^"]+)"', wb):
        t = tgt[m.group(2)].lstrip('/')
        out[m.group(1)] = t if t.startswith('xl/') else 'xl/' + t
    return out


def fmt(v):
    r = round(float(v), 2)
    return repr(int(r)) if r == int(r) else repr(r)


def poner_valor(xml, ref, valor):
    """Pone un numero en la celda ref (conserva el estilo). Devuelve xml."""
    pat = re.compile(r'<c r="%s"( [^>]*?)?(/>|>.*?</c>)' % ref, re.S)
    m = pat.search(xml)
    if not m:
        raise SystemExit('No encuentro la celda %s' % ref)
    attrs = re.sub(r'\s*t="[^"]*"', '', m.group(1) or '')
    return xml[:m.start()] + '<c r="%s"%s><v>%s</v></c>' % (ref, attrs, fmt(valor)) + xml[m.end():]


def main():
    a = sys.argv[1:]
    cruce = None
    if '--cruce' in a:
        i = a.index('--cruce'); cruce = a[i + 1]; del a[i:i + 2]
    src, mes, out = a
    maxi = datos_maxi(mes)
    fer = openpyxl.load_workbook(src, data_only=True)
    avisos, cargados = [], []

    # filas por fecha de cada hoja
    filas = {}
    for h in ['FLORIDA', 'BECCAR', 'OLIVOS']:
        ws = fer[h]
        for r in range(4, 35):
            c = ws.cell(r, 3).value
            if isinstance(c, dt.datetime) and c.strftime('%Y-%m') == mes:
                filas[(h, c.strftime('%Y-%m-%d'))] = r

    tmp = tempfile.mkdtemp()
    with zipfile.ZipFile(src) as z:
        z.extractall(tmp)
        mapa = hojas_xml(z)
    # 1) escribir I y J
    for h in ['FLORIDA', 'BECCAR', 'OLIVOS']:
        p = os.path.join(tmp, mapa[h]); xml = open(p, encoding='utf-8').read()
        for (hh, f), r in sorted(filas.items()):
            if hh != h or (h, f) not in maxi:
                continue
            m = maxi[(h, f)]
            xml = poner_valor(xml, 'I%d' % r, m['caja'])
            xml = poner_valor(xml, 'J%d' % r, m['medios'])
            cargados.append({'local': h, 'fecha': f, 'caja': round(m['caja'], 2), 'medios': round(m['medios'], 2), 'turnos': m['turnos']})
        open(p, 'w', encoding='utf-8').write(xml)
    # recalcular el libro de trabajo
    p = os.path.join(tmp, 'xl/workbook.xml'); w = open(p, encoding='utf-8').read()
    w = re.sub(r'<calcPr([^>]*?)/>', lambda m: '<calcPr%s fullCalcOnLoad="1"/>' % re.sub(r'\s*fullCalcOnLoad="[^"]*"', '', m.group(1)), w)
    open(p, 'w', encoding='utf-8').write(w)
    base = os.path.join(tempfile.mkdtemp(), 'base.xlsx')
    with zipfile.ZipFile(src) as zi, zipfile.ZipFile(base, 'w', zipfile.ZIP_DEFLATED) as zo:
        for it in zi.infolist():
            zo.write(os.path.join(tmp, it.filename), it.filename)

    # 2) copia para recalcular: formulas de hojas TD y las que miran 'TD ' -> valor original
    orig_v = openpyxl.load_workbook(src, data_only=True)
    cp = openpyxl.load_workbook(base)
    for ws in cp:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value.startswith('=') and (ws.title.startswith('TD ') or "TD " in c.value):
                    c.value = orig_v[ws.title][c.coordinate].value
    calc = os.path.join(os.path.dirname(base), 'calc.xlsx'); cp.save(calc)
    subprocess.run([sys.executable, RECALC, calc, '90'], check=True, capture_output=True)
    val = openpyxl.load_workbook(calc, data_only=True)
    form = openpyxl.load_workbook(base)

    # 3) meter los valores calculados en las formulas de las 4 hojas
    for h in HOJAS:
        p = os.path.join(tmp, mapa[h]); xml = open(p, encoding='utf-8').read()
        for row in form[h].iter_rows():
            for c in row:
                if not (isinstance(c.value, str) and c.value.startswith('=')):
                    continue
                v = val[h][c.coordinate].value
                if v is None or (isinstance(v, str) and v.startswith('#')):
                    v = orig_v[h][c.coordinate].value
                if v is None:
                    continue
                pat = re.compile(r'(<c r="%s"[^>]*?)(/>|>(.*?)</c>)' % c.coordinate, re.S)
                m = pat.search(xml)
                if not m or '<f' not in (m.group(3) or ''):
                    continue
                inner = re.sub(r'<v>.*?</v>', '', m.group(3))
                head = re.sub(r'\s*t="[^"]*"', '', m.group(1))
                if isinstance(v, (dt.datetime, dt.date)):
                    d0 = v if isinstance(v, dt.datetime) else dt.datetime(v.year, v.month, v.day)
                    vv = (d0 - dt.datetime(1899, 12, 30)).days; cell = '%s>%s<v>%s</v></c>' % (head, inner, vv)
                elif isinstance(v, bool):
                    cell = '%s t="b">%s<v>%d</v></c>' % (head, inner, v)
                elif isinstance(v, (int, float)):
                    cell = '%s>%s<v>%s</v></c>' % (head, inner, repr(float(v)) if v != int(v) else int(v))
                else:
                    s = str(v).replace('&', '&amp;').replace('<', '&lt;')
                    cell = '%s t="str">%s<v>%s</v></c>' % (head, inner, s)
                xml = xml[:m.start()] + cell + xml[m.end():]
        open(p, 'w', encoding='utf-8').write(xml)
    with zipfile.ZipFile(src) as zi, zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zo:
        for it in zi.infolist():
            zo.write(os.path.join(tmp, it.filename), it.filename)
    shutil.rmtree(tmp, ignore_errors=True)

    # avisos de turnos
    # en octubre Florida cerro casi siempre con 2 turnos (Mañana + Intermedio) y a veces 3;
    # Beccar Mañana + Noche; Paz Mañana (+ Intermedio). Domingos y feriados, un turno.
    esperado = {'FLORIDA': 2, 'BECCAR': 2, 'OLIVOS': 1}
    for c in cargados:
        dom = dt.date.fromisoformat(c['fecha']).weekday() == 6
        falta = 'Mañana' not in c['turnos'] or (not dom and len(c['turnos']) < esperado[c['local']])
        if falta:
            avisos.append('%s %s: solo %s (puede faltar un turno)' % (c['local'], c['fecha'][8:] + '/' + c['fecha'][5:7], ' + '.join(c['turnos'])))
    hoy = dt.date.today().isoformat()
    for (h, f), r in sorted(filas.items()):
        if f < hoy and (h, f) not in maxi:
            avisos.append('%s %s: sin cierres de Maxi' % (h, f[8:] + '/' + f[5:7]))

    chk = openpyxl.load_workbook(out, data_only=True)
    res = {'salida': out, 'dias_cargados': len(cargados), 'cargados': cargados, 'avisos': avisos,
           'control': {h: [chk[h]['I35'].value, chk[h]['J35'].value] for h in ['FLORIDA', 'BECCAR', 'OLIVOS']}}
    if cruce:
        res['cruce'] = armar_cruce(src, filas, maxi, cruce)
    print(json.dumps(res, ensure_ascii=False, indent=1))


def armar_cruce(src, filas, maxi, out):
    from openpyxl.styles import Font, PatternFill, Alignment
    fer = openpyxl.load_workbook(src, data_only=True)
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = 'Cruce'
    hdr = ['LOCAL', 'FECHA', 'CAJA Fermin', 'CAJA Maxi', 'Dif caja', 'MEDIOS Fermin', 'MEDIOS Maxi', 'Dif medios',
           'Z total Fermin', 'Z - medios Maxi', 'Turnos Maxi', 'Estado']
    ws.append(['Cruce Planilla Z de Fermin contra Maxi Rest (diferencia = Fermin - Maxi; tolerancia $1)'])
    ws.append(hdr)
    for c in ws[2]:
        c.font = Font(bold=True, color='FFFFFF', name='Arial'); c.fill = PatternFill('solid', fgColor='7A3E2B')
        c.alignment = Alignment(wrap_text=True, horizontal='center')
    rojo = PatternFill('solid', fgColor='F4CCCC'); verde = PatternFill('solid', fgColor='D9EAD3')
    n_dif = n_ok = 0
    for (h, f), r in sorted(filas.items(), key=lambda x: (['FLORIDA', 'BECCAR', 'OLIVOS'].index(x[0][0]), x[0][1])):
        s = fer[h]; fi, fj = s.cell(r, 9).value, s.cell(r, 10).value
        e, ff = s.cell(r, 5).value or 0, s.cell(r, 6).value or 0
        m = maxi.get((h, f))
        if fi is None and m is None:
            continue
        mi = m['caja'] if m else None; mj = m['medios'] if m else None
        di = (fi - mi) if (isinstance(fi, (int, float)) and mi is not None) else None
        dj = (fj - mj) if (isinstance(fj, (int, float)) and mj is not None) else None
        zt = (e + ff) if (e or ff) else None
        if m is None: est = 'Sin cierre de Maxi'
        elif fi is None: est = 'Fermin todavia no cargo'
        elif abs(di or 0) <= 1 and abs(dj or 0) <= 1: est = 'OK'; n_ok += 1
        else: est = 'REVISAR'; n_dif += 1
        ws.append([h, dt.date.fromisoformat(f), fi, mi, di, fj, mj, dj, zt, (zt - mj) if (zt and mj is not None) else None,
                   ' + '.join(m['turnos']) if m else '', est])
        ws.cell(ws.max_row, 12).fill = verde if est == 'OK' else rojo if est == 'REVISAR' else PatternFill()
    for row in ws.iter_rows(min_row=3):
        row[1].number_format = 'dd/mm/yyyy'
        for c in row[2:10]: c.number_format = '#,##0.00;[Red]-#,##0.00'
        for c in row: c.font = Font(name='Arial')
    for i, w in enumerate([10, 11, 15, 15, 13, 15, 15, 13, 15, 15, 30, 24], 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w
    ws.freeze_panes = 'C3'
    c = wb.create_sheet('Como se calculo')
    for t in ['CAJA Fermin / MEDIOS Fermin: columnas I y J de la hoja de cada local de la planilla Z de Fermin.',
              'CAJA Maxi: venta total del dia segun los mails de cierre de Maxi Rest (suma de todos los turnos).',
              'MEDIOS Maxi: venta total - EFECTIVO - CTA. CTE. de los mismos cierres.',
              'Dif = Fermin - Maxi. OK si las dos diferencias son de $1 o menos.',
              'Z total Fermin: E + F (importe gravado + IVA) que cargo Fermin; Z - medios Maxi es su control de recaudacion contra Maxi.']:
        c.append([t])
    c.column_dimensions['A'].width = 120
    wb.save(out)
    return {'archivo': out, 'ok': n_ok, 'revisar': n_dif}


if __name__ == '__main__':
    main()

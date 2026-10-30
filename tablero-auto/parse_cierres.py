"""Lee el texto de uno o varios mails "MaxiREST - Fin de turno" y agrega los cierres a data/cierres.json.

Uso:  python3 tablero-auto/parse_cierres.py <archivo> [thread_id]
<archivo> puede ser el texto plano del mail o el JSON que devuelve get_thread (se toma plaintextBody de cada mensaje).
Un mismo mail puede traer varios cierres pegados (así llegan los de Pastas Paz): se separan por "TOTALES DEL DIA:".
No duplica: la clave de cada cierre es sucursal + fecha + turno.
"""
import json, re, sys, pathlib

DATA = pathlib.Path(__file__).resolve().parent / 'data'
MESES = {m: i + 1 for i, m in enumerate(['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto',
                                          'septiembre', 'octubre', 'noviembre', 'diciembre'])}
NUM = r'(-?[\d]+(?:\.\d+)?)'


def textos(path):
    raw = pathlib.Path(path).read_text(encoding='utf-8', errors='replace')
    try:
        d = json.loads(raw)
        msgs = d.get('messages', [d]) if isinstance(d, dict) else d
        return [(m.get('plaintextBody') or m.get('body') or '', m.get('subject', ''), m.get('sender', '')) for m in msgs]
    except json.JSONDecodeError:
        return [(raw, '', '')]


def parse_bloque(pre, b):
    suc = re.findall(r'Sucursal:\s*(.+)', pre)
    suc = suc[-1].strip() if suc else ''
    f = re.search(r'\w+ (\d{1,2}) de (\w+) de (\d{4})', b)
    t = re.search(r'Turno \d+ \((\w+)', b)
    tot = re.search(r'RESUMEN DE VENTAS.*?\nTOTAL ' + NUM + r' (\d+)', b, re.S)
    if not (f and t and tot):
        return None
    fecha = f"{int(f.group(3)):04d}-{MESES[f.group(2).lower()]:02d}-{int(f.group(1)):02d}"
    o = dict(sucursal=suc, fecha=fecha, turno=t.group(1), total=float(tot.group(1)), tickets=int(tot.group(2)))
    for k, pat in [('neto21', r'TOTAL Neto 21\.00% ' + NUM), ('iva21', r'TOTAL Iva 21\.00% ' + NUM),
                   ('neto105', r'TOTAL Neto 10\.50% ' + NUM), ('iva105', r'TOTAL Iva 10\.50% ' + NUM)]:
        m = re.search(pat, b)
        o[k] = float(m.group(1)) if m else 0.0
    fc = re.search(r'VENTAS POR FORMA DE COBRO.*?Forma de cobro Total Cant\s*\n~+\n(.*?)\n=+', b, re.S)
    o['formas'] = {}
    if fc:
        for line in fc.group(1).splitlines():
            m = re.match(r'\s*(.+?)\s+' + NUM + r'\s+(\d+)\s*$', line)
            if m:
                o['formas'][m.group(1).strip()] = [float(m.group(2)), int(m.group(3))]
    m = re.search(r'\n\s*202 Generico\s*' + NUM + r'\s+' + NUM, b)
    o['cod202_unid'], o['cod202_importe'] = (float(m.group(1)), float(m.group(2))) if m else (0.0, 0.0)
    return o


def main(path, thread=''):
    C = json.loads((DATA / 'cierres.json').read_text(encoding='utf-8'))
    claves = {(c['sucursal'].lower(), c['fecha'], c['turno']) for c in C}
    nuevos = []
    for body, subj, sender in textos(path):
        partes = body.split('TOTALES DEL DIA:')
        for i in range(1, len(partes)):
            o = parse_bloque(partes[i - 1], partes[i])
            if not o:
                continue
            suma = sum(v[0] for v in o['formas'].values())
            o.update(thread=thread, subject=subj or f"MaxiREST - Fin de turno - {o['fecha']} {o['turno']}", sender=sender)
            ok = abs(suma - o['total']) < 1
            k = (o['sucursal'].lower(), o['fecha'], o['turno'])
            print(f"{o['sucursal']} {o['fecha']} {o['turno']}: total {o['total']:,.2f} tickets {o['tickets']} "
                  f"formas {suma:,.2f} {'OK' if ok else 'NO CIERRA'}{' (ya estaba)' if k in claves else ''}")
            if k in claves or not ok:
                continue
            claves.add(k)
            nuevos.append(o)
    C += nuevos
    (DATA / 'cierres.json').write_text(json.dumps(C, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(nuevos)} cierres nuevos agregados')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else '')

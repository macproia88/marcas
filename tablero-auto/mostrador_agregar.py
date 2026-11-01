"""Resume la venta detallada de Maxi Rest (un archivo por local, puede traer varios meses) en data/mostrador_det.json, un bloque por mes.
Uso: python3 tablero-auto/mostrador_agregar.py Florida=<archivo> Beccar=<archivo> Paz=<archivo>
Solo tickets de mostrador (sin apps ni notas de crédito). No guarda datos de clientes.
"""
import sys, json, pathlib, collections
from maxi_detallada import parse_auto as parse
AQUI = pathlib.Path(__file__).resolve().parent
BANDAS = [(0, 10000, 'Hasta $10.000'), (10000, 20000, '$10.000 a $20.000'), (20000, 30000, '$20.000 a $30.000'),
          (30000, 50000, '$30.000 a $50.000'), (50000, 1e12, 'Más de $50.000')]
FORMAS = {'EFECTIVO': 'Efectivo', 'VISA DEBITO': 'Débito', 'Mercado Pago': 'Mercado Pago', 'MODO': 'MODO',
          'VISA': 'Crédito', 'MASTER': 'Crédito', 'AMEX': 'Crédito', 'CABAL': 'Crédito'}

def bloque(m, L, out):
    m = m.copy(); m['dw'] = m.FECHA.map(lambda d: d.weekday())
    ndias = m.groupby('dw').FECHA.nunique()
    for (dw, h), n in m.groupby(['dw', 'H']).size().items():
        out['horas'].append(dict(local=L, dia=int(dw), hora=int(h), tickets=round(n / ndias[dw], 1)))
    for i, (a, b, n) in enumerate(BANDAS):
        s_ = m[(m.IMPORTE >= a) & (m.IMPORTE < b)]
        out['bandas'].append(dict(local=L, orden=i, banda=n, tickets=int(len(s_)), venta=round(s_.IMPORTE.sum())))
    c = collections.defaultdict(lambda: [0, 0.0])
    for fo, imp, pagos in zip(m.COBRO, m.IMPORTE, m.PAGOS):
        k = 'Pago combinado' if pagos > 1 else FORMAS.get(str(fo).strip(), 'Otros')
        c[k][0] += 1; c[k][1] += imp
    for k, (n, v) in c.items():
        out['cobro'].append(dict(local=L, forma=k, tickets=n, venta=round(v)))
    out['resumen'].append(dict(local=L, desde=str(m.FECHA.min()), hasta=str(m.FECHA.max()), tickets=int(len(m)), venta=round(m.IMPORTE.sum()), ticket=round(m.IMPORTE.mean())))


def main(archivos):
    p = AQUI / 'data' / 'mostrador_det.json'
    todo = json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
    nuevos = {}
    for L, f in archivos.items():
        df, _ = parse(f, L)
        m = df[(df.CANAL == 'Mostrador') & (df.IMPORTE > 0)].copy()
        m['mes'] = m.FECHA.map(lambda d: d.strftime('%Y-%m'))
        for mes, g in m.groupby('mes'):
            out = nuevos.setdefault(mes, {'mes': mes, 'horas': [], 'bandas': [], 'cobro': [], 'resumen': []})
            for k in ('horas', 'bandas', 'cobro', 'resumen'):
                out[k] = [r for r in out[k] if r['local'] != L]
            bloque(g, L, out)
    for mes, out in nuevos.items():
        viejo = todo.get(mes, {'mes': mes, 'horas': [], 'bandas': [], 'cobro': [], 'resumen': []})
        locs = {r['local'] for r in out['resumen']}
        for k in ('horas', 'bandas', 'cobro', 'resumen'):
            viejo[k] = [r for r in viejo[k] if r['local'] not in locs] + out[k]
        todo[mes] = viejo
        print(mes, [(r['local'], r['desde'], r['hasta'], r['tickets']) for r in out['resumen']])
    p.write_text(json.dumps(todo, ensure_ascii=False), encoding='utf-8')

if __name__ == '__main__':
    main(dict(a.split('=', 1) for a in sys.argv[1:]))

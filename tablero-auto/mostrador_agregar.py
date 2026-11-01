"""Resume la venta detallada de Maxi Rest (un archivo por local) en data/mostrador_mes_<AAAA-MM>.json.
Uso: python3 tablero-auto/mostrador_agregar.py <AAAA-MM> Florida=<archivo> Beccar=<archivo> Paz=<archivo>
Solo tickets de mostrador (sin apps ni notas de crédito). No guarda datos de clientes.
"""
import sys, json, pathlib, collections
from maxi_detallada import parse
AQUI = pathlib.Path(__file__).resolve().parent
BANDAS = [(0, 10000, 'Hasta $10.000'), (10000, 20000, '$10.000 a $20.000'), (20000, 30000, '$20.000 a $30.000'),
          (30000, 50000, '$30.000 a $50.000'), (50000, 1e12, 'Más de $50.000')]
FORMAS = {'EFECTIVO': 'Efectivo', 'VISA DEBITO': 'Débito', 'Mercado Pago': 'Mercado Pago', 'MODO': 'MODO',
          'VISA': 'Crédito', 'MASTER': 'Crédito', 'AMEX': 'Crédito', 'CABAL': 'Crédito'}

def main(mes, archivos):
    out = {'mes': mes, 'horas': [], 'bandas': [], 'cobro': [], 'resumen': []}
    for L, f in archivos.items():
        df, _ = parse(f, L)
        m = df[(df.CANAL == 'Mostrador') & (df.IMPORTE > 0)].copy()
        m['dw'] = m.FECHA.map(lambda d: d.weekday())
        ndias = m.groupby('dw').FECHA.nunique()
        g = m.groupby(['dw', 'H']).size()
        for (dw, h), n in g.items():
            out['horas'].append(dict(local=L, dia=int(dw), hora=int(h), tickets=round(n / ndias[dw], 1)))
        for i, (a, b, n) in enumerate(BANDAS):
            s = m[(m.IMPORTE >= a) & (m.IMPORTE < b)]
            out['bandas'].append(dict(local=L, orden=i, banda=n, tickets=int(len(s)), venta=round(s.IMPORTE.sum())))
        c = collections.defaultdict(lambda: [0, 0.0])
        for fo, imp, pagos in zip(m.COBRO, m.IMPORTE, m.PAGOS):
            k = 'Pago combinado' if pagos > 1 else FORMAS.get(str(fo).strip(), 'Otros')
            c[k][0] += 1; c[k][1] += imp
        for k, (n, v) in c.items():
            out['cobro'].append(dict(local=L, forma=k, tickets=n, venta=round(v)))
        out['resumen'].append(dict(local=L, desde=str(m.FECHA.min()), hasta=str(m.FECHA.max()), tickets=int(len(m)),
                                   venta=round(m.IMPORTE.sum()), ticket=round(m.IMPORTE.mean())))
    p = AQUI / 'data' / f'mostrador_mes_{mes}.json'
    p.write_text(json.dumps(out, ensure_ascii=False), encoding='utf-8'); print('ok', p.name, out['resumen'])

if __name__ == '__main__':
    main(sys.argv[1], dict(a.split('=', 1) for a in sys.argv[2:]))

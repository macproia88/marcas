"""Referencia del año pasado día por día desde la venta detallada de Maxi Rest de 2025 (un archivo por local).
Uso: python3 tablero-auto/ref_det_2025.py Florida=<archivo> Beccar=<archivo> Paz=<archivo>
Escribe data/ref_2025_det.json: para cada día de 2026, el mismo día de la semana de 2025 (364 días antes), con
venta total, venta y tickets de mostrador, venta y pedidos de apps. Solo tickets con importe > 0 (sin notas de crédito).
actualizar.py la usa para completar los días que no tienen referencia de la planilla de la presentación (ref_2025.json manda)."""
import sys, json, pathlib, datetime as dt, collections
from maxi_detallada import parse_auto as parse
DATA = pathlib.Path(__file__).resolve().parent / 'data'


def main(archivos):
    p = DATA / 'ref_2025_det.json'
    R = {(r['fecha'], r['local']): r for r in (json.loads(p.read_text(encoding='utf-8')) if p.exists() else [])}
    for L, f in archivos.items():
        df, _ = parse(f, L)
        df = df[df.IMPORTE > 0]
        g = collections.defaultdict(lambda: [0.0, 0, 0.0, 0])
        for fe, canal, imp in zip(df.FECHA, df.CANAL, df.IMPORTE):
            a = g[str(fe)[:10]]
            if canal == 'Mostrador': a[0] += imp; a[1] += 1
            elif str(canal).startswith('App'): a[2] += imp; a[3] += 1
        for d25, (vm, tm, va, pa) in g.items():
            f26 = (dt.date.fromisoformat(d25) + dt.timedelta(days=364)).isoformat()
            R[(f26, L)] = dict(fecha=f26, local=L, fecha_2025=d25, venta_2025=round(vm + va, 2), venta_mostrador_2025=round(vm, 2),
                               tickets_mostrador_2025=tm, venta_app_2025=round(va, 2), pedidos_app_2025=pa)
        print(L, len(g), 'días de 2025', min(g), max(g))
    p.write_text(json.dumps(sorted(R.values(), key=lambda r: (r['fecha'], r['local'])), ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main(dict(a.split('=', 1) for a in sys.argv[1:]))

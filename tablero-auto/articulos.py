"""Venta de mostrador por artículo y por rubro, mes a mes, para el tablero de mostrador.

De dónde sale:
  1. Base del mes (opcional): el informe de Maxi Rest "unidades por artículo" (columnas CODIGO, NOMBRE, NOMSUC, UNIDADES, IMPORTE).
     Ese informe es solo de mostrador más el código 202 (Generico), que es la venta de apps: el 202 se descarta.
     Carga:  python3 tablero-auto/articulos.py base <archivo.xlsx> <AAAA-MM> <último día que cubre, AAAA-MM-DD>
  2. Días siguientes: VENTAS POR ARTICULO de los mails de fin de turno (campo articulos de data/cierres.json, sin el 202).
     Se suman solos en cada corrida del tablero.
Rubro de cada artículo: el que trae el mail de cierre ("Rubro: 29 - Ravioles"); si el código nunca apareció en un mail,
el del informe de venta por rubro (top_mostrador.json); si no, "Otros".
Control: para cada local, la suma de la base sin el 202 tiene que dar la venta de mostrador de esos días (ventas_diarias.json).
"""
import collections, json, pathlib, sys

DATA = pathlib.Path(__file__).resolve().parent / 'data'
LOCAL = {'fpastas': 'Florida', 'florida': 'Florida', 'beccar': 'Beccar', 'pastas paz': 'Paz', 'olivos': 'Paz', 'paz': 'Paz'}
FUERA = {202, 1}  # 202 = Generico (apps); 1 = DESCRIPCION (línea de texto, importe 0)


def cargar(n, defecto):
    p = DATA / n
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else defecto


def base(xlsx, mes, hasta):
    import pandas as pd
    x = pd.read_excel(xlsx)
    x['local'] = x['NOMSUC'].astype(str).str.strip().str.lower().map(LOCAL)
    filas = [[r.local, int(r.CODIGO), str(r.NOMBRE).strip(), float(r.UNIDADES), float(r.IMPORTE)]
             for r in x.itertuples() if int(r.CODIGO) not in FUERA and r.local]
    B = cargar('art_base.json', {})
    B[mes] = dict(desde=f'{mes}-01', hasta=hasta, archivo=pathlib.Path(xlsx).name, filas=filas)
    (DATA / 'art_base.json').write_text(json.dumps(B, ensure_ascii=False), encoding='utf-8')
    # control contra la venta de mostrador de esos días
    V = cargar('ventas_diarias.json', [])
    vm = collections.Counter(); ba = collections.Counter()
    for r in V:
        if f'{mes}-01' <= r['fecha'] <= hasta: vm[r['local']] += r['venta_mostrador']
    for f in filas: ba[f[0]] += f[4]
    for L in sorted(ba):
        print(f'{L}: artículos ${ba[L]:,.0f}  mostrador ${vm[L]:,.0f}  diferencia ${ba[L]-vm[L]:,.0f}')


def armar():
    """Devuelve {mes: dict(desde, hasta, filas=[{local, codigo, articulo, rubro, cantidad, venta}])}."""
    B = cargar('art_base.json', {}); C = cargar('cierres.json', []); T = cargar('top_mostrador.json', [])
    rubro = {r['codigo']: r['rubro'] for r in T if r.get('codigo') is not None}
    nombre = {}
    for m in B.values():
        for L, cod, nom, u, imp in m['filas']: nombre[cod] = nom
    for c in C:
        for cod, nom, rb, u, imp in c.get('articulos') or []:
            if rb: rubro[cod] = rb
            nombre.setdefault(cod, nom)
    acc = collections.defaultdict(lambda: collections.defaultdict(lambda: [0.0, 0.0]))
    rango = {}
    for mes, m in B.items():
        rango[mes] = [m['desde'], m['hasta']]
        for L, cod, nom, u, imp in m['filas']:
            a = acc[mes][(L, cod)]; a[0] += u; a[1] += imp
    for c in C:
        mes = c['fecha'][:7]; L = LOCAL.get(c['sucursal'].strip().lower())
        if not L or not c.get('articulos'): continue
        if mes in B and c['fecha'] <= B[mes]['hasta']: continue
        r = rango.setdefault(mes, [c['fecha'], c['fecha']]); r[0] = min(r[0], c['fecha']); r[1] = max(r[1], c['fecha'])
        for cod, nom, rb, u, imp in c['articulos']:
            if cod in FUERA: continue
            a = acc[mes][(L, cod)]; a[0] += u; a[1] += imp
    out = {}; porkilo = por_kilo(B, C)
    for mes, d in acc.items():
        out[mes] = dict(desde=rango[mes][0], hasta=rango[mes][1],
                        filas=[dict(local=L, codigo=cod, articulo=nombre.get(cod, str(cod)), rubro=('Descuentos del club' if cod == 4000 else rubro.get(cod, 'Otros')),
                                    cantidad=round(u, 2), venta=round(v, 2), kg=cod in porkilo) for (L, cod), (u, v) in d.items()])
    return out


def por_kilo(B, C):
    """Productos que se venden por peso: los que alguna vez aparecen con cantidad con decimales (400 g = 0,4)."""
    k = set()
    for m in B.values():
        for L, cod, nom, u, imp in m['filas']:
            if abs(u - round(u)) > 1e-6: k.add(cod)
    for c in C:
        for cod, nom, rb, u, imp in c.get('articulos') or []:
            if abs(u - round(u)) > 1e-6: k.add(cod)
    return k


if __name__ == '__main__':
    if len(sys.argv) >= 5 and sys.argv[1] == 'base':
        base(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        for mes, d in sorted(armar().items()):
            s = collections.Counter()
            for f in d['filas']: s[f['local']] += f['venta']
            print(mes, d['desde'], d['hasta'], {k: round(v) for k, v in s.items()})

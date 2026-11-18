"""Tarjeta de rendimiento estilo "Meta Business" con los datos del robot de métricas.
Uso: python3 tarjeta_rendimiento.py datos.json salida.png carpeta_ttf
"""
import sys, json, datetime as dt
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch

d = json.load(open(sys.argv[1])); SAL = sys.argv[2]; TTF = sys.argv[3]
R = fm.FontProperties(fname=f"{TTF}/lato-latin-400-normal.ttf")
B = fm.FontProperties(fname=f"{TTF}/lato-latin-700-normal.ttf")
D = d["dias"]; ks = sorted(D)
fin = dt.date.fromisoformat(ks[-1]); ini = fin - dt.timedelta(days=13)
a_fin = ini - dt.timedelta(days=1); a_ini = a_fin - dt.timedelta(days=13)
rng = lambda a, b: [k for k in ks if a.isoformat() <= k <= b.isoformat()]
act, ant = rng(ini, fin), rng(a_ini, a_fin)
suma = lambda ds, m: sum(D[k][m] for k in ds)
v1, v0 = suma(act, "views"), suma(ant, "views")
r1, r0 = suma(act, "reach"), suma(ant, "reach")
pct = lambda a, b: (a - b) / b * 100 if b else 0
miles = lambda n: f"{n:,}".replace(",", ".")
MES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
fecha = lambda x: f"{x.day} {MES[x.month-1]}"

# publicaciones de hoy (después del período) para el bloque "Hoy"
hoy = d["actualizado"][:10]
pubs = [p for p in d["publicaciones"] if p["timestamp"][:10] >= hoy and p.get("metricas")]
hist = [h for h in d.get("historias", []) if h.get("metricas")]

W, H = 10.8, 17.2
fig = plt.figure(figsize=(W, H), dpi=100); fig.patch.set_facecolor("white")
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1080); ax.set_ylim(1720, 0); ax.axis("off")
NEG, GRIS, VERDE_OK, ROJO = "#1c1e21", "#65676b", "#1a8f3c", "#c62828"
def txt(x, y, s, f=R, size=30, c=NEG, **k): ax.text(x, y, s, fontproperties=f, fontsize=size * 0.72, color=c, va="top", **k)
# pestañas
for x, s, act_ in [(80, "Inicio", 0), (282, "Rendimiento", 1), (572, "Contenido", 0), (846, "Audiencia", 0)]:
    txt(x, 40, s, B if act_ else R, 34, NEG if act_ else GRIS)
ax.plot([297, 513], [124, 124], color=NEG, lw=5); ax.plot([0, 1080], [128, 128], color="#e4e6eb", lw=1.5)
txt(50, 205, "Todo el contenido", B, 40); txt(838, 210, "14 días", R, 36, GRIS)
txt(50, 262, f"@escuelatallerfatima · {fecha(ini)} al {fecha(fin)}", R, 26, GRIS)
def caja(x, y, w, h, tit, val, var, borde):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=34", fc="#f0f2f5", ec=NEG if borde else "#f0f2f5", lw=4 if borde else 0))
    txt(x + 46, y + 48, tit, R, 32, GRIS); txt(x + 46, y + 108, val, B, 52)
    txt(x + 46, y + 198, f"{'+' if var >= 0 else ''}{var:.1f}".replace(".", ",") + f"% vs. {fecha(a_ini)} al {fecha(a_fin)}", R, 26, VERDE_OK if var >= 0 else ROJO)
caja(50, 315, 470, 280, "Reproducciones", miles(v1), pct(v1, v0), True)
caja(560, 315, 470, 280, "Alcance (personas)", miles(r1), pct(r1, r0), False)
# gráfico
g = fig.add_axes([0.14, 0.40, 0.81, 0.21]); xs = list(range(len(act))); ys = [D[k]["views"] for k in act]
g.plot(xs, ys, color="#c40ccc", lw=4); top = max(ys) * 1.1
for y in (0, top / 2, top): g.axhline(y, color="#e4e6eb", lw=1.5, zorder=0)
g.set_yticks([0, top / 2, top]); g.set_yticklabels(["0", (f"{top/2/1000:.1f} mil".replace(".", ",") if top >= 2000 else miles(round(top/2))), (f"{top/1000:.1f} mil".replace(".", ",") if top >= 2000 else miles(round(top)))], fontproperties=R, fontsize=21, color=GRIS)
g.set_xticks([0, len(xs) - 1]); g.set_xticklabels([fecha(ini), fecha(fin)], fontproperties=R, fontsize=22, color=GRIS)
for s in g.spines.values(): s.set_visible(False)
g.tick_params(length=0, pad=12); g.set_ylim(0, top * 1.02); g.set_xlim(-0.3, len(xs) - 0.7)
txt(50, 1118, "Reproducciones por día. El alcance es la suma diaria de cuentas alcanzadas.", R, 24, GRIS)
# bloque hoy
ax.plot([50, 1030], [1175, 1175], color="#e4e6eb", lw=1.5)
txt(50, 1195, f"Hoy {dt.date.fromisoformat(hoy).day}/{dt.date.fromisoformat(hoy).month}: vuelve a publicar la cuenta", B, 34)
y = 1265
for p in pubs:
    m = p["metricas"]
    txt(50, y, "Carrusel Expo 2026", B, 30, "#00894C")
    txt(50, y + 48, f"{miles(m.get('views',0))} reproducciones · {miles(m.get('reach',0))} personas · {m.get('likes',0)} me gusta · {m.get('profile_visits',0)} visitas al perfil", R, 26); y += 115
for h in hist[:1]:
    m = h["metricas"]
    txt(50, y, "Historia con flashes", B, 30, "#00894C")
    txt(50, y + 48, f"{miles(m.get('views',0))} reproducciones · {miles(m.get('reach',0))} personas · {m.get('shares',0)} compartida", R, 26); y += 115
r_9_17 = suma(rng(fin - dt.timedelta(days=8), fin), "reach")
if pubs:
    txt(50, y + 5, f"Solo el carrusel de hoy llegó a {miles(pubs[0]['metricas'].get('reach',0))} personas: más que los 9 días anteriores juntos ({miles(r_9_17)}).", B, 26, NEG)
txt(50, 1640, f"Datos de Instagram · actualizado {d['actualizado']} h", R, 22, GRIS)
fig.savefig(SAL, dpi=100, facecolor="white"); print(v1, v0, r1, r0, r_9_17)

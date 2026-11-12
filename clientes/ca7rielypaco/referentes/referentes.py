"""Seguidores y actividad de las cuentas de los artistas y de otros fan clubs (Business Discovery de la API de Instagram).
Uso (en GitHub Actions): IG_TOKEN=... python3 referentes.py -> escribe datos.json (con historial por fecha)."""
import os, json, datetime, urllib.request, urllib.parse
AQUI = os.path.dirname(os.path.abspath(__file__))
IG = "17841475673833807"
CUENTAS = ["ca7riel", "pacoamoroso", "ca7rielypacoamoroso", "ca7rielypacoamorosoarg",
           "ca7rielypaco_usa", "pacoyca7o", "ca7rielxpacochile", "pacoyca7riel_", "pacoxamoroso"]
T = os.environ["IG_TOKEN"].strip().strip('"')
campos = "username,name,followers_count,media_count,media.limit(12){timestamp,like_count,comments_count,media_type}"
hoy = (datetime.datetime.utcnow() - datetime.timedelta(hours=3)).strftime("%Y-%m-%d %H:%M")
f = os.path.join(AQUI, "datos.json")
d = json.load(open(f)) if os.path.exists(f) else {"historial": {}}
res = {}
for u in CUENTAS:
    q = urllib.parse.urlencode({"fields": f"business_discovery.username({u}){{{campos}}}", "access_token": T})
    try:
        r = json.load(urllib.request.urlopen(f"https://graph.facebook.com/v23.0/{IG}?{q}", timeout=30))
        b = r["business_discovery"]; m = (b.get("media") or {}).get("data", [])
        res[u] = {"nombre": b.get("name"), "seguidores": b.get("followers_count"), "publicaciones": b.get("media_count"),
                  "ultimas12_likes_prom": round(sum(x.get("like_count", 0) for x in m) / len(m)) if m else None,
                  "ultima_pub": m[0]["timestamp"] if m else None}
    except urllib.error.HTTPError as e:
        res[u] = {"error": json.loads(e.read().decode() or "{}").get("error", {}).get("message", str(e))[:150]}
    except Exception as e:
        res[u] = {"error": str(e)[:150]}
d["actualizado"] = hoy; d["cuentas"] = res
# historial por corrida (fecha y hora): seguidores, publicaciones totales y promedio de me gusta
h = d.setdefault("historial", {})
for k in list(h):  # formato viejo (solo fecha -> seguidores)
    if len(k) == 10 and all(isinstance(x, int) for x in h[k].values()):
        h[k + " 22:05"] = {u: {"seg": n} for u, n in h.pop(k).items()}
h[hoy] = {u: {"seg": v["seguidores"], "pubs": v.get("publicaciones"), "likes": v.get("ultimas12_likes_prom")}
          for u, v in res.items() if v.get("seguidores")}
json.dump(d, open(f, "w"), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))

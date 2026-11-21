# Analiza SOLO horarios de mensajes (sin textos ni nombres) para ver si conviene la caché de Claude.
import json, os, datetime, statistics, sys
sys.path.insert(0, os.path.dirname(__file__))
import rapido as r
DIAS = 60; ESPERA = 45; CACHE = 300
desde = r.ahora - datetime.timedelta(days=DIAS)
convs, url_p = [], {"platform": "instagram", "limit": 50, "fields": "id,updated_time,messages.limit(100){from,created_time}"}
data = r.get(f"{r.IG}/conversations", **url_p)
while True:
    for c in data.get("data", []):
        if r.fecha(c["updated_time"]) < desde: continue
        convs.append(c)
    nxt = (data.get("paging") or {}).get("cursors", {}).get("after")
    if not nxt or len(convs) > 600 or not data.get("data") or r.fecha(data["data"][-1]["updated_time"]) < desde: break
    data = r.get(f"{r.IG}/conversations", after=nxt, **url_p)
llamadas, por_charla, msgs_cli = [], [], 0
for c in convs:
    ms = sorted((c.get("messages") or {}).get("data", []), key=lambda m: m["created_time"])
    t_cli = [r.fecha(m["created_time"]) for m in ms if (m.get("from") or {}).get("username") != r.YO and r.fecha(m["created_time"]) >= desde]
    msgs_cli += len(t_cli)
    turnos = []
    for t in t_cli:  # mensajes del cliente a menos de 45 s se contestan juntos = 1 llamada
        if turnos and (t - turnos[-1][1]).total_seconds() <= ESPERA: turnos[-1][1] = t
        else: turnos.append([t, t])
    llamadas += [x[1] for x in turnos]; por_charla.append(len(turnos))
llamadas.sort()
gaps = [(b - a).total_seconds() for a, b in zip(llamadas, llamadas[1:])]
hits = sum(1 for g in gaps if g <= CACHE)
hits_1h = sum(1 for g in gaps if g <= 3600)
dias_act = len({t.date() for t in llamadas}) or 1
out = {"generado": r.ahora.strftime("%Y-%m-%d %H:%M"), "dias_analizados": DIAS, "charlas": len(convs),
       "mensajes_cliente": msgs_cli, "llamadas_estimadas": len(llamadas), "dias_con_mensajes": dias_act,
       "llamadas_por_dia_activo": round(len(llamadas) / dias_act, 1),
       "pct_llamadas_dentro_5min": round(100 * hits / max(len(llamadas), 1), 1),
       "pct_llamadas_dentro_1h": round(100 * hits_1h / max(len(llamadas), 1), 1),
       "mediana_min_entre_llamadas": round(statistics.median(gaps) / 60, 1) if gaps else None,
       "turnos_por_charla_prom": round(sum(por_charla) / max(len(por_charla), 1), 1),
       "por_hora": {h: sum(1 for t in llamadas if t.hour == h) for h in range(24)}}
json.dump(out, open(os.path.join(os.path.dirname(__file__), "analisis_tiempos.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "por_hora"}))

"""Carga única: busca clientes tibios de los últimos 7 días (más de 24 h sin respuesta, ya no se les puede escribir por el bot)
y los suma a la lista de tibios para que Juan les escriba a mano. No manda ningún mensaje."""
import json, datetime
import rapido as r

def main():
    convs = r.get(f"{r.IG}/conversations", platform="instagram", limit=100,
                  fields="id,updated_time,participants,messages.limit(12){id,from,message,created_time,story}").get("data", [])
    sistema = r.instrucciones(); n = t_n = 0
    for c in convs:
        msgs = (c.get("messages") or {}).get("data", [])
        if not msgs: continue
        cli = next((m for m in msgs if (m.get("from") or {}).get("username") != r.YO), None)
        if not cli: continue
        edad = (r.ahora - r.fecha(cli["created_time"])).total_seconds() / 3600
        if not (24 <= edad <= 24 * 7): continue
        if any(t in (m.get("message") or "") for m in msgs for t in r.NO_CLIENTE): continue
        cliente = next((p for p in (c.get("participants") or {}).get("data", []) if p.get("username") != r.YO), {})
        usuario = cliente.get("username")
        if not usuario or any(x.get("usuario") == usuario for x in r.tibios()): continue
        charla = [{"de": "nosotros" if (m.get("from") or {}).get("username") == r.YO else "cliente",
                   "texto": m.get("message") or "[adjunto/audio/foto]",
                   "hora": r.fecha(m["created_time"]).strftime("%d/%m %H:%M")} for m in reversed(msgs)]
        n += 1
        try: j = r.json_de(r.claude(sistema + r.RECORDATORIO, charla)) or {}
        except Exception as e: print("error:", type(e).__name__); continue
        if j.get("tibio"):
            t_n += 1
            r.tibios().append({"usuario": usuario, "cuando": r.fecha(cli["created_time"]).strftime("%Y-%m-%d"),
                               "quinta": j.get("quinta", "?"), "fecha": j.get("fecha", "?"), "personas": j.get("personas", "?"),
                               "resumen": j.get("resumen", ""), "estado": "sin respuesta", "recordatorio": False})
    r._TIBIOS_CAMBIO = True; r.guardar_tibios()
    print(f"revisadas {n}, tibios {t_n}")

if __name__ == "__main__":
    main()

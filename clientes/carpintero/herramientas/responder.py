"""Respuestas automáticas de El carpintero3 (@elcarpintero3f): cada 2 horas contesta comentarios y mensajes nuevos
pasando el WhatsApp del negocio. Pedido y aprobado por Juan el 16/11/2026.

- Comentarios: de las últimas 15 publicaciones, los de los últimos 7 días que todavía no tienen respuesta de la cuenta.
- Mensajes directos: charlas donde lo último lo escribió el cliente, dentro de las 24 h que permite Instagram,
  y a las que no les mandamos este mensaje en los últimos 3 días.
- No guarda nombres ni textos en el repo (es público): el registro va fuera del repo, en /tmp, y la API es la fuente de verdad
  para no responder dos veces (si la cuenta ya contestó, se saltea).
Lo llama publicar.py en cada vuelta del reloj; acá adentro se controla que pasen 2 horas entre vueltas.
"""
import datetime, json, os, sys, urllib.error, urllib.parse, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "quinta-ig", "publicador"))
import conectar  # noqa: E402

USUARIO = "elcarpintero3f"
CADA = datetime.timedelta(hours=2)
MARCA = "/tmp/carpintero-responder.json"
AR = datetime.timezone(datetime.timedelta(hours=-3))
ahora = datetime.datetime.now(AR)

WHATSAPP = "11 4194-3328"
LINK = "https://wa.me/5491141943328"
COMENTARIO = f"¡Gracias por escribir! 🙌 Te pasamos precio, medidas y colores por WhatsApp al {WHATSAPP} 📲 (link en el perfil)."
DM = (f"¡Hola! Gracias por escribirnos 🙌 Para precios, medidas y colores escribinos al WhatsApp {WHATSAPP} 👉 {LINK} "
      f"y te respondemos enseguida.\n📍 Showroom: Román Gómez 1893, José Ingenieros (lun a vie 11 a 18:30, sáb 11 a 16).")
FIRMA = "Para precios, medidas y colores escribinos al WhatsApp"


def fecha(s):
    return datetime.datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=datetime.timezone.utc).astimezone(AR)


def main(forzar=False):
    estado = json.load(open(MARCA)) if os.path.exists(MARCA) else {}
    ult = estado.get("ultima")
    if ult and not forzar and ahora - datetime.datetime.fromisoformat(ult) < CADA:
        return
    cuentas = json.load(open(os.path.join(REPO, "quinta-ig", "publicador", "cuentas.json"), encoding="utf-8"))
    fila = next(c for c in cuentas if c["usuario"] == USUARIO)
    token = conectar.llave_de(fila)
    ig = fila["ig_id"]
    api = "https://graph.instagram.com/v23.0" if token.startswith("IG") else "https://graph.facebook.com/v23.0"

    def llamar(metodo, ruta, tok=token, **p):
        p["access_token"] = tok
        datos = urllib.parse.urlencode(p).encode()
        req = urllib.request.Request(f"{api}/{ruta}" + ("?" + datos.decode() if metodo == "GET" else ""),
                                     data=None if metodo == "GET" else datos, method=metodo)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            cuerpo = e.read().decode(errors="ignore")
            try:
                cuerpo = json.loads(cuerpo)["error"].get("message", cuerpo)
            except Exception:
                pass
            raise RuntimeError(cuerpo[:200])

    res = {"comentarios": 0, "dms": 0, "errores": []}
    # 1) Comentarios
    try:
        for m in llamar("GET", f"{ig}/media", fields="id,timestamp", limit=15).get("data", []):
            for cm in llamar("GET", f"{m['id']}/comments", fields="id,username,timestamp,replies{username}", limit=50).get("data", []):
                if cm.get("username") == USUARIO or (ahora - fecha(cm["timestamp"])).days > 7:
                    continue
                if any(r.get("username") == USUARIO for r in (cm.get("replies") or {}).get("data", [])):
                    continue
                try:
                    llamar("POST", f"{cm['id']}/replies", message=COMENTARIO)
                    res["comentarios"] += 1
                except Exception as e:
                    res["errores"].append("respuesta comentario: " + str(e)[:120])
    except Exception as e:
        res["errores"].append("comentarios: " + str(e)[:150])

    # 2) Mensajes directos (si la llave tiene permiso de mensajes)
    def charlas(dueno, tok):
        return llamar("GET", f"{dueno}/conversations", tok=tok, platform="instagram", limit=40,
                      fields="id,updated_time,participants,messages.limit(6){from,message,created_time}").get("data", [])
    fuentes = [(ig, token)]
    try:
        for pg in llamar("GET", "me/accounts", fields="id,access_token,instagram_business_account", limit=50).get("data", []):
            if (pg.get("instagram_business_account") or {}).get("id") == ig:
                fuentes.append((pg["id"], pg["access_token"]))
    except Exception:
        pass
    hecho = False
    for dueno, tok in fuentes:
        try:
            convs = charlas(dueno, tok)
        except Exception as e:
            res["errores"].append(f"mensajes ({'cuenta' if dueno == ig else 'página'}): " + str(e)[:150])
            continue
        hecho = True
        for c in convs:
            msgs = (c.get("messages") or {}).get("data", [])
            if not msgs:
                continue
            ultimo = msgs[0]
            de = (ultimo.get("from") or {}).get("username")
            if de == USUARIO or (ahora - fecha(ultimo["created_time"])) > datetime.timedelta(hours=23):
                continue
            # ¿Le mandamos este mensaje hace menos de 3 días?
            ya = any((m.get("from") or {}).get("username") == USUARIO and FIRMA in (m.get("message") or "")
                     and (ahora - fecha(m["created_time"])).days < 3 for m in msgs)
            if ya:
                continue
            cliente = next((p for p in (c.get("participants") or {}).get("data", []) if p.get("username") != USUARIO), {})
            if not cliente.get("id"):
                continue
            try:
                llamar("POST", f"{dueno}/messages", tok=tok, recipient=json.dumps({"id": cliente["id"]}),
                       message=json.dumps({"text": DM}))
                res["dms"] += 1
            except Exception as e:
                res["errores"].append("respuesta mensaje: " + str(e)[:120])
        break
    if not hecho and not any(e.startswith("mensajes") for e in res["errores"]):
        res["errores"].append("mensajes: sin acceso")

    estado = {"ultima": ahora.isoformat(), "ultimo_resultado": res}
    json.dump(estado, open(MARCA, "w"), ensure_ascii=False)
    print(f"Carpintero respuestas: {res['comentarios']} comentarios, {res['dms']} mensajes, errores: {res['errores']}")


if __name__ == "__main__":
    main(forzar="--ya" in sys.argv)

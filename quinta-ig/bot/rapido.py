"""Respondedor rápido de mensajes directos de Quinta El Florido (Instagram).
Corre en GitHub Actions cada ~1 minuto (workflow ig-rapido.yml).
- Lee las charlas, busca las que tienen un mensaje del cliente sin responder.
- Le pide la respuesta a Claude Haiku con las mismas reglas del bot (INSTRUCCIONES.md + quinta.json + precios).
- La manda por la API de Instagram.
El repo y los logs de Actions son públicos: acá nunca se imprimen mensajes, nombres ni precios.
Los comentarios de publicaciones los sigue contestando el bot de cada 3 horas."""
import re, os, json, base64, datetime, hashlib, urllib.request, urllib.parse, urllib.error
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

AQUI = os.path.dirname(os.path.abspath(__file__))
IG = "17841454960836233"; YO = "quintaelflorido"; API = "https://graph.facebook.com/v23.0"
T = os.environ.get("IG_TOKEN", "").strip().strip('"')
KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
MODELO = "claude-haiku-5-5"
TOPE_DIA = 150          # máximo de respuestas por día (por si algo se descontrola)
ESPERA_SEG = 45         # espera a que el cliente termine de escribir
VENTANA_HS = 23         # Instagram solo deja responder dentro de las 24 h del último mensaje del cliente
AR = datetime.timezone(datetime.timedelta(hours=-3))
ahora = datetime.datetime.now(AR)
LOG = os.path.join(AQUI, "rapido.log.json")
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
# Charlas que NO son clientes (prospección de nuestro servicio a otras quintas)
NO_CLIENTE = ("Soy Juan, de Quinta El Florido", "demo-quintas", "marcas/resultados", "Instagram de otras quintas")
AUTO = ("¡Hola! 👋 Gracias por escribir", "¡Hola! 🌙", "¡Hola! 🎄 Gracias por escribir", "📲 Escribinos al WhatsApp",
        "¡Hola! 👋 Gracias por tu comentario", "Estamos en General Rodríguez, a solo", "☀️ Quinta de día", "☀ Quinta de día",
        "¡Pasanos la fecha", "💰 Hasta diciembre", "¡Hola! Gracias por ponerte en contacto")

# Desde 21/11 las automáticas de Meta que quedan (preguntas frecuentes y respuesta a comentarios) contestan bien,
# así que cuentan como respuesta. Solo se ignoran los mensajes sin texto (fotos, vista previa de links).
def es_auto(t): return not t.strip()
def fecha(s): return datetime.datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=datetime.timezone.utc).astimezone(AR)
def leer(nombre, defecto):
    f = os.path.join(AQUI, nombre)
    return json.load(open(f)) if os.path.exists(f) else defecto
def get(path, **p):
    p["access_token"] = T
    return json.load(urllib.request.urlopen(f"{API}/{path}?{urllib.parse.urlencode(p)}", timeout=30))
def post(path, **p):
    p["access_token"] = T
    r = urllib.request.Request(f"{API}/{path}", data=urllib.parse.urlencode(p).encode(), method="POST")
    return json.load(urllib.request.urlopen(r, timeout=30))

def precios():
    k = os.environ.get("PRECIOS_KEY", "").strip()
    f = os.path.join(AQUI, "precios.rapido.enc.json")
    if not k or not os.path.exists(f): return None
    e = json.load(open(f)); u = base64.b64decode
    return json.loads(AESGCM(u(k)).decrypt(u(e["iv"]), u(e["data"]), None))

def instrucciones():
    q = leer("quinta.json", {})
    hoy = ahora.date()
    cal = [c for c in q.get("calendario", []) if hoy.isoformat() <= c["fecha"] <= (hoy + datetime.timedelta(days=120)).isoformat()]
    datos = {k: q[k] for k in ("quintas", "comodidades", "reglas", "ubicacion", "feriados", "links_fotos") if k in q}
    pr = precios()
    if pr:  # solo lo que el bot puede decir
        pr = {"precio_por_dia": pr.get("precio_por_dia"),
              "lista": [x for x in pr.get("lista", []) if x.get("bot_lo_dice") is not False]}
    reglas = open(os.path.join(AQUI, "INSTRUCCIONES.md"), encoding="utf-8").read()
    reglas = reglas.split("## Reglas de respuesta", 1)[-1].split("## Aviso a Juan", 1)[0]
    return f"""Sos quien atiende los mensajes directos de Instagram de Quinta El Florido (@quintaelflorido), dos quintas de alquiler en General Rodríguez, Buenos Aires.
Hoy es {DIAS[hoy.weekday()]} {hoy.strftime('%d/%m/%Y')}, hora {ahora.strftime('%H:%M')} (Argentina).

REGLAS (las mismas que usa el equipo):
{reglas}
Además:
- Respondé SOLO el último mensaje del cliente, teniendo en cuenta toda la charla (no repitas preguntas que ya contestó).
- Si alguien quiere reservar: pedile fecha, cuántas personas y un teléfono, y derivalo al WhatsApp con el link wa.me/5491138777015. Nunca confirmes la reserva ni pases datos de pago.
- Si un dato dice [COMPLETAR] o no está acá: "eso te lo pasamos por WhatsApp". No inventes nada.
- La quinta de día NO es para dormir. Para quedarse, ofrecé la casa.
- Si no corresponde responder (charla cerrada con "gracias"/"ok", spam, insultos, otra quinta ofreciendo servicios, publicidad), respondé exactamente: NADA
- Escribí solo el texto del mensaje, sin comillas ni explicaciones.

FOTOS: si piden fotos (o preguntan "cómo es", "qué tiene", "tenés fotos"), además de tu texto agregá al final, en una línea sola, una de estas marcas: FOTOS:dia (pasar el día), FOTOS:casa (casa / dormir) o FOTOS:ambas (si no queda claro). El sistema manda 4 fotos reales de esa quinta. En el texto decí algo como "te paso unas fotos" y sumá el link de las destacadas para ver más. No uses la marca si no piden o no sirve.

TONO (que se sienta una charla con una persona, pero profesional):
- Mensajes cortos: 2 a 4 líneas. Voseo rioplatense, natural, cálido. Nada de "estimado cliente" ni frases de folleto.
- Si en la charla ya saludamos, no vuelvas a saludar. Si el cliente dijo su nombre, usalo una vez.
- Contestá primero exactamente lo que preguntó; después agregá un solo dato que ayude (ej: la pileta, la parrilla, que la fecha en principio está libre).
- Como mucho 1 emoji, y solo si el cliente usa emojis.
- Cerrá con UNA pregunta que acerque a reservar (qué fecha, cuántos son), no con varias.
- No repitas información que ya le pasamos en la charla.
- Si preguntan si sos un bot o una persona, no mientas: decí que respondemos rápido por acá y que Juan lo sigue personalmente por WhatsApp.
- Si el cliente está molesto o hay un problema, disculpate corto y derivá a WhatsApp con Juan.

DATOS DE LAS QUINTAS:
{json.dumps(datos, ensure_ascii=False)}

FECHAS YA ALQUILADAS (próximos 4 meses; si una fecha no figura, "en principio está libre", nunca "confirmado"):
{json.dumps(cal, ensure_ascii=False)}

PRECIOS (privados, decirlos solo si preguntan o si suma para cerrar):
{json.dumps(pr, ensure_ascii=False) if pr else "No disponibles: decir que el precio se lo pasamos por WhatsApp."}
"""

DIAG = {}
BASE_FOTOS = "https://macproia88.github.io/marcas/quinta-ig/destacadas/"
FOTOS = {"dia": ["portada-dia.jpg", "dia-1.jpg", "dia-4.jpg", "dia-8.jpg"],
         "casa": ["portada-casa.jpg", "casa-1.jpg", "casa-3.jpg", "casa-6.jpg"]}
def claude(sistema, charla):
    texto = "Charla con el cliente (de más vieja a más nueva):\n" + "\n".join(
        f"[{m['hora']}] {'NOSOTROS' if m['de'] == 'nosotros' else 'CLIENTE'}: {m['texto']}" for m in charla)
    body = json.dumps({"model": MODELO, "max_tokens": 3000, "system": sistema,
                       "messages": [{"role": "user", "content": texto}]}).encode()
    r = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, method="POST", headers={
        "x-api-key": KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    d = json.load(urllib.request.urlopen(r, timeout=60))
    global DIAG
    DIAG = {"stop": d.get("stop_reason"), "tipos": [b.get("type") for b in d.get("content", [])],
            "largo": sum(len(b.get("text", "")) for b in d.get("content", []))}
    return "".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text").strip()

def main():
    if not T or not KEY:
        print("falta IG_TOKEN o ANTHROPIC_API_KEY"); return
    log = leer("rapido.log.json", {"dias": {}, "ultimo": {}})
    hoy = ahora.strftime("%Y-%m-%d")
    log["dias"] = {k: v for k, v in log.get("dias", {}).items() if k >= (ahora - datetime.timedelta(days=30)).strftime("%Y-%m-%d")}
    usados = log["dias"].get(hoy, {}).get("enviados", 0)
    if usados >= TOPE_DIA:
        print("tope diario alcanzado"); return
    pendientes_bot = {x.get("para_id") for x in leer("responder.json", []) if x.get("estado") == "pendiente"}
    convs = get(f"{IG}/conversations", platform="instagram", limit=25,
                fields="id,updated_time,participants,messages.limit(12){id,from,message,created_time}").get("data", [])
    sistema = None; enviados = nadas = errores = 0; motivos = {}
    def salto(m): motivos[m] = motivos.get(m, 0) + 1
    for c in convs:
        if (ahora - fecha(c["updated_time"])).total_seconds() > VENTANA_HS * 3600: salto("vieja"); continue
        msgs = (c.get("messages") or {}).get("data", [])   # el primero es el más nuevo
        if not msgs: continue
        ult = next((m for m in msgs if not ((m.get("from") or {}).get("username") == YO and es_auto(m.get("message") or ""))), None)
        if not ult or (ult.get("from") or {}).get("username") == YO: salto("ya_respondida"); continue        # ya respondimos
        edad = (ahora - fecha(ult["created_time"])).total_seconds()
        if edad < ESPERA_SEG or edad > VENTANA_HS * 3600: salto("espera"); continue
        if any(t in (m.get("message") or "") for m in msgs for t in NO_CLIENTE): salto("prospeccion"); continue   # prospección, no cliente
        cliente = next((p for p in (c.get("participants") or {}).get("data", []) if p.get("username") != YO), {})
        pid = cliente.get("id")
        if not pid or pid in pendientes_bot: salto("bot3h"); continue                                   # el bot de 3 h ya tiene algo preparado
        h = hashlib.sha256(f"{pid}|{ult['id']}".encode()).hexdigest()[:16]
        if h in log["ultimo"].values(): salto("ya_procesada"); continue                                        # ese mensaje ya lo procesamos
        charla = [{"de": "nosotros" if (m.get("from") or {}).get("username") == YO else "cliente",
                   "texto": m.get("message") or "[adjunto/audio/foto]",
                   "hora": fecha(m["created_time"]).strftime("%d/%m %H:%M")} for m in reversed(msgs)]
        try:
            sistema = sistema or instrucciones()
            resp = claude(sistema, charla)
        except urllib.error.HTTPError as e:
            try: det = json.loads(e.read().decode()).get("error", {}); det = f"{det.get('type')} {det.get('message','')[:120]}"
            except Exception: det = ""
            errores += 1; print("error claude:", e.code, det); log["ultimo_error"] = f"claude {e.code} {det}"[:200]; break
        except Exception as e:
            errores += 1; print("error claude:", type(e).__name__); break
        clave = hashlib.sha256(pid.encode()).hexdigest()[:12]
        log["ultimo"][clave] = h
        if not resp or resp.strip().upper().startswith("NADA"):
            nadas += 1; log["diag_nada"] = DIAG; continue
        try:
            m = re.search(r"\n?\s*FOTOS:\s*(dia|casa|ambas)\s*$", resp, re.I)
            cuales = []
            if m:
                k = m.group(1).lower(); resp = resp[:m.start()].rstrip()
                cuales = FOTOS["dia"][:3] + FOTOS["casa"][:3] if k == "ambas" else FOTOS[k]
            post(f"{IG}/messages", recipient=json.dumps({"id": pid}), message=json.dumps({"text": resp[:950]}))
            enviados += 1
            for f in cuales:
                try:
                    post(f"{IG}/messages", recipient=json.dumps({"id": pid}),
                         message=json.dumps({"attachment": {"type": "image", "payload": {"url": BASE_FOTOS + f}}}))
                    log.setdefault("fotos", {}); log["fotos"][hoy] = log["fotos"].get(hoy, 0) + 1
                except urllib.error.HTTPError as e:
                    print("error foto:", e.code); log["ultimo_error"] = f"foto {e.code}"; break
        except urllib.error.HTTPError as e:
            errores += 1; print("error instagram:", e.code); log["ultimo_error"] = f"instagram {e.code}"
        if usados + enviados >= TOPE_DIA: break
    d = log["dias"].setdefault(hoy, {"enviados": 0, "nada": 0, "errores": 0})
    d["enviados"] += enviados; d["nada"] += nadas; d["errores"] += errores
    if enviados or nadas or errores:
        log["actualizado"] = ahora.strftime("%Y-%m-%d %H:%M")
        json.dump(log, open(LOG, "w"), ensure_ascii=False, indent=1)
    log["motivos"] = motivos; log["revisado"] = ahora.strftime("%Y-%m-%d %H:%M")
    json.dump(log, open(LOG, "w"), ensure_ascii=False, indent=1)
    print(f"enviados {enviados} nada {nadas} errores {errores}", motivos)

if __name__ == "__main__":
    main()

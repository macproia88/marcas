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
RECORDAR_HS = (20, 23.3) # recordatorio único a los que quedaron cerca de reservar (dentro de la ventana de 24 h)
RECORDAR_POR_VUELTA = 3
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
AUTO_META = ("te respondemos enseguida", "Gracias por comentar", "Gracias por escribirnos")
def es_auto(t):
    """Mensajes vacíos o respuestas automáticas de Meta: no cuentan como respuesta nuestra."""
    return not t.strip() or any(a.lower() in t.lower() for a in AUTO_META)
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
              "lista": [x for x in pr.get("lista", []) if x.get("bot_lo_dice") is not False],
              "sena": pr.get("sena")}
    reglas = open(os.path.join(AQUI, "INSTRUCCIONES.md"), encoding="utf-8").read()
    reglas = reglas.split("## Reglas de respuesta", 1)[-1].split("## Aviso a Juan", 1)[0]
    return f"""Sos quien atiende los mensajes directos de Instagram de Quinta El Florido (@quintaelflorido), dos quintas de alquiler en General Rodríguez, Buenos Aires.
Hoy es {DIAS[hoy.weekday()]} {hoy.strftime('%d/%m/%Y')}, hora {ahora.strftime('%H:%M')} (Argentina).

REGLAS (las mismas que usa el equipo):
{reglas}
Además:
- Respondé SOLO el último mensaje del cliente, teniendo en cuenta toda la charla (no repitas preguntas que ya contestó).
- LLEVAR A LA RESERVA (sin presionar): cada respuesta termina con un paso siguiente natural (preguntar fecha, cuántos son, o si quiere reservar). Cuando el cliente muestra interés ("me gusta", "me encanta", "quiero", "está buenísimo", "dale", "nos sirve", pregunta detalles de una fecha concreta) y la fecha está libre, cerrá con una pregunta directa y amable: "Querés que te la reserve para el sábado 12?" o "Te la dejo apartada?". Si dice que sí (o pregunta cómo reservar, cómo se paga, si hay que señar o el alias): pasale la seña (50%; si la estadía tiene días en febrero, 60% y el 40% al ingresar; calculá el monto con el precio de esa fecha y las personas) por transferencia al alias que figura en PRECIOS > sena (a nombre del titular), aclarale que el resto se paga al ingresar y que cuando transfiera mande el comprobante al WhatsApp wa.me/5491138777015 para que Juan le confirme. Si todavía no dijo fecha o cuántos son, preguntalo antes de pasar el monto.
- CIERRE DEL CLIENTE: si el último mensaje del cliente cierra la charla sin preguntar nada ("lo analizo y te aviso", "lo hablo con la gente", "te aviso", "gracias", "dale", "ok", "me imagino que sí", un emoji o un like), NO respondas: devolvé solo NADA. No mandes despedidas ni "quedo atento". Si además pregunta algo, respondé solo la pregunta, corto.
- ESTADÍAS DE VARIOS DÍAS O CONSULTAS COMBINADAS: calculá vos el total y dalo en el mismo mensaje. Sumá el precio de cada día según el día de la semana y la tabla de precios de esa fecha (casa: se cobra cada día; si incluye sábado y domingo juntos, usá el precio de finde completo si existe) + adicional por persona si de día son más de 15. Mostrá el total y, si son varios días, el detalle en una línea corta ("lun a jue 4 x 180 mil + vie 200 mil + sáb y dom 450 mil = 1.370.000"). NUNCA digas "lo consulto con Juan" para un precio que se puede calcular con la tabla. "Lo consulto" solo si el dato de verdad no está.
- FINDE LARGO: si piden "el finde del X" o "finde largo", ofrecé TODOS los días de ese finde (los que te paso en FECHAS) que estén libres, nunca uno solo. Para la casa con noches: el total es la suma de cada día. Dales opciones claras (ej: "sáb 5 a lun 7: 3 días X; sáb 5 a mar 8: 4 días Y").
- Capacidad casa: duermen cómodas 5 (si son 5 o menos para dormir, decilo como algo bueno y seguí). Después del precio, cerrá: "Querés que te aparte esas fechas?".
- PRECIO FIJO: el precio es por el día completo (incluye hasta 15 personas) y no cambia por ser pocos. NUNCA bajes el precio ni digas "te la dejo en" ni inventes descuentos; si son pocos, decilo como algo bueno ("van re cómodos"). Si son más de 15, sumá el adicional por persona.
- MENSAJES CORTOS: máximo 3 líneas. No repitas lo que dijo el cliente ni expliques de más.
- La pregunta de cierre es sutil: "Querés que te aparte la fecha?" o "Querés reservarla?". Nunca uses frases que enfríen ("tomátelo con calma", "sin apuro") ni que apuren ("se llenan rápido", "quedan pocas fechas").
- No ofrezcas el alias en frío (si no mostró interés ni preguntó). Una sola pregunta de cierre por mensaje; si dice que lo piensa o que no, respetalo y dejá la puerta abierta ("Dale, cualquier cosa me escribís").
- Nunca digas que la reserva está confirmada: la confirma Juan por WhatsApp cuando ve la transferencia.
- Si igual manda el comprobante por acá ([adjunto/audio/foto] después de pasarle el alias) o dice que ya transfirió: "Gracias! Mandalo también al WhatsApp wa.me/5491138777015 así Juan lo ve y te confirma 🙌"
- Si un dato dice [COMPLETAR] o no está acá: "Lo consulto y te respondo por acá". No inventes nada y no mandes al WhatsApp por eso.
- WhatsApp (wa.me/5491138777015) SOLO en estos casos: (1) el cliente ya transfirió o manda el comprobante, (2) el cliente pide explícitamente hablar por WhatsApp o por teléfono, (3) ya señó y pide la dirección exacta. Todo lo demás (precios, fechas, fotos, ubicación aproximada, capacidad, visitas, dudas) se resuelve por acá, en Instagram.
- Visitas para conocer la quinta: "Sí! Decime qué día y horario te queda bien y te confirmamos por acá".
- Dirección exacta: dar la zona (General Rodríguez, a 600 m de la autopista del Oeste) y ofrecer venir a conocerla antes de señar. Si igual quiere la dirección exacta, pasale el WhatsApp para que Juan se la mande.
- CONFIANZA: que nunca parezca una estafa. Si el cliente quiere hablar por WhatsApp o llamar, pasale el número enseguida y con buena onda (wa.me/5491138777015), sin vueltas. Si duda de pagar, decile que puede venir a conocer la quinta antes de señar. Nunca presiones ni apures.
- FOTOS: si pide fotos, mandá las mejores de la quinta que pregunta (marca FOTOS:dia o FOTOS:casa); si no dice cuál o pregunta por las dos, FOTOS:ambas. Solo existen estas 2 quintas: no menciones ni ofrezcas ninguna otra.
- La quinta de día NO es para dormir. Para quedarse, ofrecé la casa.
- Si no corresponde responder (charla cerrada con "gracias"/"ok", spam, insultos, otra quinta ofreciendo servicios, publicidad), respondé exactamente: NADA
- Escribí solo el texto del mensaje, sin comillas ni explicaciones.

FOTOS: si piden fotos (o preguntan "cómo es", "qué tiene", "tenés fotos"), además de tu texto agregá al final, en una línea sola, una de estas marcas: FOTOS:dia (pasar el día), FOTOS:casa (casa / dormir) o FOTOS:ambas (si no queda claro). El sistema manda 4 fotos reales de esa quinta. En el texto decí algo como "te paso unas fotos" y NO pongas el link de las destacadas (su vista previa muestra una tapa verde que no queremos); las fotos alcanzan. No uses la marca si no piden o no sirve.

TONO (que se sienta una charla con una persona, pero profesional):
- Mensajes cortos: 2 a 4 líneas. Voseo rioplatense, natural, cálido. Nada de "estimado cliente" ni frases de folleto.
- Escribí como escribe una persona por chat en Argentina, como Juan: SIN los signos que abren (nunca "¡" ni "¿"), solo los que cierran ("Hola! como andas?", "Dale, te paso fotos"). Frases simples, palabras de todos los días: "dale", "genial", "buenísimo", "te cuento", "cualquier cosa avisame". Nada de listas, viñetas ni negritas. Sin muletillas de bot ("con gusto", "estaré encantado", "no dudes en"). Ortografía correcta, pero relajada.
- Ejemplos de cómo sí: "Hola! Para el sábado 12 la de pasar el día está libre, sale 170 mil de 10 a 19. Cuántos serían?" / "Dale, te paso unas fotos de la casa" / "Buenísimo, cualquier cosa me escribís por acá"
- Si en la charla ya saludamos, no vuelvas a saludar. Si el cliente dijo su nombre, usalo una vez.
- Contestá primero exactamente lo que preguntó; después agregá un solo dato que ayude (ej: la pileta, la parrilla, que la fecha en principio está libre).
- Como mucho 1 emoji, y solo si el cliente usa emojis.
- Cerrá con UNA pregunta que acerque a reservar (qué fecha, cuántos son), no con varias.
- No repitas información que ya le pasamos en la charla.
- Si el mensaje es [NOS MENCIONÓ EN SU HISTORIA]: es alguien que está o estuvo en la quinta y nos etiquetó. Agradecé con calidez y corto (ej: "Gracias por la mención! Qué lindo día, que lo disfruten mucho 💚"). No hables de WhatsApp, precios ni reservas.
- Si el único mensaje del cliente es [adjunto/audio/foto] y antes no preguntó nada: casi siempre es una mención en su historia o un post compartido. Respondé igual que con una mención (agradecer corto y cálido), sin WhatsApp ni precios. Si ya le agradecimos antes en la charla, respondé NADA.
- Si preguntan algo que NO está en los datos (ej: qué negocios hay cerca, el barrio, la ruta exacta): no lo rellenes con la lista de comodidades ni con otra cosa. Contestá corto y directo a ESA pregunta: "Eso te lo paso bien por WhatsApp" + el link, y nada más. Nunca contestes una pregunta distinta a la que hicieron.
- Si preguntan si sos un bot o una persona, no mientas: decí que respondemos rápido por acá y que Juan sigue cada consulta personalmente.
- Si el cliente está molesto o hay un problema, disculpate corto y decile que Juan le escribe por acá a la brevedad.

DATOS DE LAS QUINTAS:
{json.dumps(datos, ensure_ascii=False)}

FECHAS YA ALQUILADAS (próximos 4 meses; si una fecha no figura, "en principio está libre", nunca "confirmado"):
{json.dumps(cal, ensure_ascii=False)}

PRECIOS (privados, decirlos solo si preguntan o si suma para cerrar):
{json.dumps(pr, ensure_ascii=False) if pr else 'No disponibles: decir "lo consulto y te respondo por acá".'}
"""

DIAG = {}
BASE_FOTOS = "https://macproia88.github.io/marcas/quinta-ig/destacadas/"
FOTOS = {"dia": ["dia-11.jpg", "dia-12.jpg", "dia-8.jpg", "dia-6.jpg"],     # quincho+pileta, parque, juegos, pileta cerca
         "casa": ["casa-1.jpg", "casa-4.jpg", "casa-3.jpg", "casa-7.jpg"]}
def clave_de(nombre):
    """La lista de tibios usa una clave derivada: el link para verla no revela la clave de precios."""
    k = os.environ.get("PRECIOS_KEY", "").strip()
    if not k: return None
    k = base64.b64decode(k)
    return hashlib.sha256(k + b"tibios").digest() if nombre.startswith("tibios") else k
def cifrar_guardar(nombre, datos):
    kk = clave_de(nombre)
    if not kk: return
    iv = os.urandom(12)
    ct = AESGCM(kk).encrypt(iv, json.dumps(datos, ensure_ascii=False).encode(), None)
    json.dump({"iv": base64.b64encode(iv).decode(), "data": base64.b64encode(ct).decode()}, open(os.path.join(AQUI, nombre), "w"))
def leer_cifrado(nombre):
    kk = clave_de(nombre); f = os.path.join(AQUI, nombre)
    if not kk or not os.path.exists(f): return []
    e = json.load(open(f)); u = base64.b64decode
    return json.loads(AESGCM(kk).decrypt(u(e["iv"]), u(e["data"]), None))
def aviso_whatsapp(texto):
    """Aviso a Juan por WhatsApp con CallMeBot (secreto CALLMEBOT_KEY). Si no está, no hace nada."""
    k = os.environ.get("CALLMEBOT_KEY", "").strip()
    if not k: return False
    try:
        urllib.request.urlopen("https://api.callmebot.com/whatsapp.php?" + urllib.parse.urlencode(
            {"phone": "+5491138777015", "text": texto, "apikey": k}), timeout=30); return True
    except Exception as e:
        print("aviso whatsapp falló:", type(e).__name__); return False
def registrar_sena(marca, usuario, pid, msgs):
    p = [x.strip() for x in marca.split("|")]
    quinta = p[0].lower() if p else "?"; fechas = [f.strip() for f in (p[1] if len(p) > 1 else "").split(",") if re.match(r"\d{4}-\d{2}-\d{2}$", f.strip())]
    monto = p[2] if len(p) > 2 else "?"; nombre = p[3] if len(p) > 3 else "-"
    adj = []
    for m in msgs[:3]:
        try: atts = (get(m["id"], fields="attachments").get("attachments") or {}).get("data") or []
        except Exception: atts = []
        for a in atts:
            u = (a.get("image_data") or {}).get("url") or (a.get("file_url")) or ""
            if u: adj.append(u)
    senas = leer_cifrado("senas.enc.json")
    senas.append({"cuando": ahora.strftime("%Y-%m-%d %H:%M"), "usuario": usuario, "pid": pid, "quinta": quinta,
                  "fechas": fechas, "monto": monto, "nombre": nombre, "comprobante": adj, "estado": "a confirmar"})
    cifrar_guardar("senas.enc.json", senas)
    q = leer("quinta.json", {}); cal = q.setdefault("calendario", [])
    for f in fechas:
        if not any(c["fecha"] == f and c["quinta"] == quinta for c in cal):
            cal.append({"fecha": f, "quinta": quinta, "estado": "señado"})
    cal.sort(key=lambda c: (c["fecha"], c["quinta"]))
    json.dump(q, open(os.path.join(AQUI, "quinta.json"), "w"), ensure_ascii=False, indent=1)
    aviso_whatsapp(f"💰 Seña recibida en Instagram\n@{usuario} ({nombre})\n{'Casa' if quinta == 'casa' else 'Quinta de día'}: {', '.join(fechas)}\nSeña: ${monto}\nRevisá la cuenta y avisale a Claude si llegó. El día quedó bloqueado como señado.")

RECORDATORIO = """
TAREA ESPECIAL: esta charla quedó sin respuesta del cliente hace casi un día. Decidí si es un cliente TIBIO: alguien que mostró interés real
(preguntó precio para una fecha, dijo cuántos son, pidió fotos o disponibilidad) pero no avanzó ni dijo que no.
NO es tibio si: ya reservó o señó, dijo que no / que lo piensa con otro lugar y cerró, solo agradeció una mención, fue un saludo suelto,
pidió algo que no tenemos (más de 20 personas, fecha ocupada sin alternativa), o ya le mandamos un recordatorio antes.
Respondé SOLO un JSON en una línea, sin nada más:
{"tibio": true/false, "quinta": "dia|casa|?", "fecha": "AAAA-MM-DD o texto corto o ?", "personas": "número o ?", "resumen": "máx 12 palabras de qué buscaba",
 "mensaje": "recordatorio o null"}
El "mensaje" (solo si es tibio Y la fecha que buscaba sigue libre según el calendario, o si no había dicho fecha): UN mensaje corto y amable,
estilo chat como escribe Juan (sin ¡ ni ¿ de apertura), que retome lo que buscaba y deje la puerta abierta, sin presionar ni apurar.
Ej: "Hola! Te quedó alguna duda con lo de la quinta? El sábado 12 sigue libre por ahora, cualquier cosa avisame". Si la fecha ya se ocupó, "mensaje": null.
"""
def json_de(texto):
    m = re.search(r"\{.*\}", texto or "", re.S)
    try: return json.loads(m.group(0)) if m else None
    except Exception: return None
_TIBIOS = None; _TIBIOS_CAMBIO = False
def tibios():
    global _TIBIOS
    if _TIBIOS is None:
        try: _TIBIOS = leer_cifrado("tibios.enc.json") or []
        except Exception: _TIBIOS = []
    return _TIBIOS
def guardar_tibios():
    if _TIBIOS is None or not _TIBIOS_CAMBIO: return
    corte = (ahora - datetime.timedelta(days=21)).strftime("%Y-%m-%d")
    cifrar_guardar("tibios.enc.json", [t for t in _TIBIOS if t.get("cuando", "") >= corte])

_PPD = None
def precio_de(f):
    """Precio de lista de ese día según la tabla cifrada (sin feriados: si es feriado, vale el de finde)."""
    global _PPD
    try:
        if _PPD is None: _PPD = (precios() or {}).get("precio_por_dia") or {}
        if not _PPD: return ""
        wd = f.weekday()
        fer = set(leer("quinta.json", {}).get("feriados", {}).get("fechas", []))
        es_fer = f.isoformat() in fer
        finde_largo = wd == 4 and ((f + datetime.timedelta(days=3)).isoformat() in fer)
        if es_fer: wd = 5  # feriado = precio de finde
        if f.year >= 2027:
            t = _PPD["desde_enero_2027"]
            dia = t["dia"]["lunes a jueves"] if wd <= 3 else t["dia"]["viernes, sábado, domingo y feriado"]
            casa = (t["casa"]["lunes a jueves"] if wd <= 3 else t["casa"]["viernes y feriados"] if wd == 4
                    else t["casa"]["sábado o domingo (un solo día)"] + " (sáb+dom juntos con noche: " + t["casa"]["sábado + domingo juntos con noche"] + ")")
        else:
            dia = _PPD["dia"]["lunes a jueves"] if wd <= 3 else _PPD["dia"]["viernes, sábado, domingo y feriado"]
            casa = _PPD["casa"]["lunes a viernes"] if wd <= 4 and not finde_largo else _PPD["casa"]["sábado, domingo, feriado y viernes de finde largo"]
        return f" [{'FERIADO, ' if es_fer else ''}de día {dia} / casa {casa}]"
    except Exception:
        return ""

def fechas_mencionadas(textos):
    """Pasa a fechas con día de la semana lo que el cliente escribió (ej "1/2 al 7/2"), para que el bot calcule bien."""
    hoy = ahora.date(); out = []
    def a_fecha(d, m):
        try:
            f = datetime.date(hoy.year, m, d)
            return f if f >= hoy - datetime.timedelta(days=1) else datetime.date(hoy.year + 1, m, d)
        except ValueError: return None
    MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    def palabras(t):
        # "15 de enero" / "del 10 al 12 de febrero" -> formato 15/1, 10/2 al 12/2
        t = re.sub(r"(\d{1,2})\s*(al|a|-)\s*(\d{1,2})\s+de\s+(" + "|".join(MESES) + r")",
                   lambda m: f"{m[1]}/{MESES.index(m[4]) + 1} al {m[3]}/{MESES.index(m[4]) + 1}", t, flags=re.I)
        return re.sub(r"(\d{1,2})\s+de\s+(" + "|".join(MESES) + r")", lambda m: f"{m[1]}/{MESES.index(m[2].lower()) + 1}", t, flags=re.I)
    for t in textos:
        t = palabras((t or "").lower())
        for a, b in re.findall(r"(\d{1,2}\s*/\s*\d{1,2})(?:\s*(?:al|a|hasta el|-)\s*(\d{1,2}\s*/\s*\d{1,2}))?", t or ""):
            d1, m1 = [int(x) for x in a.replace(" ", "").split("/")]
            f1 = a_fecha(d1, m1)
            if not f1: continue
            f2 = None
            if b:
                d2, m2 = [int(x) for x in b.replace(" ", "").split("/")]; f2 = a_fecha(d2, m2)
            dias = [f1] if not f2 or not (0 <= (f2 - f1).days <= 31) else [f1 + datetime.timedelta(days=i) for i in range((f2 - f1).days + 1)]
            if not f2 and re.search(r"\bfinde|fin de semana|feriado", t):
                # "el finde del 8": todo el finde largo (sábado, domingo y feriados pegados)
                fer = set(leer("quinta.json", {}).get("feriados", {}).get("fechas", []))
                libre = lambda x: x.weekday() >= 5 or x.isoformat() in fer
                if libre(f1) or f1.weekday() == 4:
                    a = b2 = f1
                    while libre(a - datetime.timedelta(days=1)) or (a - datetime.timedelta(days=1)).weekday() == 4 and libre(a): a -= datetime.timedelta(days=1)
                    while libre(b2 + datetime.timedelta(days=1)): b2 += datetime.timedelta(days=1)
                    if (b2 - a).days <= 6: dias = [a + datetime.timedelta(days=i) for i in range((b2 - a).days + 1)]
            for f in dias:
                txt = f"{f.strftime('%d/%m/%Y')} {DIAS[f.weekday()]}" + precio_de(f)
                if txt not in out: out.append(txt)
    return out[:40]

COMENTARIO = """

AHORA NO ES UN DM: es un COMENTARIO público en una publicación nuestra. Respondé UNA línea corta (máximo 15 palabras), con humor y buena onda, en rioplatense, sin signos de apertura. Si el comentario es un chiste o etiqueta a alguien, seguile el juego. Si pregunta precio, fecha, info o promo: respondé algo atractivo que lo lleve a leer el privado, variando la frase, ej: "Te mandamos por privado precios y fechas libres 👀 fijate en tus mensajes 📩", "Te escribimos al privado con las promos de esta semana 🔥", "Ya te llega por privado, mirá que hay fechas lindas libres 😉". Nunca nombres el WhatsApp en público. Nunca precios ni alias en comentarios. Si es spam, ofensivo, de otra quinta o solo un emoji suelto que no amerita, respondé NADA."""

def claude(sistema, charla):
    texto = "Charla con el cliente (de más vieja a más nueva):\n" + "\n".join(
        f"[{m['hora']}] {'NOSOTROS' if m['de'] == 'nosotros' else ('DATO DEL SISTEMA' if m['de'] == 'sistema' else 'CLIENTE')}: {m['texto']}" for m in charla)
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
    convs = get(f"{IG}/conversations", platform="instagram", limit=50,
                fields="id,updated_time,participants,messages.limit(12){id,from,message,created_time,story}").get("data", [])
    if os.path.exists(os.path.join(AQUI, "diag.trigger")):
        # Foto cifrada de las últimas charlas para revisar a mano (repo público: va cifrado con la clave de precios).
        foto = []
        for c in convs[:12]:
            cl = next((p for p in (c.get("participants") or {}).get("data", []) if p.get("username") != YO), {})
            foto.append({"usuario": cl.get("username"), "id": cl.get("id"), "charla": [
                {"de": "nos" if (m.get("from") or {}).get("username") == YO else "cli", "t": m.get("message") or "[adj]",
                 "h": fecha(m["created_time"]).strftime("%d/%m %H:%M")} for m in reversed((c.get("messages") or {}).get("data", [])[:8])]})
        kk = clave_de("diag"); iv = os.urandom(12)
        log["diag_cifrado"] = {"iv": base64.b64encode(iv).decode(), "data": base64.b64encode(
            AESGCM(kk).encrypt(iv, json.dumps(foto, ensure_ascii=False).encode(), None)).decode(), "hora": ahora.strftime("%H:%M")}
    sistema = None; enviados = nadas = errores = recordados = retomadas = 0; motivos = {}
    def salto(m): motivos[m] = motivos.get(m, 0) + 1
    for c in convs:
        if (ahora - fecha(c["updated_time"])).total_seconds() > VENTANA_HS * 3600: salto("vieja"); continue
        msgs = (c.get("messages") or {}).get("data", [])   # el primero es el más nuevo
        if not msgs: continue
        ult = next((m for m in msgs if not ((m.get("from") or {}).get("username") == YO and es_auto(m.get("message") or ""))), None)
        if ult and (ult.get("from") or {}).get("username") == YO:
            # ya respondimos: ¿toca recordatorio a un cliente tibio?
            cli_msg = next((m for m in msgs if (m.get("from") or {}).get("username") != YO), None)
            cliente = next((p for p in (c.get("participants") or {}).get("data", []) if p.get("username") != YO), {})
            pid = cliente.get("id")
            # Si le dijimos "lo consulto" y el precio se podía calcular, retomamos una sola vez con la respuesta.
            nuestro = (ult.get("message") or "").lower()
            clave_x = hashlib.sha256(f"{pid}|{ult.get('id')}".encode()).hexdigest()[:12] if pid else ""
            if (pid and cli_msg and retomadas < 2 and any(f in nuestro for f in ("lo consulto", "lo consultamos", "consultarlo", "lo veo con juan", "lo chequeo con juan"))
                    and clave_x not in log.setdefault("rehechos", {})
                    and (ahora - fecha(ult["created_time"])).total_seconds() < 6 * 3600
                    and (ahora - fecha(cli_msg["created_time"])).total_seconds() < 23 * 3600
                    and not any(t in (m.get("message") or "") for m in msgs for t in NO_CLIENTE)):
                log["rehechos"][clave_x] = hoy; retomadas += 1
                charla = [{"de": "nosotros" if (m.get("from") or {}).get("username") == YO else "cliente",
                           "texto": m.get("message") or "[adjunto/audio/foto]",
                           "hora": fecha(m["created_time"]).strftime("%d/%m %H:%M")} for m in reversed(msgs)]
                fm = fechas_mencionadas([x["texto"] for x in charla if x["de"] == "cliente"][-4:])
                nota = ("Nuestro último mensaje dijo que lo consultábamos. Si el precio o el dato se puede sacar de la tabla y el calendario, "
                        "escribí ahora el mensaje de seguimiento: arrancá natural (ej: 'Ya lo tengo:'), dá el total con el detalle en una línea, "
                        "la capacidad si aplica y cerrá con 'Querés que te aparte esas fechas?'. Máximo 3 líneas, sin disculpas ni presión. "
                        "Si de verdad falta un dato que no está, respondé NADA.")
                if fm: nota += " FECHAS QUE MENCIONÓ EL CLIENTE (con día de la semana): " + ", ".join(fm)
                charla.append({"de": "sistema", "texto": nota, "hora": ""})
                try:
                    sistema = sistema or instrucciones()
                    resp = claude(sistema, charla)
                    if resp and not resp.strip().upper().startswith("NADA"):
                        post(f"{IG}/messages", recipient=json.dumps({"id": pid}), message=json.dumps({"text": resp[:950]}))
                        enviados += 1; salto("retomada")
                    else: salto("retomada_nada")
                except Exception as e:
                    print("error retomar:", type(e).__name__); salto("retomada_error")
                continue
            if (cli_msg and pid and recordados < RECORDAR_POR_VUELTA
                    and RECORDAR_HS[0] * 3600 <= (ahora - fecha(cli_msg["created_time"])).total_seconds() <= RECORDAR_HS[1] * 3600
                    and hashlib.sha256(pid.encode()).hexdigest()[:12] not in log.setdefault("recordados", {})
                    and not any(t in (m.get("message") or "") for m in msgs for t in NO_CLIENTE)):
                clave_r = hashlib.sha256(pid.encode()).hexdigest()[:12]
                log["recordados"][clave_r] = hoy; recordados += 1
                charla = [{"de": "nosotros" if (m.get("from") or {}).get("username") == YO else "cliente",
                           "texto": m.get("message") or "[adjunto/audio/foto]",
                           "hora": fecha(m["created_time"]).strftime("%d/%m %H:%M")} for m in reversed(msgs)]
                try:
                    sistema = sistema or instrucciones()
                    j = json_de(claude(sistema + RECORDATORIO, charla)) or {}
                except Exception as e:
                    print("error recordatorio:", type(e).__name__); j = {}
                if j.get("tibio"):
                    global _TIBIOS_CAMBIO; _TIBIOS_CAMBIO = True
                    usuario = cliente.get("username", "?")
                    t = next((x for x in tibios() if x.get("usuario") == usuario), None)
                    if not t:
                        t = {"usuario": usuario}; tibios().append(t)
                    t.update({"cuando": hoy, "quinta": j.get("quinta", "?"), "fecha": j.get("fecha", "?"), "personas": j.get("personas", "?"),
                              "resumen": j.get("resumen", ""), "estado": "sin respuesta", "recordatorio": bool(j.get("mensaje"))})
                    if j.get("mensaje"):
                        try:
                            post(f"{IG}/messages", recipient=json.dumps({"id": pid}), message=json.dumps({"text": str(j["mensaje"])[:600]}))
                            log.setdefault("recordatorios", {}); log["recordatorios"][hoy] = log["recordatorios"].get(hoy, 0) + 1
                        except urllib.error.HTTPError as e:
                            print("error recordatorio ig:", e.code); t["recordatorio"] = False
                    salto("tibio")
                else:
                    salto("no_tibio")
            else:
                salto("ya_respondida")
            continue
        if not ult: salto("ya_respondida"); continue
        edad = (ahora - fecha(ult["created_time"])).total_seconds()
        if edad < ESPERA_SEG or edad > VENTANA_HS * 3600: salto("espera"); continue
        if any(t in (m.get("message") or "") for m in msgs for t in NO_CLIENTE): salto("prospeccion"); continue   # prospección, no cliente
        cliente = next((p for p in (c.get("participants") or {}).get("data", []) if p.get("username") != YO), {})
        pid = cliente.get("id")
        if not pid or pid in pendientes_bot: salto("bot3h"); continue                                   # el bot de 3 h ya tiene algo preparado
        h = hashlib.sha256(f"{pid}|{ult['id']}".encode()).hexdigest()[:16]
        if h in log["ultimo"].values(): salto("ya_procesada"); continue                                        # ese mensaje ya lo procesamos
        charla = [{"de": "nosotros" if (m.get("from") or {}).get("username") == YO else "cliente",
                   "texto": m.get("message") or ("[NOS MENCIONÓ EN SU HISTORIA]" if (m.get("story") or {}).get("mention") else "[adjunto/audio/foto]"),
                   "hora": fecha(m["created_time"]).strftime("%d/%m %H:%M")} for m in reversed(msgs)]
        fm = fechas_mencionadas([c["texto"] for c in charla if c["de"] == "cliente"][-4:])
        if fm:
            charla = charla + [{"de": "sistema", "texto": "FECHAS QUE MENCIONÓ EL CLIENTE con día de la semana y PRECIO DE LISTA de cada una (usá ESTOS precios, no otros, salvo que en esta charla ya le hayamos pasado otro precio para esa misma fecha): " + ", ".join(fm), "hora": ""}]
        t_v = next((x for x in tibios() if x.get("usuario") == cliente.get("username")), None)
        if t_v and t_v.get("estado") != "volvió":
            t_v["estado"] = "volvió"; globals()["_TIBIOS_CAMBIO"] = True
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
            ms = re.search(r"\n?\s*SENA:\s*(.+?)\s*$", resp)
            if ms:
                resp = resp[:ms.start()].rstrip()
                try: registrar_sena(ms.group(1), cliente.get("username", "?"), pid, msgs); log.setdefault("senas", 0); log["senas"] += 1
                except Exception as e: print("error seña:", type(e).__name__); log["ultimo_error"] = "seña " + type(e).__name__
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
                         message=json.dumps({"attachment": {"type": "image", "payload": {"url": f if f.startswith("http") else BASE_FOTOS + f}}}))
                    log.setdefault("fotos", {}); log["fotos"][hoy] = log["fotos"].get(hoy, 0) + 1
                except urllib.error.HTTPError as e:
                    print("error foto:", e.code); log["ultimo_error"] = f"foto {e.code}"; break
        except urllib.error.HTTPError as e:
            errores += 1; print("error instagram:", e.code); log["ultimo_error"] = f"instagram {e.code}"
        if usados + enviados >= TOPE_DIA: break
    # Comentarios en publicaciones de las últimas 48 h: respuesta corta y con onda al toque (ayuda a viralizar).
    try:
        cr = log.setdefault("comentarios_resp", {}); hechos_c = 0
        for md in get(f"{IG}/media", fields="id,timestamp,caption", limit=4).get("data", []):
            if (ahora - fecha(md["timestamp"])).total_seconds() > 48 * 3600: continue
            for cm in get(f"{md['id']}/comments", fields="id,text,username,timestamp,replies{username}", limit=50).get("data", []):
                if hechos_c >= 8: break
                if cm.get("username") == YO or cm["id"] in cr: continue
                if any(r.get("username") == YO for r in (cm.get("replies") or {}).get("data", [])): cr[cm["id"]] = hoy; continue
                if (ahora - fecha(cm["timestamp"])).total_seconds() < 60: continue
                sistema = sistema or instrucciones()
                nota = (COMENTARIO + "\nPUBLICACIÓN: " + (md.get("caption") or "")[:300])
                resp = claude(sistema + nota, [{"de": "cliente", "texto": cm.get("text") or "", "hora": ""}])
                cr[cm["id"]] = hoy
                if resp and not resp.strip().upper().startswith("NADA"):
                    post(f"{cm['id']}/replies", message=resp.strip()[:300]); hechos_c += 1; salto("comentario")
        corte_c = (ahora - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
        log["comentarios_resp"] = {k: v for k, v in cr.items() if v >= corte_c}
    except Exception as e:
        print("error comentarios:", type(e).__name__)
    d = log["dias"].setdefault(hoy, {"enviados": 0, "nada": 0, "errores": 0})
    d["enviados"] += enviados; d["nada"] += nadas; d["errores"] += errores
    if enviados or nadas or errores:
        log["actualizado"] = ahora.strftime("%Y-%m-%d %H:%M")
        json.dump(log, open(LOG, "w"), ensure_ascii=False, indent=1)
    guardar_tibios()
    corte_r = (ahora - datetime.timedelta(days=10)).strftime("%Y-%m-%d")
    log["recordados"] = {k: v for k, v in log.get("recordados", {}).items() if v >= corte_r}
    log["motivos"] = motivos; log["revisado"] = ahora.strftime("%Y-%m-%d %H:%M")
    json.dump(log, open(LOG, "w"), ensure_ascii=False, indent=1)
    print(f"enviados {enviados} nada {nadas} errores {errores}", motivos)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        tb = traceback.extract_tb(e.__traceback__)[-1]
        try:
            lg = leer("rapido.log.json", {}); lg["crash"] = f"{ahora.strftime('%d/%m %H:%M')} {type(e).__name__} línea {tb.lineno}: {tb.line}"[:300]
            json.dump(lg, open(LOG, "w"), ensure_ascii=False, indent=1)
        except Exception: pass
        raise

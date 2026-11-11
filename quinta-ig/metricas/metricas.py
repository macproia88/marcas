"""Junta las métricas de Instagram de @quintaelflorido con la API oficial y las guarda en datos.json.
Corre en GitHub Actions (secret IG_TOKEN). Nunca imprime la llave.
Guarda: cuenta, métricas por día, audiencia, horas en que los seguidores están conectados,
publicaciones (con sus métricas) e historias (se guardan antes de que desaparezcan a las 24 h).
"""
import json, os, sys, time, datetime, urllib.parse, urllib.request

IG = os.environ.get("METRICAS_IG", "17841454960836233")  # cuenta a medir (por defecto El Florido)
API = "https://graph.facebook.com/v23.0"
TOKEN = os.environ.get("IG_TOKEN", "")
AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.environ.get("METRICAS_OUT") or os.path.join(AQUI, "datos.json")
ART = datetime.timezone(datetime.timedelta(hours=-3))
avisos = []


def get(ruta, **p):
    p["access_token"] = TOKEN
    url = f"{API}/{ruta}?" + urllib.parse.urlencode(p)
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            msg = json.loads(e.read())["error"].get("message", "")
        except Exception:
            msg = str(e)
        raise RuntimeError(msg[:200])


def intentar(nombre, f, defecto=None):
    try:
        return f()
    except Exception as e:
        avisos.append(f"{nombre}: {e}")
        return defecto


def total(resp):
    out = {}
    for m in resp.get("data", []):
        tv = m.get("total_value") or {}
        if "breakdowns" in tv and tv["breakdowns"]:
            out[m["name"]] = {"total": tv.get("value"), "desglose": {
                ",".join(r.get("dimension_values", [])): r.get("value") for r in tv["breakdowns"][0].get("results", [])}}
        elif "value" in tv:
            out[m["name"]] = tv["value"]
        elif m.get("values"):
            out[m["name"]] = m["values"][-1].get("value")
    return out


def dia_cuenta(d):
    """Métricas de la cuenta para un día (hora Argentina)."""
    ini = int(datetime.datetime(d.year, d.month, d.day, tzinfo=ART).timestamp())
    fin = ini + 86400
    res = {}
    for metricas in ("reach,views,accounts_engaged,total_interactions,likes,comments,shares,saves,profile_links_taps",
                     "replies,website_clicks,profile_views"):
        r = intentar(f"cuenta {d} {metricas[:20]}", lambda: get(f"{IG}/insights", metric=metricas, period="day",
                     metric_type="total_value", since=ini, until=fin))
        if r:
            res.update(total(r))
    f = intentar(f"seguidores {d}", lambda: get(f"{IG}/insights", metric="follows_and_unfollows", period="day",
                 metric_type="total_value", breakdown="follow_type", since=ini, until=fin))
    if f:
        t = total(f).get("follows_and_unfollows")
        if isinstance(t, dict):
            des = t.get("desglose", {})
            res["seguidos_nuevos"] = des.get("FOLLOWER", 0)
            res["dejaron_de_seguir"] = des.get("NON_FOLLOWER", 0)
    return res


def insights_media(mid, tipo, producto):
    if producto == "STORY":
        juegos = ["reach,views,replies,shares,total_interactions,follows,profile_visits,navigation", "reach,views,replies,shares"]
    elif producto == "REELS":
        juegos = ["views,reach,saved,shares,total_interactions,likes,comments,ig_reels_avg_watch_time", "views,reach,saved,shares,total_interactions"]
    else:
        juegos = ["views,reach,saved,shares,total_interactions,likes,comments,follows,profile_visits", "views,reach,saved,shares,total_interactions"]
    for metricas in juegos:
        try:
            r = get(f"{mid}/insights", metric=metricas, **({"breakdown": "story_navigation_action_type"} if "navigation" in metricas else {}))
            out = {}
            for m in r.get("data", []):
                if m["name"] == "navigation":
                    tv = m.get("total_value", {})
                    out["navegacion"] = {",".join(x.get("dimension_values", [])): x.get("value") for b in tv.get("breakdowns", []) for x in b.get("results", [])}
                    out["navigation"] = tv.get("value")
                else:
                    v = (m.get("total_value") or {}).get("value")
                    if v is None and m.get("values"):
                        v = m["values"][0].get("value")
                    out[m["name"]] = v
            return out
        except Exception as e:
            ultimo = str(e)
    avisos.append(f"insights {producto} {mid}: {ultimo}")
    return {}


def main():
    if not TOKEN:
        sys.exit("Falta IG_TOKEN")
    datos = json.load(open(DATOS, encoding="utf-8")) if os.path.exists(DATOS) else {}
    ahora = datetime.datetime.now(ART)
    datos["actualizado"] = ahora.strftime("%Y-%m-%d %H:%M")

    datos["cuenta"] = intentar("cuenta", lambda: get(IG, fields="username,name,followers_count,follows_count,media_count")) or datos.get("cuenta", {})
    hoy_txt = ahora.strftime("%Y-%m-%d")
    hist = datos.setdefault("seguidores_hist", {})
    if datos["cuenta"].get("followers_count") is not None:
        hist[hoy_txt] = datos["cuenta"]["followers_count"]

    # Días: completa los que faltan de los últimos 30 y recalcula siempre los últimos 3 (Instagram los corrige)
    dias = datos.setdefault("dias", {})
    for i in range(1, 31):
        d = (ahora - datetime.timedelta(days=i)).date()
        k = d.isoformat()
        if k not in dias or i <= 3:
            v = dia_cuenta(d)
            if v:
                dias[k] = v
    datos["dias"] = dict(sorted(dias.items())[-120:])

    # Totales de la semana sin repetir personas (el alcance por día sumado cuenta varias veces a la misma persona)
    def rango(dias_atras_fin, largo=7):
        fin_d = (ahora - datetime.timedelta(days=dias_atras_fin)).date()
        ini_d = fin_d - datetime.timedelta(days=largo - 1)
        ini = int(datetime.datetime(ini_d.year, ini_d.month, ini_d.day, tzinfo=ART).timestamp())
        fin = int(datetime.datetime(fin_d.year, fin_d.month, fin_d.day, tzinfo=ART).timestamp()) + 86400
        r = intentar(f"semana {ini_d}", lambda: get(f"{IG}/insights", metric="reach,accounts_engaged,views,profile_links_taps",
                     period="day", metric_type="total_value", since=ini, until=fin))
        return {"desde": ini_d.isoformat(), "hasta": fin_d.isoformat(), **(total(r) if r else {})}
    datos["semana"] = {"actual": rango(1), "anterior": rango(8)}

    # Audiencia (una vez por día alcanza)
    if datos.get("audiencia_fecha") != hoy_txt or not any(datos.get("horas_conectados") or []):
        aud = {}
        for b in ("age", "gender", "city"):
            r = intentar(f"audiencia {b}", lambda: get(f"{IG}/insights", metric="follower_demographics", period="lifetime",
                         metric_type="total_value", breakdown=b, timeframe="this_month"))
            if r:
                t = total(r).get("follower_demographics")
                if isinstance(t, dict):
                    aud[b] = t["desglose"]
        if aud:
            datos["audiencia"] = aud
            datos["audiencia_fecha"] = hoy_txt
        # Horas en que los seguidores están conectados
        hasta_on = int((ahora - datetime.timedelta(days=1)).timestamp())
        on = intentar("online_followers", lambda: get(f"{IG}/insights", metric="online_followers", period="lifetime",
                      since=hasta_on - 29 * 86400, until=hasta_on))
        if on is not None:
            datos["online_crudo"] = json.dumps(on)[:1500]
        if on and on.get("data"):
            horas = [0] * 24
            for v in on["data"][0].get("values", []):
                for h, n in (v.get("value") or {}).items():
                    horas[int(h)] += n or 0
            # la API da las horas en hora del Pacífico (UTC-8 / UTC-7): se pasan a hora Argentina (+5 en noviembre)
            corrimiento = 5
            datos["horas_conectados"] = [horas[(h - corrimiento) % 24] for h in range(24)]

    # Publicaciones de los últimos 60 días
    media = intentar("media", lambda: get(f"{IG}/media", fields="id,caption,media_type,media_product_type,timestamp,permalink,thumbnail_url,media_url,like_count,comments_count", limit=40))
    if media:
        pubs = {p["id"]: p for p in datos.get("publicaciones", [])}
        limite = (ahora - datetime.timedelta(days=60)).isoformat()
        for m in media.get("data", []):
            if m.get("timestamp", "") < limite[:19]:
                continue
            m["metricas"] = insights_media(m["id"], m.get("media_type"), m.get("media_product_type"))
            m["caption"] = (m.get("caption") or "")[:300]
            pubs[m["id"]] = m
        datos["publicaciones"] = sorted(pubs.values(), key=lambda p: p.get("timestamp", ""), reverse=True)[:60]

    # Historias activas: se guarda la última foto de sus números
    st = intentar("stories", lambda: get(f"{IG}/stories", fields="id,media_type,media_product_type,timestamp,permalink,thumbnail_url,media_url"))
    if st:
        hs = {h["id"]: h for h in datos.get("historias", [])}
        for h in st.get("data", []):
            h["metricas"] = insights_media(h["id"], h.get("media_type"), "STORY")
            h["visto_el"] = datos["actualizado"]
            hs[h["id"]] = h
        datos["historias"] = sorted(hs.values(), key=lambda h: h.get("timestamp", ""), reverse=True)[:200]

    datos["avisos"] = avisos[-30:]
    json.dump(datos, open(DATOS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("ok", len(datos.get("dias", {})), "días,", len(datos.get("publicaciones", [])), "publicaciones,",
          len(datos.get("historias", [])), "historias,", len(avisos), "avisos")
    for a in avisos[:15]:
        print("AVISO", a)


if __name__ == "__main__":
    main()

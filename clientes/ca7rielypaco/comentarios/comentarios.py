"""Comentarios del fan club por la API de Instagram (graph.facebook.com).
- leer: guarda en datos.json los comentarios de las últimas publicaciones (con respuestas).
- responder: publica las respuestas de responder.json que estén en estado "pendiente" y las marca "respondido"/"error".
Uso (GitHub Actions): IG_TOKEN=... python3 comentarios.py leer|responder"""
import os, sys, json, datetime, urllib.request, urllib.parse
AQUI = os.path.dirname(os.path.abspath(__file__))
IG = "17841475673833807"; API = "https://graph.facebook.com/v23.0"
T = os.environ["IG_TOKEN"].strip().strip('"')
def get(path, **p):
    p["access_token"] = T
    return json.load(urllib.request.urlopen(f"{API}/{path}?{urllib.parse.urlencode(p)}", timeout=30))
def post(path, **p):
    p["access_token"] = T
    r = urllib.request.Request(f"{API}/{path}", data=urllib.parse.urlencode(p).encode(), method="POST")
    return json.load(urllib.request.urlopen(r, timeout=30))
ahora = (datetime.datetime.utcnow() - datetime.timedelta(hours=3)).strftime("%Y-%m-%d %H:%M")
modo = sys.argv[1] if len(sys.argv) > 1 else "leer"
if modo == "leer":
    media = get(f"{IG}/media", fields="id,caption,timestamp,permalink,comments_count", limit=int(os.environ.get("N_POSTS", "6")))["data"]
    out = {"actualizado": ahora, "posts": []}
    for m in media:
        cs = get(f"{m['id']}/comments", fields="id,text,username,timestamp,like_count,replies{id,text,username,timestamp}", limit=100).get("data", [])
        out["posts"].append({"id": m["id"], "fecha": m["timestamp"], "link": m.get("permalink"), "caption": (m.get("caption") or "")[:80],
                             "comentarios": [{"id": c["id"], "usuario": c.get("username"), "texto": c.get("text"), "fecha": c.get("timestamp"),
                                              "respuestas": [{"usuario": r.get("username"), "texto": r.get("text")} for r in (c.get("replies") or {}).get("data", [])]} for c in cs]})
    json.dump(out, open(os.path.join(AQUI, "datos.json"), "w"), ensure_ascii=False, indent=1)
    print(sum(len(p["comentarios"]) for p in out["posts"]), "comentarios")
else:
    f = os.path.join(AQUI, "responder.json")
    lista = json.load(open(f)) if os.path.exists(f) else []
    for x in lista:
        if x.get("estado") != "pendiente": continue
        try:
            r = post(f"{x['comment_id']}/replies", message=x["texto"]); x["estado"] = "respondido"; x["reply_id"] = r.get("id"); x["hora"] = ahora
        except urllib.error.HTTPError as e:
            x["estado"] = "error"; x["error"] = e.read().decode()[:200]
        except Exception as e:
            x["estado"] = "error"; x["error"] = str(e)[:200]
    json.dump(lista, open(f, "w"), ensure_ascii=False, indent=1)
    print([(x["comment_id"], x["estado"]) for x in lista[-20:]])

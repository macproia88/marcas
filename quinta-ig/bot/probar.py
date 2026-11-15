"""Prueba qué permite la llave de la quinta (DMs y comentarios). Nunca imprime la llave."""
import os, json, urllib.request, urllib.parse, urllib.error
T = os.environ["IG_TOKEN"].strip().strip('"'); IG = "17841454960836233"
def call(base, path, **p):
    p["access_token"] = T
    try: return json.load(urllib.request.urlopen(f"{base}/{path}?{urllib.parse.urlencode(p)}", timeout=30))
    except urllib.error.HTTPError as e:
        try: return {"error": json.loads(e.read().decode()).get("error", {}).get("message", "")[:200]}
        except Exception: return {"error": f"HTTP {e.code}"}
FB = "https://graph.facebook.com/v23.0"; IGB = "https://graph.instagram.com/v23.0"
out = {}
perm = call(FB, "me/permissions"); out["permisos"] = [p["permission"] for p in perm.get("data", []) if p.get("status") == "granted"] if "data" in perm else perm
out["me_fb"] = {k: v for k, v in call(FB, "me", fields="id,name").items() if k in ("name", "error")}
out["me_ig"] = {k: v for k, v in call(IGB, "me", fields="user_id,username").items() if k in ("username", "error")}
for base, nombre in ((IGB, "ig_api"), (FB, "fb_api")):
    c = call(base, f"{IG if base==FB else 'me'}/conversations", platform="instagram", fields="id,updated_time", limit=5)
    out["dm_" + nombre] = {"n": len(c.get("data", []))} if "data" in c else c
    if base == FB:
        pg = call(FB, "me/accounts", fields="id,name"); out["paginas"] = [p.get("name") for p in pg.get("data", [])] if "data" in pg else pg
m = call(FB, f"{IG}/media", fields="id", limit=1)
if "data" in m and m["data"]:
    c = call(FB, f"{m['data'][0]['id']}/comments", fields="id,text", limit=3); out["comentarios"] = {"n": len(c.get("data", []))} if "data" in c else c
json.dump(out, open(os.path.join(os.path.dirname(__file__), "prueba.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False))

import os,json,urllib.request,io
from PIL import Image
T=os.environ["IG_TOKEN"];IG="17841454960836233";V="https://graph.facebook.com/v23.0/"
def g(u):return json.load(urllib.request.urlopen(u))
u=f"{V}{IG}/media?fields=id,media_type,media_url,thumbnail_url,timestamp,like_count,children{{media_type,media_url,thumbnail_url}}&limit=50&access_token={T}"
out="quinta-ig/archivo-feed/";idx=[]
while u:
  d=g(u)
  for m in d["data"]:
    items=m.get("children",{}).get("data") or [m]
    for k,c in enumerate(items):
      url=c.get("thumbnail_url") if c.get("media_type")=="VIDEO" else c.get("media_url")
      if not url:continue
      n=f"{m['timestamp'][:10]}_{m['id'][-6:]}_{k}.jpg"
      try:
        im=Image.open(io.BytesIO(urllib.request.urlopen(url).read())).convert("RGB");im.thumbnail((700,700));im.save(out+n,quality=80)
        idx.append({"f":n,"likes":m.get("like_count"),"tipo":c.get("media_type")})
      except Exception as e:print(e)
  u=d.get("paging",{}).get("next")
json.dump(idx,open(out+"indice.json","w"),indent=0);print(len(idx))

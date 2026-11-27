"""Arma la biblioteca de música y efectos libres para reels (Mixkit: licencia libre para uso comercial
en redes sociales, sin atribución). Corre en GitHub Actions (tiene internet).
Guarda recortes de 45 s en mp3 128k: biblioteca/<estilo>/<slug>.mp3 y biblioteca/indice.json
Efectos (whoosh, pop, etc.): biblioteca/efectos/<slug>.mp3
"""
import os, re, json, subprocess, urllib.request, random
B = os.path.join(os.path.dirname(os.path.abspath(__file__)), "biblioteca")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
ESTILOS = {  # estilo -> páginas de Mixkit donde buscar
    "alegre": ["free-stock-music/mood/cheerful/", "free-stock-music/mood/happy/", "free-stock-music/tag/upbeat/"],
    "urbano": ["free-stock-music/hip-hop/", "free-stock-music/tag/trap/", "free-stock-music/tag/beat/"],
    "latino": ["free-stock-music/tag/latin/", "free-stock-music/tag/reggaeton/", "free-stock-music/tag/summer/"],
    "acustico": ["free-stock-music/tag/acoustic-guitar/", "free-stock-music/tag/acoustic/", "free-stock-music/mood/relaxing/"],
    "energico": ["free-stock-music/mood/energetic/", "free-stock-music/tag/sports/", "free-stock-music/electronica/"],
    "pop": ["free-stock-music/pop/", "free-stock-music/tag/funk/", "free-stock-music/mood/lighthearted/"],
    "tranquilo": ["free-stock-music/mood/calm/", "free-stock-music/tag/lofi/", "free-stock-music/tag/chill/"],
    "fiestas": ["free-stock-music/tag/christmas/"],
}
EFECTOS = ["free-sound-effects/whoosh/", "free-sound-effects/transition/", "free-sound-effects/pop/", "free-sound-effects/cash-register/", "free-sound-effects/wood/"]
POR_ESTILO, POR_EFECTO = 10, 3


def html(p):
    try:
        return urllib.request.urlopen(urllib.request.Request("https://mixkit.co/" + p, headers=UA), timeout=30).read().decode("utf-8", "ignore")
    except Exception as e:
        print("  sin página", p, e); return ""


def mp3s(h):
    urls = re.findall(r'https://assets\.mixkit\.co/[^"\'\s>]+?\.mp3', h)
    return list(dict.fromkeys(urls))


def bajar(u, destino, seg):
    tmp = destino + ".orig.mp3"
    data = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read()
    open(tmp, "wb").write(data)
    args = ["ffmpeg", "-v", "error", "-y", "-i", tmp, "-t", str(seg), "-af", f"afade=t=out:st={max(0, seg - 2)}:d=2,loudnorm=I=-16:TP=-1.5", "-ac", "2", "-b:a", "128k", destino]
    subprocess.run(args, check=True); os.remove(tmp)


os.makedirs(B, exist_ok=True)
idx_p = os.path.join(B, "indice.json")
idx = json.load(open(idx_p)) if os.path.exists(idx_p) else {"musica": {}, "efectos": []}
vistos = {t["url"] for v in idx["musica"].values() for t in v} | {e["url"] for e in idx["efectos"]}
for estilo, paginas in ESTILOS.items():
    lista = idx["musica"].setdefault(estilo, [])
    cand = []
    for p in paginas:
        cand += [u for u in mp3s(html(p)) if u not in vistos and u not in cand]
    print(estilo, len(cand), "candidatos")
    for u in cand[: max(0, POR_ESTILO - len(lista))]:
        slug = re.sub(r"[^a-z0-9-]", "", os.path.basename(u).replace(".mp3", "").lower())[:60]
        d = os.path.join(B, estilo); os.makedirs(d, exist_ok=True)
        try:
            bajar(u, os.path.join(d, slug + ".mp3"), 45); lista.append({"archivo": f"{estilo}/{slug}.mp3", "url": u}); vistos.add(u); print("  +", slug)
        except Exception as e:
            print("  falla", u, e)
for p in EFECTOS:
    tipo = p.rstrip("/").split("/")[-1]
    for u in [u for u in mp3s(html(p)) if u not in vistos][:POR_EFECTO]:
        slug = tipo + "-" + re.sub(r"[^a-z0-9-]", "", os.path.basename(u).replace(".mp3", "").lower())[:40]
        d = os.path.join(B, "efectos"); os.makedirs(d, exist_ok=True)
        try:
            bajar(u, os.path.join(d, slug + ".mp3"), 4); idx["efectos"].append({"archivo": f"efectos/{slug}.mp3", "tipo": tipo, "url": u}); vistos.add(u); print("  fx", slug)
        except Exception as e:
            print("  falla", u, e)
json.dump(idx, open(idx_p, "w"), ensure_ascii=False, indent=1)
print({k: len(v) for k, v in idx["musica"].items()}, len(idx["efectos"]), "efectos")

"""Pista de música para reels.
Primero usa la biblioteca de música libre (herramientas-musica/biblioteca, Mixkit, uso comercial permitido),
rotando temas para que no se repita: toma el que hace más tiempo que no se usa del estilo pedido.
Si la biblioteca está vacía, genera una pista instrumental original (abajo).
Uso: python3 musica.py salida.wav segundos [estilo]   estilos: alegre urbano latino acustico energico pop tranquilo fiestas (o 'auto')
"""
import sys, wave, os, json, random, subprocess, time

def _desde_biblioteca(salida, dur, estilo):
    raiz = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "herramientas-musica", "biblioteca")
    ip = os.path.join(raiz, "indice.json")
    if not os.path.exists(ip):
        return False
    idx = json.load(open(ip))["musica"]
    up = os.path.join(raiz, "usados.json")
    usados = json.load(open(up)) if os.path.exists(up) else {}
    if estilo in (None, "", "auto") or estilo not in idx or not idx[estilo]:
        estilos = [e for e, v in idx.items() if v and e != "fiestas"]
        if not estilos:
            return False
        # el estilo usado hace más tiempo
        estilo = min(estilos, key=lambda e: max([usados.get(t["archivo"], 0) for t in idx[e]] + [0]) + random.random())
    temas = [t for t in idx[estilo] if os.path.exists(os.path.join(raiz, t["archivo"]))]
    if not temas:
        return False
    tema = min(temas, key=lambda t: usados.get(t["archivo"], 0) + random.random() * 0.001)
    usados[tema["archivo"]] = time.time(); json.dump(usados, open(up, "w"), indent=1)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-stream_loop", "-1", "-i", os.path.join(raiz, tema["archivo"]), "-t", str(dur),
                    "-af", f"afade=t=in:d=0.4,afade=t=out:st={max(0, dur - 2)}:d=2", "-ar", "44100", "-ac", "2", salida], check=True)
    print("ok", dur, "biblioteca", estilo, tema["archivo"])
    return True

if len(sys.argv) > 2 and _desde_biblioteca(sys.argv[1], float(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else "auto"):
    sys.exit(0)
import numpy as np

SR = 44100
BPM = 100
BEAT = 60 / BPM
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 40
N = int(SR * DUR)
rng = np.random.default_rng(7)

def hz(m): return 440 * 2 ** ((m - 69) / 12)

# acordes (notas MIDI): C, G, Am, F
ACORDES = [[48, 60, 64, 67], [43, 59, 62, 67], [45, 60, 64, 69], [41, 60, 65, 69]]
L, R = np.zeros(N), np.zeros(N)

def poner(sig, t0, pan=0.0, g=1.0):
    i = int(t0 * SR)
    if i >= N: return
    s = sig[: N - i] * g
    L[i:i + len(s)] += s * (1 - pan) * 0.5 * 2 ** 0.5 * 0.71
    R[i:i + len(s)] += s * (1 + pan) * 0.5 * 2 ** 0.5 * 0.71

def pad(notas, dur):
    t = np.arange(int(dur * SR)) / SR
    s = np.zeros_like(t)
    for n in notas[1:]:
        f = hz(n)
        for det in (-0.12, 0.12):
            ff = f * 2 ** (det / 12)
            s += np.sin(2 * np.pi * ff * t) + 0.25 * np.sin(4 * np.pi * ff * t) + 0.08 * np.sin(6 * np.pi * ff * t)
    env = np.minimum(1, t / 0.6) * np.minimum(1, (dur - t) / 0.6)
    return s * env / 10

def pulsada(f, dur=1.6):
    # Karplus-Strong: cuerda pulsada
    n = int(dur * SR); p = int(SR / f)
    buf = rng.uniform(-1, 1, p); out = np.zeros(n)
    for k in range(n):
        out[k] = buf[k % p]
        buf[k % p] = 0.5 * (buf[k % p] + buf[(k + 1) % p]) * 0.996
    return out * np.exp(-np.arange(n) / SR * 1.8)

def bajo(f, dur):
    t = np.arange(int(dur * SR)) / SR
    return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * np.exp(-t * 1.5) * 0.5

def bombo():
    t = np.arange(int(0.35 * SR)) / SR
    f = 110 * np.exp(-t * 25) + 45
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)

def shaker():
    t = np.arange(int(0.08 * SR)) / SR
    s = rng.normal(0, 1, len(t)); s = np.diff(s, prepend=0)
    return s * np.exp(-t * 60) * 0.25

cache = {}
compas = 4 * BEAT
total = int(DUR / compas) + 1
for c in range(total):
    t0 = c * compas
    ac = ACORDES[c % 4]
    poner(pad(ac, compas + 0.3), t0, 0, 0.9)
    poner(bajo(hz(ac[0]), compas), t0, 0, 0.8)
    patron = [1, 2, 3, 2, 1, 2, 3, 2]
    for k, idx in enumerate(patron):
        n = ac[idx] + 12
        if n not in cache: cache[n] = pulsada(hz(n))
        poner(cache[n], t0 + k * BEAT / 2, (-0.35 if k % 2 else 0.35), 0.32)
    if c >= 1:
        for b in (0, 2):
            poner(bombo(), t0 + b * BEAT, 0, 0.55)
        for k in range(8):
            poner(shaker(), t0 + k * BEAT / 2 + BEAT / 4, 0.2, 0.5 if k % 2 else 0.3)

mix = np.stack([L, R], 1)
t = np.arange(N) / SR
fade = np.minimum(1, t / 1.0) * np.minimum(1, (DUR - t) / 2.5)
mix *= fade[:, None]
mix = np.tanh(mix / np.abs(mix).max() * 1.4) * 0.85
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
print("ok", DUR)

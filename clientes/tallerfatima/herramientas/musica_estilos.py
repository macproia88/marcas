"""Pistas originales (sin derechos de terceros) en distintos estilos, para no repetir siempre la misma música.
Estilos:
  festiva  -> ritmo de cumbia: güira, bajo saltado, acordes tipo acordeón. Para la feria, los stands y la alegría.
  emotiva  -> piano lento con eco. Para agradecimientos y cierres.
  acustica -> guitarra pulsada suave y alegre. Para recorridos y trabajos de los alumnos.
  marimba  -> marimba liviana con shaker. Para trabajos y talleres, tono simpático.
  pop      -> ritmo bailable (bombo en negras, palmas, bajo sintetizado). Para chicos bailando.
Uso: python3 musica_estilos.py estilo salida.wav segundos
"""
import sys, wave
import numpy as np

ESTILO, SAL, DUR = sys.argv[1], sys.argv[2], float(sys.argv[3])
SR = 44100; N = int(SR * DUR)
rng = np.random.default_rng(23)
L, R = np.zeros(N), np.zeros(N)
def hz(m): return 440 * 2 ** ((m - 69) / 12)
def env(n, at=0.005, dec=4.0):
    t = np.arange(n) / SR
    return np.minimum(1, t / at) * np.exp(-t * dec)
def poner(s, t0, pan=0.0, g=1.0):
    i = int(t0 * SR)
    if i >= N or i < 0: return
    s = s[: N - i] * g
    L[i:i + len(s)] += s * (1 - pan) * 0.7; R[i:i + len(s)] += s * (1 + pan) * 0.7
def ruido(dur, dec):
    n = int(dur * SR); x = rng.normal(0, 1, n); x = np.diff(x, prepend=0)
    return x * env(n, 0.001, dec)
def bombo():
    t = np.arange(int(0.3 * SR)) / SR; f = 100 * np.exp(-t * 30) + 48
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 10)
def pulsada(f, dur=1.4, dec=0.996):
    n = int(dur * SR); p = int(SR / f); buf = rng.uniform(-1, 1, p); out = np.zeros(n)
    for k in range(n):
        out[k] = buf[k % p]; buf[k % p] = 0.5 * (buf[k % p] + buf[(k + 1) % p]) * dec
    return out * np.exp(-np.arange(n) / SR * 1.5)
def acordeon(notas, dur):
    t = np.arange(int(dur * SR)) / SR; s = np.zeros_like(t)
    for n in notas:
        f = hz(n); vib = 1 + 0.004 * np.sin(2 * np.pi * 5.5 * t)
        for d in (1, 1.003):
            ph = 2 * np.pi * f * d * np.cumsum(vib) / SR
            s += np.sign(np.sin(ph)) * 0.25 + np.sin(ph) * 0.5 + 0.2 * np.sin(2 * ph)
    return s * np.minimum(1, t / 0.02) * np.minimum(1, (dur - t) / 0.05) / len(notas) * 0.35
def piano(f, dur=2.5):
    t = np.arange(int(dur * SR)) / SR
    s = sum(np.sin(2 * np.pi * f * k * t) * np.exp(-t * (1.2 + k * 0.9)) / k ** 1.4 for k in range(1, 7))
    return s * np.minimum(1, t / 0.004) * 0.5

if ESTILO == "festiva":
    BPM = 98; B = 60 / BPM
    ACS = [[57, 60, 64], [55, 59, 62], [53, 57, 60], [52, 56, 59]]   # Lam Sol Fa Mi
    BAJO = [45, 43, 41, 40]
    for c in range(int(DUR / (4 * B)) + 1):
        t0 = c * 4 * B; ac = ACS[c % 4]; b = BAJO[c % 4]
        for k in range(16):                                          # güira
            poner(ruido(0.07, 55), t0 + k * B / 4, 0.3, 0.5 if k % 2 == 0 else 0.28)
        for k, (dt, nn) in enumerate([(0, b), (1.5 * B, b + 7), (2 * B, b), (3.5 * B, b + 7)]):
            t = np.arange(int(0.4 * SR)) / SR
            poner(np.sin(2 * np.pi * hz(nn) * t) * np.exp(-t * 5) * 0.8, t0 + dt)
        for k in (1, 3): poner(acordeon(ac, 0.28 * B), t0 + k * B - 0.5 * B + B / 2, -0.2, 0.9)
        for k in (0.5, 1.5, 2.5, 3.5): poner(acordeon(ac, 0.2 * B), t0 + k * B, -0.2, 0.7)
        poner(bombo(), t0, 0, 0.7); poner(bombo(), t0 + 2 * B, 0, 0.7)
        poner(ruido(0.15, 18), t0 + B, -0.1, 0.35); poner(ruido(0.15, 18), t0 + 3 * B, -0.1, 0.35)
        mel = [ac[2] + 12, ac[1] + 12, ac[0] + 12, ac[1] + 12]        # melodía de acordeón
        for k, nn in enumerate(mel): poner(acordeon([nn], 0.9 * B), t0 + k * B, 0.25, 0.8)
elif ESTILO == "emotiva":
    BPM = 72; B = 60 / BPM
    ACS = [[48, 55, 64, 67], [43, 55, 62, 71], [45, 57, 64, 72], [41, 53, 60, 69]]
    for c in range(int(DUR / (4 * B)) + 1):
        t0 = c * 4 * B; ac = ACS[c % 4]
        poner(piano(hz(ac[0]), 4), t0, -0.2, 0.7)
        for k, i in enumerate([1, 2, 3, 2, 1, 2, 3, 2]): poner(piano(hz(ac[i])), t0 + k * B / 2, 0.2, 0.42)
        poner(piano(hz(ac[3] + 12), 3), t0 + 2 * B, 0.1, 0.3)
    eco = int(0.32 * SR)                                              # eco suave
    for _ in range(3):
        L[eco:] += L[:-eco] * 0.28; R[eco:] += R[:-eco] * 0.28
elif ESTILO == "marimba":
    BPM = 104; B = 60 / BPM
    ACS = [[60, 64, 67, 72], [57, 60, 64, 69], [53, 57, 60, 65], [55, 59, 62, 67]]   # Do Lam Fa Sol
    def mar(f, dur=0.6):
        t = np.arange(int(dur * SR)) / SR
        return (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 3.9 * t) * np.exp(-t * 30)) * np.exp(-t * 7) * 0.6
    for c in range(int(DUR / (4 * B)) + 1):
        t0 = c * 4 * B; ac = ACS[c % 4]
        for k, i in enumerate([0, 2, 1, 3, 2, 3, 1, 2]): poner(mar(hz(ac[i] + 12)), t0 + k * B / 2, 0.3 if k % 2 else -0.3, 0.5)
        for k in range(8): poner(ruido(0.05, 80), t0 + k * B / 2 + B / 4, 0.4, 0.22)
        t = np.arange(int(B * SR)) / SR
        for k in (0, 2): poner(np.sin(2 * np.pi * hz(ac[0] - 24) * t) * np.exp(-t * 4) * 0.7, t0 + k * B)
elif ESTILO == "pop":
    BPM = 120; B = 60 / BPM
    ACS = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]   # Lam Fa Do Sol
    for c in range(int(DUR / (4 * B)) + 1):
        t0 = c * 4 * B; ac = ACS[c % 4]
        for k in range(4): poner(bombo(), t0 + k * B, 0, 0.9)
        for k in (1, 3): poner(ruido(0.12, 25), t0 + k * B, 0.1, 0.55); poner(ruido(0.12, 25), t0 + k * B + 0.012, -0.1, 0.4)
        for k in range(8): poner(ruido(0.03, 120), t0 + k * B / 2 + B / 4, 0.3, 0.25)
        t = np.arange(int(B / 2 * SR)) / SR
        for k in range(8):
            f = hz(ac[0] - 24 + (12 if k % 2 else 0)); w = 2 * ((f * t) % 1) - 1
            poner(w * np.exp(-t * 6) * 0.35, t0 + k * B / 2)
        tt = np.arange(int(0.18 * SR)) / SR
        for k in (0.5, 1.5, 2.5, 3.5):
            st = sum(np.sign(np.sin(2 * np.pi * hz(n) * tt)) for n in ac) * np.exp(-tt * 12) * 0.12
            poner(st, t0 + k * B, -0.3, 1)
else:  # acustica
    BPM = 112; B = 60 / BPM
    ACS = [[50, 62, 66, 69], [45, 61, 64, 69], [47, 62, 66, 71], [43, 59, 62, 67]]   # Re La Sim Sol
    cache = {}
    for c in range(int(DUR / (4 * B)) + 1):
        t0 = c * 4 * B; ac = ACS[c % 4]
        for k, i in enumerate([0, 2, 1, 3, 2, 1, 3, 2]):
            n = ac[i] if i else ac[0] + 12
            if n not in cache: cache[n] = pulsada(hz(n))
            poner(cache[n], t0 + k * B / 2, -0.35 if k % 2 else 0.35, 0.3)
        t = np.arange(int(4 * B * SR)) / SR
        poner(np.sin(2 * np.pi * hz(ac[0] - 12) * t) * np.exp(-t * 1.2) * 0.5, t0)
        if c: [poner(ruido(0.06, 70), t0 + k * B + B / 2, 0.2, 0.3) for k in range(4)]   # palmas suaves
        if c: [poner(bombo(), t0 + k * B, 0, 0.45) for k in (0, 2)]

mix = np.stack([L, R], 1); tt = np.arange(N) / SR
mix *= (np.minimum(1, tt / 0.4) * np.minimum(1, (DUR - tt) / 2.0))[:, None]
mix = np.tanh(mix / (np.abs(mix).max() + 1e-9) * 1.4) * 0.85
with wave.open(SAL, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
print("ok", ESTILO)

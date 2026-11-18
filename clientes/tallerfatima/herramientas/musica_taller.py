"""Pista original "de taller" (sin derechos de terceros): ritmo hecho con sonidos de oficios
(martillo sobre madera, serrucho, máquina de coser, tijera) más una melodía suave pulsada,
y un clic de cámara en cada flash.
Uso: python3 musica_taller.py salida.wav segundos [segundos_entre_flashes] [cantidad_flashes]
"""
import sys, wave
import numpy as np

SR = 44100
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 12
FLASH = float(sys.argv[3]) if len(sys.argv) > 3 else 0
NFLASH = int(sys.argv[4]) if len(sys.argv) > 4 else 0
BPM = 104; BEAT = 60 / BPM
N = int(SR * DUR)
rng = np.random.default_rng(11)
L, R = np.zeros(N), np.zeros(N)

def poner(s, t0, pan=0.0, g=1.0):
    i = int(t0 * SR)
    if i >= N or i < 0: return
    s = s[: N - i] * g
    L[i:i + len(s)] += s * (1 - pan) * 0.7
    R[i:i + len(s)] += s * (1 + pan) * 0.7

def lp(x, a):  # filtro pasa bajos simple
    y = np.zeros_like(x); acc = 0.0
    for k, v in enumerate(x): acc += a * (v - acc); y[k] = acc
    return y

def martillo():
    t = np.arange(int(0.35 * SR)) / SR
    golpe = rng.normal(0, 1, len(t)) * np.exp(-t * 90)
    madera = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 28) + 0.5 * np.sin(2 * np.pi * 420 * t) * np.exp(-t * 40)
    metal = 0.25 * np.sin(2 * np.pi * 2350 * t) * np.exp(-t * 22)
    return (golpe * 0.6 + madera + metal) * 0.9

def serrucho(dur=BEAT * 2):
    t = np.arange(int(dur * SR)) / SR
    ruido = rng.normal(0, 1, len(t))
    ruido = ruido - lp(ruido, 0.08)                                  # saca graves
    vaiven = np.abs(np.sin(np.pi * t / (BEAT / 2))) ** 1.5          # ida y vuelta al ritmo
    tono = 1 + 0.3 * np.sin(2 * np.pi * 2200 * t * (1 + 0.05 * np.sin(2 * np.pi * 2 * t)))
    return ruido * vaiven * tono * 0.22

def costura(dur=BEAT * 2):
    t = np.arange(int(dur * SR)) / SR
    s = np.zeros_like(t); paso = BEAT / 4
    for k in range(int(dur / paso)):
        i = int(k * paso * SR); m = int(0.03 * SR)
        tt = np.arange(m) / SR
        clic = (np.sin(2 * np.pi * 1500 * tt) + 0.5 * rng.normal(0, 1, m)) * np.exp(-tt * 180)
        s[i:i + m] += clic[: len(s) - i]
    zumbido = 0.08 * np.sin(2 * np.pi * 110 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 4 / BEAT * t))
    return s * 0.35 + zumbido

def tijera():
    t = np.arange(int(0.09 * SR)) / SR
    return (rng.normal(0, 1, len(t)) - 0) * np.exp(-t * 70) * np.sin(2 * np.pi * 3000 * t) * 0.35

def obturador():
    t = np.arange(int(0.12 * SR)) / SR
    c1 = rng.normal(0, 1, len(t)) * np.exp(-t * 120)
    c2 = np.zeros_like(t); j = int(0.05 * SR); c2[j:] = rng.normal(0, 1, len(t) - j) * np.exp(-(t[j:] - t[j]) * 150)
    return (c1 + 0.8 * c2) * 0.5

def pulsada(f, dur=1.4):
    n = int(dur * SR); p = int(SR / f)
    buf = rng.uniform(-1, 1, p); out = np.zeros(n)
    for k in range(n):
        out[k] = buf[k % p]; buf[k % p] = 0.5 * (buf[k % p] + buf[(k + 1) % p]) * 0.996
    return out * np.exp(-np.arange(n) / SR * 2)

def hz(m): return 440 * 2 ** ((m - 69) / 12)

ACORDES = [[48, 64, 67, 72], [43, 62, 67, 71], [45, 64, 69, 72], [41, 65, 69, 72]]
cache = {}
compas = 4 * BEAT
for c in range(int(DUR / compas) + 1):
    t0 = c * compas; ac = ACORDES[c % 4]
    # melodía pulsada suave
    for k, idx in enumerate([1, 2, 3, 2, 1, 3, 2, 3]):
        n = ac[idx]
        if n not in cache: cache[n] = pulsada(hz(n))
        poner(cache[n], t0 + k * BEAT / 2, -0.3 if k % 2 else 0.3, 0.22)
    t = np.arange(int(compas * SR)) / SR
    poner(np.sin(2 * np.pi * hz(ac[0]) * t) * np.exp(-t * 1.2) * 0.35, t0)
    # ritmo de taller
    poner(martillo(), t0, -0.1, 0.9); poner(martillo(), t0 + 2 * BEAT, 0.1, 0.8)
    poner(martillo(), t0 + 3.5 * BEAT, 0.1, 0.45)
    poner(tijera(), t0 + 1 * BEAT, 0.4); poner(tijera(), t0 + 3 * BEAT, -0.4)
    if c % 2 == 0: poner(costura(), t0, 0.35, 0.8)
    else: poner(serrucho(), t0, -0.35, 0.9)
for k in range(NFLASH):
    poner(obturador(), k * FLASH, 0, 1.0)

mix = np.stack([L, R], 1)
tt = np.arange(N) / SR
mix *= (np.minimum(1, tt / 0.3) * np.minimum(1, (DUR - tt) / 1.5))[:, None]
mix = np.tanh(mix / np.abs(mix).max() * 1.5) * 0.85
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
print("ok")

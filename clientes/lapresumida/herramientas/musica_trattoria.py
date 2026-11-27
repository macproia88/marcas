"""Pista instrumental original (sin derechos de terceros) estilo trattoria: vals 3/4 a 96 BPM,
acordeón suave + mandolina con trémolo + bajo, en Re mayor (D - A - Bm - G).
Uso: python3 musica_trattoria.py salida.wav segundos
"""
import sys, wave
import numpy as np

SR = 44100
BEAT = 60 / 96
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 20
N = int(SR * DUR)
L, R = np.zeros(N), np.zeros(N)


def hz(m): return 440 * 2 ** ((m - 69) / 12)


def poner(s, t0, pan=0.0, g=1.0):
    i = int(t0 * SR)
    if i >= N: return
    s = s[: N - i] * g
    L[i:i + len(s)] += s * (1 - pan) * 0.7
    R[i:i + len(s)] += s * (1 + pan) * 0.7


def acordeon(notas, dur):
    t = np.arange(int(dur * SR)) / SR
    s = np.zeros_like(t)
    for n in notas:
        f = hz(n)
        for det in (-0.08, 0.0, 0.08):  # lengüetas levemente desafinadas
            ff = f * 2 ** (det / 12)
            s += np.sign(np.sin(2 * np.pi * ff * t)) * 0.25 + np.sin(2 * np.pi * ff * t)
    trem = 1 + 0.12 * np.sin(2 * np.pi * 5.2 * t)
    env = np.minimum(1, t / 0.08) * np.minimum(1, (dur - t) / 0.15)
    return s * trem * env / 28


def mandolina(f, dur):
    t = np.arange(int(dur * SR)) / SR
    s = np.zeros_like(t)
    paso = 1 / 13  # trémolo de púa
    for k in range(int(dur / paso)):
        i = int(k * paso * SR); tt = t[: len(t) - i]
        nota = (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(4 * np.pi * f * tt) + 0.15 * np.sin(6 * np.pi * f * tt)) * np.exp(-tt * 18)
        s[i:] += nota * (0.85 if k % 2 else 1)
    env = np.minimum(1, (dur - t) / 0.1)
    return s * env / 6


def bajo(f, dur):
    t = np.arange(int(dur * SR)) / SR
    return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * np.exp(-t * 4) / 3


# D, A, Bm, G (acordes) y melodía simple por compás
ACORDES = [[62, 66, 69], [61, 64, 69], [62, 66, 71], [62, 67, 71]]
BAJOS = [38, 33, 35, 31]
MELO = [[74, 78, 76], [76, 73, 69], [74, 71, 74], [79, 78, 76], [74, 78, 81], [81, 79, 76], [78, 74, 71], [74, 74, 74]]
compas = 3 * BEAT
t0, c = 0.0, 0
while t0 < DUR:
    a = c % 4
    poner(bajo(hz(BAJOS[a]), BEAT * 0.9), t0, -0.1, 1.0)
    for b in (1, 2):
        poner(acordeon(ACORDES[a], BEAT * 0.8), t0 + b * BEAT, 0.25, 1.0)
    if c >= 2:
        for k, n in enumerate(MELO[c % 8]):
            poner(mandolina(hz(n), BEAT * 0.95), t0 + k * BEAT, -0.3, 0.9)
    t0 += compas; c += 1

mx = np.max(np.abs(np.stack([L, R]))) or 1
st = (np.stack([L, R], 1) / mx * 0.85 * 32767).astype(np.int16)
fade = int(SR * 1.2)
st[-fade:] = (st[-fade:] * np.linspace(1, 0, fade)[:, None]).astype(np.int16)
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())
print("ok", DUR)

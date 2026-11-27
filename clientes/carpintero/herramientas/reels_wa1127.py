"""Reels con los videos reales que mandó Shuli el 27/11/2026 (fotos/wa-1127).
Cada reel: tramos de video 1080x1920 con un título arriba (letra blanca con sombra, sin cajas negras),
sello de WhatsApp + firma, placa final con dirección. Música original; la voz se agrega después con el robot.
Uso: python3 reels_wa1127.py
"""
import os, sys, subprocess, tempfile
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import piezas_v2 as pv

B = pv.BASE
W = os.path.join(B, "fotos", "wa-1127")
FU = os.path.join(B, "herramientas", "fuentes")
OUT = os.path.join(B, "videos", "v2")
def f(n, s): return ImageFont.truetype(os.path.join(FU, n), s)
TERRA = (168, 67, 42)


def capa_titulo(texto, sub=None):
    c = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    sombra = Image.new("L", (1080, 1920), 0); ds = ImageDraw.Draw(sombra)
    d = ImageDraw.Draw(c)
    y = 190
    lineas = texto.split("\n")
    for l in lineas:
        ds.text((540, y), l, font=f("InterDisplay-Black.otf", 72), fill=255, anchor="ma"); y += 84
    if sub: ds.text((540, y + 10), sub, font=f("Inter-SemiBold.otf", 44), fill=255, anchor="ma")
    sombra = sombra.filter(ImageFilter.GaussianBlur(14))
    c.paste((20, 12, 6, 200), (0, 0), sombra.point(lambda v: min(255, int(v * 1.6))))
    y = 190
    for l in lineas:
        d.text((540, y), l, font=f("InterDisplay-Black.otf", 72), fill="white", anchor="ma"); y += 84
    if sub: d.text((540, y + 10), sub, font=f("Inter-SemiBold.otf", 44), fill=(255, 236, 214), anchor="ma")
    pv.dibujar_sello(c, 34, 1920 - 150, vidrio=False)
    return c


def tramo(video, ini, dur, texto, sub, dst, tmp):
    capa = capa_titulo(texto, sub); p = dst + ".png"; capa.save(p)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(ini), "-t", str(dur), "-i", os.path.join(W, video), "-i", p,
                    "-filter_complex",
                    "[0:v]scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,setsar=1,fps=30,"
                    "unsharp=5:5:0.6,eq=saturation=1.06:contrast=1.05:brightness=0.02[v];[v][1:v]overlay=0:0,format=yuv420p",
                    "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", dst], check=True)


def placa_final(titulo, lineas, dst, seg=3.0):
    L = pv.fondo_estudio(1080, 1920, piso=0.999).convert("RGB"); d = ImageDraw.Draw(L)
    y = 520
    for l in titulo.split("\n"):
        d.text((540, y), l, font=f("InterDisplay-Black.otf", 96), fill=TERRA, anchor="ma"); y += 108
    y += 40
    for l in lineas:
        d.text((540, y), l, font=f("Inter-Medium.otf", 46), fill=(31, 27, 22), anchor="ma"); y += 70
    L = pv.sello(pv.firma(L), k=1.45); p = dst + ".png"; L.save(p)
    n = int(seg * 30)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", p, "-vf", "scale=1080:1920,fps=30,format=yuv420p,setsar=1",
                    "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", dst], check=True)


def armar(nombre, tramos, final, estilo="auto"):
    tmp = tempfile.mkdtemp(); partes = []
    for k, (v, ini, dur, t, s) in enumerate(tramos):
        q = f"{tmp}/{k}.mp4"; tramo(v, ini, dur, t, s, q, tmp); partes.append(q)
    q = f"{tmp}/fin.mp4"; placa_final(*final, q); partes.append(q)
    open(f"{tmp}/l.txt", "w").write("".join(f"file '{p}'\n" for p in partes))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{tmp}/l.txt", "-c", "copy", f"{tmp}/c.mp4"], check=True)
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{tmp}/c.mp4"]))
    musica = os.path.join(B, "..", "tallerfatima", "herramientas", "musica.py")
    subprocess.run([sys.executable, musica, f"{tmp}/m.wav", str(dur + 0.5), estilo], check=True)
    # efectos de transición (whoosh) en cada corte, tomados de la biblioteca y rotando
    import json, random
    bib = os.path.join(B, "..", "..", "herramientas-musica", "biblioteca")
    fx = [os.path.join(bib, e["archivo"]) for e in json.load(open(os.path.join(bib, "indice.json")))["efectos"] if e["tipo"] in ("whoosh", "transition")]
    cortes, t = [], 0.0
    for (_, _, dd, _, _) in tramos:
        t += dd; cortes.append(t)
    if fx:
        ins = ["-i", f"{tmp}/m.wav"]; filt = "[0:a]volume=0.85[m0];"; mezcla = "[m0]"
        for k, c in enumerate(cortes):
            ins += ["-i", random.choice(fx)]
            filt += f"[{k + 1}:a]volume=0.55,adelay={int(max(0, c - 0.35) * 1000)}|{int(max(0, c - 0.35) * 1000)}[f{k}];"; mezcla += f"[f{k}]"
        filt += f"{mezcla}amix=inputs={len(cortes) + 1}:normalize=0:duration=first[a]"
        subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", filt, "-map", "[a]", f"{tmp}/m2.wav"], check=True)
        os.replace(f"{tmp}/m2.wav", f"{tmp}/m.wav")
    out = os.path.join(OUT, nombre)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{tmp}/c.mp4", "-i", f"{tmp}/m.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "160k", "-af", f"afade=t=out:st={dur - 1.5}:d=1.5", "-shortest", "-movflags", "+faststart", out], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1", "-i", out, "-frames:v", "1", out.replace(".mp4", "-tapa.jpg")], check=True)
    print(out, round(dur, 1))
    return out


DIR = ["Román Gómez 1893 · José Ingenieros", "Lun a Vie 11 a 18:30 · Sáb 11 a 16"]

if __name__ == "__main__":
    armar("1128-reel-fabrica.mp4", [
        ("v1.mp4", 0.5, 5.0, "ASÍ SALE UN PEDIDO\nDE FÁBRICA", "Bajo mesadas listos para entregar"),
        ("v5.mp4", 1.0, 5.0, "Banquetas embaladas", "una por una"),
        ("v4.mp4", 1.0, 6.0, "Roperos de pino macizo", "revisados puerta por puerta"),
        ("v2.mp4", 0.0, 5.5, "Y a cargar el camión", "directo de fábrica"),
    ], ("Directo de fábrica\na tu casa", DIR), "energico")
    armar("1128-reel-silla-soga.mp4", [
        ("v8.mp4", 0.0, 7.0, "SILLA DE SOGA\nTEJIDA A MANO", "Madera maciza"),
        ("v8.mp4", 7.0, 6.0, "¿La querés?", "Comentá SOGA y te pasamos el precio"),
    ], ("Comentá SOGA", ["y te pasamos el precio por mensaje"] + DIR), "latino")
    armar("1128-reel-dormitorio.mp4", [
        ("v7.mp4", 0.0, 6.0, "CAMA DE PINO MACIZO", "1 plaza · reforzada"),
        ("v3.mp4", 0.5, 6.5, "Respaldo tapizado\ncon botones", "Para sommier · 1 y 2 plazas"),
        ("v6.mp4", 0.5, 4.5, "Y para la cocina", "Bajo mesada + alacena con vidrio"),
    ], ("Armá tu casa\ncon madera maciza", DIR), "acustico")

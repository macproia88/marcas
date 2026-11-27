"""Más piezas con el material de Shuli (27/11): reel cocina+ropero, historias en video y carrusel de respaldos en estudio."""
import os, sys, subprocess, tempfile
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw
import piezas_v2 as pv
import reels_wa1127 as r

def historia_video(video, ini, dur, titulo, sub, nombre):
    tmp = tempfile.mkdtemp(); q = f"{tmp}/a.mp4"
    r.tramo(video, ini, dur, titulo, sub, q, tmp)
    musica = os.path.join(pv.BASE, "..", "tallerfatima", "herramientas", "musica.py")
    subprocess.run([sys.executable, musica, f"{tmp}/m.wav", str(dur + 0.3), "auto"], check=True)
    out = os.path.join(r.OUT, nombre)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", q, "-i", f"{tmp}/m.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
                    "-shortest", "-movflags", "+faststart", out], check=True)
    print(out)

def respaldos():
    out = os.path.join(pv.BASE, "img", "viral"); arch = []
    textos = [("RESPALDOS TAPIZADOS", "con botones · para sommier"), ("1 y 2 plazas", "terminación prolija"), ("Hechos en fábrica", "consultá medidas y colores")]
    for k, (f, (t, s)) in enumerate(zip(["f3.jpg", "f4.jpg", "f1.jpg"], textos)):
        rel = pv.a_estudio("wa-1127/" + f, f"respaldo-{k}.jpg", alto=0.58)
        L = Image.open(os.path.join(pv.F, rel)).convert("RGB"); d = ImageDraw.Draw(L)
        d.text((540, 90), t, font=r.f("InterDisplay-Black.otf", 70), fill=r.TERRA, anchor="ma")
        d.text((540, 180), s, font=r.f("Inter-Medium.otf", 38), fill=(31, 27, 22), anchor="ma")
        p = os.path.join(out, f"1129-respaldo-{k}.jpg"); pv.sello(pv.firma(L)).save(p, quality=93); arch.append(p)
    print(arch)

if __name__ == "__main__":
    r.armar("1130-reel-cocina-ropero.mp4", [
        ("v6.mp4", 0.3, 5.5, "COCINA DE PINO MACIZO", "Bajo mesada + alacena con vidrio"),
        ("v4.mp4", 0.5, 7.0, "Ropero placard", "Con alzada y cajonera"),
    ], ("Muebles para\ntoda la casa", r.DIR), "pop")
    historia_video("v5.mp4", 0.5, 10.0, "Banquetas listas", "Embaladas y para entregar", "1128-historia-banquetas.mp4")
    historia_video("v8.mp4", 0.0, 10.0, "Silla de soga", "Tejida a mano · ¿te gusta?", "1129-historia-silla.mp4")
    respaldos()

"""Voz en off para reels: lee <carpeta>/pedidos.json [{video, texto, salida}], genera la voz con Piper
(voz argentina es_AR, modelo abierto) y la mezcla con el video bajando la música. Si la voz dura más que el
video, estira el último cuadro. Corre en GitHub Actions (voz-en-off.yml), que tiene salida a internet."""
import json, os, subprocess, sys, wave
pedidos = json.load(open(sys.argv[1], encoding="utf-8"))
MODELO = os.environ.get("VOZ_MODELO", "voces/es_AR-daniela-high.onnx")

def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))

for p in pedidos:
    if os.path.exists(p["salida"]) and not p.get("rehacer"):
        print("ya existe", p["salida"]); continue
    subprocess.run(["piper", "--model", MODELO, "--output_file", "/tmp/voz.wav", "--length_scale", str(p.get("velocidad", 0.95))],
                   input=p["texto"].encode(), check=True)
    dv, dvid = dur("/tmp/voz.wav"), dur(p["video"])
    total = max(dvid, dv + 1.0)
    extra = max(0, total - dvid)
    filtro = (f"[0:v]tpad=stop_mode=clone:stop_duration={extra:.2f}[v];"
              f"[0:a]apad,atrim=0:{total:.2f},volume=0.22[m];"
              f"[1:a]adelay=400|400,volume=1.6,apad,atrim=0:{total:.2f}[vo];"
              f"[m][vo]amix=inputs=2:normalize=0,afade=t=out:st={total-1.2:.2f}:d=1.2[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", p["video"], "-i", "/tmp/voz.wav", "-filter_complex", filtro,
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "160k",
                    "-t", f"{total:.2f}", "-movflags", "+faststart", p["salida"]], check=True)
    print("ok", p["salida"], f"voz {dv:.1f}s video {dvid:.1f}s")

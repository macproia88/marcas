#!/usr/bin/env bash
# Baja videos de Drive compartidos con enlace temporal y los guarda achicados en el repo.
# Lista: clientes/tallerfatima/herramientas/bajar_drive.txt  (una línea por video: ID_DE_DRIVE  nombre-de-salida)
# Videos largos (más de 4 minutos) se aceleran para que duren 4 minutos (sirven de base para la cámara rápida).
set -u
LISTA=clientes/tallerfatima/herramientas/bajar_drive.txt
OUT=clientes/tallerfatima/fotos/expo-2026
mkdir -p "$OUT" /tmp/drv
pip install -q gdown
: > "$OUT/info-videos.txt"
while read -r ID NOMBRE; do
  [ -z "${ID:-}" ] && continue; case "$ID" in \#*) continue;; esac
  echo "== $NOMBRE"
  gdown -q "$ID" -O "/tmp/drv/$NOMBRE.orig.mp4" || { echo "$NOMBRE: no se pudo bajar" >> "$OUT/info-videos.txt"; continue; }
  DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "/tmp/drv/$NOMBRE.orig.mp4" | cut -d. -f1)
  VF="scale='if(gt(iw,ih),1280,-2)':'if(gt(iw,ih),-2,1280)',fps=30"
  if [ "${DUR:-0}" -gt 240 ]; then
    VEL=$(python3 -c "print(round($DUR/240,3))")
    VF="setpts=PTS/$VEL,$VF"
    echo "$NOMBRE: original ${DUR}s, acelerado x$VEL a 240s" >> "$OUT/info-videos.txt"
  else
    echo "$NOMBRE: ${DUR}s" >> "$OUT/info-videos.txt"
  fi
  ffmpeg -v error -y -i "/tmp/drv/$NOMBRE.orig.mp4" -vf "$VF" -an -c:v libx264 -preset veryfast -crf 27 -movflags +faststart "$OUT/$NOMBRE.mp4"
  ls -la "$OUT/$NOMBRE.mp4"
  rm -f "/tmp/drv/$NOMBRE.orig.mp4"
done < "$LISTA"
cat "$OUT/info-videos.txt"

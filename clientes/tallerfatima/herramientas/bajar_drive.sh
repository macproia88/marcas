#!/usr/bin/env bash
# Baja videos de Drive compartidos con enlace temporal y los guarda achicados en el repo.
# Lista: clientes/tallerfatima/herramientas/bajar_drive.txt  (una línea por video: ID_DE_DRIVE  nombre-de-salida)
# Videos largos (más de 2,5 minutos) se aceleran para que duren 2 minutos (sirven de base para la cámara rápida).
set -u
LISTA=clientes/tallerfatima/herramientas/bajar_drive.txt
FOTOS="$(cat clientes/tallerfatima/herramientas/fotos_momentos.txt 2>/dev/null)"
OUT=clientes/tallerfatima/fotos/expo-2026
mkdir -p "$OUT" /tmp/drv
pip install -q gdown
: >> "$OUT/info-videos.txt"
while read -r ID NOMBRE MODO; do
  [ -z "${ID:-}" ] && continue; case "$ID" in \#*) continue;; esac
  echo "== $NOMBRE"
  gdown -q "$ID" -O "/tmp/drv/$NOMBRE.orig.mp4" || { echo "$NOMBRE: no se pudo bajar" >> "$OUT/info-videos.txt"; continue; }
  DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "/tmp/drv/$NOMBRE.orig.mp4" | cut -d. -f1)
  VF="scale='if(gt(iw,ih),720,-2)':'if(gt(iw,ih),-2,720)',fps=30"
  if [ "${MODO:-}" = "fotos" ]; then
    python3 -m pip install -q numpy pillow
    python3 clientes/tallerfatima/herramientas/fotogramas.py "/tmp/drv/$NOMBRE.orig.mp4" "$OUT/cuadros" "$(python3 -c "print($DUR/120)")" $FOTOS
    rm -f "/tmp/drv/$NOMBRE.orig.mp4"; continue
  fi
  AUDIO="-an"
  if [ "${MODO:-}" = "normal" ]; then
    AUDIO="-c:a aac -b:a 128k"
    echo "$NOMBRE: ${DUR}s, velocidad normal con sonido" >> "$OUT/info-videos.txt"
  elif [ "${DUR:-0}" -gt 150 ]; then
    VEL=$(python3 -c "print(round($DUR/120,3))")
    VF="setpts=PTS/$VEL,$VF"
    echo "$NOMBRE: original ${DUR}s, acelerado x$VEL a 120s" >> "$OUT/info-videos.txt"
  else
    echo "$NOMBRE: ${DUR}s" >> "$OUT/info-videos.txt"
  fi
  ffmpeg -nostdin -v error -y -i "/tmp/drv/$NOMBRE.orig.mp4" -vf "$VF" $AUDIO -c:v libx264 -preset veryfast -crf 28 -movflags +faststart "$OUT/$NOMBRE.mp4"
  if [ $(stat -c%s "$OUT/$NOMBRE.mp4") -gt 95000000 ]; then
    ffmpeg -nostdin -v error -y -i "$OUT/$NOMBRE.mp4" -c:v libx264 -preset veryfast -crf 34 "/tmp/drv/chico.mp4" && mv /tmp/drv/chico.mp4 "$OUT/$NOMBRE.mp4"
  fi
  ls -la "$OUT/$NOMBRE.mp4"
  rm -f "/tmp/drv/$NOMBRE.orig.mp4"
done < <(grep -v '^#' "$LISTA")
cat "$OUT/info-videos.txt"

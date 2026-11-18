# Voz en off para reels (todos los clientes)

1. Escribir el guion en `<carpeta del cliente>/voz/pedidos.json` (lista de pedidos):
   `{"video": "ruta/al/video.mp4", "salida": "ruta/al/video-voz.mp4", "texto": "Guion..."}`
   - Carpetas: `clientes/<cliente>/voz/` (carpintero, tallerfatima, ca7rielypaco…) o `quinta-ig/voz/`.
   - Opcional: `"velocidad": 0.95` (más bajo = más rápido), `"rehacer": true` para regenerar.
   - Guion: ~2,5 palabras por segundo de video. Los números se escriben en letras ("seiscientos metros").
2. Hacer push del pedidos.json: el workflow `voz-en-off.yml` genera la voz (Piper, voz argentina es_AR "daniela",
   de mujer) y la mezcla con el video bajando la música. Si la voz es más larga, estira el último cuadro.
3. Cuando aparece el commit "Voz en off agregada a reels", poner la ruta `-voz.mp4` en el `media` del item de la cola.
Música de fondo opcional: `"musica": "ruta.m4a"` (y `"vol_musica": 0.35`). Pistas originales sin derechos: `python3 herramientas-voz/musica_verano.py salida.wav segundos`.
Si el cliente prefiere su propia voz: que mande un audio y se mezcla con ffmpeg de la misma forma.

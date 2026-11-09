# Publicador propio de @quintaelflorido (reemplaza a Metricool)

Desde el 08/11/2026 todo se publica con la API oficial de Instagram, gratis y sin límite de cupo
(Meta permite muchas publicaciones por día; el script imprime el cupo usado en las últimas 24 h).

## Cómo programar algo
1. Subí la imagen o el video a `quinta-ig/` (JPG para fotos; MP4 H.264 para reels/historias de video).
   - Feed: 1080x1350 (4:5) ideal; se acepta hasta 1.91:1.
   - Historia: 1080x1920, dejando libre el borde de abajo (~180 px).
2. Agregá un item a `quinta-ig/publicador/cola.json`:
   ```json
   {"id": "texto-unico", "tipo": "STORY|POST|REEL|CARRUSEL",
    "media": ["quinta-ig/archivo.jpg"], "texto": "caption (vacío en historias)",
    "fecha": "AAAA-MM-DD HH:MM", "estado": "pendiente"}
   ```
   La fecha es hora Argentina. Mantené la lista ordenada por fecha.
3. Commit + push (fetch + rebase antes). Si hay conflicto en cola.json, juntá las dos listas por "id":
   gana el item con estado "publicado"/"error" (lo escribió el robot).
4. GitHub Actions (`.github/workflows/ig-publicar.yml`) corre cada ~15 min y además en cada push de cola.json.
   Publica lo vencido y anota `estado: publicado` + `ig_media_id`, o `estado: error` + `error`.

## Reglas de contenido
- Feed a las 21:00 (pico 21-24 h; días fuertes: domingo, jueves, lunes). Historias 20:00 (o 10:30 los sábados).
- Máximo 1 posteo de feed por día; no repetir el mismo tema/foto en 3-4 días.
- No tocar los items del sorteo (id con "sorteo") salvo pedido de Walter.
- Precio base "Desde $140.000 el día"; promo entre semana "desde $110.000" solo si Walter lo pidió esa semana.
- La quinta de día NO es para dormir; solo la quinta con casa (5 personas).
- WhatsApp 11 3877-7015. Ubicación: General Rodríguez, a 600 m de la autopista.

## La llave
Secret `IG_TOKEN` del repo (usuario del sistema, no vence). Nunca imprimirla ni guardarla en archivos.
Cuenta de Instagram: quintaelflorido, id 17841454960836233. API: graph.facebook.com/v23.0.
Verificación rápida: push que toque `quinta-ig/publicador/verificar.trigger` → escribe `estado-conexion.json`.

## Varias cuentas (clientes)
- Lista de cuentas: `quinta-ig/publicador/cuentas.json` (nombre, usuario, ig_id, secret, cola, activa).
- Cada cliente: carpeta `clientes/<slug>/` con su `cola.json` y sus imágenes; su llave en el secret indicado.
- Al sumar un secret nuevo hay que agregarlo también en el `env:` de `.github/workflows/ig-publicar.yml`.
- Alta de un cliente: en la app "Publicador Quinta El Florido" (developers.facebook.com/apps/1441500650864869)
  → Roles → agregar "Evaluador de Instagram" con su usuario → el cliente acepta en Instagram
  (Configuración → Apps y sitios web → Invitaciones de prueba) → Casos de uso → API setup with Unified login
  → paso 2 "Generar identificador" → guardar la llave como secret → anotar el ig_id que muestra esa pantalla.
- La cuenta de Instagram tiene que ser profesional (empresa o creador).

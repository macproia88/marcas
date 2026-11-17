# El carpintero3 (@elcarpintero3f)

Cliente de manejo de Instagram. Mueblería con showroom en **Román Gómez 1893, José Ingenieros**.
Horario: lunes a viernes de 11 a 18:30 y sábados de 11 a 16. WhatsApp las 24 horas: **11 4194-3328** (agregado a la bio el 16/11).

- Cuenta conectada al robot publicador el 16/11/2026 (`quinta-ig/publicador/cuentas.json`, ig_id `17841431830396652`, llave cifrada en `quinta-ig/publicador/llaves/elcarpintero3f.enc`).
- Métricas cada 3 horas en `metricas/datos.json` (paso "El carpintero3" de `ig-metricas.yml`).
- Informe de 7 días para el cliente: https://macproia88.github.io/marcas/c/carpintero-13866e0c/
- Diagnóstico en imagen: `img/diagnostico-2026-11-16.png`

## Carpetas
| Carpeta | Qué hay |
|---|---|
| `fotos/` | Fotos y videos originales que manda el cliente (taller, showroom, muebles terminados) |
| `img/` | Piezas terminadas (carruseles 1080x1350, historias 1080x1920) |
| `cola.json` | Cola de publicación que lee el reloj (`ig-reloj`) |
| `metricas/datos.json` | Métricas que se juntan cada 3 horas |

## Diagnóstico al 16/11/2026
- 1.991 seguidores, 74 publicaciones, sigue a 3.743 cuentas (casi el doble de las que lo siguen).
- **19 días sin publicar** (último posteo: 28/10, "Combos para cocina").
- Alcance de los últimos 7 días: **79 personas**, contra 2.398 la semana anterior (−97%). Vistas: 1.047 contra 5.223 (−80%).
- Hubo un pico del 30/10 al 3/11 (alrededor de 3.000 vistas por día) sin posteos nuevos en esos días. Después, el alcance cayó casi a cero.
- Los últimos tres carruseles (entre ellos "Combos para cocina" y "Combo para espacios pequeños") tuvieron entre 296 y 543 vistas cada uno.
- Público: 72% mujeres; 6 de cada 10 tienen entre 35 y 54 años. La ciudad principal es CABA, seguida por el oeste del GBA (Hurlingham, Ramos Mejía, Billinghurst, Morón).
- Horario: los seguidores están más conectados de 19 a 23 h, con el pico a las 22 h.
- Estética actual mezclada: fotos reales en la vereda o el taller, ambientes hechos con IA y flyers sueltos.
- Tiene una cuenta publicitaria con un saldo pendiente chico, de unos $420 (dato visto en "Pagos de anuncios" el 16/11).

## Estilo propuesto: "carpintería de barrio, real y prolija"
- Mostrar que fabrica él: reels de 10 a 20 segundos del proceso (madera cruda → lijado → armado → mueble terminado).
- Producto real, sacado en el showroom con luz de día y fondo limpio, no en la vereda.
- Si se usa una imagen de ambiente hecha con IA, siempre al lado de la foto real del mismo mueble.
- Una sola estética de marca, con los colores del logo (verde del casco, amarillo y madera clara). Nada de flyers con colores sueltos.
- En cada texto: medidas, tipo de madera, si se hace a medida, el showroom y "consultá por WhatsApp 24 hs al 11 4194-3328".

## Reglas de publicación
- Feed: 3 posteos y 2 reels por semana, a las **20:30**. Máximo un posteo de feed por día.
- Historias todos los días a las 13:00, más una a las 20:45 los días que hay feed.
- **Todo entra a la cola como `"estado": "borrador"`.** El robot solo publica lo que está en `"pendiente"`. Cuando Juan aprueba,
  se cambia a `"pendiente"` y se agrega `"aprobado": "AAAA-MM-DD HH:MM (quién)"`.
- Hashtags: #ElCarpintero3 #MueblesDePino #MueblesAMedida #JoséIngenieros #Showroom.
- No inventar precios, promociones, plazos de entrega ni medidas que el cliente no haya pasado.

## Plan semana 1 (martes 17 al domingo 23/11)
| Día | Feed 20:30 | Historia 13:00 |
|---|---|---|
| Mar 17 | Carrusel "Volvimos al taller": cómo se hace un mueble en El carpintero3 (fotos del taller) | Encuesta: "¿Qué mueble estás buscando?" |
| Mié 18 | **Reel**: de la madera cruda a la banqueta terminada | Detrás de escena del taller |
| Jue 19 | Carrusel producto: mesa redonda con base de varillas y sillas (medidas, madera, a medida) | Recordatorio: showroom y horarios |
| Vie 20 | **Reel**: recorrida por el showroom, "vení a verlo a Román Gómez 1893" | Mueble terminado del día |
| Sáb 21 | Carrusel "Combos para espacios chicos" (bajo mesada y alacena de pino) | "Hoy abrimos hasta las 16 h" |
| Dom 22 | — | Pregunta abierta: "¿Qué mueble te gustaría ver hecho?" |
| Lun 23 | — | Resultado de la encuesta y adelanto de la semana |

## Plan del mes (resumen)
- Semana 1: volver a aparecer y mostrar el taller por dentro.
- Semana 2: producto estrella (mesas y sillas) y primer testimonio de un cliente con su mueble en casa.
- Semana 3: muebles a medida (cocina y baño) y preguntas frecuentes (maderas, terminaciones, tiempos).
- Semana 4: muebles para regalar en las fiestas y para el living de fin de año.
- Cada semana, ver en el informe qué funcionó y repetir el formato que más alcance tuvo.

## Lo que hace falta pedirle al cliente
- 8 a 10 fotos y 3 o 4 videos cortos (vertical) del **taller trabajando** y del **showroom**.
- Fotos de los muebles que tiene hoy en el showroom, con medidas y madera de cada uno.
- Logo en buena calidad.
- Si quiere mostrar precios o prefiere "consultá por WhatsApp".

## Qué rinde más (análisis del 16/11/2026, 50 posteos con métricas)
- **Época dorada: febrero a junio de 2025.** Los posteos sacaban de 3.000 a 5.200 vistas y llegaban a unas 1.000 personas cada uno. En 2026 la mayoría quedó entre 300 y 1.000 vistas.
- **Los 5 mejores:** comedor "todo Paraíso" (5.235 vistas), rack para TV varillado (4.753), cama nido (4.510), sillón "YPF" tapizado en pana, chenille o ecocuero (4.256) y juguetero (4.027).
- **Los que más visitas al perfil generan** (es lo más cerca del WhatsApp): sillón "YPF" (29 visitas y 3 seguidores nuevos), comedor Paraíso (17), mini tolva de baño (14), banqueta de peteribí (12 visitas y 5 seguidores nuevos) y materas de peteribí (12).
- **Patrón:** rinde el producto con nombre propio, la madera (paraíso, peteribí) y las opciones de tapizado. Los posteos sin texto o con solo hashtags rinden menos.
- **Reels:** hubo solo 3, pero en 2026 llegaron al doble de gente que los carruseles (unas 900 personas contra 400 a 600). Por eso esta semana hay 5 reels.

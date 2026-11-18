# Escuela Taller Fátima (@escuelatallerfatima)

Cliente de manejo de Instagram. Cuenta conectada al robot publicador (`quinta-ig/publicador/cuentas.json`, llave cifrada en `quinta-ig/publicador/llaves/`).
Informe de 7 días para la clienta: https://macproia88.github.io/marcas/c/tallerfatima-6a5edf0a/

## Carpetas
| Carpeta | Qué hay |
|---|---|
| `marca/` | Manual de marca 2023 (PDF) y logos sacados del manual (`logo-verde.png`, `logo-blanco.png`, `hoja-verde.png`) |
| `fotos/` | Material original elegido del Drive de la escuela, ordenado por taller |
| `img/` | Piezas terminadas (carruseles 1080x1350 e historias 1080x1920) |
| `videos/` | Reels terminados (1080x1920, H.264) |
| `herramientas/armar_piezas.py` | Script que arma las piezas con la identidad de marca |
| `cola.json` | Cola de publicación que lee el reloj (`ig-reloj`) |
| `metricas/datos.json` | Métricas que se juntan cada 3 horas |

## Identidad (manual de marca 2023)
- Colores principales: verde **#00894C**, crema **#F5FBF6**, marrón **#52453B**.
- Secundarios: turquesa #17919C, verde claro #78B02A, amarillo #FFCB33.
- Tipografías: **League Spartan Bold** para títulos y **Lato** para textos.
- Logo en su versión principal; si no se puede, en blanco y negro. Ancho mínimo 40 mm.

## Origen del material (Drive)
- Carpeta "2026 Banco de Fotos" de redestallerfatima@gmail.com, compartida con lapresumidapastas@gmail.com.
  Tiene unas 34 subcarpetas por evento (marzo a septiembre de 2026), cientos de fotos y videos.
- Carpeta "2026 Manual de Identidad", que contiene el manual de marca.
- **No se sube todo el banco al repo.** Hay videos de 100 a 270 MB (GitHub rechaza los archivos de más de 100 MB) y la descarga
  automática solo acepta archivos de hasta 10 MB. Se baja una selección por semana, según el plan.

Subido hasta ahora (16/11):
| Carpeta del repo | Evento en el Drive |
|---|---|
| `fotos/carpinteria` | 2026.08.24 Capacitación Carpintería Adultos (6 fotos y 1 video) |
| `fotos/costura` | 2026.04.07 Costura Jóvenes Talleres en Acción (6 fotos) |
| `fotos/soldadura` | 2026.03.18 Soldadura Primeras Prácticas (3 fotos) |
| `fotos/manicuria` | 2026.08.20 Taller Manicuría Com 2 (2 fotos) |
| `fotos/testimonio-corina` | 2026.08.19 Testimonio Corina Ex Alumna (3 videos) |
| `fotos/intercambio-oficios` | 2026.09.23 Intercambio de oficios (4 videos) |

## Diagnóstico al 16/11
- 2.982 seguidores, 13 días sin publicar. El alcance semanal bajó de 1.147 a 127 personas.
- Lo que mejor funciona son los reels de alumnos aprendiendo un oficio. El del 18/9 llegó a 4.109 personas.
- Público: 2 de cada 3 son mujeres, de 25 a 54 años.
- Horario: los seguidores están más conectados entre las 21 y las 23 h (hora argentina). La madrugada es lo más bajo.

## Reglas de publicación
- Feed de 3 a 4 veces por semana a las **21:00**. Historias todos los días, a las 13:00 o a las 21:15 los días que hay feed.
- Un reel por semana con alumnos trabajando en un oficio.
- Carruseles por taller con fotos reales y testimonios.
- Máximo un posteo de feed por día.
- **Todo entra a la cola como `"estado": "borrador"`.** El robot solo publica lo que está en `"pendiente"`. Cuando Juan o la clienta aprueban,
  se cambia a `"pendiente"` y se agrega `"aprobado": "AAAA-MM-DD HH:MM (quién)"`.
- Caption con llamado a escribir por mensaje y los hashtags #EscuelaTallerFatima #ComunidadFátima.
- No inventar fechas de inscripción, precios ni datos de contacto que la escuela no haya pasado.

## Semana Expo (18 al 23/11): toda la semana se habla de la Expo Fátima 2026
Material: carpeta "Expo 2026" del Drive de la escuela, bajada a `fotos/expo-2026/`: fotos, 19 tomas de 4 s (`tomas/`), fotos fijas (`cuadros/`) y videos del show con sonido (`sonido-*.mp4`).
El video largo original es de 432x768, así que sus fotos fijas van enmarcadas tipo foto instantánea, no a pantalla completa.
Música: cada pieza lleva un sonido distinto según el contenido (`herramientas/musica_estilos.py`: festiva, emotiva, acústica; `musica_taller.py`: sonidos de taller; o el sonido en vivo).
| Día | Feed | Historia |
|---|---|---|
| Mié 18 | 10:00 Carrusel "Así se vivió nuestra Expo 2026" (pedido de la clienta: a las 10) | 16:00 flashes, sonido de taller (pedido de la clienta) |
| Jue 19 | 21:00 Reel spoiler, 11 tomas a velocidad normal, música festiva | 13:00 "Hoy 21 h el spoiler", acústica |
| Vie 20 | 21:00 Carrusel "Lo que hicieron nuestros alumnos" | 21:15 taller, sonido de taller |
| Sáb 21 | 21:00 Carrusel "Una Expo para toda la comunidad" | 21:15 nenas bailando, festiva |
| Dom 22 | 21:00 Reel "Y la Expo también fue fiesta", sonido en vivo de la banda | 21:15 banda en vivo |
| Lun 23 | 21:00 Carrusel "¡Gracias!" con las fotos "Gracias 1 a 5" del Drive y cierre con el video "Gracias-cierre" (pedido de la clienta) | 21:15 escenario al atardecer, piano emotivo |

## Semana 2 (24 al 30/11): lo que estaba planeado antes, corrido una semana
| Día | Feed 21:00 | Historia |
|---|---|---|
| Mar 24 | Carrusel "Aprender un oficio con las manos" (carpintería) | 21:15 |
| Mié 25 | — | 13:00 soldadura |
| Jue 26 | Reel "Intercambio de oficios" (con música original) | 13:00 manicuría |
| Vie 27 | — | 13:00 profes |
| Sáb 28 | Carrusel "Del molde a la prenda" (costura) | 21:15 |
| Dom 29 | Reel testimonio de Corina | 21:15 |
| Lun 30 | — | 13:00 "¿Querés sumarte?" |

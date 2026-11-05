# Actualización automática del tablero

El tablero publicado es `tablero-presumida-v2.html`, en la raíz del repo. Se arma con `tablero-auto/actualizar.py` a partir de los datos de `tablero-auto/data/`.

## Qué hace cada corrida

1. **Traer los cierres nuevos de Gmail.** Hay dos búsquedas:
   - Florida y Beccar: `subject:"Fin de turno" newer_than:3d`.
   - Pastas Paz: `from:cielitomioolivos@gmail.com newer_than:3d`. Paz reenvía los cierres en un solo mail, con varios cierres pegados en el cuerpo, y el asunto es el texto del cierre.

   La forma más segura de cargarlos es `python3 tablero-auto/parse_cierres.py <archivo> <thread_id>`, donde `<archivo>` es el texto o el JSON del mail. Si `get_thread` devuelve un resultado demasiado largo, el sistema lo guarda en un archivo: se le pasa ese archivo al script. El script separa los cierres, controla que las formas de cobro sumen el total y no duplica: la clave es sucursal + fecha + turno.
2. **Leer cada mail nuevo** con `get_thread` en formato `PLAIN_TEXT` y agregar a `cierres.json` un objeto con este formato:

```json
{"thread": "id del hilo", "subject": "asunto", "sender": "remitente",
 "sucursal": "código de 'Sucursal:' del encabezado (fpastas = Florida, Beccar = Beccar)",
 "fecha": "YYYY-MM-DD del día de venta, de la línea de fecha del cuerpo (no la fecha del mail)",
 "turno": "Mañana / Intermedio / Noche",
 "total": 0, "tickets": 0,
 "neto21": 0, "iva21": 0, "neto105": 0, "iva105": 0,
 "formas": {"EFECTIVO": [importe, cantidad], "PEDIDOS YA ONLINE": [importe, cantidad]},
 "cod202_unid": 0, "cod202_importe": 0}
```

   De dónde sale cada campo:
   - `total` y `tickets`: la línea `TOTAL <importe> <cantidad>` de RESUMEN DE VENTAS.
   - `neto21`, `iva21`, `neto105` e `iva105`: las líneas `TOTAL Neto/Iva`. Si no están, se usan las de `Neto ACF/Iva ACF`. Si no hay ninguna, va 0.
   - `formas`: todas las líneas de VENTAS POR FORMA DE COBRO, salvo la del TOTAL.
   - `cod202_unid` y `cod202_importe`: la línea del código 202 en VENTAS POR ARTICULO. Si no está, va 0.
   - `articulos`: todas las líneas de VENTAS POR ARTICULO como `[codigo, nombre, rubro, unidades, importe]`. Las arma solo `parse_cierres.py` (el nombre viene cortado a 17 letras y a veces pegado a las unidades). La suma de los importes tiene que dar el `total`.

   Los números se copian tal cual vienen en el mail.
3. **Armar el tablero:** `python3 tablero-auto/actualizar.py`. El script suma los turnos de cada día y local. Si un turno todavía no cerró, el día queda parcial y se completa en la corrida siguiente.
4. **Control:** para cada mail, la suma de las formas de cobro tiene que dar el `total`. Si no da, revisar la extracción antes de seguir.
5. **Subir el cambio:** commit y push a `main` con el mensaje `Tablero: cierres hasta <fecha> <turno>`. Si no hubo mails nuevos, no se hace commit.

## Datos que no salen de los mails

- **Pedidos de apps:** se estiman con venta de apps (código 202) ÷ ticket promedio de apps del 1 al 25/10.
- **Comparación con 2025:** sale de `data/ref_2025.json`, que hoy cubre octubre. Para noviembre hay que cargar la referencia del plan de noviembre.
- **Pastas Paz:** sus cierres van a otra casilla. Cuando lleguen a este Gmail, agregar su código de sucursal en `SUCURSALES` dentro de `actualizar.py`.
- **Resumen de arriba del tablero** (avance contra el plan, KPIs y alertas): no se actualiza solo.

## Regla para todas las páginas de la web

Toda página que se publique en este repo lleva la línea "Última actualización: dd/mm/aaaa a las HH:MM (hora Argentina)" arriba. Después de cambiar una página, correr `python3 tablero-auto/sello.py <archivo.html>`. El tablero principal la pone solo (`actualizar.py`). La Agenda de reconocimiento se arma con `python3 tablero-auto/reconocimiento.py` y después `sello.py reconocimiento.html`.

## Tableros por canal (apps.html y mostrador.html)

1. Apps del mes: `python3 tablero-auto/apps_agregar.py <orderDetails.csv de PedidosYa> <orders.xlsx de Rappi> <AAAA-MM>`.
2. Mostrador: `python3 tablero-auto/mostrador_agregar.py Florida=<detallada> Beccar=<detallada> Paz=<detallada>` (venta detallada de Maxi Rest; separa sola por mes).
3. Armar las dos páginas: `python3 tablero-auto/canales.py`. `actualizar.py` ya lo corre en cada cierre, así que los días y meses se actualizan solos; el detalle de un mes aparece cuando se cargan sus archivos (pasos 1 y 2). Ya llevan la fecha y hora de actualización.

## Venta de mostrador por artículo y rubro

`tablero-auto/articulos.py` arma el top de productos y la venta por rubro de `mostrador.html`, mes a mes:
- Base del mes, si hay: informe de unidades por artículo de Maxi Rest (solo mostrador más el 202 de apps, que se descarta). Carga: `python3 tablero-auto/articulos.py base <archivo.xlsx> <AAAA-MM> <último día que cubre>`. Imprime el control contra la venta de mostrador.
- Los días siguientes se suman solos con el campo `articulos` de cada cierre (sin el 202). No hace falta ningún paso extra: `canales.py` lo lee en cada corrida.
- El código 4000 (Descuento Alax) es el descuento del club: queda aparte, no entra en el top ni en los rubros.

## Links entre páginas

Abajo de cada página del negocio va la lista de links a las otras (`tablero-auto/nav.py`). `actualizar.py` y `reconocimiento.py` la ponen solos. Si se suma una página nueva del negocio, agregarla a `PAGINAS` en `nav.py`.

## Club: grupos semana a semana (tablero-club.html)

- Sección "¿Cómo se mueven los grupos semana a semana?" sale de `DATA['grupos_semana']`.
- Para actualizarla: `python3 tablero-auto/club_grupos.py <carpetas o archivos con los Reporte_de_ventas de ALAX>` (los de julio en adelante; se juntan por venta_id). Después actualizar `info.actualizado`.
- Solo publica cantidades por grupo, local y semana. La ficha con nombres, DNI y mails NO va a la web (es pública): queda en el Excel Club_Ficha_y_Grupos_Semanales.xlsx.
- Grupos (últimos 30 días a cada domingo): Frecuentes 4+ días con compra, Recurrentes 2-3, Nuevos 1ª compra en 30 días, Ocasionales 1 vez y ya eran clientes, En riesgo 31-60 días sin venir, Dormidos +60.
- Corrida semanal completa (CRM): `python3 tablero-auto/crm/club_crm.py <carpeta con los 6 reportes de ALAX + históricos + el último Club_CRM_*.xlsx> <carpeta salida> [AAAA-MM-DD]`. Escribe Club_CRM_<fecha>.xlsx (privado, va al Drive "01 Club", id 1E2Hu-V88MzKEtA5M5MnUuqPQAjO4Z3mx) y actualiza `grupos_semana` y `contactos_resultado` en tablero-club.html.

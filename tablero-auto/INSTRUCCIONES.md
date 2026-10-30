# Actualización automática del tablero

El tablero publicado es `tablero-presumida-v2.html`, en la raíz del repo. Se arma con `tablero-auto/actualizar.py` a partir de los datos de `tablero-auto/data/`.

## Qué hace cada corrida

1. **Traer los cierres nuevos de Gmail.** Buscar con `subject:"Fin de turno" newer_than:3d`. Un mail cuenta como nuevo si su thread id no está en `tablero-auto/data/cierres.json`.
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

   Los números se copian tal cual vienen en el mail.
3. **Armar el tablero:** `python3 tablero-auto/actualizar.py`. El script suma los turnos de cada día y local. Si un turno todavía no cerró, el día queda parcial y se completa en la corrida siguiente.
4. **Control:** para cada mail, la suma de las formas de cobro tiene que dar el `total`. Si no da, revisar la extracción antes de seguir.
5. **Subir el cambio:** commit y push a `main` con el mensaje `Tablero: cierres hasta <fecha> <turno>`. Si no hubo mails nuevos, no se hace commit.

## Datos que no salen de los mails

- **Pedidos de apps:** se estiman con venta de apps (código 202) ÷ ticket promedio de apps del 1 al 25/10.
- **Comparación con 2025:** sale de `data/ref_2025.json`, que hoy cubre octubre. Para noviembre hay que cargar la referencia del plan de noviembre.
- **Pastas Paz:** sus cierres van a otra casilla. Cuando lleguen a este Gmail, agregar su código de sucursal en `SUCURSALES` dentro de `actualizar.py`.
- **Resumen de arriba del tablero** (avance contra el plan, KPIs y alertas): no se actualiza solo.

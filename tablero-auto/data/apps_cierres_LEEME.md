# apps_cierres.json — cierre mensual de PedidosYa y Rappi (enero a octubre 2026)

Una fila por **mes × local × app**: `{mes, local, app, pedidos, facturado, se_queda, depositado, efectivo, completo, fuente, nota}`.
Armado el 01/11/2026. Scripts en `scratchpad/apps_cierres/` (`build_py.py`, `build_rappi.py`, `build_meses.py`).

## Definiciones (las mismas que `apps_liq.json`)

| Campo | Qué es | En apps_liq.json |
|---|---|---|
| facturado | Lo que pagó el cliente con IVA, ya descontado lo que regala el local ("venta") | `venta` |
| se_queda | Todo lo que retiene la app: comisión, cargos, publicidad neta de reintegros, IVA sobre comisión, percepciones y retenciones | `costo_app + impuestos` |
| depositado | Lo que la app transfiere al banco por esos pedidos | `deposito` |
| efectivo | **Campo extra.** Ventas de PedidosYa cobradas en efectivo por el propio local (solo hubo hasta abril). No pasan por el banco | — |
| pedidos | Pedidos de la liquidación | `pedidos` |
| completo | `false` si al mes le faltan días sin liquidación, o si es estimado | — |

Siempre se cumple **facturado = se_queda + depositado + efectivo** (verificado en las 50 filas). Desde mayo efectivo = 0, así que facturado = se_queda + depositado.

## PedidosYa (cuentas 77651 Florida + V. López, 77652 Beccar + San Isidro, 370256 Paz)

Fuente: estado de cuenta semanal (lunes a domingo). Líneas del PDF:
- **facturado** = "Ventas netas".
- **se_queda** = "Ventas netas" − "Ingresos por ventas en PedidosYa" (o sea Servicios PedidosYa + Cargos operativos + Publicidad − Reintegros + Ajustes + Impuestos y Retenciones).
- **depositado** = "Subtotal" / "Total liquidado".
- **efectivo** = "Ventas con pago fuera de la App cobradas".
- **pedidos** = filas de la hoja "Lista de Pedidos" del Excel (.xls) de la semana.

Control: en todas las semanas con Excel, la suma de "Monto de Venta Neta ($)" (o "Monto neto de la Venta ($)" en los Excels viejos) da igual al peso que "Ventas netas" del PDF.

De dónde salió cada semana:
- Florida ene–jul: zips `estado-de-cuenta_77651` (PDF + Excel) de "02 Seguimiento Apps".
- Beccar y Paz ene–may: solo PDF (carpetas de la contadora). **No hay Excel de pedidos** → pedidos ESTIMADOS = venta ÷ ticket promedio (ticket de Florida de ese mes × relación ticket local/Florida de jun–jul: Beccar 0,94, Paz 0,92).
- Beccar y Paz jun–jul: Excel de pedidos + PDF leído desde Drive (números copiados en `pdf_manual.json` con el id de cada archivo).
- Ago 03 al Sep 27 (las 3 cuentas): totales de la hoja Liquidaciones de `peya/ago/apps.xlsx` (misma base que apps_liq); pedidos de los Excels donde están.
- Semanas 31/08–06/09 y 28/09–04/10 (las 3 cuentas): zips bajados ahora (PDF + Excel).
- Octubre (05/10 al 25/10): zips de "02 Seguimiento Apps".

**Semanas que cruzan de mes**: con Excel, cada pedido va al mes de su "Fecha de pedido"; la venta es exacta y lo que se queda la app, el depósito y el efectivo de esa semana se reparten en la misma proporción que la venta. Sin Excel (Beccar/Paz ene–may) se reparte por días (ej. 29/12–04/01: 4/7 a enero). La nota de cada fila dice qué semanas se partieron y con qué %.

## Rappi (Florida = "La Presumida Pastas - Florida", Beccar = "La Presumida Pastas"; Paz no tiene Rappi)

- **Ene–jul**: `Rappi_Report_AAAA-MM-01_AAAA-MM-fin.xlsx`, hoja Detalle (la hoja Resumen viene en cero porque son fórmulas sin calcular).
  - facturado = col R "Venta Bruta" + col T "Descuento de Producto asumido por el aliado", filas ORDEN.
  - depositado = "Valor total a transferir" = suma de columnas R a CK de **todas** las filas (órdenes, compensaciones, EXTRA SERVICE = RappiAds, filas de impuestos globales y descuentos DAR), sin la col AQ (subtotal).
  - pedidos = filas con Tipo de transacción = ORDEN. se_queda = facturado − depositado.
  - Control: con este método el sales-report de Florida 01–15/09 da 181 pedidos, $4.512.000 y $2.938.441, igual al peso que la hoja Liquidaciones.
  - Archivos de julio duplicados (mismo paidlot) se contaron una sola vez.
- **Ago–sep**: hoja Liquidaciones de `peya/ago/apps.xlsx` (2 quincenas por mes, mes calendario).
- **Octubre: ESTIMADO**. Todavía no hay liquidación. facturado y pedidos = pedidos "Terminada" del historial de pedidos de Rappi (`apps3031/rappi.xlsx`, 01–31/10); se_queda y depositado con el % de septiembre de cada local. `completo=false`.

## Huecos

| Mes | Local / app | Qué falta |
|---|---|---|
| Feb | Florida Rappi | El reporte cubre 01–22/02. Faltan 23–28/02 (según el historial de Rappi: 73 pedidos, $1.292.900, no sumados) |
| May | Paz PedidosYa | No está el estado de cuenta 25–31/05 de la cuenta 370256 en Drive (solo está la factura de comisión) |
| Oct | las 3 / PedidosYa | Falta la semana 26/10–01/11 (todavía no liquidada) → octubre = 01 al 25/10 |
| Oct | Florida y Beccar / Rappi | Sin liquidación: estimado (ver arriba) |
| Ene–may | Beccar y Paz PedidosYa | Plata exacta del PDF; **pedidos estimados** |
| Sep | Florida PedidosYa | Semana 14–20/09 sin Excel: sus 456 pedidos son estimados (plata exacta) |

## Validación contra apps_liq.json (agosto y septiembre)

apps_liq.json **no usa mes calendario para PedidosYa**: "Agosto" = 4 semanas 03/08–30/08 y "Septiembre" = 4 semanas 31/08–27/09 (Rappi sí es mes calendario).
- Con el **mismo período de 4 semanas**, PedidosYa coincide al peso en los 3 locales (venta, depósito, se_queda y pedidos: diferencia 0,0%). Rappi coincide al peso.
- En **mes calendario** (lo que trae este archivo), PedidosYa da entre 8% y 12% más que apps_liq porque suma los días que el período de 4 semanas deja afuera (agosto suma 01–02 y 31/08; septiembre suma 28–30/09 y deja el 31/08 en agosto). No es un error: es otro período. Detalle en `scratchpad/apps_cierres/validacion.json`.

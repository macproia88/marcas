"""Genera las tiendas online de La Presumida (Florida + Beccar) y Pastas Paz (Olivos).
Uso: python3 tienda/generar.py
Precios: lista de precios de Maxi Rest (tienda/lista_precios.json, archivo precios_articulos que pasó Juan el 18/11/2026).
Si un código no está en la lista, se usa la mediana de lo cobrado en los cierres o el precio fijo de abajo.
"""
import json, pathlib, statistics, datetime, collections, html

RAIZ = pathlib.Path(__file__).resolve().parent.parent
CIERRES = RAIZ / 'tablero-auto' / 'data' / 'cierres.json'

# (categoria, codigo Maxi Rest o None, nombre, descripcion, unidad, precio de respaldo)
# unidad: 'caja', 'kg', 'u', 'chica', 'mediana', 'porción', 'docena', ''
CAT_LP = [
 ('Ravioles', 7, 'Ravioles de ricota', 'Caja de ravioles caseros', 'caja', 6500),
 ('Ravioles', 8, 'Ravioles de ricota y verdura', 'Caja de ravioles caseros', 'caja', 6500),
 ('Ravioles', 9, 'Ravioles de ricota, jamón y nuez', 'Caja de ravioles caseros', 'caja', 6500),
 ('Ravioles', 10, 'Ravioles de pollo y verdura', 'Caja de ravioles caseros', 'caja', 6500),
 ('Ravioles', 11, 'Ravioles de pavita, jamón y provolone', 'Caja de ravioles caseros', 'caja', 6500),
 ('Ravioles', 14, 'Ravioles de masa verde', 'Masa de espinaca, relleno de ricota', 'caja', 6500),
 ('Raviolones', 17, 'Raviolones de calabaza y muzzarella', 'Rellenos generosos', 'caja', 7600),
 ('Raviolones', 15, 'Raviolones cuatro quesos', 'Rellenos generosos', 'caja', 7600),
 ('Raviolones', 16, 'Raviolones de pollo y verdura', 'Rellenos generosos', 'caja', 7600),
 ('Raviolones', 18, 'Raviolones de ricota y albahaca', 'Rellenos generosos', 'caja', 7600),
 ('Raviolones', 380, 'Raviolones de cordero', 'Rellenos generosos', 'caja', 7600),
 ('Raviolones', 19, 'Raviolones de salmón', 'Rellenos generosos', 'caja', 15200),
 ('Sorrentinos y rellenas', 29, 'Sorrentinos de jamón y queso', 'Se venden por peso', 'kg', 30400),
 ('Sorrentinos y rellenas', 32, 'Panzottis de espinaca y port salut', '', 'caja', 8400),
 ('Sorrentinos y rellenas', 1163, 'Capelettinis cuatro quesos', '', 'kg', 18900),
 ('Sorrentinos y rellenas', 1164, 'Capelettinis de pollo', '', 'kg', 17800),
 ('Sorrentinos y rellenas', 30, 'Tortelettis', '', '', 18700),
 ('Ñoquis', 23, 'Ñoquis de papa', 'Se venden por peso', 'kg', 13000),
 ('Ñoquis', 2403, 'Ñoquis de espinaca', 'Se venden por peso', 'kg', 13000),
 ('Ñoquis', 2404, 'Ñoquis de calabaza', 'Se venden por peso', 'kg', 13000),
 ('Ñoquis', 2414, 'Ñoquis tricolor', 'Se venden por peso', 'kg', 13000),
 ('Ñoquis', 24, 'Ñoquis romanos', 'De sémola, para gratinar', '', 17000),
 ('Ñoquis', 25, 'Ñoquis romanos con jamón y queso', 'De sémola, para gratinar', '', 20000),
 ('Fideos', 2, 'Fideos caseros al huevo', 'Se venden por peso', 'kg', 13000),
 ('Fideos', 2205, 'Cinta ancha', 'Se venden por peso', 'kg', 13000),
 ('Fideos', 2204, 'Media cinta', 'Se venden por peso', 'kg', 13000),
 ('Fideos', 2203, 'Cordón al huevo', 'Se venden por peso', 'kg', 13000),
 ('Fideos', 2202, 'Finitos al huevo', 'Se venden por peso', 'kg', 13000),
 ('Fideos', 4, 'Fusiles al huevo', 'Se venden por peso', 'kg', 13000),
 ('Fideos', 2217, 'Fusiles tricolor', 'Se venden por peso', 'kg', 13000),
 ('Fideos', 2216, 'Fusiles de espinaca', 'Se venden por peso', 'kg', 13000),
 ('Fideos', 5, 'Macarrones', 'Se venden por peso', 'kg', 13000),
 ('Fideos', 6, 'Mostacholes', 'Se venden por peso', 'kg', 13000),
 ('Fideos', 3, 'Papardelle', 'Se venden por peso', 'kg', 13000),
 ('Canelones y lasagna', 21, 'Canelones de ricota y verdura', 'Para hornear', 'u', 3000),
 ('Canelones y lasagna', 286, 'Canelones de pollo', 'Para hornear', 'u', 3000),
 ('Canelones y lasagna', 287, 'Canelones de espinaca', 'Para hornear', 'u', 3000),
 ('Canelones y lasagna', 288, 'Canelones de pavita', 'Para hornear', 'u', 3000),
 ('Canelones y lasagna', 2324, 'Canelones con salsa', 'Bandeja lista para el horno', 'kg', 23300),
 ('Canelones y lasagna', 26, 'Lasagna de ricota', 'Para hornear', 'u', 9200),
 ('Canelones y lasagna', 275, 'Lasagna de muzzarella', 'Para hornear', 'u', 9200),
 ('Canelones y lasagna', 2319, 'Lasagna con salsa', 'Bandeja lista para el horno', 'kg', 24900),
 ('Canelones y lasagna', 20, 'Panqueques', 'Para canelones', 'docena', 6800),
 ('Salsas', 50, 'Fileto', 'Hecha por nosotros', 'chica', 4200),
 ('Salsas', 255, 'Fileto', 'Hecha por nosotros', 'mediana', 5800),
 ('Salsas', 51, 'Bolognesa', 'Hecha por nosotros', 'chica', 5000),
 ('Salsas', 363, 'Bolognesa', 'Hecha por nosotros', 'mediana', 6400),
 ('Salsas', 54, 'Pomarola', 'Hecha por nosotros', 'chica', 5000),
 ('Salsas', 264, 'Pomarola', 'Hecha por nosotros', 'mediana', 6400),
 ('Salsas', 276, 'Blanca', 'Hecha por nosotros', 'chica', 4200),
 ('Salsas', 254, 'Blanca', 'Hecha por nosotros', 'mediana', 5800),
 ('Salsas', 280, 'Cuatro quesos', 'Hecha por nosotros', 'chica', 5000),
 ('Salsas', 262, 'Cuatro quesos', 'Hecha por nosotros', 'mediana', 6400),
 ('Salsas', 279, 'Champignon', 'Hecha por nosotros', 'chica', 5000),
 ('Salsas', 379, 'Mixta o rosa', 'Hecha por nosotros', 'chica', 4200),
 ('Salsas', 56, 'Pesto', 'Hecha por nosotros', '', 8200),
 ('Salsas', 258, 'Estofado de pollo', 'Hecha por nosotros', 'mediana', 6400),
 ('Salsas', 256, 'Estofado de carne', 'Hecha por nosotros', 'mediana', 6400),
 ('Salsas', 98, 'Queso rallado', '', 'chico', 5000),
 ('Salsas', 99, 'Queso rallado', '', 'grande', 9500),
 ('Listas para comer', 34, 'Porción de ravioles con salsa', 'Caliente, para llevar', 'porción', 11500),
 ('Listas para comer', 42, 'Porción de ñoquis con salsa', 'Caliente, para llevar', 'porción', 11500),
 ('Listas para comer', 33, 'Porción de fideos caseros con salsa', 'Caliente, para llevar', 'porción', 13500),
 ('Listas para comer', 36, 'Porción de canelones', 'Caliente, para llevar', 'porción', 16700),
 ('Listas para comer', 39, 'Porción de sorrentinos con salsa', 'Caliente, para llevar', 'porción', 17700),
 ('Listas para comer', 27, 'Lasagna con salsa', 'Caliente, para llevar', 'porción', 20000),
 ('Listas para comer', 437, 'Menú pastas', 'Menú del día', '', 7500),
 ('Listas para comer', 376, 'Menú mix de ravioles', 'Menú del día', '', 6000),
 ('Listas para comer', 337, 'Menú económico', 'Menú del día', '', 6000),
 ('Listas para comer', 177, 'Menú risotto', 'Menú del día', '', 8500),
 ('Rotisería', 107, 'Pollo al horno', 'Se vende por peso', 'kg', 23000),
 ('Rotisería', 217, 'Cuarto de pollo', '', 'u', 7500),
 ('Rotisería', 294, 'Suprema napolitana', 'Se vende por peso', 'kg', 30800),
 ('Rotisería', 105, 'Suprema', 'Se vende por peso', 'kg', 31100),
 ('Rotisería', 350, 'Bastones de pollo', 'Se vende por peso', 'kg', 25000),
 ('Rotisería', 233, 'Milanesa de berenjena', 'Se vende por peso', 'kg', 19600),
 ('Rotisería', 113, 'Pastel de papas', 'Se vende por peso', 'kg', 29000),
 ('Rotisería', 101, 'Tortilla de papa', 'Se vende por peso', 'kg', 22700),
 ('Rotisería', 100, 'Tortilla de acelga', 'Se vende por peso', 'kg', 23000),
 ('Rotisería', 115, 'Bomba de papa', 'Se vende por peso', 'kg', 22800),
 ('Rotisería', 211, 'Buñuelos de acelga', 'Se vende por peso', 'kg', 26700),
 ('Rotisería', 166, 'Berenjena rellena', 'Se vende por peso', 'kg', 28800),
 ('Rotisería', 232, 'Zapallito relleno', 'Se vende por peso', 'kg', 22300),
 ('Rotisería', 238, 'Albóndigas con tuco', 'Se vende por peso', 'kg', 29600),
 ('Rotisería', 110, 'Arrollado primavera', 'Se vende por peso', 'kg', 31400),
 ('Rotisería', 106, 'Matambre relleno', 'Se vende por peso', 'kg', 70000),
 ('Rotisería', 128, 'Vitel toné', 'Se vende por peso', 'kg', 55600),
 ('Tartas y empanadas', 131, 'Tarta de verdura', 'Individual', 'u', 9000),
 ('Tartas y empanadas', 134, 'Tarta de jamón y queso', 'Individual', 'u', 9000),
 ('Tartas y empanadas', 130, 'Tarta de calabaza', 'Individual', 'u', 9000),
 ('Tartas y empanadas', 136, 'Tarta de pollo', 'Individual', 'u', 9000),
 ('Tartas y empanadas', 133, 'Tarta de puerro', 'Individual', 'u', 9000),
 ('Tartas y empanadas', 135, 'Tarta de zapallito', 'Individual', 'u', 9000),
 ('Tartas y empanadas', 121, 'Tarta de berenjena', 'Individual', 'u', 9000),
 ('Tartas y empanadas', 422, 'Tarta de queso y cebolla', 'Individual', 'u', 9000),
 ('Tartas y empanadas', 396, 'Tarta grande de verdura', 'Grande', 'kg', 26400),
 ('Tartas y empanadas', 140, 'Tarta grande de jamón y queso', 'Grande', 'kg', 29700),
 ('Tartas y empanadas', 470, 'Tarta grande de pollo', 'Grande', 'kg', 31100),
 ('Tartas y empanadas', 124, 'Empanada de carne', '', 'u', 2800),
 ('Tartas y empanadas', 125, 'Empanada de pollo', '', 'u', 2800),
 ('Tartas y empanadas', 126, 'Empanada de jamón y queso', '', 'u', 2800),
 ('Tartas y empanadas', 222, 'Empanada de humita', '', 'u', 2800),
 ('Tartas y empanadas', 129, 'Empanada de espinaca', '', 'u', 2800),
 ('Tartas y empanadas', 127, 'Empanada de cebolla', '', 'u', 2800),
 ('Tartas y empanadas', 94, 'Pizza de muzzarella', '', 'u', 14500),
 ('Tartas y empanadas', 95, 'Pizza de jamón y morrones', '', 'u', 17800),
 ('Postres', 203, 'Flan casero', '', 'u', 4000),
 ('Postres', 229, 'Budín de pan', '', '', 12600),
 ('Postres', 370, 'Mousse', '', 'u', 4300),
 ('Postres', 476, 'Strudel', '', 'u', 6000),
 ('Sin TACC', 2704, 'Sorrentinos sin TACC', 'Congelados', '', 15100),
 ('Sin TACC', 2701, 'Fideos sin TACC', 'Congelados', '', 12200),
 ('Sin TACC', 2706, 'Ñoquis sin TACC', 'Congelados', '', 12200),
 ('Bebidas', 180, 'Coca-Cola 500 ml', '', 'u', 2900),
 ('Bebidas', 181, 'Coca-Cola 1,75 l', '', 'u', 6500),
 ('Bebidas', 183, 'Agua 500 ml', '', 'u', 2900),
 ('Bebidas', 184, 'Agua 1,5 l', '', 'u', 4000),
]

CAT_PZ = [
 ('Ravioles', 7, 'Ravioles de ricota', 'Caja de ravioles caseros', 'caja', 6500),
 ('Ravioles', 8, 'Ravioles de ricota y verdura', 'Caja de ravioles caseros', 'caja', 6500),
 ('Ravioles', 11, 'Ravioles de pavita, jamón y provolone', 'Caja de ravioles caseros', 'caja', 6500),
 ('Ravioles', 2101, 'Ravioles de pollo y jamón', 'Caja de ravioles caseros', 'caja', 6400),
 ('Raviolones', 2151, 'Raviolones caseros de verdura', 'Rellenos generosos', 'caja', 7600),
 ('Raviolones', 2152, 'Raviolones caseros de ricota', 'Rellenos generosos', 'caja', 7600),
 ('Raviolones', 2153, 'Raviolones caseros de pavita', 'Rellenos generosos', 'caja', 7600),
 ('Raviolones', 2155, 'Raviolones caseros de boniato', 'Rellenos generosos', 'caja', 7600),
 ('Raviolones', 2156, 'Raviolones caseros de cheddar', 'Rellenos generosos', 'caja', 7600),
 ('Raviolones', 2154, 'Raviolones caseros de berenjena', 'Rellenos generosos', 'caja', 7600),
 ('Sorrentinos y rellenas', 29, 'Sorrentinos de jamón y queso', 'Se venden por peso', 'kg', 31000),
 ('Sorrentinos y rellenas', 2309, 'Sorrentinos de espinaca', 'Se venden por peso', 'kg', 28400),
 ('Sorrentinos y rellenas', 28, 'Sorrentinos light', 'Se venden por peso', 'kg', 24100),
 ('Sorrentinos y rellenas', 4012, 'Panzottis de calabaza', '', 'caja', 8400),
 ('Sorrentinos y rellenas', 1163, 'Capelettinis cuatro quesos', '', 'kg', 18300),
 ('Sorrentinos y rellenas', 1164, 'Capelettinis de pollo', '', 'kg', 17700),
 ('Sorrentinos y rellenas', 30, 'Tortelettis', '', '', 19000),
 ('Ñoquis', 23, 'Ñoquis de papa', 'Se venden por peso', 'kg', 13000),
 ('Ñoquis', 2403, 'Ñoquis de espinaca', 'Se venden por peso', 'kg', 13000),
 ('Ñoquis', 2404, 'Ñoquis de calabaza', 'Se venden por peso', 'kg', 13000),
 ('Ñoquis', 2414, 'Ñoquis tricolor', 'Se venden por peso', 'kg', 13000),
 ('Ñoquis', 2406, 'Ñoquis de muzzarella', '', '', 19000),
 ('Ñoquis', 2405, 'Ñoquis precocidos', '', '', 20000),
 ('Ñoquis', 24, 'Ñoquis romanos', 'De sémola, para gratinar', '', 18000),
 ('Ñoquis', 25, 'Ñoquis romanos con jamón y queso', 'De sémola, para gratinar', '', 18800),
 ('Fideos', 2207, 'Fideos caseros', 'Se venden por peso', 'kg', 16000),
 ('Fideos', 2205, 'Cinta ancha', 'Se venden por peso', 'kg', 13000),
 ('Fideos', 2204, 'Media cinta', 'Se venden por peso', 'kg', 13000),
 ('Fideos', 2203, 'Cordón al huevo', 'Se venden por peso', 'kg', 13000),
 ('Fideos', 2202, 'Finitos al huevo', 'Se venden por peso', 'kg', 13000),
 ('Fideos', 4, 'Fusiles al huevo', 'Se venden por peso', 'kg', 13000),
 ('Fideos', 2217, 'Fusiles tricolor', 'Se venden por peso', 'kg', 13000),
 ('Fideos', 2218, 'Fusiles de morrón', 'Se venden por peso', 'kg', 13000),
 ('Fideos', 5, 'Macarrones', 'Se venden por peso', 'kg', 13000),
 ('Fideos', 6, 'Mostacholes', 'Se venden por peso', 'kg', 13000),
 ('Fideos', 2209, 'Penetas', 'Se venden por peso', 'kg', 13000),
 ('Canelones y lasagna', 21, 'Canelones de ricota y verdura', 'Para hornear', 'u', 3000),
 ('Canelones y lasagna', 286, 'Canelones de pollo', 'Para hornear', 'u', 3000),
 ('Canelones y lasagna', 287, 'Canelones de espinaca', 'Para hornear', 'u', 3000),
 ('Canelones y lasagna', 2324, 'Canelones con salsa', 'Bandeja lista para el horno', 'kg', 24000),
 ('Canelones y lasagna', 2318, 'Lasagna con salsa', 'Bandeja lista para el horno', 'kg', 21800),
 ('Salsas', 50, 'Fileto', 'Hecha por nosotros', 'chica', 4200),
 ('Salsas', 255, 'Fileto', 'Hecha por nosotros', 'mediana', 5800),
 ('Salsas', 51, 'Bolognesa', 'Hecha por nosotros', 'chica', 5000),
 ('Salsas', 363, 'Bolognesa', 'Hecha por nosotros', 'mediana', 6400),
 ('Salsas', 54, 'Pomarola', 'Hecha por nosotros', 'chica', 5000),
 ('Salsas', 264, 'Pomarola', 'Hecha por nosotros', 'mediana', 6400),
 ('Salsas', 276, 'Blanca', 'Hecha por nosotros', 'chica', 4200),
 ('Salsas', 254, 'Blanca', 'Hecha por nosotros', 'mediana', 5800),
 ('Salsas', 280, 'Cuatro quesos', 'Hecha por nosotros', 'chica', 5000),
 ('Salsas', 262, 'Cuatro quesos', 'Hecha por nosotros', 'mediana', 6400),
 ('Salsas', 279, 'Champignon', 'Hecha por nosotros', 'chica', 5000),
 ('Salsas', 379, 'Mixta o rosa', 'Hecha por nosotros', 'chica', 4200),
 ('Salsas', 56, 'Pesto', 'Hecha por nosotros', '', 8200),
 ('Salsas', 98, 'Queso rallado', '', 'chico', 5000),
 ('Salsas', 99, 'Queso rallado', '', 'grande', 9500),
 ('Listas para comer', 34, 'Porción de ravioles con salsa', 'Caliente, para llevar', 'porción', 11500),
 ('Listas para comer', 42, 'Porción de ñoquis con salsa', 'Caliente, para llevar', 'porción', 11500),
 ('Listas para comer', 39, 'Porción de sorrentinos con salsa', 'Caliente, para llevar', 'porción', 12900),
 ('Listas para comer', 437, 'Menú pastas', 'Menú del día', '', 7500),
 ('Listas para comer', 376, 'Menú mix de ravioles', 'Menú del día', '', 6000),
 ('Listas para comer', 177, 'Menú risotto', 'Menú del día', '', 8400),
 ('Rotisería', 107, 'Pollo al horno', 'Se vende por peso', 'kg', 23000),
 ('Rotisería', 217, 'Cuarto de pollo', '', 'u', 7500),
 ('Rotisería', 294, 'Suprema napolitana', 'Se vende por peso', 'kg', 30200),
 ('Rotisería', 105, 'Suprema', 'Se vende por peso', 'kg', 31400),
 ('Rotisería', 350, 'Bastones de pollo', 'Se vende por peso', 'kg', 26000),
 ('Rotisería', 113, 'Pastel de papas', 'Se vende por peso', 'kg', 28600),
 ('Rotisería', 101, 'Tortilla de papa', 'Se vende por peso', 'kg', 21900),
 ('Rotisería', 115, 'Bomba de papa', 'Se vende por peso', 'kg', 23200),
 ('Rotisería', 211, 'Buñuelos de acelga', 'Se vende por peso', 'kg', 27300),
 ('Rotisería', 166, 'Berenjena rellena', 'Se vende por peso', 'kg', 27800),
 ('Rotisería', 238, 'Albóndigas con tuco', 'Se vende por peso', 'kg', 29100),
 ('Rotisería', 110, 'Arrollado primavera', 'Se vende por peso', 'kg', 31200),
 ('Rotisería', 106, 'Matambre relleno', 'Se vende por peso', 'kg', 67400),
 ('Rotisería', 128, 'Vitel toné', 'Se vende por peso', 'kg', 56800),
 ('Tartas y empanadas', 131, 'Tarta de verdura', 'Individual', 'u', 9000),
 ('Tartas y empanadas', 134, 'Tarta de jamón y queso', 'Individual', 'u', 9000),
 ('Tartas y empanadas', 130, 'Tarta de calabaza', 'Individual', 'u', 9000),
 ('Tartas y empanadas', 136, 'Tarta de pollo', 'Individual', 'u', 9000),
 ('Tartas y empanadas', 121, 'Tarta de berenjena', 'Individual', 'u', 9000),
 ('Tartas y empanadas', 2654, 'Tarta caprese', 'Individual', 'u', 8700),
 ('Tartas y empanadas', 2651, 'Tarta de brócoli', 'Individual', 'u', 8900),
 ('Tartas y empanadas', 2652, 'Tarta de champignon', 'Individual', 'u', 8800),
 ('Tartas y empanadas', 396, 'Tarta grande de verdura', 'Grande', 'kg', 26000),
 ('Tartas y empanadas', 470, 'Tarta grande de pollo', 'Grande', 'kg', 31200),
 ('Tartas y empanadas', 124, 'Empanada de carne', '', 'u', 2800),
 ('Tartas y empanadas', 125, 'Empanada de pollo', '', 'u', 2800),
 ('Tartas y empanadas', 126, 'Empanada de jamón y queso', '', 'u', 2800),
 ('Tartas y empanadas', 222, 'Empanada de humita', '', 'u', 2800),
 ('Tartas y empanadas', 129, 'Empanada de espinaca', '', 'u', 2800),
 ('Tartas y empanadas', 127, 'Empanada de cebolla', '', 'u', 2800),
 ('Tartas y empanadas', 313, 'Empanada caprese', '', 'u', 2800),
 ('Tartas y empanadas', 2606, 'Empanada de roquefort', '', 'u', 2800),
 ('Tartas y empanadas', 94, 'Pizza de muzzarella', '', 'u', 14500),
 ('Tartas y empanadas', 95, 'Pizza de jamón y morrones', '', 'u', 17800),
 ('Postres', 203, 'Flan casero', '', 'u', 4000),
 ('Postres', 229, 'Budín de pan', '', '', 12900),
 ('Postres', 370, 'Mousse', '', 'u', 4300),
 ('Postres', 476, 'Strudel', '', 'u', 6000),
 ('Sin TACC', 2704, 'Sorrentinos sin TACC', 'Congelados', '', 15500),
 ('Sin TACC', 2701, 'Fideos sin TACC', 'Congelados', '', 11000),
 ('Sin TACC', 2706, 'Ñoquis sin TACC', 'Congelados', '', 11000),
 ('Bebidas', 180, 'Coca-Cola 500 ml', '', 'u', 2900),
 ('Bebidas', 1033, 'Coca-Cola Zero 500 ml', '', 'u', 2900),
 ('Bebidas', 1046, 'Sprite 500 ml', '', 'u', 2900),
]

DESC_WEB = 0.10  # descuento pidiendo por la web (retiro en el local)

IMG = {'Ravioles': 'ravioles', 'Raviolones': 'raviolones', 'Sorrentinos y rellenas': 'sorrentinos',
       'Ñoquis': 'noquis', 'Fideos': 'fideos', 'Listas para comer': 'cocidas', 'Canelones y lasagna': 'cocidas'}

MARCAS = {
 'presumida': dict(
   archivo='tienda-presumida.html', grupo='LP', catalogo=CAT_LP,
   nombre='La Presumida', titulo='La Presumida · Pedí online', slogan='Rica, fresca y casera',
   sub='Pastas frescas de elaboración diaria en Florida y Beccar',
   anuncio='<b>10% OFF pidiendo por la web</b> · Retirás en el local sin esperar · Socios del club: 1 kg de fideos de regalo en tu primera compra',
   hero=[('2','locales en zona norte'),('100+','productos caseros'),('7','días a la semana')],
   colores=dict(fondo='#FBF5EE', fondo2='#F3E6DC', marca='#7A2735', marca2='#5E1C28', acento='#C9A04E',
                rosa='#E9C9C3', tinta='#3A2A26', suave='#7C6A62'),
   logo='tienda/img/logo-lp.jpg', logo_txt='',
   instagram='https://www.instagram.com/lapresumidapastas',
   club=dict(nombre='Club La Presumida', link='https://alax.tech/landing/160-la-presumida',
             texto='Registrate gratis, mostrá tu DNI en caja y recibí promos exclusivas para socios en cada compra.',
             regalo='1 kg de fideos gratis en tu primera compra de más de $10.000.'),
   locales=[
     dict(id='florida', nombre='Florida', dir='Gral. J. de San Martín 2207, Florida', tel='011 4796-4591',
          telraw='+541147964591', wa='5491165464546', watxt='11 6546-4546', mapa='La Presumida, Gral. José de San Martín 2207, Florida, Buenos Aires',
          horario=[('Lunes a sábado', '9 a 22 hs'), ('Domingos y feriados', '9 a 14 hs')]),
     dict(id='beccar', nombre='Beccar', dir='Juan B. Justo 201, Beccar', tel='011 4742-0149',
          telraw='+541147420149', wa='5491144010033', watxt='11 4401-0033', mapa='La Presumida, Juan B. Justo 201, Beccar, Buenos Aires',
          horario=[('Lunes a sábado', '9 a 20 hs'), ('Domingos y feriados', '9 a 14 hs')]),
   ]),
 'paz': dict(
   archivo='tienda-paz.html', grupo='PZ', catalogo=CAT_PZ,
   nombre='Pastas Paz', titulo='Pastas Paz · Pedí online', slogan='Pastas frescas en Olivos',
   sub='El clásico de Olivos hace 25 años: pastas frescas, salsas y comidas caseras',
   anuncio='<b>10% OFF pidiendo por la web</b> · Retirás en el local sin esperar · Socios del Paz Club: regalo en tu primera compra',
   hero=[('25','años en Olivos'),('100+','productos caseros'),('7','días a la semana')],
   colores=dict(fondo='#F6F7FA', fondo2='#E6EAF2', marca='#1B2A4A', marca2='#121D35', acento='#D2322D',
                rosa='#F4D5D3', tinta='#1E2533', suave='#5D6679'),
   logo='', logo_txt='Paz',
   instagram='https://www.instagram.com/pastaspaz/',
   club=dict(nombre='Paz Club', link='https://alax.tech/landing/162-pastas-paz',
             texto='Registrate gratis, mostrá tu DNI en caja y recibí promos exclusivas para socios en cada compra.',
             regalo='1 kg de fideos caseros gratis al sumarte, con tu primera compra.'),
   locales=[
     dict(id='olivos', nombre='Olivos', dir='Ricardo Gutiérrez 1186, Olivos', tel='011 4711-5152 / 5251',
          telraw='+541147115152', wa='5491172161020', watxt='11 7216-1020', mapa='Pastas Frescas Paz, Ricardo Gutiérrez 1186, Olivos, Buenos Aires',
          horario=[('Lunes a sábado', '9 a 20 hs'), ('Domingos y feriados', '9 a 14 hs')]),
   ]),
}


def precios_reales(grupo):
    d = json.loads(CIERRES.read_text())
    ult = max(r['fecha'] for r in d)
    desde = (datetime.date.fromisoformat(ult) - datetime.timedelta(days=10)).isoformat()
    P = collections.defaultdict(list)
    for r in d:
        g = 'PZ' if 'paz' in r['sucursal'].lower() else 'LP'
        if g != grupo or r['fecha'] < desde:
            continue
        for c, n, rub, q, imp in r['articulos']:
            if q > 0 and imp > 0:
                P[c].append(imp / q)
    return {c: round(statistics.median(v) / 100) * 100 for c, v in P.items() if len(v) >= 2}, ult


def armar(clave):
    m = MARCAS[clave]
    reales, ult = precios_reales(m['grupo'])
    lista = {int(k): v for k, v in json.loads((RAIZ / 'tienda' / 'lista_precios.json').read_text()).items()}
    prods = []
    for i, (cat, cod, nom, desc, uni, pr) in enumerate(m['catalogo']):
        prods.append(dict(id=i, cat=cat, n=nom, d=desc, u=uni, p=round(lista.get(cod) or reales.get(cod, pr)), img=IMG.get(cat, '')))
    cats = list(dict.fromkeys(p['cat'] for p in prods))
    ahora = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3)))
    datos = dict(marca=m['nombre'], locales=m['locales'], prods=prods, cats=cats, clave=clave, desc=DESC_WEB)
    c = m['colores']
    tpl = (RAIZ / 'tienda' / 'plantilla.html').read_text()
    reemplazos = {
        '{{TITULO}}': m['titulo'], '{{NOMBRE}}': m['nombre'], '{{SLOGAN}}': m['slogan'], '{{SUB}}': m['sub'],
        '{{DATOS}}': json.dumps(datos, ensure_ascii=False),
        '{{ACT}}': ahora.strftime('%d/%m/%Y %H:%M'),
        '{{LOGO}}': (f'<img src="{m["logo"]}" alt="{m["nombre"]}" class="logo-img">' if m['logo']
                     else f'<span class="logo-txt">{m["logo_txt"]}</span><span class="logo-sub">pastas<br>frescas</span>'),
        '{{CLUB_NOMBRE}}': m['club']['nombre'], '{{CLUB_TEXTO}}': m['club']['texto'], '{{CLUB_REGALO}}': m['club']['regalo'],
        '{{CLUB_BTN}}': (f'<a class="btn btn-claro" href="{m["club"]["link"]}" target="_blank" rel="noopener">Quiero ser socio</a>'
                         if m['club']['link'] else '<span class="btn btn-claro">Pedí el QR en el local</span>'),
        '{{IG_URL}}': m['instagram'], '{{IG_USER}}': m['instagram'].rstrip('/').split('/')[-1], '{{ANUNCIO}}': m['anuncio'],
        '{{DATOS_HERO}}': ''.join(f'<div><b>{a}</b>{b}</div>' for a, b in m['hero']),
        '{{LOCALES_TXT}}': ' y '.join(l['nombre'] for l in m['locales']),
    }
    for k, v in c.items():
        reemplazos['{{C_%s}}' % k.upper()] = v
    for k, v in reemplazos.items():
        tpl = tpl.replace(k, v)
    (RAIZ / m['archivo']).write_text(tpl)
    print(m['archivo'], len(prods), 'productos;', sum(1 for i, x in enumerate(m['catalogo']) if x[1] in reales),
          'con precio de la lista de Maxi Rest:', sum(1 for x in m['catalogo'] if x[1] in lista))


if __name__ == '__main__':
    for k in MARCAS:
        armar(k)

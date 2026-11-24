# Formulario de inscripción - Escuela Taller Fátima

- Formulario público: https://macproia88.github.io/marcas/clientes/tallerfatima/inscripcion/
- Base de datos: una planilla de Google Sheets.
  - Hoja "Todas las inscripciones": todas juntas.
  - Una hoja por curso (se crea sola con la primera inscripción de ese curso).
  - Fotos del DNI (frente y dorso) en Drive: carpeta "Inscripciones Taller Fátima - Fotos DNI", con una subcarpeta por curso. Si alguien elige dos cursos, en el segundo queda un acceso directo.
- Cursos (sacados de las carpetas del banco de fotos 2026): Carpintería Jóvenes, Carpintería Adultos, Costura, Soldadura, Manicuría, Cocina, Informática, Operador Sociocomunitario, Emprendedurismo. Confirmar con Ana.

## Conectar la planilla (una sola vez, 5 minutos)

1. Con la cuenta de Google del taller, crear una planilla nueva: "Inscripciones Taller Fátima".
2. Menú **Extensiones > Apps Script**. Borrar lo que haya y pegar todo el contenido de `planilla.gs`. Guardar.
3. Arriba elegir la función `prueba` y tocar **Ejecutar**. Google pide permisos: aceptar ("Configuración avanzada > Ir a…" si avisa que la app no está verificada). Tienen que aparecer una fila de prueba (en "Todas las inscripciones" y en "Carpintería Adultos") y la carpeta de fotos en Drive. Borrar la prueba.
4. **Implementar > Nueva implementación > Tipo: Aplicación web.**
   - Ejecutar como: **Yo**
   - Quién tiene acceso: **Cualquier usuario**
   - Implementar y copiar la URL que termina en `/exec`.
5. Pegar esa URL en `index.html`, en la línea `const SCRIPT_URL = "";`, y publicar. El cartel amarillo de "Modo prueba" desaparece solo.

Opcional: en `planilla.gs`, poner un mail en `AVISAR_A` para recibir un aviso por cada inscripción.

## Cómo se usa la planilla

- Las fotos del DNI quedan privadas en el Drive de la cuenta del taller: no las ve nadie más.
- La columna **Estado** tiene una lista: Nuevo, Contactado, Inscripto, En espera, No sigue.
- La columna **Notas del taller** es libre.
- Para cambiar los talleres del formulario: editar la lista `TALLERES` en `index.html`.
- Si alguien es menor de 18, el formulario pide los datos de un adulto responsable.

/**
 * Base de datos de inscripciones - Escuela Taller Fátima
 * Va pegado en la planilla de Google: Extensiones > Apps Script.
 * Cada inscripción del formulario se agrega como una fila nueva en la hoja "Inscripciones".
 */

const HOJA = "Inscripciones";
// Mail que recibe un aviso con cada inscripción nueva. Dejar vacío ("") para no recibir avisos.
const AVISAR_A = "";

const COLUMNAS = [
  ["fecha", "Fecha de inscripción"],
  ["nombre", "Nombre"], ["apellido", "Apellido"], ["dni", "DNI"],
  ["nacimiento", "Fecha de nacimiento"], ["edad", "Edad"],
  ["telefono", "Celular / WhatsApp"], ["email", "Email"],
  ["localidad", "Localidad / Barrio"], ["direccion", "Dirección"],
  ["talleres", "Talleres"], ["turnos", "Horarios"],
  ["estudios", "Estudios"], ["trabaja", "¿Trabaja?"], ["experiencia", "Experiencia"],
  ["conociste", "¿Cómo nos conoció?"], ["comentarios", "Comentarios"],
  ["adulto_nombre", "Adulto responsable"], ["adulto_telefono", "Cel. adulto"], ["adulto_vinculo", "Vínculo"],
  ["estado", "Estado"], ["notas", "Notas del taller"]
];

function doPost(e) {
  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const hoja = prepararHoja_();
    const p = e.parameter || {};
    p.fecha = Utilities.formatDate(new Date(), "America/Argentina/Buenos_Aires", "dd/MM/yyyy HH:mm");
    p.estado = "Nuevo";
    const fila = COLUMNAS.map(([k]) => limpiar_(p[k]));
    hoja.appendRow(fila);
    if (AVISAR_A) {
      MailApp.sendEmail(AVISAR_A, "Nueva inscripción: " + p.nombre + " " + p.apellido,
        COLUMNAS.map(([k, t]) => t + ": " + (p[k] || "")).join("\n"));
    }
    return ContentService.createTextOutput(JSON.stringify({ ok: true })).setMimeType(ContentService.MimeType.JSON);
  } finally {
    lock.releaseLock();
  }
}

// Evita que un texto que empieza con = + - @ se tome como fórmula.
function limpiar_(v) {
  v = (v == null ? "" : String(v)).slice(0, 1000);
  return /^[=+\-@]/.test(v) ? "'" + v : v;
}

function prepararHoja_() {
  const libro = SpreadsheetApp.getActiveSpreadsheet();
  let hoja = libro.getSheetByName(HOJA);
  if (!hoja) hoja = libro.insertSheet(HOJA);
  if (hoja.getLastRow() === 0) {
    hoja.appendRow(COLUMNAS.map(([, t]) => t));
    hoja.getRange(1, 1, 1, COLUMNAS.length)
      .setFontWeight("bold").setBackground("#00894C").setFontColor("#FFFFFF");
    hoja.setFrozenRows(1);
    const col = COLUMNAS.findIndex(([k]) => k === "estado") + 1;
    const regla = SpreadsheetApp.newDataValidation()
      .requireValueInList(["Nuevo", "Contactado", "Inscripto", "En espera", "No sigue"], true).build();
    hoja.getRange(2, col, 1000, 1).setDataValidation(regla);
  }
  return hoja;
}

// Para probar desde el editor: ejecutar "prueba" y mirar que aparezca una fila.
function prueba() {
  doPost({ parameter: { nombre: "Prueba", apellido: "Test", dni: "12345678", telefono: "1100000000",
    localidad: "Tigre", talleres: "Carpintería", turnos: "Tarde", estudios: "Secundaria completa", trabaja: "No" } });
}

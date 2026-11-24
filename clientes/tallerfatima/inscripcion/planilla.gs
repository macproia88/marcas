/**
 * Base de datos de inscripciones - Escuela Taller Fátima
 * Va pegado en la planilla de Google: Extensiones > Apps Script.
 *
 * Qué hace con cada inscripción:
 *  1. La agrega a la hoja "Todas las inscripciones".
 *  2. La agrega a la hoja de cada curso que eligió (una hoja por curso, se crean solas).
 *  3. Guarda las fotos del DNI (frente y dorso) en Drive, en la carpeta
 *     "Inscripciones Taller Fátima - Fotos DNI / <Curso>". Si eligió más de un curso,
 *     en los otros cursos queda un acceso directo a las mismas fotos.
 *  4. En las hojas quedan los links a las fotos.
 */

const HOJA_GENERAL = "Todas las inscripciones";
const CARPETA_FOTOS = "Inscripciones Taller Fátima - Fotos DNI";
// Mail que recibe un aviso con cada inscripción nueva. Dejar vacío ("") para no recibir avisos.
const AVISAR_A = "";

const COLUMNAS = [
  ["fecha", "Fecha de inscripción"],
  ["nombre", "Nombre"], ["apellido", "Apellido"], ["dni", "DNI"],
  ["nacimiento", "Fecha de nacimiento"], ["edad", "Edad"],
  ["telefono", "Celular / WhatsApp"], ["email", "Email"],
  ["localidad", "Localidad / Barrio"], ["direccion", "Dirección"],
  ["talleres", "Cursos elegidos"], ["turnos", "Horarios"],
  ["foto_frente", "DNI frente"], ["foto_dorso", "DNI dorso"],
  ["estudios", "Estudios"], ["trabaja", "¿Trabaja?"], ["experiencia", "Experiencia"],
  ["conociste", "¿Cómo nos conoció?"], ["comentarios", "Comentarios"],
  ["adulto_nombre", "Adulto responsable"], ["adulto_telefono", "Cel. adulto"], ["adulto_vinculo", "Vínculo"],
  ["estado", "Estado"], ["notas", "Notas del taller"]
];
const ESTADOS = ["Nuevo", "Contactado", "Inscripto", "En espera", "No sigue"];

function doPost(e) {
  const lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    const p = e.parameter || {};
    p.fecha = Utilities.formatDate(new Date(), "America/Argentina/Buenos_Aires", "dd/MM/yyyy HH:mm");
    p.estado = "Nuevo";
    const cursos = String(p.talleres || "Sin curso").split(",").map(c => c.trim()).filter(String);

    // Fotos del DNI
    const persona = [p.apellido, p.nombre, p.dni].filter(String).join(" - ");
    const fotos = guardarFotos_(cursos, persona, p.dni_frente, p.dni_dorso);
    p.foto_frente = fotos.frente; p.foto_dorso = fotos.dorso;

    // Filas
    const fila = COLUMNAS.map(([k]) => limpiar_(p[k]));
    hoja_(HOJA_GENERAL).appendRow(fila);
    cursos.forEach(c => hoja_(c).appendRow(fila));

    if (AVISAR_A) {
      MailApp.sendEmail(AVISAR_A, "Nueva inscripción: " + p.nombre + " " + p.apellido + " (" + cursos.join(", ") + ")",
        COLUMNAS.map(([k, t]) => t + ": " + (p[k] || "")).join("\n"));
    }
    return ContentService.createTextOutput(JSON.stringify({ ok: true })).setMimeType(ContentService.MimeType.JSON);
  } finally {
    lock.releaseLock();
  }
}

function guardarFotos_(cursos, persona, frente64, dorso64) {
  const out = { frente: "", dorso: "" };
  if (!frente64 && !dorso64) return out;
  const raiz = carpeta_(DriveApp.getRootFolder(), CARPETA_FOTOS);
  const principal = carpeta_(raiz, cursos[0]);
  [["frente", frente64], ["dorso", dorso64]].forEach(([lado, b64]) => {
    if (!b64) return;
    const blob = Utilities.newBlob(Utilities.base64Decode(b64), "image/jpeg", persona + " - DNI " + lado + ".jpg");
    const archivo = principal.createFile(blob);
    out[lado] = archivo.getUrl();
    cursos.slice(1).forEach(c => {
      try { DriveApp.createShortcut(archivo.getId()).moveTo(carpeta_(raiz, c)); } catch (err) {}
    });
  });
  return out;
}

function carpeta_(padre, nombre) {
  const it = padre.getFoldersByName(nombre);
  return it.hasNext() ? it.next() : padre.createFolder(nombre);
}

// Evita que un texto que empieza con = + - @ se tome como fórmula.
function limpiar_(v) {
  v = (v == null ? "" : String(v)).slice(0, 1000);
  return /^[=+\-@]/.test(v) ? "'" + v : v;
}

function hoja_(nombre) {
  const libro = SpreadsheetApp.getActiveSpreadsheet();
  nombre = String(nombre).slice(0, 90);
  let hoja = libro.getSheetByName(nombre);
  if (!hoja) {
    hoja = libro.insertSheet(nombre);
    hoja.appendRow(COLUMNAS.map(([, t]) => t));
    hoja.getRange(1, 1, 1, COLUMNAS.length)
      .setFontWeight("bold").setBackground(nombre === HOJA_GENERAL ? "#00894C" : "#17919C").setFontColor("#FFFFFF");
    hoja.setFrozenRows(1);
    const col = COLUMNAS.findIndex(([k]) => k === "estado") + 1;
    hoja.getRange(2, col, 2000, 1).setDataValidation(
      SpreadsheetApp.newDataValidation().requireValueInList(ESTADOS, true).build());
    if (nombre === HOJA_GENERAL) libro.setActiveSheet(hoja), libro.moveActiveSheet(1);
  }
  return hoja;
}

// Para probar desde el editor: ejecutar "prueba". Tiene que aparecer una fila en
// "Todas las inscripciones" y en "Carpintería Adultos", y una carpeta de fotos en Drive.
function prueba() {
  const px = Utilities.base64Encode(Utilities.newBlob(
    Utilities.base64Decode("/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA="),
    "image/jpeg").getBytes());
  doPost({ parameter: { nombre: "Prueba", apellido: "Test", dni: "12345678", telefono: "1100000000",
    localidad: "Tigre", talleres: "Carpintería Adultos", turnos: "Tarde", estudios: "Secundaria completa",
    trabaja: "No", dni_frente: px, dni_dorso: px } });
}

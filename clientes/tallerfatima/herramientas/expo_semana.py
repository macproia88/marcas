"""Piezas de la semana de la Expo 2026 (viernes, sábado y lunes).
Las fotos sacadas del video original (432x768) se muestran enmarcadas como fotos instantáneas para que no se vean pixeladas.
Uso: python3 expo_semana.py <carpeta_fuentes>
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import armar_piezas as a
from PIL import Image, ImageDraw, ImageFilter

E = a.F + "/expo-2026"; C = E + "/cuadros"; O = a.OUT
W, H = 1080, 1350

def placa_polaroid(foto, frase, salida, n=None, ang=-3, centro=(0.5, 0.45)):
    c = Image.new("RGB", (W, H), a.VERDE)
    hoja = Image.open(os.path.join(a.BASE, "marca", "hoja-verde.png")).convert("RGBA").resize((760, 550))
    r, g, b, al = hoja.split()
    hoja = Image.merge("RGBA", (r.point(lambda v: 0), g.point(lambda v: 160), b.point(lambda v: 90), al.point(lambda v: int(v * 0.35))))
    c.paste(hoja, (W - 560, H - 520), hoja)
    ft = a.recortar(foto, 600, 760, centro)
    marco = Image.new("RGB", (650, 860), "white"); marco.paste(ft, (25, 25))
    sh = Image.new("RGBA", (700, 910), (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle([18, 22, 682, 892], fill=(0, 0, 0, 120))
    sh = sh.filter(ImageFilter.GaussianBlur(14)); sh.paste(marco, (25, 25))
    sh = sh.rotate(ang, resample=Image.BICUBIC, expand=True)
    c.paste(sh, ((W - sh.width) // 2, 70), sh)
    d = ImageDraw.Draw(c)
    lineas = a.partir(d, frase, a.SP(60), W - 160)
    y0 = H - 110 - len(lineas) * 64
    d.rectangle([70, y0 - 4, 82, y0 + len(lineas) * 64 - 12], fill=a.AMARILLO)
    a.texto_lineas(d, lineas, a.SP(60), 110, y0, "white", 1.06)
    a.logo(c, a.LOGO_B, 250, 70, H - 90)
    if n: d.text((W - 150, H - 85), n, font=a.LATOB(34), fill=a.CREMA)
    c.save(salida, quality=92)

# Viernes 20: trabajos de los alumnos
a.portada(f"{E}/muebles-alumnos.jpg", "EXPO FÁTIMA 2026", "Lo que hicieron nuestros alumnos",
          "Muebles, piezas y proyectos hechos en los talleres durante todo el año.", f"{O}/expo-trabajos-1.jpg")
placa_polaroid(f"{C}/cuadro-040.0.jpg", "El taller de carpintería, abierto para todos.", f"{O}/expo-trabajos-2.jpg", "2/7", -3)
placa_polaroid(f"{C}/cuadro-042.0.jpg", "Muebles terminados, listos para mostrar.", f"{O}/expo-trabajos-3.jpg", "3/7", 3)
a.foto_con_texto(f"{E}/muestra-carpinteria-mesa.jpg", "Lámparas, macetas y estantes hechos a mano.", f"{O}/expo-trabajos-4.jpg", "4/7", (0.4, 0.4))
placa_polaroid(f"{C}/cuadro-051.0.jpg", "Las máquinas del taller, en manos de los alumnos.", f"{O}/expo-trabajos-5.jpg", "5/7", -2)
placa_polaroid(f"{C}/cuadro-053.0.jpg", "Profes y alumnos contando cómo se trabaja.", f"{O}/expo-trabajos-6.jpg", "6/7", 3)
a.cierre("Orgullo de Fátima", "Detrás de cada pieza hay horas de trabajo, aprendizaje y superación.", f"{O}/expo-trabajos-7.jpg")

# Sábado 21: comunidad, stands e historia
a.portada(f"{E}/stand-grupo-sonriendo.jpg", "EXPO FÁTIMA 2026", "Una Expo para toda la comunidad",
          "Stands, emprendimientos, historia y mucha gente compartiendo el día.", f"{O}/expo-comunidad-1.jpg")
placa_polaroid(f"{C}/cuadro-012.5.jpg", "Vestidos de época que no pasaron desapercibidos.", f"{O}/expo-comunidad-2.jpg", "2/7", -3, (0.5, 0.5))
a.foto_con_texto(f"{E}/stand-feria.jpg", "Stands llenos de creatividad y emprendimientos.", f"{O}/expo-comunidad-3.jpg", "3/7", (0.5, 0.4))
placa_polaroid(f"{C}/cuadro-016.5.jpg", "Nuestra historia en fotos: generaciones que pasaron por Fátima.", f"{O}/expo-comunidad-4.jpg", "4/7", 2)
placa_polaroid(f"{C}/cuadro-083.0.jpg", "Tazas, stickers y productos de los emprendimientos.", f"{O}/expo-comunidad-5.jpg", "5/7", -2)
placa_polaroid(f"{C}/cuadro-086.0.jpg", "Familias, chicos y vecinos recorriendo cada rincón.", f"{O}/expo-comunidad-6.jpg", "6/7", 3)
a.cierre("Somos comunidad", "La Expo es de todos los que hacen Fátima día a día.", f"{O}/expo-comunidad-7.jpg")

# Lunes 23: cierre de la semana
a.portada(f"{E}/foto-grupal-carpinteria.jpg", "EXPO FÁTIMA 2026", "¡Gracias!",
          "A todos los que trabajaron y colaboraron para que este día sea posible.", f"{O}/expo-gracias-1.jpg", deslizar=False)
print("listo")

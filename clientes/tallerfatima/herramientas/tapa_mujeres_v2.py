"""Tapa nueva para Mujeres en Concreto (estilo 'dato grande', distinta a la de la Expo)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import armar_piezas as a
from tapas_variadas import degradado, W, H
from PIL import ImageDraw
c = a.recortar(f"{a.F}/mujeres-2000/certificados-grupal-banderas.jpg", W, H, (0.5, 0.22))
degradado(c, 760, color=(20, 16, 12), maxa=230); d = ImageDraw.Draw(c)
et = "MUJERES EN CONCRETO · 3° CICLO"
d.rounded_rectangle([70, 70, 70 + d.textlength(et, font=a.LATOB(32)) + 60, 130], 30, outline="white", width=3)
d.text((100, 82), et, font=a.LATOB(32), fill="white")
d.text((62, 905), "32", font=a.SP(250), fill=a.AMARILLO)
a.texto_lineas(d, ["mujeres", "se capacitaron"], a.SP(72), 400, 975, "white", 1.0)
d.rectangle([70, 1180, 190, 1188], fill=a.AMARILLO)
a.texto_lineas(d, a.partir(d, "Albañilería, pintura, instalaciones sanitarias y eléctricas.", a.LATO(36), W - 330), a.LATO(36), 70, 1205, "white", 1.3)
from tapas_variadas import flecha
flecha(d, W - 120, H - 85, a.AMARILLO)
c.save(f"{a.OUT}/mec-1-v2.jpg", quality=92)

"""Mejora una foto para Instagram (Quinta El Florido).
Uso: python3 -I mejorar_foto.py ENTRADA SALIDA FORMATO [desplazamiento_x]
FORMATO: cuadrado (1080x1080) | vertical (1080x1350, feed 4:5) | historia (1080x1920)
Requiere: pip install --break-system-packages opencv-contrib-python-headless pillow
"""
import sys, os, cv2, numpy as np
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
TAM = {"cuadrado": (1080, 1080), "vertical": (1080, 1350), "historia": (1080, 1920)}

def enhance(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB); l, a, b = cv2.split(lab)
    l = cv2.createCLAHE(clipLimit=1.15, tileGridSize=(8, 8)).apply(l)
    img = cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
    s = hsv[..., 1] / 255.0; hsv[..., 1] = np.clip(s + 0.22 * (1 - s) * s, 0, 1) * 255
    img = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    img = cv2.LUT(img, np.array([((i / 255.0) ** 0.96) * 255 for i in range(256)]).astype(np.uint8))
    blur = cv2.GaussianBlur(img, (0, 0), 1.2)
    return cv2.addWeighted(img, 1.3, blur, -0.3, 0)

def main(src, dst, formato, shift=0):
    W, H = TAM[formato]
    img = cv2.imread(src); h, w = img.shape[:2]
    r = W / H
    if w / h > r:   # más ancha: recorto los costados
        nw = int(h * r); x = max(0, min((w - nw) // 2 + shift, w - nw)); crop = img[:, x:x + nw]
    else:           # más alta: recorto arriba/abajo
        nh = int(w / r); y = (h - nh) // 2; crop = img[y:y + nh, :]
    if crop.shape[1] < W:
        sr = cv2.dnn_superres.DnnSuperResImpl_create()
        sr.readModel(os.path.join(AQUI, "FSRCNN_x2.pb")); sr.setModel("fsrcnn", 2)
        crop = sr.upsample(crop)
    crop = cv2.resize(crop, (W, H), interpolation=cv2.INTER_AREA if crop.shape[1] >= W else cv2.INTER_LANCZOS4)
    Image.fromarray(cv2.cvtColor(enhance(crop), cv2.COLOR_BGR2RGB)).save(dst, quality=95, subsampling=0)
    print("ok", dst)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 0)

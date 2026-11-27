from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
SP=lambda s:ImageFont.truetype('/tmp/ttf/league-spartan-latin-700-normal.ttf',s)
LB=lambda s:ImageFont.truetype('/tmp/ttf/lato-latin-700-normal.ttf',s)
LR=lambda s:ImageFont.truetype('/tmp/ttf/lato-latin-400-normal.ttf',s)
VERDE=(0,137,76); AMA=(255,203,51); MAR=(82,69,59); CREMA=(245,251,246); TURQ=(23,145,156); VCLARO=(120,176,42)
LOGO_V='/home/claude/marcas/clientes/tallerfatima/marca/logo-verde.png'
HOJA='/home/claude/marcas/clientes/tallerfatima/marca/hoja-verde.png'
def foto(path,w,h,cx=0.5,cy=0.4,top_cut=0.17):
    im=Image.open(path).convert('RGB'); W0,H0=im.size; im=im.crop((0,int(H0*top_cut),W0,H0)); W0,H0=im.size
    k=max(w/W0,h/H0); im=im.resize((int(W0*k)+1,int(H0*k)+1),Image.LANCZOS)
    x=int((im.width-w)*cx); y=int((im.height-h)*cy); im=im.crop((x,y,x+w,y+h))
    return ImageEnhance.Color(ImageEnhance.Sharpness(im).enhance(1.4)).enhance(1.08)
def c_(d,y,t,f,col,W): d.text(((W-d.textlength(t,font=f))/2,y),t,font=f,fill=col)
def tarjeta(W,H,salida,k=1.0):
    c=Image.new('RGB',(W,H),CREMA); d=ImageDraw.Draw(c)
    # marco verde fino
    m=int(34*k); d.rounded_rectangle([m,m,W-m,H-m],int(30*k),outline=VERDE,width=int(5*k))
    # logo
    lg=Image.open(LOGO_V).convert('RGBA'); lg.thumbnail((int(330*k),int(150*k))); c.paste(lg,((W-lg.width)//2,int(80*k)),lg)
    y=int(80*k)+lg.height+int(40*k)
    c_(d,y,'Querida familia:',SP(int(86*k)),VERDE,W); y+=int(110*k)
    for l in ['Con mucha alegría los invitamos','a acompañar a']:
        c_(d,y,l,LR(int(40*k)),MAR,W); y+=int(52*k)
    y+=int(40*k)
    d.line([(int(170*k),y),(W-int(170*k),y)],fill=MAR,width=max(2,int(3*k))); y+=int(16*k)
    c_(d,y,'(nombre del alumno o alumna)',LR(int(24*k)),(150,140,130),W); y+=int(52*k)
    for l in ['en la entrega de su certificado.','¡Es un logro de toda la familia!']:
        c_(d,y,l,LB(int(40*k)) if '¡' in l else LR(int(40*k)),MAR,W); y+=int(52*k)
    y+=int(30*k)
    # foto redondeada
    pw,ph=W-int(220*k),int(640*k)
    p=foto('silla.jpg',pw,ph,0.5,0.35); mk=Image.new('L',(pw,ph),0); ImageDraw.Draw(mk).rounded_rectangle([0,0,pw,ph],int(26*k),fill=255)
    c.paste(p,(int(110*k),y),mk); 
    # cinta con fecha sobre la foto
    yb=y+ph-int(60*k); bw=int(700*k); bx=(W-bw)//2
    d.rounded_rectangle([bx,yb,bx+bw,yb+int(120*k)],int(20*k),fill=VERDE)
    c_(d,yb+int(16*k),'Jueves 10 de diciembre · 18 h',SP(int(48*k)),'white',W)
    c_(d,yb+int(72*k),'Mozart 550 · Escuela Taller Fátima',LB(int(32*k)),AMA,W)
    y=yb+int(150*k)
    c_(d,y,'Los esperamos para celebrar juntos 💚'.replace(' 💚',''),SP(int(44*k)),VERDE,W)
    # puntos de color
    yy=H-int(80*k)
    for i,col in enumerate([AMA,TURQ,VCLARO]):
        cx=W//2+(i-1)*int(40*k); d.ellipse([cx-int(10*k),yy-int(10*k),cx+int(10*k),yy+int(10*k)],fill=col)
    c.save(salida,quality=94,dpi=(300,300) if k>1.5 else (72,72))
tarjeta(1080,1620,'invitacion-familias.jpg')          # para mandar por WhatsApp
tarjeta(1748,2622,'invitacion-familias-A5.jpg',k=1.62) # A5 a 300 dpi (aprox 14,8 x 22,2 cm)

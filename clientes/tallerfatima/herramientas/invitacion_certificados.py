from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
SP=lambda s:ImageFont.truetype('/tmp/ttf/league-spartan-latin-700-normal.ttf',s)
LB=lambda s:ImageFont.truetype('/tmp/ttf/lato-latin-700-normal.ttf',s)
LR=lambda s:ImageFont.truetype('/tmp/ttf/lato-latin-400-normal.ttf',s)
VERDE=(0,137,76); AMA=(255,203,51); MAR=(82,69,59); CREMA=(245,251,246); TURQ=(23,145,156); VCLARO=(120,176,42)
LOGO='/home/claude/marcas/clientes/tallerfatima/marca/logo-blanco.png'
def foto(path,w,h,cy=0.5,top_cut=0.0):
    im=Image.open(path).convert('RGB'); W0,H0=im.size
    im=im.crop((0,int(H0*top_cut),W0,H0))  # saca logos del video
    W0,H0=im.size; k=max(w/W0,h/H0); im=im.resize((int(W0*k)+1,int(H0*k)+1),Image.LANCZOS)
    x=(im.width-w)//2; y=int((im.height-h)*cy); im=im.crop((x,y,x+w,y+h))
    im=ImageEnhance.Sharpness(im).enhance(1.4); return ImageEnhance.Color(im).enhance(1.08)
def centrado(d,y,t,f,col,W):
    d.text(((W-d.textlength(t,font=f))/2,y),t,font=f,fill=col)
def calendario(c,x,y,s=1.0):
    d=ImageDraw.Draw(c); w,h=int(250*s),int(270*s)
    sh=Image.new('RGBA',(w+40,h+40),(0,0,0,0)); ImageDraw.Draw(sh).rounded_rectangle([20,26,w+20,h+26],int(28*s),fill=(0,0,0,110))
    c.paste(sh.filter(ImageFilter.GaussianBlur(10)),(x-20,y-20),sh.filter(ImageFilter.GaussianBlur(10)))
    d.rounded_rectangle([x,y,x+w,y+h],int(28*s),fill='white')
    d.rounded_rectangle([x,y,x+w,y+int(78*s)],int(28*s),fill=AMA); d.rectangle([x,y+int(50*s),x+w,y+int(78*s)],fill=AMA)
    f=SP(int(42*s)); t='JUEVES'; d.text((x+(w-d.textlength(t,font=f))/2,y+int(20*s)),t,font=f,fill=MAR)
    f=SP(int(140*s)); t='10'; d.text((x+(w-d.textlength(t,font=f))/2,y+int(88*s)),t,font=f,fill=VERDE)
    f=SP(int(40*s)); t='DICIEMBRE'; d.text((x+(w-d.textlength(t,font=f))/2,y+int(215*s)),t,font=f,fill=MAR)
FALTAN=0
def pieza(W,H,salida,story=False):
    c=Image.new('RGB',(W,H),VERDE)
    fh=int(H*(0.50 if story else 0.52))
    c.paste(foto('festejo.jpg',W,fh,0.62),(0,0))
    # degradé hacia el verde
    g=Image.new('L',(1,fh)); 
    for yy in range(fh): g.putpixel((0,yy),int(255*max(0,(yy-fh*0.55)/(fh*0.45))**1.3))
    c.paste(Image.new('RGB',(W,fh),VERDE),(0,0),g.resize((W,fh)))
    c=c.convert('RGBA'); d=ImageDraw.Draw(c)
    # logo arriba
    lg=Image.open(LOGO).convert('RGBA'); lg.thumbnail((300,150))
    pad=Image.new('RGBA',(lg.width+44,lg.height+30),(0,0,0,0)); ImageDraw.Draw(pad).rounded_rectangle([0,0,pad.width,pad.height],18,fill=(0,90,50,200))
    py=60 if not story else 150
    c.alpha_composite(pad,(48,py)); c.alpha_composite(lg,(70,py+15))
    # calendario
    s=1.0 if not story else 1.15
    calendario(c,W-int(250*s)-60,fh-int(270*s)+60,s)
    d=ImageDraw.Draw(c)
    y=fh+ (40 if not story else 70)
    et='TE INVITAMOS A LA'; f=LB(36 if not story else 40)
    d.rounded_rectangle([60,y,60+d.textlength(et,font=f)+40,y+(58 if not story else 64)],10,fill=AMA); d.text((80,y+10),et,font=f,fill=MAR)
    y+= 84 if not story else 100
    f=SP(118 if not story else 132)
    for l in ['Entrega de','Certificados']:
        d.text((56,y),l,font=f,fill='white'); y+= (112 if not story else 126)
    f=SP(64 if not story else 72); d.text((60,y+4),'2026',font=f,fill=AMA)
    y+= 100 if not story else 120
    # hora
    f=SP(62 if not story else 70); t='18 h'
    d.rounded_rectangle([60,y,60+d.textlength(t,font=f)+56,y+(84 if not story else 94)],42,outline='white',width=4)
    d.text((88,y+14),t,font=f,fill='white')
    fr=LB(34 if not story else 38); 
    xx=60+d.textlength(t,font=f)+90
    d.text((xx,y+2),'Mozart 550',font=SP(46 if not story else 52),fill='white')
    d.text((xx,y+(52 if not story else 60)),'Escuela Taller Fátima',font=fr,fill=CREMA)
    if FALTAN:
        y2=y+(140 if not story else 170)
        txt=f'FALTAN {FALTAN} DÍAS'; ff=SP(60 if not story else 76)
        tw=d.textlength(txt,font=ff)
        d.rounded_rectangle([60,y2,60+tw+60,y2+(90 if not story else 110)],16,fill=AMA)
        d.text((90,y2+(18 if not story else 22)),txt,font=ff,fill=MAR)
    # franja inferior
    d.rectangle([0,H-16,W//3,H],fill=AMA); d.rectangle([W//3,H-16,2*W//3,H],fill=TURQ); d.rectangle([2*W//3,H-16,W,H],fill=VCLARO)
    if story:
        f=LB(36); centrado(d,H-95,'@escuelatallerfatima',f,CREMA,W)
    c.convert('RGB').save(salida,quality=93)
pieza(1080,1350,'invitacion-posteo.jpg')
pieza(1080,1920,'invitacion-historia.jpg',story=True)
FALTAN=8; pieza(1080,1920,'recordatorio-8dias.jpg',story=True)
FALTAN=4; pieza(1080,1920,'recordatorio-4dias.jpg',story=True)

"""CRM del club (ALAX) - corrida semanal.
Uso: python3 tablero-auto/crm/club_crm.py <carpeta con los reportes de ALAX y el último Club_CRM_*.xlsx> <carpeta de salida> [AAAA-MM-DD fecha de la lista]
- Lee todos los Reporte_de_ventas* (se juntan por venta_id) y los Reporte_de_usuarios* de ALAX.
- Arma grupos, ficha, lista de 100 (sin repetir a quien se contactó en las últimas 3 semanas) y mide quién volvió de las listas anteriores.
- Escribe <salida>/Club_CRM_<fecha>.xlsx (al chat) y Club_CRM_contactos_<fecha>.csv (al Drive 01 Club, para medir la semana siguiente) (PRIVADO: tiene nombres, DNI y mails; va al Drive 01 Club, nunca a la web)
- Actualiza tablero-club.html con DATA['grupos_semana'] y DATA['contactos_resultado'] (solo cantidades).
"""
import sys,os,glob,json,re,warnings
import pandas as pd,numpy as np,openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill,Alignment,Border,Side
from openpyxl.utils import get_column_letter as CL
from openpyxl.formatting.rule import CellIsRule
warnings.filterwarnings('ignore')
IN,OUT=sys.argv[1],sys.argv[2]
HOY=pd.Timestamp(sys.argv[3]) if len(sys.argv)>3 else pd.Timestamp.now().normalize()
HTML=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','tablero-club.html')
V=[];U=[];prev_crm=[]
prev_csv=glob.glob(os.path.join(IN,'**','Club_CRM_contactos_*.csv'),recursive=True)
for f in glob.glob(os.path.join(IN,'**','*.xlsx'),recursive=True):
    b=os.path.basename(f)
    if b.startswith('Club_CRM_'): prev_crm.append(f); continue
    try:
        ws=openpyxl.load_workbook(f,read_only=True,data_only=True).active; it=ws.iter_rows(values_only=True); h=next(it)
    except Exception: continue
    if h and h[0]=='venta_id': V.append(pd.DataFrame([r for r in it if r[0]],columns=h))
    elif h and h[0]=='id' and 'dni' in h and 'fecha_alta' in h:
        d=pd.DataFrame([r for r in it if r[0]],columns=h); d['_m']=os.path.getmtime(f); U.append(d)
v=pd.concat(V).drop_duplicates('venta_id')
v['t']=pd.to_datetime(v.venta_fecha_hora); v['imp']=pd.to_numeric(v.importe,errors='coerce').fillna(0); v=v[v.imp>1].copy()
v['dni']=v.usuario_dni.astype(str).str.replace(r'\D','',regex=True); v=v[(v.dni.str.len()>=6)&~v.dni.str.fullmatch(r'(\d)\1+')]
v['club']=np.where(v.local_nombre.str.contains('Paz'),'Paz','La Presumida')
v['local']=v.local_nombre.map({'La Presumida Vte López':'Florida','La Presumida Beccar':'Beccar','Pastas Paz':'Paz'})
v['dia']=v.t.dt.normalize(); v['key']=v.club+'|'+v.dni
vis=v.groupby(['key','dia']).agg(imp=('imp','sum'),local=('local','first')).reset_index()
locp=v.groupby('key').local.agg(lambda s:s.value_counts().index[0])
END=v.dia.max()
cuts=list(pd.date_range('2026-07-12',END,freq='W-SUN'))
if not cuts or cuts[-1]<END: cuts.append(END)
RANK={'Frecuentes':6,'Recurrentes':5,'Ocasionales':4,'Nuevos':4,'En riesgo':2,'Dormidos':1}
G=['Frecuentes','Recurrentes','Nuevos','Ocasionales','En riesgo','Dormidos']
D30=pd.Timedelta(days=30)
def snap(t):
    x=vis[vis.dia<=t]; g=x.groupby('key'); last=g.dia.max(); fst=g.dia.min()
    n=x[x.dia>t-D30].groupby('key').size().reindex(last.index,fill_value=0); s=pd.Series(index=last.index,dtype=object)
    s[n>=4]='Frecuentes'; s[(n>=2)&(n<=3)]='Recurrentes'; s[(n==1)&(fst>t-D30)]='Nuevos'; s[(n==1)&(fst<=t-D30)]='Ocasionales'
    d=(t-last).dt.days; s[(n==0)&(d<=60)]='En riesgo'; s[(n==0)&(d>60)]='Dormidos'; return s
S={t:snap(t) for t in cuts}
rows=[];prev=None
for t in cuts:
    s=S[t]; loc=locp.reindex(s.index)
    for L in ['Total','Florida','Beccar','Paz']:
        m=s if L=='Total' else s[loc==L]; c=m.value_counts()
        r=dict(local=L,semana=(t-pd.Timedelta(days=t.weekday())).strftime('%Y-%m-%d'),hasta=t.strftime('%Y-%m-%d'),dias=int(t.weekday())+1)
        for k in G: r[k]=int(c.get(k,0))
        if prev is not None:
            pm=S[prev].reindex(m.index); both=pm.notna(); a=m[both].map(RANK); b=pm[both].map(RANK)
            r.update(primeras_compras=int((~both).sum()),mejoraron=int((a>b).sum()),empeoraron=int((a<b).sum()),
              nuevos_que_volvieron=int(((pm=='Nuevos')&m.isin(['Recurrentes','Frecuentes'])).sum()),
              nuevos_que_no_volvieron=int(((pm=='Nuevos')&(m=='En riesgo')).sum()),
              recuperados=int((pm.isin(['En riesgo','Dormidos'])&m.isin(['Frecuentes','Recurrentes','Ocasionales'])).sum()),
              pasaron_a_dormidos=int(((pm=='En riesgo')&(m=='Dormidos')).sum()),
              subieron_a_frecuentes=int((pm.notna()&(pm!='Frecuentes')&(m=='Frecuentes')).sum()),
              bajaron_de_frecuentes=int(((pm=='Frecuentes')&(m!='Frecuentes')).sum()))
        rows.append(r)
    prev=t
W=pd.DataFrame(rows)
# ficha
u=pd.concat(U) if U else pd.DataFrame(columns=['dni','fecha_alta','_m'])
if len(u):
    fmin=u.groupby('_m').fecha_alta.transform('min').astype(str)
    u['club']=np.where(fmin=='2025-07-01','La Presumida','Paz')
    u['dni']=u.dni.astype(str).str.replace(r'\D','',regex=True); u['key']=u.club+'|'+u.dni
    u=u.sort_values('_m').drop_duplicates('key',keep='last').set_index('key')
t1=cuts[-2] if len(cuts)>1 else cuts[-1]
g=vis.groupby('key')
F=pd.DataFrame({'primera_compra':g.dia.min(),'ultima_compra':g.dia.max(),'visitas':g.size(),'gasto_total':g.imp.sum()})
F['visitas_30d']=vis[vis.dia>END-D30].groupby('key').size().reindex(F.index,fill_value=0)
F['ticket_prom']=(F.gasto_total/F.visitas).round(0); F['dias_sin_venir']=(END-F.ultima_compra).dt.days
F['grupo']=S[END]; F['grupo_semana_ant']=S[t1].reindex(F.index)
a=F.grupo.map(RANK); b=F.grupo_semana_ant.map(RANK)
F['tendencia']=np.select([b.isna(),a>b,a<b],['Nuevo','Mejoró','Empeoró'],'Igual')
F['local']=locp; F['club']=F.index.str.split('|').str[0]; F['dni']=F.index.str.split('|').str[1]
last=v.sort_values('t').groupby('key').last()
F['nombre']=last.usuario_nombre.astype(str).str.strip().str.title()+' '+last.usuario_apellido.astype(str).str.strip().str.title()
F['email']=last.usuario_email
if len(u):
    mov=u.telefono_movil_area.fillna('').astype(str).str.replace(r'\.0$','',regex=True)+u.telefono_movil.fillna('').astype(str).str.replace(r'\.0$','',regex=True)
    F['telefono']=mov.reindex(F.index).replace('',np.nan).fillna(last.usuario_movil)
    F['fecha_alta']=u.fecha_alta.reindex(F.index); F['fecha_nac']=u.fecha_nac.reindex(F.index); F['email']=F.email.fillna(u.email.reindex(F.index))
else: F['telefono']=last.usuario_movil; F['fecha_alta']=None; F['fecha_nac']=None
F['key']=F.index
# historial previo y medición
H=pd.DataFrame(columns=['fecha_lista','key','club','dni','nombre','prioridad','mensaje','control'])
if prev_crm:
    pf=sorted(prev_crm)[-1]
    try: H=pd.read_excel(pf,sheet_name='Historial contactos',dtype={'dni':str}); H['fecha_lista']=pd.to_datetime(H.fecha_lista)
    except Exception: pass
if prev_csv:
    TP={'1':'1. Nuevo sin segunda compra','2':'2. En riesgo','3':'3. Frecuente que bajó','4':'4. Dormido'}
    parts=[]
    for f in prev_csv:
        d=pd.read_csv(f,dtype=str)
        if 'f' not in d.columns and 'c' in d.columns:
            d['f']=re.search(r'(\d{4}-\d{2}-\d{2})',os.path.basename(f)).group(1)
        if 'f' in d.columns:
            d=pd.DataFrame({'fecha_lista':d.f,'club':np.where(d.c=='P','Paz','La Presumida'),'dni':d.dni,'prioridad':d.t.map(TP),'control':np.where(d.k=='1','Sí','No')})
        parts.append(d)
    H2=pd.concat(parts); H2['fecha_lista']=pd.to_datetime(H2.fecha_lista)
    if 'control' not in H2: H2['control']='No'
    H2['control']=H2.control.fillna('No')
    H2['key']=H2.club+'|'+H2.dni; H2['nombre']=None; H2['mensaje']=None
    H=pd.concat([H,H2]).drop_duplicates(['fecha_lista','key'])
H=H[H.fecha_lista<HOY] if len(H) else H
def volvio(r):
    x=vis[(vis.key==r.key)&(vis.dia>=r.fecha_lista)]
    return (x.dia.min()-r.fecha_lista).days if len(x) else None
if len(H):
    H['dias_hasta_volver']=H.apply(volvio,axis=1); H['volvio']=np.where(H.dias_hasta_volver.notna(),'Sí','No')
recientes=set(H[H.fecha_lista>=HOY-pd.Timedelta(days=21)].key) if len(H) else set()
cand=F[~F.key.isin(recientes)]
import hashlib
C=cand[(cand.grupo_semana_ant=='Frecuentes')&(cand.grupo!='Frecuentes')].assign(prioridad='3. Frecuente que bajó',motivo=lambda d:'Venía 4+ veces al mes; bajó a '+d.grupo.str.lower(),mensaje='Hola {n}, te extrañamos esta semana en {m}. Te guardamos una salsa de regalo con tu próxima compra.')
B=cand[cand.grupo=='En riesgo'].assign(prioridad='2. En riesgo',motivo=lambda d:'Hace '+d.dias_sin_venir.astype(str)+' días que no viene; vino '+d.visitas.astype(str)+' veces',mensaje='Hola {n}, hace un tiempo que no te vemos en {m}. Esta semana, con tu DNI, te llevás 1/2 kg de ñoquis de regalo en tu compra.')
A=cand[(cand.grupo=='Nuevos')&cand.dias_sin_venir.between(14,30)].assign(prioridad='1. Nuevo sin segunda compra',motivo=lambda d:'Compró una vez hace '+d.dias_sin_venir.astype(str)+' días y no volvió',mensaje='Hola {n}, gracias por sumarte al Club de {m}. Tenés 15 días para usar tu beneficio de segunda compra: 10% en pastas frescas.')
Dm=cand[cand.grupo=='Dormidos'].assign(prioridad='4. Dormido',motivo=lambda d:'Hace '+d.dias_sin_venir.astype(str)+' días que no viene',mensaje='Hola {n}, te esperamos de nuevo en {m}: con tu DNI tenés 15% en tu próxima compra hasta el domingo.')
LI=pd.concat([A,B,C,Dm]).drop_duplicates('key')
LI=LI.sort_values(['prioridad','gasto_total'],ascending=[True,False])
LI['mensaje']=[mm.replace('{n}',str(n).split(' ')[0]).replace('{m}','Pastas Paz' if c=='Paz' else 'La Presumida') for mm,n,c in zip(LI.mensaje,LI.nombre,LI.club)]
# grupo de control: 10% al azar (fijo por socio y fecha), no recibe el mail
LI['control']=['Sí' if int(hashlib.md5(f"{k}|{HOY:%Y-%m-%d}".encode()).hexdigest(),16)%10==0 else 'No' for k in LI.key]
CTRL=LI[LI.control=='Sí']; LI_all=LI; LI=LI[LI.control=='No']
newH=LI_all.assign(fecha_lista=HOY)[['fecha_lista','key','club','dni','nombre','prioridad','mensaje','control']]
HH=pd.concat([H.drop(columns=[c for c in ['dias_hasta_volver','volvio'] if c in H.columns]),newH],ignore_index=True)
# resultado agregado para la web
res=[]
if len(H):
    H['control']=H.control.fillna('No') if 'control' in H else 'No'
    for (fl,pr),x in H.groupby(['fecha_lista','prioridad']):
        e=x[x.control!='Sí']; c=x[x.control=='Sí']
        res.append(dict(fecha_lista=fl.strftime('%Y-%m-%d'),prioridad=pr,contactados=int(len(e)),volvieron=int((e.volvio=='Sí').sum()),control=int(len(c)),control_volvieron=int((c.volvio=='Sí').sum())))
# ---- Excel
A_='Arial'; HF=PatternFill('solid',fgColor='7A3E2B'); th=Side(style='thin',color='CCCCCC'); BX=Border(top=th,bottom=th,left=th,right=th)
GR=PatternFill('solid',fgColor='E5F4E4'); RD=PatternFill('solid',fgColor='FBEBEB')
def hdr(ws,cols,r=1):
    for i,c in enumerate(cols,1):
        x=ws.cell(r,i,c); x.font=Font(name=A_,bold=True,color='FFFFFF'); x.fill=HF; x.alignment=Alignment(wrap_text=True,vertical='center',horizontal='center'); x.border=BX
def put(ws,r,c,val,fmt=None,bold=False):
    if val is not None and not isinstance(val,str) and pd.isna(val): val=None
    if isinstance(val,pd.Timestamp): val=val.to_pydatetime(); fmt=fmt or 'DD/MM/YYYY'
    x=ws.cell(r,c,val); x.font=Font(name=A_,bold=bold); x.border=BX
    if fmt: x.number_format=fmt
    return x
wb=Workbook(); ws=wb.active; ws.title='LEEME'
txt=[f"CLUB - CRM SEMANAL. Lista del {HOY:%d/%m/%Y}, con compras de ALAX hasta el {END:%d/%m/%Y}.",
"Hojas: Lista de la semana (a quién escribir y con qué mensaje) · Resultado de los mensajes (quién volvió de las listas anteriores) · Sube o baja · Evolución semanal · Ficha de clientes · Historial contactos.",
"La Lista trae a TODOS los socios de cada grupo, menos el 10% elegido al azar que queda como grupo de control (no recibe el mail) para medir si el mail funciona. Los mails se mandan desde el email marketing de ALAX con los archivos ALAX_mail_*.csv.",
"Grupos (últimos 30 días): Frecuentes 4+ días con compra · Recurrentes 2-3 · Nuevos 1ª compra en 30 días · Ocasionales 1 vez y ya eran clientes · En riesgo 31-60 días sin venir · Dormidos +60.",
"Volvió = compró con su DNI desde el día de la lista. A quien se contactó (o quedó de control) en las últimas 3 semanas no se lo repite.",
"Los beneficios de los mensajes son sugeridos: confirmarlos antes de mandar. Archivo PRIVADO (nombres, DNI y mails): no compartir fuera del equipo."]
for i,t_ in enumerate(txt,1): ws.cell(i,1,t_).font=Font(name=A_,bold=(i==1),size=12 if i==1 else 10)
ws.column_dimensions['A'].width=160
ws=wb.create_sheet('Lista de la semana')
lc=['Prioridad','Club','Local','Nombre','Email','Teléfono','Grupo hoy','Por qué','Visitas','Gasto total ($)','Ticket promedio ($)','Última compra','Mensaje sugerido','DNI','Enviado (Sí/No)']
hdr(ws,lc)
for i,r_ in enumerate(LI.itertuples(),2):
    vals=[r_.prioridad,r_.club,r_.local,r_.nombre,r_.email,r_.telefono,r_.grupo,r_.motivo,r_.visitas,r_.gasto_total,r_.ticket_prom,r_.ultima_compra,r_.mensaje,r_.dni,None]
    for j,val in enumerate(vals,1): put(ws,i,j,val,'$#,##0' if j in(10,11) else None)
ws.freeze_panes='E2'; ws.auto_filter.ref=f"A1:O{len(LI)+1}"
for j,wd in enumerate([24,12,9,24,30,12,11,36,8,12,11,12,70,11,12],1): ws.column_dimensions[CL(j)].width=wd
ws=wb.create_sheet('Resultado de los mensajes')
hdr(ws,['Lista del','Tipo de contacto','Recibieron el mail','Volvieron','% que volvió','Grupo de control (sin mail)','Volvieron sin mail','% que volvió sin mail','Efecto del mail (puntos)'])
for i,r_ in enumerate(res,2):
    put(ws,i,1,pd.Timestamp(r_['fecha_lista'])); put(ws,i,2,r_['prioridad']); put(ws,i,3,r_['contactados']); put(ws,i,4,r_['volvieron']); ws.cell(i,5,f'=IF(C{i}=0,0,D{i}/C{i})').number_format='0%'
    put(ws,i,6,r_['control']); put(ws,i,7,r_['control_volvieron']); ws.cell(i,8,f'=IF(F{i}=0,0,G{i}/F{i})').number_format='0%'; ws.cell(i,9,f'=(E{i}-H{i})*100').number_format='+0.0;-0.0;0'
if not res: ws.cell(2,1,'Todavía no hay listas anteriores para medir: la primera medición sale la semana que viene.').font=Font(name=A_,italic=True)
for j,wd in enumerate([12,28,12,11,11,14,12,12,14],1): ws.column_dimensions[CL(j)].width=wd
ws.cell(len(res)+3,1,'Efecto del mail = % que volvió con mail − % que volvió sin mail. El grupo de control es el 10% de cada lista elegido al azar que NO recibe el mail.').font=Font(name=A_,italic=True,size=9)
ws=wb.create_sheet('Sube o baja')
hdr(ws,['Local','Grupo','Semana anterior','Esta semana','Cambio','Lectura'])
good={'Frecuentes':1,'Recurrentes':1,'Nuevos':1,'Ocasionales':1,'En riesgo':-1,'Dormidos':-1}; r=2
for L in ['Total','Florida','Beccar','Paz']:
    w=W[W.local==L].iloc[-2:]
    for gname in G:
        a_,b_=int(w.iloc[0][gname]),int(w.iloc[1][gname]); d=b_-a_; ok=d*good[gname]>0
        put(ws,r,1,L,bold=True); put(ws,r,2,gname); put(ws,r,3,a_,'#,##0'); put(ws,r,4,b_,'#,##0'); x=put(ws,r,5,d,'+#,##0;-#,##0;0')
        y=put(ws,r,6,('Sube' if d>0 else 'Baja' if d<0 else 'Igual')+(' (mejora)' if ok else ' (empeora)' if d else ''))
        if d:
            for c_ in (x,y): c_.fill=GR if ok else RD
        r+=1
for j,wd in enumerate([10,14,15,12,10,20],1): ws.column_dimensions[CL(j)].width=wd
ws=wb.create_sheet('Evolución semanal')
keys=['local','semana','hasta','dias']+G+['primeras_compras','mejoraron','empeoraron','nuevos_que_volvieron','nuevos_que_no_volvieron','recuperados','pasaron_a_dormidos','subieron_a_frecuentes','bajaron_de_frecuentes']
hdr(ws,['Local','Semana (lunes)','Hasta','Días']+G+['Primeras compras','Mejoraron','Empeoraron','Nuevos que volvieron','Nuevos que no volvieron','Recuperados','Pasaron a dormidos','Subieron a frecuentes','Bajaron de frecuentes'])
r=2
for L in ['Total','Florida','Beccar','Paz']:
    for _,x in W[W.local==L].iterrows():
        for j,k in enumerate(keys,1): put(ws,r,j,pd.Timestamp(x[k]) if k in('semana','hasta') else x[k],'#,##0' if j>4 else None)
        r+=1
ws.freeze_panes='C2'
for j in range(1,len(keys)+1): ws.column_dimensions[CL(j)].width=13
ws.row_dimensions[1].height=45
ws=wb.create_sheet('Ficha de clientes')
fc=['club','local','dni','nombre','email','telefono','fecha_alta','fecha_nac','grupo','grupo_semana_ant','tendencia','primera_compra','ultima_compra','dias_sin_venir','visitas','visitas_30d','gasto_total','ticket_prom']
hdr(ws,['Club','Local','DNI','Nombre','Email','Teléfono','Fecha de alta','Fecha de nacimiento','Grupo hoy','Grupo semana anterior','Tendencia','Primera compra','Última compra','Días sin venir','Visitas totales','Visitas 30 días','Gasto total ($)','Ticket promedio ($)'])
FF=F.sort_values(['grupo','gasto_total'],ascending=[True,False])
for i,row in enumerate(FF[fc].itertuples(index=False),2):
    for j,val in enumerate(row,1):
        if j in(7,8) and val: val=pd.Timestamp(val)
        put(ws,i,j,val,'$#,##0' if j in(17,18) else None)
ws.freeze_panes='E2'; ws.auto_filter.ref=f"A1:R{len(FF)+1}"
ws.conditional_formatting.add(f"K2:K{len(FF)+1}",CellIsRule(operator='equal',formula=['"Mejoró"'],fill=GR))
ws.conditional_formatting.add(f"K2:K{len(FF)+1}",CellIsRule(operator='equal',formula=['"Empeoró"'],fill=RD))
for j,wd in enumerate([12,9,11,26,30,13,12,12,12,12,10,12,12,9,9,9,12,11],1): ws.column_dimensions[CL(j)].width=wd
ws=wb.create_sheet('Historial contactos')
hc=['fecha_lista','key','club','dni','nombre','prioridad','mensaje','control']
hdr(ws,hc)
for i,row in enumerate(HH[hc].itertuples(index=False),2):
    for j,val in enumerate(row,1): put(ws,i,j,val)
os.makedirs(OUT,exist_ok=True)
xf=os.path.join(OUT,f'Club_CRM_{HOY:%Y-%m-%d}.xlsx'); wb.save(xf)
TIPOS={'1':'1. Nuevo sin segunda compra','2':'2. En riesgo','3':'3. Frecuente que bajó','4':'4. Dormido'}
pd.DataFrame({'c':np.where(newH.club=='Paz','P','L'),'dni':newH.dni,'t':newH.prioridad.str[0],'k':np.where(newH.control=='Sí',1,0)}).to_csv(os.path.join(OUT,f'Club_CRM_contactos_{HOY:%Y-%m-%d}.csv'),index=False)

# CSV para cargar en el email marketing de ALAX: uno por club y por tipo de mensaje
for (club,pr),x in LI.groupby(['club','prioridad']):
    tipo={'1':'nuevos','2':'en_riesgo','3':'frecuentes_que_bajaron','4':'dormidos'}[pr[0]]
    x.assign(nombre_pila=x.nombre.str.split(' ').str[0])[['email','nombre_pila','nombre','dni']].to_csv(os.path.join(OUT,f"ALAX_mail_{'Paz' if club=='Paz' else 'LaPresumida'}_{tipo}_{HOY:%Y-%m-%d}.csv"),index=False)
# web
s=open(HTML,encoding='utf-8').read(); m=re.search(r'window\.DATA=(\{.*?\});\s*\n',s,re.S); D=json.loads(m.group(1))
D['grupos_semana']=[r for r in rows if r['semana']>='2026-08-03']; D['contactos_resultado']=res
D.setdefault('info',[{}])[0]['grupos_hasta']=END.strftime('%Y-%m-%d')
D['info'][0]['actualizado']=pd.Timestamp.now(tz='America/Argentina/Buenos_Aires').strftime('%Y-%m-%dT%H:%M')
s=s[:m.start(1)]+json.dumps(D,ensure_ascii=False)+s[m.end(1):]; open(HTML,'w',encoding='utf-8').write(s)
print(json.dumps(dict(excel=xf,compras_hasta=str(END.date()),lista=len(LI),control=len(CTRL),por_tipo=LI.prioridad.value_counts().to_dict(),medidos=res,ultima_semana={k:int(W[W.local=='Total'].iloc[-1][k]) for k in G}),ensure_ascii=False))

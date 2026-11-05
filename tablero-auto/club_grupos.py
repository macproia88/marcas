"""Evolución semanal de los 6 grupos del club -> tablero-club.html (DATA['grupos_semana']).
Uso: python3 tablero-auto/club_grupos.py <archivos o carpetas con Reporte_de_ventas de ALAX ...>
Solo publica cantidades agregadas por grupo/local/semana (nada de nombres, DNI ni mails).
"""
import sys,os,glob,json,re,warnings
import pandas as pd,numpy as np,openpyxl
warnings.filterwarnings('ignore')
HTML=os.path.join(os.path.dirname(__file__),'..','tablero-club.html')
files=[]
for a in sys.argv[1:]:
    files+=glob.glob(os.path.join(a,'**','*.xlsx'),recursive=True) if os.path.isdir(a) else [a]
V=[]
for f in files:
    try:
        ws=openpyxl.load_workbook(f,read_only=True,data_only=True).active; it=ws.iter_rows(values_only=True); h=next(it)
    except Exception: continue
    if h and h[0]=='venta_id': V.append(pd.DataFrame([r for r in it if r[0]],columns=h))
v=pd.concat(V).drop_duplicates('venta_id')
v['t']=pd.to_datetime(v.venta_fecha_hora); v['imp']=pd.to_numeric(v.importe,errors='coerce').fillna(0); v=v[v.imp>1]
v['dni']=v.usuario_dni.astype(str).str.replace(r'\D','',regex=True); v=v[(v.dni.str.len()>=6)&~v.dni.str.fullmatch(r'(\d)\1+')]
v['club']=np.where(v.local_nombre.str.contains('Paz'),'Paz','La Presumida')
v['local']=v.local_nombre.map({'La Presumida Vte López':'Florida','La Presumida Beccar':'Beccar','Pastas Paz':'Paz'})
v['dia']=v.t.dt.normalize(); v['key']=v.club+'|'+v.dni
vis=v.groupby(['key','dia']).agg(local=('local','first')).reset_index()
locp=v.groupby('key').local.agg(lambda s:s.value_counts().index[0])
END=v.dia.max()
cuts=[c for c in pd.date_range('2026-07-12',END,freq='W-SUN')]
if not cuts or cuts[-1]<END: cuts.append(END)
RANK={'Frecuentes':6,'Recurrentes':5,'Ocasionales':4,'Nuevos':4,'En riesgo':2,'Dormidos':1}
D30=pd.Timedelta(days=30)
def snap(t):
    x=vis[vis.dia<=t]; g=x.groupby('key'); last=g.dia.max(); fst=g.dia.min()
    n=x[x.dia>t-D30].groupby('key').size().reindex(last.index,fill_value=0); s=pd.Series(index=last.index,dtype=object)
    s[n>=4]='Frecuentes'; s[(n>=2)&(n<=3)]='Recurrentes'; s[(n==1)&(fst>t-D30)]='Nuevos'; s[(n==1)&(fst<=t-D30)]='Ocasionales'
    d=(t-last).dt.days; s[(n==0)&(d<=60)]='En riesgo'; s[(n==0)&(d>60)]='Dormidos'; return s
rows=[]; prev=None
for t in cuts:
    s=snap(t); loc=locp.reindex(s.index)
    for L in ['Total','Florida','Beccar','Paz']:
        m=s if L=='Total' else s[loc==L]; c=m.value_counts()
        r=dict(local=L,semana=(t-pd.Timedelta(days=t.weekday())).strftime('%Y-%m-%d'),hasta=t.strftime('%Y-%m-%d'),dias=int(t.weekday())+1)
        for k in RANK: r[k]=int(c.get(k,0))
        if prev is not None:
            pm=prev.reindex(m.index); both=pm.notna(); a=m[both].map(RANK); b=pm[both].map(RANK)
            r.update(primeras_compras=int((~both).sum()),mejoraron=int((a>b).sum()),empeoraron=int((a<b).sum()),
                nuevos_que_volvieron=int(((pm=='Nuevos')&m.isin(['Recurrentes','Frecuentes'])).sum()),
                nuevos_que_no_volvieron=int(((pm=='Nuevos')&(m=='En riesgo')).sum()),
                recuperados=int((pm.isin(['En riesgo','Dormidos'])&m.isin(['Frecuentes','Recurrentes','Ocasionales'])).sum()),
                pasaron_a_dormidos=int(((pm=='En riesgo')&(m=='Dormidos')).sum()))
        rows.append(r)
    prev=s
s=open(HTML,encoding='utf-8').read()
m=re.search(r'window\.DATA=(\{.*?\});\s*\n',s,re.S); D=json.loads(m.group(1))
D['grupos_semana']=[r for r in rows if r['semana']>='2026-08-03']
D.setdefault('info',[{}])[0]['grupos_hasta']=END.strftime('%Y-%m-%d')
s=s[:m.start(1)]+json.dumps(D,ensure_ascii=False)+s[m.end(1):]
open(HTML,'w',encoding='utf-8').write(s)
print('grupos_semana',len(D['grupos_semana']),'hasta',END.date())

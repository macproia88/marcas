import openpyxl,datetime as dt,pandas as pd
APP={'PEDIDOS YA TARJ':'App PedidosYa','RAPPI TARJETA':'App Rappi','MP DELIVERY':'App MP Delivery','Pago Online':'App Pago Online'}
def s(v): return v.strip() if isinstance(v,str) else v
def parse(f,loc):
    wb=openpyxl.load_workbook(f,read_only=True,data_only=True); rows=list(wb.active.iter_rows(values_only=True))
    h=rows[0]; T=[]; cur=None; fila=1; gen=None
    for r in rows[1:]:
        fila+=1
        r=[s(x) for x in r]; d=dict(zip(h,r))
        if isinstance(d['COMPROBANT'],str) and 'TOTALES GENERALES' in d['COMPROBANT']: gen=(d['IMPORTE'],d['TOTAL'],d['DESCUENTO'])
        if isinstance(d['FECHA'],dt.datetime) and isinstance(d['HORA'],dt.time) and d['COMPROBANT']:
            cur=dict(LOCAL=loc,FILA=fila,FECHA=d['FECHA'].date(),HORA=d['HORA'],COMPROBANTE=d['COMPROBANT'],TURNO=d['TURNO'],MESA=d['MESA'],
                     VENDEDOR=str(d['MOZO']),COBRO=d['COBRO'],IMPORTE=d['IMPORTE'] or 0,TOTAL=d['TOTAL'] or 0,DESCUENTO=d['DESCUENTO'] or 0,PAGOS=1,COBRO2='')
            T.append(cur)
        elif cur is not None and (d['IMPORTE'] or 0)!=0 and not d['COMPROBANT'] and isinstance(d['FECHA'],dt.datetime):
            cur['IMPORTE']+=d['IMPORTE']; cur['PAGOS']+=1; cur['COBRO2']=(cur['COBRO2']+' + ' if cur['COBRO2'] else '')+d['COBRO']
            cur['DESCUENTO']+=d['DESCUENTO'] or 0
    df=pd.DataFrame(T)
    def canal(r):
        if r.COMPROBANTE.startswith('NCB'): return 'Nota de crédito'
        if r.COBRO in APP: return APP[r.COBRO]
        if r.COBRO.startswith('FCB'): return 'Nota de crédito'
        return 'Mostrador'
    df['CANAL']=df.apply(canal,axis=1)
    df['VENDEDOR']=df.VENDEDOR.replace({'46':'46.Sin usuario','3.Mozo':'3.Mozo (sin vendedora)','57.LARA':'57.PAULA'})
    df['H']=df.HORA.apply(lambda t:t.hour)
    return df,gen

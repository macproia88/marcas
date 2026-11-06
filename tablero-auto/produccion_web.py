"""Arma produccion.html: sugerido de la semana, control vendido vs sugerido y comportamiento diario por rubro.

Uso:  python3 tablero-auto/produccion_web.py
Lo corre solo actualizar.py (3 veces por día con los cierres de turno) y la tarea de producción de las 6:52.
Fuente: data/cierres.json (VENTAS POR ARTICULO de cada cierre de Maxi Rest, solo mostrador) y data/sugerido_hist.json
(el sugerido que se mandó cada mañana). El cálculo del sugerido es el mismo de produccion.py.
"""
import json, datetime as dt, pathlib, collections
from zoneinfo import ZoneInfo
import produccion as P

RAIZ = pathlib.Path(__file__).resolve().parent.parent
DATA = P.DATA
AR = ZoneInfo('America/Argentina/Buenos_Aires')
DIAS = ['lun', 'mar', 'mié', 'jue', 'vie', 'sáb', 'dom']


def datos():
    hoy = dt.datetime.now(AR).date()
    c = json.load(open(DATA / 'cierres.json')); mae = json.load(open(DATA / 'productos_maestro.json'))
    # ---- semana: sugerido de hoy a 6 días
    semana, dias_usados = [], {}
    prods = {}
    for i in range(7):
        t = hoy + dt.timedelta(days=i)
        filas, usados = P.sugerido(t.isoformat())
        semana.append(dict(fecha=t.isoformat(), lab=f'{DIAS[t.weekday()]} {t:%d/%m}', feriado=t.isoformat() in P.FERIADOS, dia29=t.day == 29))
        dias_usados[t.isoformat()] = {L: [dt.date.fromisoformat(x).strftime('%d/%m') for x in usados[L]] for L in P.LOCS}
        for r in filas:
            k = r['nombre']
            p = prods.setdefault(k, dict(n=r['nombre'], r=r['rubro'], kg=r['kg'], s={L: [0] * 7 for L in P.LOCS}, m={L: [0] * 7 for L in P.LOCS}))
            for L in P.LOCS:
                p['s'][L][i] += r['sug'][L]; p['m'][L][i] += round(r['mx'][L], 1)
    # ---- venta diaria de mostrador por local y producto (últimos 42 días)
    desde = (hoy - dt.timedelta(days=42)).isoformat()
    vend = collections.defaultdict(lambda: collections.defaultdict(float)); turnos = collections.defaultdict(list); rubro = {}; kgs = {}
    for x in c:
        if 'articulos' not in x or x['fecha'] < desde or x['fecha'] >= hoy.isoformat(): continue  # hoy todavía no cerró
        L = P.LOC.get(x['sucursal'], x['sucursal']); turnos[(L, x['fecha'])].append(x['turno'])
        for cod, nom, rub, q, imp in x['articulos']:
            if cod in P.EXCLUIR: continue
            m = mae.get(str(cod), {}); n = m.get('nombre') or nom; r = m.get('rubro') or rub
            if r in P.REVENTA: continue
            vend[(L, x['fecha'])][n] += q; rubro[n] = r
            kgs[n] = m.get('kg', kgs.get(n, abs(q - round(q)) > 1e-6))
    fechas = sorted({f for (_, f) in vend})
    diario = {L: {f: {} for f in fechas} for L in P.LOCS}
    for (L, f), d in vend.items():
        if L in diario:
            diario[L][f] = {n: round(q, 2) for n, q in d.items()}
    # ---- control: vendido vs sugerido de cada día que tiene sugerido guardado y cierres
    hp = DATA / 'sugerido_hist.json'; SH = json.load(open(hp)) if hp.exists() else {}
    sp = DATA / 'sugerido_sim.json'; SIM = json.load(open(sp)) if sp.exists() else {}
    SIMD = {f for f in SIM if f not in SH}            # días anteriores al primer sugerido mandado: recalculados hacia atrás
    SH = {**{f: SIM[f] for f in SIMD}, **SH}
    control = []
    for f in sorted(SH):
        if f >= hoy.isoformat(): continue
        for L in P.LOCS:
            if (L, f) not in turnos: continue
            sug = {k.split('|', 1)[1]: v for k, v in SH[f].items() if k.startswith(L + '|')}
            v = diario.get(L, {}).get(f, {})
            filas = []
            for n in set(sug) | set(v):
                s, q = sug.get(n, 0.0), v.get(n, 0.0)
                kg = kgs.get(n, False); tol = max(0.5 if kg else 1.0, 0.2 * s)
                est = 'ok' if abs(q - s) <= tol else ('mas' if q > s else 'menos')
                if q <= 0 and s >= (1.0 if kg else 3.0): est = 'cero'   # no se vendió nada: posible faltante
                filas.append([n, rubro.get(n, ''), kg, s, round(q, 2), est])
            control.append(dict(fecha=f, sim=f in SIMD, local=L, turnos=sorted(set(turnos[(L, f)])), filas=sorted(filas, key=lambda z: (z[1], z[0]))))
    meta = {n: [rubro.get(n, ''), bool(kgs.get(n, False))] for n in set(rubro)}
    for p in prods.values():
        meta.setdefault(p['n'], [p['r'], bool(p['kg'])])
    return dict(hoy=hoy.isoformat(), semana=semana, dias_usados=dias_usados, prods=list(prods.values()), fechas=fechas,
                diario=diario, turnos={f'{L}|{f}': sorted(set(t)) for (L, f), t in turnos.items()}, control=control, meta=meta,
                feriados=sorted(P.FERIADOS))


CSS = """:root{--bg:#f7f3ed;--panel:#fff;--fg:#2b211d;--muted:#6b625c;--line:#e7dfd6;--acc:#b85042;--dk:#3b2e2a;--ok:#2f6b4f;--okbg:#e6f2ea;--bad:#9a3f33;--badbg:#f6e3de;--hi:#fbf3e2}
@media (prefers-color-scheme:dark){:root{--bg:#1c1917;--panel:#26211e;--fg:#f2ece6;--muted:#b3a89f;--line:#3a332e;--acc:#e07a64;--dk:#f2ece6;--ok:#6fbf8f;--okbg:#20382b;--bad:#f0a08f;--badbg:#3d2420;--hi:#332a1f}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:8px 16px 30px}h1{font:400 30px/1.15 Georgia,serif;margin:6px 0 4px}h2{font-size:17px;margin:0 0 4px}
.sub,.note{color:var(--muted)}.note{font-size:13px;margin:0 0 10px}.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:14px}
.bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:10px 0 14px}.bar label{font-size:13px;color:var(--muted)}
select,input{font:inherit;font-size:14px;padding:6px 8px;border:1px solid var(--line);border-radius:8px;background:var(--panel);color:var(--fg)}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:999px;overflow:hidden}.seg button{font:inherit;font-size:13px;border:0;background:transparent;color:var(--fg);padding:6px 12px;cursor:pointer}
.seg button.on{background:var(--acc);color:#fff}
table{width:100%;border-collapse:collapse;font-size:13.5px}th,td{padding:6px 7px;border-bottom:1px solid var(--line);text-align:left}th{font-size:12px;color:var(--muted);font-weight:600;position:sticky;top:0;background:var(--panel)}
.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}.tw{overflow:auto;max-height:640px}tr.rub td{background:var(--hi);font-weight:700}
td.hoy,th.hoy{background:var(--hi)}td.ok{color:var(--ok)}td.mas{background:var(--badbg);color:var(--bad);font-weight:600}td.menos{background:var(--okbg);color:var(--ok);font-weight:600}td.cero{background:#fff2cc;color:#7a5a00;font-weight:700}
th.s{cursor:pointer;user-select:none}th.s:hover{color:var(--fg)}th.s::after{content:' ⇅';opacity:.35}th.s.desc::after{content:' ▼';opacity:1}th.s.asc::after{content:' ▲';opacity:1}
.kpis{display:flex;flex-wrap:wrap;gap:10px;margin:6px 0 12px}.kpi{flex:1 1 150px;border:1px solid var(--line);border-radius:10px;padding:10px 12px}.kpi b{display:block;font-size:22px;font-family:Georgia,serif}
.kpi span{font-size:12px;color:var(--muted)}.u{color:var(--muted);font-size:12px}svg text{fill:var(--muted);font-size:11px}.leg{font-size:12px;color:var(--muted)}
@media (max-width:640px){h1{font-size:23px}.card{padding:12px}table{font-size:12px}th,td{padding:5px 4px}}"""

JS = r"""
const D=window.__PROD__, LOCS=['Florida','Beccar','Paz'];
const fmt=(v,kg)=>v==null?'':(kg?(Math.round(v*10)/10).toLocaleString('es-AR',{minimumFractionDigits:1,maximumFractionDigits:1}):Math.round(v).toLocaleString('es-AR'));
const fd=s=>s.slice(8,10)+'/'+s.slice(5,7), DS=['dom','lun','mar','mié','jue','vie','sáb'];
const dname=s=>{const d=new Date(s+'T12:00:00');return DS[d.getDay()]+' '+fd(s)};
let LOC='Todos';
// ---------- ordenar tablas: tocar el título de una columna ordena de mayor a menor (otra vez: de menor a mayor)
const ORD={};
const num=t=>{t=(t||'').trim();if(!t)return null;const x=t.replace(/\./g,'').replace(',','.').replace('+','');return isNaN(+x)?null:+x};
function sortable(id){
  const box=document.getElementById(id),tb=box.querySelector('tbody'),ths=[...box.querySelectorAll('thead th')];
  ths.forEach((th,i)=>{th.classList.add('s');th.onclick=()=>{const o=ORD[id];ORD[id]={c:i,d:o&&o.c===i&&o.d==='desc'?'asc':'desc'};aplicar(id)}});
  aplicar(id);
}
function aplicar(id){
  const o=ORD[id];if(!o)return;const box=document.getElementById(id),tb=box.querySelector('tbody');if(!tb)return;
  box.querySelectorAll('thead th').forEach((th,i)=>{th.classList.toggle('desc',i===o.c&&o.d==='desc');th.classList.toggle('asc',i===o.c&&o.d==='asc')});
  const rows=[...tb.rows],grupos=[];let g=null;
  rows.forEach(r=>{if(r.classList.contains('rub')){g={h:r,rs:[]};grupos.push(g)}else{if(!g){g={h:null,rs:[]};grupos.push(g)}g.rs.push(r)}});
  const k=r=>{const t=r.cells[o.c]?r.cells[o.c].textContent:'';const n=num(t);return n==null?t.toLowerCase():n};
  const cmp=(a,b)=>{const x=k(a),y=k(b);if(typeof x==='number'&&typeof y==='number')return o.d==='desc'?y-x:x-y;if(typeof x==='number')return -1;if(typeof y==='number')return 1;return o.d==='desc'?y.localeCompare(x,'es'):x.localeCompare(y,'es')};
  if(grupos.length>1&&grupos.every(g=>g.h)){grupos.sort((a,b)=>cmp(a.h,b.h))}
  grupos.forEach(g=>{g.rs.sort(cmp);if(g.h)tb.appendChild(g.h);g.rs.forEach(r=>tb.appendChild(r))});
}
const rubros=[...new Set(Object.values(D.meta).map(m=>m[0]))].sort();
function sel(id,opts,all){const e=document.getElementById(id);e.innerHTML=(all?`<option value="">${all}</option>`:'')+opts.map(o=>`<option>${o}</option>`).join('');return e}
['f-rub','c-rub','g-rub'].forEach(id=>sel(id,rubros,id==='g-rub'?null:'Todos los rubros'));
document.getElementById('g-rub').value=rubros.includes('Ravioles')?'Ravioles':rubros[0];
document.querySelectorAll('.seg button').forEach(b=>b.onclick=()=>{document.querySelectorAll('.seg button').forEach(x=>x.classList.toggle('on',x===b));LOC=b.dataset.l;all()});
const val=(o,i)=>LOC==='Todos'?LOCS.reduce((a,L)=>a+o[L][i],0):o[LOC][i];
// ---------- 1. semana
function semana(){
  const rub=document.getElementById('f-rub').value, q=document.getElementById('f-q').value.toLowerCase(), modo=document.getElementById('f-modo').value;
  const key=modo==='max'?'m':'s';
  let ps=D.prods.filter(p=>(!rub||p.r===rub)&&(!q||p.n.toLowerCase().includes(q))).map(p=>({...p,v:[0,1,2,3,4,5,6].map(i=>val(p[key],i))})).filter(p=>p.v.some(x=>x>0));
  const g={};ps.forEach(p=>{(g[p.r+'|'+(p.kg?'kg':'u')]=g[p.r+'|'+(p.kg?'kg':'u')]||[]).push(p)});
  let h='<table><thead><tr><th>Producto</th><th>Un.</th>'+D.semana.map((d,i)=>`<th class="n ${i===0?'hoy':''}">${d.lab}${d.feriado?' (feriado)':''}${d.dia29?' (29)':''}</th>`).join('')+'<th class="n">Semana</th></tr></thead><tbody>';
  Object.keys(g).sort().forEach(k=>{const [r,u]=k.split('|'),kg=u==='kg',arr=g[k].sort((a,b)=>b.v.reduce((x,y)=>x+y)-a.v.reduce((x,y)=>x+y));
    const tot=[0,1,2,3,4,5,6].map(i=>arr.reduce((a,p)=>a+p.v[i],0));
    h+=`<tr class="rub"><td>${r}</td><td>${u}</td>`+tot.map((v,i)=>`<td class="n ${i===0?'hoy':''}">${fmt(v,kg)}</td>`).join('')+`<td class="n">${fmt(tot.reduce((a,b)=>a+b),kg)}</td></tr>`;
    arr.forEach(p=>{h+=`<tr><td>${p.n}</td><td class="u">${u}</td>`+p.v.map((v,i)=>`<td class="n ${i===0?'hoy':''}">${v?fmt(v,kg):''}</td>`).join('')+`<td class="n">${fmt(p.v.reduce((a,b)=>a+b),kg)}</td></tr>`})});
  document.getElementById('t-sem').innerHTML=h+'</tbody></table>';sortable('t-sem');
  const du=D.dias_usados[D.semana[0].fecha];
  document.getElementById('n-sem').textContent='Hoy sale de: '+LOCS.filter(L=>LOC==='Todos'||L===LOC).map(L=>`${L} ${du[L].join(', ')||'sin datos'}`).join(' · ')+'.';
}
// ---------- 2. control
function control(){
  const fs=[...new Set(D.control.map(c=>c.fecha))].sort().reverse(), fe=document.getElementById('c-dia');
  if(!fs.length){document.getElementById('t-ctl').innerHTML='<p class="note">Todavía no hay días para comparar: la primera comparación es la venta del lunes 02/11, que aparece cuando lleguen sus cierres.</p>';document.getElementById('k-ctl').innerHTML='';return}
  if(!fe.options.length){fe.innerHTML=fs.map(f=>`<option value="${f}">${dname(f)}${D.control.find(c=>c.fecha===f&&c.sim)?' (recalculado)':''}</option>`).join('')}
  const f=fe.value||fs[0], rub=document.getElementById('c-rub').value, solo=document.getElementById('c-dif').checked;
  const cs=D.control.filter(c=>c.fecha===f&&(LOC==='Todos'||c.local===LOC));
  let n=0,ok=0,mas=0,men=0,cer=0,rows=[];
  cs.forEach(c=>c.filas.forEach(r=>{if(rub&&r[1]!==rub)return;n++;if(r[5]==='ok')ok++;else if(r[5]==='mas')mas++;else if(r[5]==='cero')cer++;else men++;if(!solo||r[5]!=='ok')rows.push([c.local,...r])}));
  document.getElementById('k-ctl').innerHTML=`<div class="kpi"><b>${n?Math.round(ok/n*100):0}%</b><span>productos dentro del sugerido (${ok} de ${n})</span></div><div class="kpi"><b>${mas}</b><span>vendieron más que el sugerido</span></div><div class="kpi"><b>${men}</b><span>vendieron menos (posible sobrante)</span></div><div class="kpi"><b>${cer}</b><span>no se vendió nada: ¿faltó? (revisar con el local)</span></div>`
   +`<div class="kpi"><b style="font-size:15px">${cs.map(c=>c.local+': '+c.turnos.join(', ')).join('<br>')||'sin cierres'}</b><span>turnos leídos</span></div>`;
  rows.sort((a,b)=>Math.abs(b[5]-b[4])-Math.abs(a[5]-a[4]));
  let h='<table><thead><tr><th>Local</th><th>Rubro</th><th>Producto</th><th class="n">Sugerido</th><th class="n">Vendido</th><th class="n">Diferencia</th><th>Qué pasó</th></tr></thead><tbody>';
  const tx={ok:'Dentro del sugerido',mas:'Vendió más',menos:'Vendió menos',cero:'No se vendió nada: ¿faltó?'};
  rows.forEach(r=>{const kg=r[3],d=r[5]-r[4];h+=`<tr><td>${r[0]}</td><td>${r[2]}</td><td>${r[1]}</td><td class="n">${fmt(r[4],kg)}</td><td class="n">${fmt(r[5],kg)}</td><td class="n ${r[6]}">${d>0?'+':''}${fmt(d,kg)}</td><td class="${r[6]}">${tx[r[6]]}</td></tr>`});
  document.getElementById('t-ctl').innerHTML=h+'</tbody></table>';sortable('t-ctl');
}
// ---------- 3. comportamiento
function graf(){
  const rub=document.getElementById('g-rub').value, el=document.getElementById('g-svg'), F=D.fechas;
  const kgR=Object.entries(D.meta).some(([n,m])=>m[0]===rub&&m[1]);
  const day=(L,f)=>Object.entries(D.diario[L][f]||{}).reduce((a,[n,q])=>a+(D.meta[n]&&D.meta[n][0]===rub&&D.meta[n][1]===kgR?q:0),0);
  const has=(L,f)=>!!D.turnos[L+'|'+f];
  const Ls=LOC==='Todos'?LOCS:[LOC], col={Florida:'#b85042',Beccar:'#3b2e2a',Paz:'#9db59a'};
  const W=Math.max(640,F.length*22),H=260,pl=44,pb=40,pt=12,vals=[];
  Ls.forEach(L=>F.forEach(f=>{if(has(L,f))vals.push(day(L,f))}));const mx=Math.max(1,...vals);
  const x=i=>pl+i*(W-pl-10)/Math.max(1,F.length-1), y=v=>pt+(H-pt-pb)*(1-v/mx);
  let s=`<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-label="Venta diaria de ${rub}">`;
  for(let k=0;k<=4;k++){const v=mx*k/4;s+=`<line x1="${pl}" x2="${W-10}" y1="${y(v)}" y2="${y(v)}" stroke="currentColor" stroke-opacity=".12"/><text x="${pl-6}" y="${y(v)+4}" text-anchor="end">${fmt(v,kgR)}</text>`}
  F.forEach((f,i)=>{const d=new Date(f+'T12:00:00');if(d.getDay()===1)s+=`<line x1="${x(i)}" x2="${x(i)}" y1="${pt}" y2="${H-pb}" stroke="currentColor" stroke-opacity=".18" stroke-dasharray="3 3"/>`;
    if(i%2===0||F.length<20)s+=`<text x="${x(i)}" y="${H-pb+14}" text-anchor="middle">${DS[d.getDay()].slice(0,2)}</text><text x="${x(i)}" y="${H-pb+27}" text-anchor="middle">${fd(f)}</text>`});
  Ls.forEach(L=>{let pts=F.map((f,i)=>has(L,f)?[x(i),y(day(L,f))]:null);let p='',seg=[];pts.forEach(q=>{if(q)seg.push(q);else if(seg.length){p+=`M${seg.map(z=>z.join(',')).join('L')}`;seg=[]}});if(seg.length)p+=`M${seg.map(z=>z.join(',')).join('L')}`;
    s+=`<path d="${p}" fill="none" stroke="${col[L]}" stroke-width="2.2"/>`+pts.filter(Boolean).map(q=>`<circle cx="${q[0]}" cy="${q[1]}" r="2.6" fill="${col[L]}"/>`).join('')});
  el.innerHTML=s+'</svg>';
  document.getElementById('g-leg').innerHTML=Ls.map(L=>`<span style="color:${col[L]}">●</span> ${L}`).join(' &nbsp; ')+` · ${rub} en ${kgR?'kg':'unidades'} · línea punteada = lunes · los días sin cierre del local quedan en blanco`;
}
function all(){semana();control();graf()}
['f-rub','f-q','f-modo'].forEach(i=>document.getElementById(i).oninput=semana);
['c-dia','c-rub','c-dif'].forEach(i=>document.getElementById(i).oninput=control);
document.getElementById('g-rub').oninput=graf;
all();
"""


def armar():
    D = datos()
    hoy = dt.date.fromisoformat(D['hoy'])
    html = f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Producción por datos</title><style>{CSS}</style></head><body>
<div class="wrap"><h1>Producción por datos</h1>
<p class="sub">Cuánto producir cada día según lo que se vende en mostrador, el control de cómo salió y el comportamiento de cada rubro · La Presumida Florida, Beccar y Pastas Paz · sin apps (Maxi carga PedidosYa y Rappi juntos en el código 202).</p>
<div class="bar"><span class="seg"><button class="on" data-l="Todos">Los 3 locales</button><button data-l="Florida">Florida</button><button data-l="Beccar">Beccar</button><button data-l="Paz">Paz</button></span></div>
<section class="card"><h2>Sugerido de la semana</h2>
<p class="note">Para cada día: mediana (el valor del medio) de lo vendido en mostrador los últimos 4 días iguales de la semana que sirven de referencia, por local, redondeada para arriba (unidades enteras, kg al medio kilo). Se dejan afuera feriados, días especiales como el Día de la Madre, días con turnos faltantes y días que vendieron 35% más o 40% menos de lo normal; el día 29 se compara con los 29 anteriores. "Máximo" muestra el mejor de esos días, para cubrirse. La columna resaltada es hoy. Tocá el título de cualquier columna para ordenar de mayor a menor (dentro de cada rubro).</p>
<div class="bar"><label>Rubro</label><select id="f-rub"></select><label>Buscar</label><input id="f-q" placeholder="producto"><label>Ver</label><select id="f-modo"><option value="s">Sugerido (mediana)</option><option value="max">Máximo de los 4 días</option></select></div>
<p class="note" id="n-sem"></p><div class="tw" id="t-sem"></div></section>
<section class="card"><h2>Control: vendido contra sugerido</h2>
<p class="note">Lo que se vendió en mostrador cada día contra el sugerido que se mandó esa mañana. Dentro = diferencia de hasta 20% (mínimo 1 unidad o 0,5 kg). Vendió más: se produjo de más y se vendió, o faltó. Vendió menos: posible sobrante. Los días antes del 02/11 dicen "(recalculado)": es el sugerido que se hubiera mandado esa mañana con los cierres que había hasta el día anterior (en las primeras semanas de octubre, con 1 a 3 semanas de historia). Cero con sugerido de 3 unidades o 1 kg o más: no se vendió nada, revisar si faltó. Tocá el título de cualquier columna para ordenar de mayor a menor.</p>
<div class="bar"><label>Día</label><select id="c-dia"></select><label>Rubro</label><select id="c-rub"></select><label><input type="checkbox" id="c-dif" checked> solo diferencias</label></div>
<div class="kpis" id="k-ctl"></div><div class="tw" id="t-ctl"></div></section>
<section class="card"><h2>Comportamiento día por día</h2>
<p class="note">Venta diaria de mostrador del rubro elegido, por local, en las últimas semanas. Sirve para ver qué días de la semana se vende más y si un producto viene subiendo o bajando.</p>
<div class="bar"><label>Rubro</label><select id="g-rub"></select></div>
<div class="tw" id="g-svg"></div><p class="leg" id="g-leg"></p></section>
<p class="note">Fuente: mails "Fin de turno" de Maxi Rest de cada local (sección venta por artículo), que se leen 3 veces por día. Paz: cierres de septiembre y desde el 24/10. Datos al {hoy:%d/%m/%Y}.</p>
</div>
<script>window.__PROD__={json.dumps(D, ensure_ascii=False, separators=(',', ':'))};</script>
<script>{JS}</script>
</body></html>"""
    (RAIZ / 'produccion.html').write_text(html, encoding='utf-8')
    print('produccion.html', len(html) // 1024, 'KB', len(D['prods']), 'productos', len(D['control']), 'controles')


if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    armar()
    import nav, sello
    nav.main(); sello.sellar(RAIZ / 'produccion.html', dt.datetime.now(sello.AR))

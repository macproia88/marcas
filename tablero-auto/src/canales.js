let LOCAL = 'Todos';
const LOCS = ['Florida', 'Beccar', 'Paz'];
const COL = { Florida: '#b85042', Beccar: '#3b2e2a', Paz: '#8c6b3f', PedidosYa: '#b85042', Rappi: '#8c6b3f', y25: '#9a928b' };
const DS = ['Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sá', 'Do'];
const MES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
const nf = (x) => Math.round(x).toLocaleString('es-AR');
const mf = (x) => '$' + (x / 1e6).toLocaleString('es-AR', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + 'M';
const pf = (x, d = 0) => (x * 100).toLocaleString('es-AR', { minimumFractionDigits: d, maximumFractionDigits: d }) + '%';
const sel = (rows) => rows.filter((r) => LOCAL === 'Todos' || r.local === LOCAL);
const sum = (rows, f) => rows.reduce((s, r) => s + (+r[f] || 0), 0);
const el = (tag, attrs = {}, kids = []) => { const e = document.createElement(tag); for (const [k, v] of Object.entries(attrs)) { if (k === 'text') e.textContent = v; else e.setAttribute(k, v); } kids.forEach((k) => e.appendChild(k)); return e; };
let tip;
function showTip(ev, t) { if (!tip) { tip = el('div', { class: 'tip' }); document.body.appendChild(tip); } tip.textContent = t; tip.style.display = 'block'; const x = Math.min(ev.clientX + 12, window.innerWidth - tip.offsetWidth - 8); tip.style.left = x + 'px'; tip.style.top = (ev.clientY + 12) + 'px'; }
function hideTip() { if (tip) tip.style.display = 'none'; }
function card(id, title, note, wide) { const c = el('section', { class: 'card', id }); c.appendChild(el('h2', { text: title })); if (note) c.appendChild(el('p', { class: 'note', text: note })); return c; }
function width(c) { return Math.max(300, c.clientWidth - 32); }

function hbars(c, items, fmt, color) {
  const W = width(c), lw = Math.min(260, W * 0.42), bh = 24, H = items.length * bh + 6;
  const x = d3.scaleLinear().domain([0, d3.max(items, (d) => d.v) || 1]).range([0, W - lw - 70]);
  const s = d3.select(c).append('svg').attr('viewBox', `0 0 ${W} ${H}`);
  const g = s.selectAll('g').data(items).join('g').attr('transform', (d, i) => `translate(0,${i * bh})`);
  g.append('text').attr('x', lw - 8).attr('y', 16).attr('text-anchor', 'end').text((d) => d.k.length > 38 ? d.k.slice(0, 37) + '…' : d.k);
  g.append('rect').attr('x', lw).attr('y', 4).attr('height', bh - 8).attr('rx', 3).attr('width', (d) => x(d.v)).attr('fill', (d) => d.c || color || COL.Florida)
    .on('mousemove', (ev, d) => showTip(ev, d.k + ': ' + fmt(d.v) + (d.t ? ' · ' + d.t : ''))).on('mouseleave', hideTip);
  g.append('text').attr('x', (d) => lw + x(d.v) + 6).attr('y', 16).text((d) => fmt(d.v) + (d.t ? '  ' + d.t : ''));
}

function vbars(c, cats, series, fmt, opts = {}) {
  // series: [{name, color, values[]}] apiladas; opts.line: {name, color, values[]}
  const W = width(c), H = opts.h || 240, m = { t: 18, r: 8, b: 34, l: 44 };
  const tot = cats.map((_, i) => series.reduce((s, se) => s + (se.values[i] || 0), 0));
  const mx = d3.max([...tot, ...(opts.line ? opts.line.values.filter((v) => v != null) : [])]) || 1;
  const x = d3.scaleBand().domain(cats.map((_, i) => i)).range([m.l, W - m.r]).padding(0.2);
  const y = d3.scaleLinear().domain([0, mx * 1.12]).nice().range([H - m.b, m.t]);
  const s = d3.select(c).append('svg').attr('viewBox', `0 0 ${W} ${H}`);
  s.append('g').attr('class', 'axis').attr('transform', `translate(${m.l},0)`).call(d3.axisLeft(y).ticks(5).tickFormat((v) => fmt(v)));
  const step = Math.ceil(cats.length / Math.max(1, Math.floor((W - m.l) / 34)));
  s.append('g').attr('class', 'axis').attr('transform', `translate(0,${H - m.b})`).call(d3.axisBottom(x).tickFormat((i) => (i % step ? '' : cats[i])).tickSizeOuter(0))
    .selectAll('text').each(function (i) { const t = d3.select(this); const parts = String(cats[i]).split('\n'); if (i % step) return; t.text(null); parts.forEach((p, k) => t.append('tspan').attr('x', 0).attr('dy', k ? '1.1em' : '0.8em').text(p)); });
  const base = cats.map(() => 0);
  series.forEach((se) => {
    s.append('g').selectAll('rect').data(se.values).join('rect').attr('x', (_, i) => x(i)).attr('width', x.bandwidth())
      .attr('y', (v, i) => y(base[i] + (v || 0))).attr('height', (v, i) => y(base[i]) - y(base[i] + (v || 0))).attr('fill', se.color)
      .on('mousemove', (ev, v) => { const i = se.values.indexOf(v); showTip(ev, `${String(cats[i]).replace('\n', ' ')} · ${se.name}: ${fmt(v)}`); }).on('mouseleave', hideTip)
      .each((v, i) => { base[i] += v || 0; });
  });
  if (opts.labels !== false && cats.length <= 14) s.append('g').selectAll('text').data(tot).join('text').attr('x', (_, i) => x(i) + x.bandwidth() / 2).attr('y', (v) => y(v) - 4).attr('text-anchor', 'middle').attr('font-size', 11).text((v) => fmt(v));
  if (opts.line) {
    const ln = d3.line().defined((v) => v != null).x((_, i) => x(i) + x.bandwidth() / 2).y((v) => y(v));
    s.append('path').attr('d', ln(opts.line.values)).attr('fill', 'none').attr('stroke', opts.line.color).attr('stroke-width', 2).attr('stroke-dasharray', '4 3');
  }
  const leg = el('div', { class: 'leg' });
  [...series, ...(opts.line ? [opts.line] : [])].forEach((se) => { if (series.length > 1 || opts.line) { const sp = el('span'); sp.appendChild(el('i', { style: `background:${se.color}` })); sp.appendChild(document.createTextNode(se.name)); leg.appendChild(sp); } });
  c.appendChild(leg);
}

function heat(c, rows, campo, fmt) {
  const hs = [...new Set(rows.map((r) => r.hora))].sort((a, b) => a - b);
  if (!hs.length) return;
  const hmin = d3.min(hs), hmax = d3.max(hs), H0 = d3.range(hmin, hmax + 1);
  const val = {}; rows.forEach((r) => { const k = r.dia + '-' + r.hora; val[k] = (val[k] || 0) + r[campo]; });
  const W = width(c), cw = (W - 30) / H0.length, ch = 26, H = ch * 7 + 22;
  const mx = d3.max(Object.values(val)) || 1;
  const col = d3.scaleSequential([0, mx], d3.interpolateRgb('#f6e3de', '#a33a2c'));
  const s = d3.select(c).append('svg').attr('viewBox', `0 0 ${W} ${H}`);
  H0.forEach((h, j) => s.append('text').attr('x', 30 + j * cw + cw / 2).attr('y', 12).attr('text-anchor', 'middle').attr('font-size', 10).attr('fill', 'currentColor').text(h + 'h'));
  for (let d = 0; d < 7; d++) {
    s.append('text').attr('x', 0).attr('y', 22 + d * ch + 17).attr('font-size', 11).text(DS[d]);
    H0.forEach((h, j) => {
      const v = val[d + '-' + h] || 0;
      s.append('rect').attr('x', 30 + j * cw + 1).attr('y', 22 + d * ch + 1).attr('width', cw - 2).attr('height', ch - 2).attr('rx', 3).attr('fill', v ? col(v) : 'transparent').attr('stroke', 'var(--line)')
        .on('mousemove', (ev) => showTip(ev, `${DS[d]} ${h} a ${h + 1} h: ${fmt(v)}`)).on('mouseleave', hideTip);
      if (v && cw > 22) s.append('text').attr('x', 30 + j * cw + cw / 2).attr('y', 22 + d * ch + 17).attr('text-anchor', 'middle').attr('font-size', 10).attr('fill', v > mx * 0.55 ? '#fff' : '#3b2e2a').text(fmt(v));
    });
  }
}

function table(c, head, rows) {
  const tw = el('div', { class: 'tw' }), t = el('table'), th = el('thead'), tr = el('tr');
  head.forEach((h) => tr.appendChild(el('th', { text: h }))); th.appendChild(tr); t.appendChild(th);
  const tb = el('tbody'); rows.forEach((r) => { const x = el('tr'); r.forEach((v) => { const td = el('td'); if (v && v.cls) { td.textContent = v.t; td.className = v.cls; } else td.textContent = v; x.appendChild(td); }); tb.appendChild(x); });
  t.appendChild(tb); tw.appendChild(t); c.appendChild(tw);
}

function kpis(list) { const k = document.getElementById('kpis'); k.replaceChildren(); list.forEach(([a, b, c]) => { const d = el('div', { class: 'kpi' }); d.appendChild(el('div', { class: 'k', text: a })); d.appendChild(el('div', { class: 'v', text: b })); d.appendChild(el('div', { class: 'd', text: c || '' })); k.appendChild(d); }); }
function textos() { const u = document.getElementById('txt'); u.replaceChildren(); (D.textos[LOCAL] || []).forEach((t) => u.appendChild(el('li', { text: t }))); }
function diaLabel(f) { const d = new Date(f + 'T12:00:00'); return DS[(d.getDay() + 6) % 7] + '\n' + d.getDate(); }
function mesesSerie(campo) {
  const ms = [...new Set(D.men.map((r) => r.mes))].filter((m) => m >= '2026-01').sort();
  return { cats: ms.map((m) => MES[+m.slice(5) - 1]), series: (LOCAL === 'Todos' ? LOCS : [LOCAL]).map((L) => ({ name: L, color: COL[L], values: ms.map((m) => { const r = D.men.find((x) => x.mes === m && x.local === L); return r ? r[campo] : 0; }) })) };
}
function arrancar(dibujar) {
  document.querySelectorAll('#loc button').forEach((b) => b.addEventListener('click', () => { LOCAL = b.dataset.l; document.querySelectorAll('#loc button').forEach((x) => x.setAttribute('aria-pressed', String(x === b))); dibujar(); }));
  let w = window.innerWidth; window.addEventListener('resize', () => { if (Math.abs(window.innerWidth - w) > 40) { w = window.innerWidth; dibujar(); } });
  dibujar();
}

function paginaApps() {
  const A = D.apps;
  arrancar(() => {
    textos();
    const dias = sel(A.dias), ped = sum(dias, 'pedidos'), nd = new Set(A.dias.map((r) => r.fecha)).size;
    const py = sel(A.plata).filter((r) => r.app === 'PedidosYa'), ra = sel(A.plata).filter((r) => r.app === 'Rappi');
    const vpy = sum(py, 'venta'), vra = sum(ra, 'venta'), npy = sum(py, 'pedidos'), nra = sum(ra, 'pedidos');
    const rec = sel(A.reclamos), tiempos = sel(A.tiempos), can = sel(A.canasta);
    kpis([['Pedidos del mes', nf(ped), nf(ped / nd) + ' por día'], ['Venta en apps', mf(vpy + vra), 'PedidosYa ' + mf(vpy) + ' · Rappi ' + mf(vra)],
      ['Ticket promedio', '$' + nf((vpy + vra) / (npy + nra)), 'PedidosYa $' + nf(vpy / npy) + (nra ? ' · Rappi $' + nf(vra / nra) : '')],
      ['Vuelve al local (PedidosYa)', pf(sum(py, 'neto') / vpy), mf(sum(py, 'neto')) + ' de ' + mf(vpy)],
      ['Reclamos', (sum(rec, 'reclamos') / sum(rec, 'pedidos') * 100).toLocaleString('es-AR', { maximumFractionDigits: 1 }) + ' cada 100', nf(sum(rec, 'reclamos')) + ' reclamos en PedidosYa'],
      ['Preparación (mediana)', (LOCAL === 'Todos' ? d3.median(tiempos, (t) => t.preparacion) : tiempos[0].preparacion) + ' min', 'de aceptado a listo para retirar']]);
    const S = document.getElementById('secs'); S.replaceChildren();
    // día por día
    const fechas = [...new Set(A.dias.map((r) => r.fecha))].sort();
    let c = card('c-dias', 'Pedidos día por día', 'PedidosYa (entregados) + Rappi (terminados). Pasá el mouse por una barra para ver el número.'); S.appendChild(c);
    vbars(c, fechas.map(diaLabel), [{ name: 'PedidosYa', color: COL.PedidosYa, values: fechas.map((f) => sum(dias.filter((r) => r.fecha === f), 'pedidosya')) }, { name: 'Rappi', color: COL.Rappi, values: fechas.map((f) => sum(dias.filter((r) => r.fecha === f), 'rappi')) }], nf, { labels: false });
    // mes a mes
    c = card('c-mes', 'Pedidos mes a mes', 'Pedidos de apps por mes. Enero a mayo de Beccar y Paz son estimados (venta de apps ÷ ticket); desde junio, reales.'); S.appendChild(c);
    const mm = mesesSerie('pedidos'); vbars(c, mm.cats, mm.series, nf);
    // horas
    c = card('c-hora', 'A qué hora y qué día piden', 'Pedidos del mes en cada franja de una hora (PedidosYa + Rappi). Más oscuro = más pedidos.'); S.appendChild(c);
    heat(c, sel(A.horas), 'pedidos', nf);
    // productos y agregados
    const g = el('div', { class: 'grid2' }); S.appendChild(g);
    c = card('c-prod', 'Qué es lo que más se vende', 'PedidosYa, unidades del mes. Producto como figura en el menú de la app.'); const c2a = card('c-agr', 'Qué le agregan al pedido', 'Opciones elegidas dentro de cada producto (salsa, queso, relleno, guarnición). Unidades del mes en PedidosYa.'); g.append(c, c2a);
    const pr = {}; sel(A.productos).forEach((r) => { pr[r.producto] = (pr[r.producto] || 0) + r.unidades; });
    hbars(c, Object.entries(pr).sort((a, b) => b[1] - a[1]).slice(0, 15).map(([k, v]) => ({ k, v })), nf);
    c = c2a;
    const ag = {}; sel(A.agregados).forEach((r) => { ag[r.agregado] = (ag[r.agregado] || 0) + r.unidades; });
    hbars(c, Object.entries(ag).sort((a, b) => b[1] - a[1]).slice(0, 12).map(([k, v]) => ({ k, v })), nf, COL.Paz);
    // cómo compra
    const g2 = el('div', { class: 'grid2' }); S.appendChild(g2);
    c = card('c-bandas', 'Cuánto gasta cada pedido', 'PedidosYa: pedidos según el total del pedido. Al lado, qué parte de la plata del mes aportan.'); const c2b = card('c-plata', 'Lo que queda en el bolsillo (PedidosYa)', 'De la venta del mes: comisión de PedidosYa, descuentos y vales que paga el local, otros cargos y lo que deposita la app (ingreso estimado del reporte).'); g2.append(c, c2b);
    const bd = {}; sel(A.bandas).forEach((r) => { bd[r.orden] = bd[r.orden] || { k: r.banda, v: 0, venta: 0 }; bd[r.orden].v += r.pedidos; bd[r.orden].venta += r.venta; });
    const tv = Object.values(bd).reduce((s, b) => s + b.venta, 0), tp = Object.values(bd).reduce((s, b) => s + b.v, 0);
    hbars(c, Object.keys(bd).sort().map((k) => ({ k: bd[k].k, v: bd[k].v, t: `${pf(bd[k].v / tp)} de los pedidos · ${pf(bd[k].venta / tv)} de la plata` })), nf, COL.Beccar);
    const up = LOCAL === 'Todos' ? d3.mean(can, (r) => r.unidades_pedido) : can[0].unidades_pedido;
    c.appendChild(el('p', { class: 'note', text: `En promedio cada pedido lleva ${up.toLocaleString('es-AR', { maximumFractionDigits: 1 })} productos (sin contar los agregados).` }));
    c = c2b;
    const pl = ['venta', 'comision', 'descuentos', 'publicidad', 'otros', 'neto'].map((f) => sum(py, f));
    table(c, ['Concepto', 'Pesos', '% de la venta'], [['Venta', mf(pl[0]), '100%'], ['Comisión', mf(pl[1]), pf(pl[1] / pl[0])], ['Descuentos que paga el local', mf(pl[2]), pf(pl[2] / pl[0])], ['Publicidad', mf(pl[3]), pf(pl[3] / pl[0])], ['Otros cargos', mf(pl[4]), pf(pl[4] / pl[0])], [{ t: 'Vuelve al local', cls: 'good' }, { t: mf(pl[5]), cls: 'good' }, { t: pf(pl[5] / pl[0]), cls: 'good' }]]);
    // reclamos y servicio
    c = card('c-rec', 'Reclamos y servicio', 'PedidosYa. Reclamos por motivo, cancelados y tiempos. Menos es mejor.'); S.appendChild(c);
    const rows = (LOCAL === 'Todos' ? LOCS : [LOCAL]).map((L) => { const r = A.reclamos.find((x) => x.local === L), t = A.tiempos.find((x) => x.local === L), k = A.cancelados.find((x) => x.local === L);
      return [L, nf(r.pedidos), (r.reclamos / r.pedidos * 100).toLocaleString('es-AR', { maximumFractionDigits: 1 }), nf(r['Producto faltante'] || 0), nf(r['Producto incorrecto'] || 0), nf(r['Orden equivocada'] || 0), nf(r['Calidad de la comida'] || 0), nf(k.cancelados), t.preparacion + ' min', pf(t.prep_mas_20), t.total + ' min']; });
    table(c, ['Local', 'Pedidos', 'Reclamos c/100', 'Faltante', 'Incorrecto', 'Orden equivocada', 'Calidad', 'Cancelados', 'Preparación', 'Tardan +20 min', 'Pedido a entrega'], rows);
    document.getElementById('pie').textContent = 'Fuentes: PedidosYa (detalle de pedidos, estado "Entregado") y Rappi (estado "Terminada") del mes; pedidos por mes del tablero La Presumida. Productos, agregados, plata, reclamos y tiempos: solo PedidosYa (Rappi no trae ese detalle).';
  });
}

function paginaMostrador() {
  const Mo = D.mo;
  arrancar(() => {
    textos();
    const dias = sel(D.dias), tk = sum(dias, 'tickets'), vm = sum(dias, 'venta'), nd = new Set(D.dias.map((r) => r.fecha)).size;
    const d25 = dias.filter((r) => r.tickets_2025 != null), t25 = sum(d25, 'tickets_2025'), t26 = sum(d25, 'tickets');
    const cl = sel(D.club), vc = sum(cl, 'venta_club'), vcm = sum(cl, 'venta_mostrador'), nc = sum(cl, 'tickets_club'), tkc = sum(cl, 'tickets');
    kpis([['Clientes del mes', nf(tk), nf(tk / nd) + ' por día'], ['Venta de mostrador', mf(vm), 'sin apps'], ['Ticket promedio', '$' + nf(vm / tk), 'mostrador'],
      ['Clientes vs 2025', (t26 / t25 - 1 >= 0 ? '+' : '') + pf(t26 / t25 - 1, 1), 'mismos días de la semana' + (LOCAL === 'Paz' || LOCAL === 'Todos' ? ' (Paz desde el 13/10)' : '')],
      ['Venta del club', pf(vc / vcm), 'socio gasta ' + pf((vc / nc) / ((vcm - vc) / (tkc - nc)) - 1) + ' más']]);
    const S = document.getElementById('secs'); S.replaceChildren();
    const fechas = [...new Set(D.dias.map((r) => r.fecha))].sort();
    let c = card('c-dias', 'Clientes día por día', 'Tickets de mostrador (cierres de caja de Maxi Rest). Línea: mismo día de la semana de 2025.'); S.appendChild(c);
    vbars(c, fechas.map(diaLabel), [{ name: '2026', color: COL.Florida, values: fechas.map((f) => sum(dias.filter((r) => r.fecha === f), 'tickets')) }], nf,
      { labels: false, line: { name: '2025', color: COL.y25, values: fechas.map((f) => { const r = dias.filter((x) => x.fecha === f); return r.some((x) => x.tickets_2025 == null) ? null : sum(r, 'tickets_2025'); }) } });
    c = card('c-mes', 'Clientes por día, mes a mes', 'Promedio de tickets de mostrador por día en cada mes.'); S.appendChild(c);
    const ms = [...new Set(D.men.map((r) => r.mes))].sort();
    vbars(c, ms.map((m) => MES[+m.slice(5) - 1]), (LOCAL === 'Todos' ? LOCS : [LOCAL]).map((L) => ({ name: L, color: COL[L], values: ms.map((m) => { const r = D.men.find((x) => x.mes === m && x.local === L); return r && r.dias ? r.tickets / r.dias : 0; }) })), nf);
    c = card('c-tk', 'Ticket promedio, mes a mes', 'Venta de mostrador ÷ tickets de mostrador.'); S.appendChild(c);
    const g0 = ms.map((m) => { const r = sel(D.men.filter((x) => x.mes === m && x.local !== 'Todos')); return sum(r, 'tickets') ? sum(r, 'venta_mostrador') / sum(r, 'tickets') : 0; });
    vbars(c, ms.map((m) => MES[+m.slice(5) - 1]), [{ name: 'Ticket', color: COL.Beccar, values: g0 }], (v) => '$' + nf(v / 1000) + 'k');
    c = card('c-hora', 'A qué hora y qué día vienen', 'Clientes promedio en un día, por franja de una hora (1 al 25 de octubre, venta detallada de Maxi Rest).'); S.appendChild(c);
    heat(c, sel(Mo.horas), 'tickets', (v) => nf(v));
    const g = el('div', { class: 'grid2' }); S.appendChild(g);
    c = card('c-cobro', 'Cómo paga', 'De cada 100 tickets de mostrador (1 al 25 de octubre).'); const c3 = card('c-bandas', 'Cuánto gasta cada cliente', 'Tickets según el total. Al lado, qué parte de la venta aportan (1 al 25 de octubre).'); g.append(c, c3);
    const co = {}; sel(Mo.cobro).forEach((r) => { co[r.forma] = (co[r.forma] || 0) + r.tickets; }); const tco = Object.values(co).reduce((a, b) => a + b, 0);
    hbars(c, Object.entries(co).sort((a, b) => b[1] - a[1]).map(([k, v]) => ({ k, v: v / tco })), (v) => pf(v), COL.Beccar);
    c = c3;
    const bd = {}; sel(Mo.bandas).forEach((r) => { bd[r.orden] = bd[r.orden] || { k: r.banda, v: 0, venta: 0 }; bd[r.orden].v += r.tickets; bd[r.orden].venta += r.venta; });
    const tv = Object.values(bd).reduce((s, b) => s + b.venta, 0), tp = Object.values(bd).reduce((s, b) => s + b.v, 0);
    hbars(c, Object.keys(bd).sort().map((k) => ({ k: bd[k].k, v: bd[k].v, t: `${pf(bd[k].v / tp)} · ${pf(bd[k].venta / tv)} de la venta` })), nf, COL.Paz);
    const g2 = el('div', { class: 'grid2' }); S.appendChild(g2);
    c = card('c-top', 'Qué es lo que más se vende', 'Top 15 de mostrador por venta en pesos (1 al 22 de octubre, venta por rubro de Maxi Rest, a precio de lista). Fideos incluye el kilo de regalo de la bienvenida del club.'); const c4 = card('c-rubro', 'Por rubro', 'Venta de mostrador por rubro (1 al 22 de octubre).'); g2.append(c, c4);
    const tp2 = {}; sel(D.top).forEach((r) => { tp2[r.articulo] = (tp2[r.articulo] || 0) + r.venta; });
    hbars(c, Object.entries(tp2).sort((a, b) => b[1] - a[1]).slice(0, 15).map(([k, v]) => ({ k, v })), mf);
    c = c4;
    const rb = {}; sel(D.top).forEach((r) => { rb[r.rubro] = (rb[r.rubro] || 0) + r.venta; });
    hbars(c, Object.entries(rb).sort((a, b) => b[1] - a[1]).slice(0, 15).map(([k, v]) => ({ k, v })), mf, COL.Beccar);
    c = card('c-club', 'Socio contra no socio', 'Octubre completo. Compras con DNI del reporte de ALAX contra los tickets de mostrador.'); S.appendChild(c);
    table(c, ['Local', 'Tickets', 'Tickets del club', '% de la venta', 'Ticket socio', 'Ticket no socio', 'Diferencia'], (LOCAL === 'Todos' ? D.club : sel(D.club)).map((r) => [r.local, nf(r.tickets), nf(r.tickets_club), pf(r.venta_club / r.venta_mostrador), '$' + nf(r.ticket_socio), '$' + nf(r.ticket_no_socio), { t: '+' + pf(r.ticket_socio / r.ticket_no_socio - 1), cls: 'good' }]));
    document.getElementById('pie').textContent = 'Fuentes: cierres de caja y venta detallada de Maxi Rest (tickets de mostrador, sin apps ni notas de crédito), venta por rubro de Maxi Rest y reporte de ventas de ALAX. Horarios, formas de pago y tamaño del ticket: 1 al 25 de octubre; productos: 1 al 22; clientes y venta: mes completo.';
  });
}

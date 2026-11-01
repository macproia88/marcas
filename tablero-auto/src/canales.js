let LOCAL = 'Todos';
const LOCS = ['Florida', 'Beccar', 'Paz'];
const COL = { Florida: '#b85042', Beccar: '#3b2e2a', Paz: '#8c6b3f', PedidosYa: '#b85042', Rappi: '#8c6b3f', y25: '#9a928b', ok: '#2f6b4f', bad: '#c4655a' };
const DS = ['Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sá', 'Do'];
const MESC = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
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
  const x = d3.scaleLinear().domain([0, d3.max(items, (d) => d.v) || 1]).range([0, W - lw - (items.some((d) => d.t) ? (W < 520 ? 120 : 200) : 70)]);
  const s = d3.select(c).append('svg').attr('viewBox', `0 0 ${W} ${H}`);
  const g = s.selectAll('g').data(items).join('g').attr('transform', (d, i) => `translate(0,${i * bh})`);
  const mx = Math.max(10, Math.floor(lw / 6.6)); g.append('text').attr('x', lw - 8).attr('y', 16).attr('text-anchor', 'end').text((d) => d.k.length > mx ? d.k.slice(0, mx - 1) + '…' : d.k);
  g.append('rect').attr('x', lw).attr('y', 4).attr('height', bh - 8).attr('rx', 3).attr('width', (d) => x(d.v)).attr('fill', (d) => d.c || color || COL.Florida)
    .on('mousemove', (ev, d) => showTip(ev, d.k + ': ' + fmt(d.v) + (d.t ? ' · ' + d.t : ''))).on('mouseleave', hideTip);
  const angosto = W < 520; g.append('text').attr('x', (d) => lw + x(d.v) + 6).attr('y', 16).text((d) => fmt(d.v) + (d.t ? '  ' + (angosto && d.ts ? d.ts : d.t) : ''));
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
  const angosto = x.bandwidth() < 34;
  const corto = (v) => fmt === mf ? '$' + Math.round(v / 1e6) + 'M' : (v >= 10000 ? (v / 1000).toLocaleString('es-AR', { maximumFractionDigits: 1 }) + 'k' : fmt(v));
  if (opts.labels !== false && cats.length <= 14) s.append('g').selectAll('text').data(tot).join('text').attr('x', (_, i) => x(i) + x.bandwidth() / 2).attr('y', (v) => y(v) - 4).attr('text-anchor', 'middle').style('font-size', angosto ? '8.5px' : '11px').text((v) => angosto ? corto(v) : fmt(v));
  if (opts.line) {
    const ln = d3.line().defined((v) => v != null).x((_, i) => x(i) + x.bandwidth() / 2).y((v) => y(v));
    s.append('path').attr('d', ln(opts.line.values)).attr('fill', 'none').attr('stroke', opts.line.color).attr('stroke-width', 2).attr('stroke-dasharray', '4 3');
  }
  const leg = el('div', { class: 'leg' });
  [...series, ...(opts.line ? [opts.line] : [])].forEach((se) => { if (series.length > 1 || opts.line) { const sp = el('span'); sp.appendChild(el('i', { style: `background:${se.color}` })); sp.appendChild(document.createTextNode(se.name)); leg.appendChild(sp); } });
  c.appendChild(leg);
}

function heat(c0, rows, campo, fmt) {
  const c = el('div', { class: 'hscroll' }); c0.appendChild(c); c.style.width = '100%';
  const hs = [...new Set(rows.map((r) => r.hora))].sort((a, b) => a - b);
  if (!hs.length) return;
  const hmin = d3.min(hs), hmax = d3.max(hs), H0 = d3.range(hmin, hmax + 1);
  const val = {}; rows.forEach((r) => { const k = r.dia + '-' + r.hora; val[k] = (val[k] || 0) + r[campo]; });
  const W = Math.max(width(c0), 30 + H0.length * 34), cw = (W - 30) / H0.length, ch = 26, H = ch * 7 + 22;
  const mx = d3.max(Object.values(val)) || 1;
  const col = d3.scaleSequential([0, mx], d3.interpolateRgb('#f6e3de', '#a33a2c'));
  const s = d3.select(c).append('svg').attr('viewBox', `0 0 ${W} ${H}`).style('min-width', W + 'px');
  H0.forEach((h, j) => s.append('text').attr('x', 30 + j * cw + cw / 2).attr('y', 12).attr('text-anchor', 'middle').style('font-size', '10px').attr('fill', 'currentColor').text(h + 'h'));
  for (let d = 0; d < 7; d++) {
    s.append('text').attr('x', 0).attr('y', 22 + d * ch + 17).style('font-size', '11px').text(DS[d]);
    H0.forEach((h, j) => {
      const v = val[d + '-' + h] || 0;
      s.append('rect').attr('x', 30 + j * cw + 1).attr('y', 22 + d * ch + 1).attr('width', cw - 2).attr('height', ch - 2).attr('rx', 3).attr('fill', v ? col(v) : 'transparent').attr('stroke', 'var(--line)')
        .on('mousemove', (ev) => showTip(ev, `${DS[d]} ${h} a ${h + 1} h: ${fmt(v)}`)).on('mouseleave', hideTip);
      if (v && cw > 22) s.append('text').attr('x', 30 + j * cw + cw / 2).attr('y', 22 + d * ch + 17).attr('text-anchor', 'middle').style('font-size', '10px').attr('fill', v > mx * 0.55 ? '#fff' : '#3b2e2a').text(fmt(v));
    });
  }
}

function table(c, head, rows) {
  const tw = el('div', { class: 'tw' }), t = el('table'), th = el('thead'), tr = el('tr');
  head.forEach((h) => tr.appendChild(el('th', { text: h }))); th.appendChild(tr); t.appendChild(th);
  const tb = el('tbody'); rows.forEach((r) => { const x = el('tr'); r.forEach((v) => { const td = el('td'); if (v && v.cls) { td.textContent = v.t; td.className = v.cls; } else td.textContent = v; x.appendChild(td); }); tb.appendChild(x); });
  t.appendChild(tb); tw.appendChild(t); c.appendChild(tw);
}

let MES = null;
const MESN = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
const mesNom = (m) => MESN[+m.slice(5) - 1] + ' ' + m.slice(0, 4);
function kpis(list) { const k = document.getElementById('kpis'); k.replaceChildren(); list.forEach(([a, b, c]) => { const d = el('div', { class: 'kpi' }); d.appendChild(el('div', { class: 'k', text: a })); d.appendChild(el('div', { class: 'v', text: b })); d.appendChild(el('div', { class: 'd', text: c || '' })); k.appendChild(d); }); }
function textos() { const u = document.getElementById('txt'); u.replaceChildren(); ((D.textos[MES] || {})[LOCAL] || []).forEach((t) => u.appendChild(el('li', { text: t }))); }
function diaLabel(f) { const d = new Date(f + 'T12:00:00'); return DS[(d.getDay() + 6) % 7] + '\n' + d.getDate(); }
const delMes = (rows) => rows.filter((r) => r.fecha.slice(0, 7) === MES);
const prevMes = () => { const d = new Date(MES + '-15T12:00:00'); d.setMonth(d.getMonth() - 1); return d.toISOString().slice(0, 7); };
function sec(S, t) { S.appendChild(el('h2', { class: 'sec', text: t })); }
function sinDetalle(S, que) { const c = card('c-vacio', 'Detalle de ' + MESN[+MES.slice(5) - 1], ''); c.appendChild(el('p', { class: 'vacio', text: que })); S.appendChild(c); }
function anio(S, campoCant, campoVenta, nomCant) {
  sec(S, 'El año mes a mes');
  const ms = D.meses.filter((m) => { const r = D.men.find((x) => x.mes === m && x.local === 'Florida'); return r && r.dias >= 7; }), locs = LOCAL === 'Todos' ? LOCS : [LOCAL];
  const g = el('div', { class: 'grid2' }); S.appendChild(g);
  const c1 = card('a-cant', nomCant + ' por día', 'Promedio por día de cada mes (así se comparan meses de distinto largo).');
  const c2 = card('a-venta', 'Venta del mes', 'Pesos de cada mes, con IVA. Un mes en curso aparece cuando tiene una semana cargada (marcado con *).');
  const c3 = card('a-ticket', 'Ticket promedio', 'Venta ÷ ' + nomCant.toLowerCase() + ' de cada mes.');
  const c4 = card('a-tot', nomCant + ' del mes', 'Total de cada mes.');
  g.append(c1, c2); const g2 = el('div', { class: 'grid2' }); S.appendChild(g2); g2.append(c3, c4);
  const R = (m, L) => D.men.find((x) => x.mes === m && x.local === L) || {};
  const cats = ms.map((m) => MES_C(m));
  vbars(c1, cats, locs.map((L) => ({ name: L, color: COL[L], values: ms.map((m) => R(m, L).dias ? R(m, L)[campoCant] / R(m, L).dias : 0) })), nf);
  vbars(c2, cats, locs.map((L) => ({ name: L, color: COL[L], values: ms.map((m) => R(m, L)[campoVenta] || 0) })), mf);
  vbars(c3, cats, [{ name: 'Ticket', color: COL.Beccar, values: ms.map((m) => { const c = locs.reduce((s, L) => s + (R(m, L)[campoCant] || 0), 0), v = locs.reduce((s, L) => s + (R(m, L)[campoVenta] || 0), 0); return c ? v / c : 0; }) }], (v) => '$' + nf(v / 1000) + 'k');
  vbars(c4, cats, locs.map((L) => ({ name: L, color: COL[L], values: ms.map((m) => R(m, L)[campoCant] || 0) })), nf);
}
const MES_C = (m) => MESC[+m.slice(5) - 1] + (m === D.meses[D.meses.length - 1] && D.meses.length > 1 ? '*' : '');

function arrancar(dibujar) {
  MES = D.mes;
  const s = document.getElementById('mes');
  [...D.meses].reverse().forEach((m) => { const o = el('option', { value: m, text: mesNom(m) + (D.det[m] ? '' : ' (sin detalle)') }); if (m === MES) o.selected = true; s.appendChild(o); });
  s.addEventListener('change', () => { MES = s.value; dibujar(); });
  document.querySelectorAll('#loc button').forEach((b) => b.addEventListener('click', () => { LOCAL = b.dataset.l; document.querySelectorAll('#loc button').forEach((x) => x.setAttribute('aria-pressed', String(x === b))); dibujar(); }));
  let w = window.innerWidth; window.addEventListener('resize', () => { if (Math.abs(window.innerWidth - w) > 40) { w = window.innerWidth; dibujar(); } });
  dibujar();
}

function cierreApps(S) {
  const L0 = sel(D.liq);
  sec(S, 'Cierre de las apps');
  const c = card('c-cierre', 'Lo facturado y lo que llega al banco · ' + MESN[+MES.slice(5) - 1], 'Facturado = lo que pagó el cliente (sin los descuentos que pone el local). Se queda la app = comisión, cargos, publicidad e impuestos (IVA de la comisión, percepciones y retenciones). Depositado = lo que llega al local: transferencia al banco más, de enero a abril, los pedidos de PedidosYa que el local cobró en efectivo.');
  S.appendChild(c);
  const R = L0.filter((r) => r.mes === MES);
  if (!R.length) c.appendChild(el('p', { class: 'vacio', text: 'Sin liquidaciones cargadas para este mes. Hoy hay agosto, septiembre y octubre.' }));
  else {
    const fila = (n, rs) => { const v = sum(rs, 'venta'), q = rs.every((r) => r.se_queda != null) ? sum(rs, 'se_queda') : null, d = rs.every((r) => r.deposito != null) ? sum(rs, 'deposito') : null, p = sum(rs, 'pedidos');
      return [n, nf(p), mf(v), q == null ? 'pendiente' : mf(q), q == null ? '—' : pf(q / v), d == null ? 'pendiente' : { t: mf(d), cls: 'good' }, d == null ? '—' : { t: pf(d / v), cls: 'good' }, d == null ? '—' : '$' + nf(d / p)]; };
    const filas = ['PedidosYa', 'Rappi'].map((a) => R.filter((r) => r.app === a)).filter((rs) => rs.length).map((rs) => fila(rs[0].app, rs));
    if (filas.length > 1) filas.push(fila('Las dos apps', R));
    if (window.innerWidth < 640) table(c, ['App', 'Facturado', 'Se queda', 'Depositado', 'Llega'], filas.map((f) => [f[0], f[2], f[3], f[5], f[6]]));
    else table(c, ['App', 'Pedidos', 'Facturado', 'Se queda la app', '%', 'Depositado', '% que llega', 'Por pedido'], filas);
    const f = [...new Set(R.map((r) => r.fuente))];
    c.appendChild(el('p', { class: 'note', text: 'Fuente: ' + f.join(' y ') + (f.includes('detalle de pedidos') ? ' (PedidosYa: venta e ingreso estimado del detalle de pedidos, hasta que llegue la liquidación del mes)' : '') + '.' }));
  }
  const ms = [...new Set(L0.map((r) => r.mes))].sort();
  if (ms.length) {
    const g = el('div', { class: 'grid2' }); S.appendChild(g);
    ['PedidosYa', 'Rappi'].forEach((a) => {
      const cc = card('c-mm-' + a, a + ' mes a mes', 'Facturado de cada mes: la parte verde llega al local, la roja se la queda la app. Octubre de Rappi es estimado hasta que llegue su liquidación.'); g.appendChild(cc);
      const rs = (m) => L0.filter((r) => r.mes === m && r.app === a);
      const okm = ms.filter((m) => rs(m).length && rs(m).every((r) => r.deposito != null));
      if (!okm.length) { cc.appendChild(el('p', { class: 'vacio', text: 'Sin datos.' })); return; }
      vbars(cc, okm.map((m) => MESC[+m.slice(5) - 1]), [{ name: 'Llega al local', color: COL.ok, values: okm.map((m) => sum(rs(m), 'deposito')) }, { name: 'Se queda la app', color: COL.bad, values: okm.map((m) => sum(rs(m), 'se_queda')) }], mf);
      table(cc, ['Mes', 'Facturado', 'Depositado', '% que llega'], okm.map((m) => [MESC[+m.slice(5) - 1], mf(sum(rs(m), 'venta')), mf(sum(rs(m), 'deposito')), pf(sum(rs(m), 'deposito') / sum(rs(m), 'venta'))]));
    });
  }
}

function paginaApps() {
  arrancar(() => {
    textos();
    const A = D.det[MES];
    const dias = sel(delMes(D.dias)), ped = sum(dias, 'pedidos'), vap = sum(dias, 'venta_app'), nd = new Set(delMes(D.dias).map((r) => r.fecha)).size;
    const pv = sel(D.dias.filter((r) => r.fecha.slice(0, 7) === prevMes())), ndp = new Set(D.dias.filter((r) => r.fecha.slice(0, 7) === prevMes()).map((r) => r.fecha)).size;
    const vs = ndp && sum(pv, 'pedidos') ? (ped / nd) / (sum(pv, 'pedidos') / ndp) - 1 : null;
    const K = [['Pedidos de ' + MESN[+MES.slice(5) - 1], nf(ped), nf(ped / nd) + ' por día' + (vs != null ? ' · ' + (vs >= 0 ? '+' : '') + pf(vs) + ' vs mes anterior' : '')],
      ['Venta en apps', mf(vap), 'cargada en Maxi Rest (código 202)'], ['Ticket promedio', '$' + nf(vap / ped), 'venta en Maxi Rest ÷ pedidos']];
    if (A) {
      const py = sel(A.plata).filter((r) => r.app === 'PedidosYa'), rec = sel(A.reclamos), tiempos = sel(A.tiempos), vpy = sum(py, 'venta');
      const pago = vpy - sum(py, 'descuentos');
      K.push(['Llega al banco (PedidosYa)', pf(sum(py, 'neto') / pago), 'de lo que pagó el cliente · ' + pf(sum(py, 'neto') / vpy) + ' del precio de lista'],
        ['Reclamos', (sum(rec, 'reclamos') / sum(rec, 'pedidos') * 100).toLocaleString('es-AR', { maximumFractionDigits: 1 }) + ' cada 100', nf(sum(rec, 'reclamos')) + ' reclamos en PedidosYa'],
        ['Preparación (mediana)', (LOCAL === 'Todos' ? d3.median(tiempos, (t) => t.preparacion) : tiempos[0].preparacion) + ' min', 'de aceptado a listo para retirar']);
    }
    kpis(K);
    const S = document.getElementById('secs'); S.replaceChildren();
    sec(S, 'Cómo vino ' + MESN[+MES.slice(5) - 1]);
    const fechas = [...new Set(delMes(D.dias).map((r) => r.fecha))].sort();
    let c = card('c-dias', 'Pedidos día por día', 'PedidosYa + Rappi. Pasá el mouse por una barra para ver el número.'); S.appendChild(c);
    if (A) vbars(c, fechas.map(diaLabel), [{ name: 'PedidosYa', color: COL.PedidosYa, values: fechas.map((f) => sum(sel(A.dias).filter((r) => r.fecha === f), 'pedidosya')) }, { name: 'Rappi', color: COL.Rappi, values: fechas.map((f) => sum(sel(A.dias).filter((r) => r.fecha === f), 'rappi')) }], nf, { labels: false });
    else vbars(c, fechas.map(diaLabel), (LOCAL === 'Todos' ? LOCS : [LOCAL]).map((L) => ({ name: L, color: COL[L], values: fechas.map((f) => sum(dias.filter((r) => r.fecha === f && r.local === L), 'pedidos')) })), nf, { labels: false });
    cierreApps(S);
    if (!A) { sinDetalle(S, 'Horarios, productos, agregados, tamaño del pedido, plata y reclamos salen del detalle de pedidos de PedidosYa y el reporte de Rappi del mes. Hoy está cargado solo octubre: con los archivos de este mes se completa.'); }
    else {
      c = card('c-hora', 'A qué hora y qué día piden', 'Pedidos del mes en cada franja de una hora (PedidosYa + Rappi). Más oscuro = más pedidos.'); S.appendChild(c);
      heat(c, sel(A.horas), 'pedidos', nf);
      const g = el('div', { class: 'grid2' }); S.appendChild(g);
      c = card('c-prod', 'Qué es lo que más se vende', 'PedidosYa, unidades del mes. Producto como figura en el menú de la app.'); const ca = card('c-agr', 'Qué le agregan al pedido', 'Opciones elegidas dentro de cada producto (salsa, queso, relleno, guarnición). Unidades del mes en PedidosYa.'); g.append(c, ca);
      const pr = {}; sel(A.productos).forEach((r) => { pr[r.producto] = (pr[r.producto] || 0) + r.unidades; });
      hbars(c, Object.entries(pr).sort((a, b) => b[1] - a[1]).slice(0, 15).map(([k, v]) => ({ k, v })), nf);
      const ag = {}; sel(A.agregados).forEach((r) => { ag[r.agregado] = (ag[r.agregado] || 0) + r.unidades; });
      hbars(ca, Object.entries(ag).sort((a, b) => b[1] - a[1]).slice(0, 12).map(([k, v]) => ({ k, v })), nf, COL.Paz);
      const g2 = el('div', { class: 'grid2' }); S.appendChild(g2);
      c = card('c-bandas', 'Cuánto gasta cada pedido', 'PedidosYa: pedidos según su total a precio de lista. Al lado: % de los pedidos · % de la plata del mes.'); const cp = card('c-plata', 'Lo que queda en el bolsillo (PedidosYa)', 'Del precio de lista a lo que llega al banco, paso a paso (detalle de pedidos del mes).'); g2.append(c, cp);
      const bd = {}; sel(A.bandas).forEach((r) => { bd[r.orden] = bd[r.orden] || { k: r.banda, v: 0, venta: 0 }; bd[r.orden].v += r.pedidos; bd[r.orden].venta += r.venta; });
      const tv = Object.values(bd).reduce((s, b) => s + b.venta, 0), tp = Object.values(bd).reduce((s, b) => s + b.v, 0);
      hbars(c, Object.keys(bd).sort().map((k) => ({ k: bd[k].k, v: bd[k].v, t: `${pf(bd[k].v / tp)} de los pedidos · ${pf(bd[k].venta / tv)} de la plata`, ts: `${pf(bd[k].v / tp)} · ${pf(bd[k].venta / tv)}` })), nf, COL.Beccar);
      const can = sel(A.canasta), up = LOCAL === 'Todos' ? d3.mean(can, (r) => r.unidades_pedido) : can[0].unidades_pedido;
      c.appendChild(el('p', { class: 'note', text: `En promedio cada pedido lleva ${up.toLocaleString('es-AR', { maximumFractionDigits: 1 })} productos (sin contar los agregados).` }));
      const py = sel(A.plata).filter((r) => r.app === 'PedidosYa'), pl = ['venta', 'comision', 'descuentos', 'publicidad', 'otros', 'neto'].map((f) => sum(py, f));
      const pc = pl[0] - pl[2], P2 = (v) => pf(v / pl[0]), P3 = (v) => pf(v / pc);
      table(cp, ['Concepto', 'Pesos', '% precio de lista', '% de lo que pagó el cliente'], [
        ['Precio de lista (menú de la app)', mf(pl[0]), '100%', '—'], ['− Descuentos que pone el local', mf(pl[2]), P2(pl[2]), '—'],
        ['= Pagó el cliente', mf(pc), P2(pc), '100%'],
        ['− Comisión', mf(pl[1]), P2(pl[1]), P3(pl[1])], ['− Publicidad', mf(pl[3]), P2(pl[3]), P3(pl[3])], ['− Otros cargos e impuestos', mf(pl[4]), P2(pl[4]), P3(pl[4])],
        [{ t: '= Llega al banco', cls: 'good' }, { t: mf(pl[5]), cls: 'good' }, { t: P2(pl[5]), cls: 'good' }, { t: P3(pl[5]), cls: 'good' }]]);
      cp.appendChild(el('p', { class: 'note', text: 'Los dos porcentajes miden lo mismo con distinta base: sobre lo que pagó el cliente (como la liquidación de la app y el cierre de arriba) o sobre el precio de lista (contando como costo los descuentos que pone el local).' }));
      c = card('c-rec', 'Reclamos y servicio', 'PedidosYa. Reclamos por motivo, cancelados y tiempos. Menos es mejor.'); S.appendChild(c);
      table(c, ['Local', 'Pedidos', 'Reclamos c/100', 'Faltante', 'Incorrecto', 'Orden equivocada', 'Calidad', 'Cancelados', 'Preparación', 'Tardan +20 min', 'Pedido a entrega'], (LOCAL === 'Todos' ? LOCS : [LOCAL]).map((L) => { const r = A.reclamos.find((x) => x.local === L), t = A.tiempos.find((x) => x.local === L), k = A.cancelados.find((x) => x.local === L);
        return [L, nf(r.pedidos), (r.reclamos / r.pedidos * 100).toLocaleString('es-AR', { maximumFractionDigits: 1 }), nf(r['Producto faltante'] || 0), nf(r['Producto incorrecto'] || 0), nf(r['Orden equivocada'] || 0), nf(r['Calidad de la comida'] || 0), nf(k.cancelados), t.preparacion + ' min', pf(t.prep_mas_20), t.total + ' min']; }));
    }
    anio(S, 'pedidos', 'venta_app', 'Pedidos');
    document.getElementById('pie').textContent = 'Fuentes: pedidos y venta de apps por día del tablero La Presumida (cierres de caja de Maxi Rest, código 202; pedidos reales de PedidosYa y Rappi cuando están, estimados con la venta ÷ ticket cuando no). Detalle del mes: PedidosYa (estado "Entregado") y Rappi ("Terminada"); productos, plata, reclamos y tiempos solo de PedidosYa. * mes en curso.';
  });
}

function paginaMostrador() {
  arrancar(() => {
    textos();
    const Mo = D.det[MES], CL = (D.club || {})[MES], TOP = (D.top || {})[MES];
    const dias = sel(delMes(D.dias)), tk = sum(dias, 'tickets'), vm = sum(dias, 'venta'), nd = new Set(delMes(D.dias).map((r) => r.fecha)).size;
    const d25 = dias.filter((r) => r.tickets_2025 != null), t25 = sum(d25, 'tickets_2025'), t26 = sum(d25, 'tickets');
    const K = [['Clientes de ' + MESN[+MES.slice(5) - 1], nf(tk), nf(tk / nd) + ' por día'], ['Venta de mostrador', mf(vm), 'sin apps'], ['Ticket promedio', '$' + nf(vm / tk), 'mostrador']];
    if (t25) K.push(['Clientes vs 2025', (t26 / t25 - 1 >= 0 ? '+' : '') + pf(t26 / t25 - 1, 1), 'mismos días de la semana']);
    if (CL) { const cl = sel(CL), vc = sum(cl, 'venta_club'), vcm = sum(cl, 'venta_mostrador'), nc = sum(cl, 'tickets_club'), tkc = sum(cl, 'tickets'); K.push(['Venta del club', pf(vc / vcm), 'el socio gasta ' + pf((vc / nc) / ((vcm - vc) / (tkc - nc)) - 1) + ' más']); }
    kpis(K);
    const S = document.getElementById('secs'); S.replaceChildren();
    sec(S, 'Cómo vino ' + MESN[+MES.slice(5) - 1]);
    const fechas = [...new Set(delMes(D.dias).map((r) => r.fecha))].sort();
    let c = card('c-dias', 'Clientes día por día', 'Tickets de mostrador.' + (t25 ? ' Línea: mismo día de la semana de 2025.' : '')); S.appendChild(c);
    vbars(c, fechas.map(diaLabel), [{ name: '2026', color: COL.Florida, values: fechas.map((f) => sum(dias.filter((r) => r.fecha === f), 'tickets')) }], nf,
      { labels: false, line: t25 ? { name: '2025', color: COL.y25, values: fechas.map((f) => { const r = dias.filter((x) => x.fecha === f); return r.some((x) => x.tickets_2025 == null) ? null : sum(r, 'tickets_2025'); }) } : null });
    if (!Mo) sinDetalle(S, 'Horarios, formas de pago, tamaño del ticket, productos y club salen de la venta detallada y la venta por rubro de Maxi Rest y de ALAX. Hoy están cargados para octubre: con los archivos de este mes se completa.');
    else {
      const hasta = Mo.resumen.map((r) => r.hasta).sort()[0];
      c = card('c-hora', 'A qué hora y qué día vienen', `Clientes promedio en un día, por franja de una hora (venta detallada de Maxi Rest hasta el ${hasta.slice(8)}/${hasta.slice(5, 7)}).`); S.appendChild(c);
      heat(c, sel(Mo.horas), 'tickets', (v) => nf(v));
      const g = el('div', { class: 'grid2' }); S.appendChild(g);
      c = card('c-cobro', 'Cómo paga', 'De cada 100 tickets de mostrador.'); const cb = card('c-bandas', 'Cuánto gasta cada cliente', 'Tickets según el total. Al lado: % de los clientes · % de la venta.'); g.append(c, cb);
      const co = {}; sel(Mo.cobro).forEach((r) => { co[r.forma] = (co[r.forma] || 0) + r.tickets; }); const tco = Object.values(co).reduce((a, b) => a + b, 0);
      hbars(c, Object.entries(co).sort((a, b) => b[1] - a[1]).map(([k, v]) => ({ k, v: v / tco })), (v) => pf(v), COL.Beccar);
      const bd = {}; sel(Mo.bandas).forEach((r) => { bd[r.orden] = bd[r.orden] || { k: r.banda, v: 0, venta: 0 }; bd[r.orden].v += r.tickets; bd[r.orden].venta += r.venta; });
      const tv = Object.values(bd).reduce((s, b) => s + b.venta, 0), tp = Object.values(bd).reduce((s, b) => s + b.v, 0);
      hbars(cb, Object.keys(bd).sort().map((k) => ({ k: bd[k].k, v: bd[k].v, t: `${pf(bd[k].v / tp)} de los clientes · ${pf(bd[k].venta / tv)} de la venta`, ts: `${pf(bd[k].v / tp)} · ${pf(bd[k].venta / tv)}` })), nf, COL.Paz);
      if (TOP) {
        const g2 = el('div', { class: 'grid2' }); S.appendChild(g2);
        c = card('c-top', 'Qué es lo que más se vende', 'Top 15 de mostrador por venta en pesos (1 al 22, venta por rubro de Maxi Rest, a precio de lista). Fideos incluye el kilo de regalo de la bienvenida del club.'); const cr = card('c-rubro', 'Por rubro', 'Venta de mostrador por rubro (1 al 22).'); g2.append(c, cr);
        const tp2 = {}; sel(TOP).forEach((r) => { tp2[r.articulo] = (tp2[r.articulo] || 0) + r.venta; });
        hbars(c, Object.entries(tp2).sort((a, b) => b[1] - a[1]).slice(0, 15).map(([k, v]) => ({ k, v })), mf);
        const rb = {}; sel(TOP).forEach((r) => { rb[r.rubro] = (rb[r.rubro] || 0) + r.venta; });
        hbars(cr, Object.entries(rb).sort((a, b) => b[1] - a[1]).slice(0, 15).map(([k, v]) => ({ k, v })), mf, COL.Beccar);
      }
      if (CL) {
        c = card('c-club', 'Socio contra no socio', 'Mes completo. Compras con DNI del reporte de ALAX contra los tickets de mostrador.'); S.appendChild(c);
        const fs = sel(CL).map((r) => [r.local, nf(r.tickets), nf(r.tickets_club), pf(r.venta_club / r.venta_mostrador), '$' + nf(r.ticket_socio), '$' + nf(r.ticket_no_socio), { t: '+' + pf(r.ticket_socio / r.ticket_no_socio - 1), cls: 'good' }]);
        if (window.innerWidth < 640) table(c, ['Local', '% venta', 'Socio', 'No socio', 'Dif.'], fs.map((f) => [f[0], f[3], f[4], f[5], f[6]]));
        else table(c, ['Local', 'Tickets', 'Tickets del club', '% de la venta', 'Ticket socio', 'Ticket no socio', 'Diferencia'], fs);
      }
    }
    anio(S, 'tickets', 'venta_mostrador', 'Clientes');
    document.getElementById('pie').textContent = 'Fuentes: tickets y venta de mostrador por día del tablero La Presumida (venta detallada de Maxi Rest hasta agosto y del 1 al 25/10; desde el 26/10, cierres de caja), venta por rubro de Maxi Rest y reporte de ventas de ALAX. Mostrador = venta total menos apps (código 202). * mes en curso.';
  });
}

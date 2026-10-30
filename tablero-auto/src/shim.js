(function(){
  const RAW = window.__LP_DATA__, CALC = {}, CACHE = {}, CBS = [];
  let P = {};
  const data = (id) => {
    if (RAW[id]) return {status: 'ok', data: RAW[id]};
    if (CALC[id]) { const key = id + (CALC[id].porFiltro ? JSON.stringify(P) : ''); if (!CACHE[key]) CACHE[key] = CALC[id].fn(...CALC[id].inputs.map((i) => data(i).data)); return {status: 'ok', data: CACHE[key]}; }
    return {status: 'empty', data: []};
  };
  const fire = () => CBS.forEach((f) => { try { f(); } catch (e) { console.error(e); } });
  window.dash = {
    calc: (id, o) => { CALC[id] = o; },
    data,
    onData: (f) => { CBS.push(f); },
    params: () => ({...P}),
    setParams: (o) => { P = {...P, ...o}; fire(); },
    setLink: (t) => { try { history.replaceState(null, '', '#' + t); } catch (e) {} },
    colors: ['#c2410c', '#94a3b8', '#0f766e', '#7c3aed']
  };
  window.addEventListener('DOMContentLoaded', fire);
})();

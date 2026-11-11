// Lógica de la página: gráficos, tablas, comparador y botón de tema.
const store = {}; for (const k in CSV) store[k] = d3.csvParse(CSV[k]);
const _draws = [], _calcs = {}; let _params = {};
window.dash = {
  colors: ['#1aa56b', '#e0a800'],
  data(id) { if (_calcs[id]) return { status: 'ok', data: _calcs[id].fn(...(_calcs[id].inputs.map((i) => store[i]))) };
    return store[id] ? { status: 'ok', data: store[id] } : { status: 'missing', data: [] }; },
  calc(id, o) { _calcs[id] = o; }, draw(n, f) { _draws.push([n, f]); },
  params() { return _params; }, setParams(p) { Object.assign(_params, p); _redraw(); }
};
function _redraw() { _draws.forEach(([n, f]) => document.querySelectorAll('[data-draw="' + n + '"]').forEach((el) => { try { f(el); } catch (e) { console.error(n, e); } })); }

const NOMBRES = {AUS:'Australia',NZL:'Nueva Zelanda',CHI:'Chile',HKG:'Hong Kong',RSA:'Sudáfrica',ITA:'Italia',GEO:'Georgia',ROU:'Rumania',FIJ:'Fiyi',ESP:'España',ARG:'Argentina',CAN:'Canadá',SCO:'Escocia',URU:'Uruguay',IRE:'Irlanda',POR:'Portugal',FRA:'Francia',USA:'Estados Unidos',JPN:'Japón',SAM:'Samoa',ENG:'Inglaterra',WAL:'Gales',TON:'Tonga',ZIM:'Zimbabue'};
// colores de camiseta: [fondo de la insignia, texto, color de barra]
const COL = {AUS:['#00843d','#ffcd00','#00a651'],NZL:['#111111','#ffffff','#7a8190'],RSA:['#007a4d','#ffb81c','#119c68'],IRE:['#169b62','#ffffff','#169b62'],FRA:['#0055a4','#ffffff','#2f7fd6'],ENG:['#ffffff','#cf142b','#cf142b'],SCO:['#0b2a6f','#ffffff','#3b5fc4'],ARG:['#74acdf','#0b2a4a','#74acdf'],WAL:['#c8102e','#ffffff','#e0344f'],FIJ:['#68bfe5','#0b2a4a','#68bfe5'],GEO:['#d4202c','#ffffff','#e04752'],ITA:['#0b6bcb','#ffffff','#2f8be6'],ROU:['#fcd116','#002b7f','#e6bb00'],ESP:['#c60b1e','#ffc400','#d9344a'],CAN:['#d52b1e','#ffffff','#e5584c'],URU:['#5aa0d8','#ffffff','#5aa0d8'],POR:['#006600','#ffcc00','#1b8f1b'],USA:['#3c3b6e','#ffffff','#6a69b5'],JPN:['#ffffff','#bc002d','#d6264a'],SAM:['#002b7f','#ffffff','#3a62c2'],TON:['#c10000','#ffffff','#dc3a3a'],ZIM:['#319b3a','#ffd200','#4cb455'],CHI:['#d52b1e','#ffffff','#e5584c'],HKG:['#de2910','#ffffff','#ec5a45']};
const nom = (c) => NOMBRES[c] || c;
const col = (c) => COL[c] || ['#555','#fff','#888'];
const pct = d3.format('.1%');
const filas = (id) => { const s = dash.data(id); return s.status === 'ok' && s.data.length ? s.data : null; };
const fechaCorta = d3.utcFormat('%d/%m');

dash.calc('partidos_x', {
  title: 'Partidos de grupo con la probabilidad de cada lado',
  description: 'La probabilidad del visitante es 1 menos la del local, porque el modelo no cuenta el empate.',
  inputs: ['partidos'],
  fn: (partidos) => partidos.map((r) => ({
    partido: r.home + '-' + r.away, fecha: r.date, grupo: r.grupo, local: r.home, visita: r.away,
    p_local: +r.p_local, p_visita: 1 - (+r.p_local)
  }))
});

function marcado(texto, ds, campo, donde, clase) {
  const b = document.createElement('b');
  b.dataset.source = ds; b.dataset.field = campo; b.dataset.where = donde;
  if (clase) b.className = clase;
  b.textContent = texto; return b;
}
function insignia(c, tam) {
  const s = document.createElement('span'); s.className = 'rw-badge' + (tam ? ' rw-' + tam : '');
  s.style.background = col(c)[0]; s.style.color = col(c)[1]; s.textContent = c; return s;
}
function calor(td, p, color) {
  td.style.background = 'color-mix(in srgb, ' + color + ' ' + Math.round(Math.min(1, p) * 70) + '%, transparent)';
}

dash.draw('resumen', (el) => {
  const t = filas('torneo');
  if (!t) { el.textContent = '—'; return; }
  const top = [...t].sort((a, b) => b['campeón'] - a['campeón']).slice(0, 3);
  const m = (r) => marcado(pct(+r['campeón']), 'torneo', 'campeón', 'equipo=' + r.equipo);
  el.replaceChildren(
    nom(top[0].equipo) + ' es la favorita con ', m(top[0]),
    ', seguida de ' + nom(top[1].equipo) + ' (', m(top[1]),
    ') ' + (/^(I|Hi)/.test(nom(top[2].equipo)) ? 'e ' : 'y ') + nom(top[2].equipo) + ' (', m(top[2]), ').'
  );
});

dash.draw('podio', (el) => {
  const t = filas('torneo');
  if (!t) { el.replaceChildren(); return; }
  const top = [...t].sort((a, b) => b['campeón'] - a['campeón']).slice(0, 3);
  el.replaceChildren(...top.map((r, i) => {
    const d = document.createElement('div'); d.className = 'rw-pod' + (i === 0 ? ' rw-uno' : '');
    const rk = document.createElement('div'); rk.className = 'rw-rank';
    rk.append(insignia(r.equipo, i === 0 ? 'g' : ''), i === 0 ? 'La más probable' : (i + 1) + 'ª más probable');
    const n = document.createElement('div'); n.className = 'rw-nom'; n.textContent = nom(r.equipo);
    const big = document.createElement('div'); big.className = 'rw-big';
    big.append(marcado(pct(+r['campeón']), 'torneo', 'campeón', 'equipo=' + r.equipo));
    const mini = document.createElement('div'); mini.className = 'rw-mini';
    mini.append('de ser campeón · final: ', marcado(pct(+r.final), 'torneo', 'final', 'equipo=' + r.equipo));
    d.append(rk, n, big, mini); return d;
  }));
});

dash.draw('meta', (el) => {
  const m = filas('corrida');
  if (!m) { el.textContent = '—'; return; }
  const r = m[0];
  const f = d3.utcFormat('%d/%m/%Y')(d3.utcParse('%Y-%m-%d')(r.ultimo_partido));
  const n = String(+r.n_simulaciones).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  const a = document.createElement('b'); a.dataset.source = 'corrida'; a.dataset.field = 'ultimo_partido'; a.dataset.row = '0'; a.textContent = f;
  const b = document.createElement('b'); b.dataset.source = 'corrida'; b.dataset.field = 'n_simulaciones'; b.dataset.row = '0'; b.textContent = n;
  el.replaceChildren('Datos hasta el último partido cargado, el ', a, ' · ', b, ' torneos simulados · foto de hoy, sin actualizar durante el torneo');
});

dash.draw('nsim', (el) => {
  const m = filas('corrida');
  if (m) el.textContent = String(+m[0].n_simulaciones).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
});

dash.draw('grafico_campeon', (el) => {
  const t = filas('torneo');
  if (!t) { el.textContent = '—'; return; }
  const top = [...t].sort((a, b) => b['campeón'] - a['campeón']).slice(0, 10);
  const w = el.clientWidth || 600, rowH = 36, mL = Math.min(150, Math.max(136, w * 0.34)), mR = 60, h = top.length * rowH + 6;
  const x = d3.scaleLinear([0, d3.max(top, (d) => +d['campeón'])], [0, Math.max(40, w - mL - mR)]);
  const svg = d3.create('svg').attr('viewBox', `0 0 ${w} ${h}`).attr('role', 'img')
    .attr('aria-label', 'Barras con la probabilidad de campeón de las diez selecciones más probables');
  const tip = d3.create('div').attr('class', 'rw-tip').style('display', 'none');
  const g = svg.selectAll('g').data(top).join('g').attr('transform', (d, i) => `translate(0,${i * rowH + 3})`);
  g.append('circle').attr('cx', 14).attr('cy', rowH / 2).attr('r', 12).style('fill', (d) => col(d.equipo)[0]).style('stroke', 'rgba(128,128,128,.5)');
  g.append('text').attr('x', 14).attr('y', rowH / 2).attr('text-anchor', 'middle').attr('dominant-baseline', 'central')
    .style('fill', (d) => col(d.equipo)[1]).style('font-size', '8.5px').style('font-weight', 700).text((d) => d.equipo);
  g.append('text').attr('x', 34).attr('y', rowH / 2).attr('dominant-baseline', 'central')
    .style('fill', 'var(--color-fg)').style('font-size', '14px').text((d) => nom(d.equipo));
  g.append('rect').attr('x', mL).attr('y', 6).attr('height', rowH - 12).attr('rx', 5)
    .attr('width', (d) => Math.max(3, x(+d['campeón']))).style('fill', (d) => col(d.equipo)[2]);
  g.append('text').attr('x', (d) => mL + Math.max(3, x(+d['campeón'])) + 8).attr('y', rowH / 2).attr('dominant-baseline', 'central')
    .style('fill', 'var(--color-fg)').style('font-size', '14px').style('font-weight', 600).style('font-variant-numeric', 'tabular-nums')
    .text((d) => pct(+d['campeón']));
  g.append('rect').attr('x', 0).attr('y', 0).attr('width', w).attr('height', rowH).style('fill', 'transparent')
    .on('mousemove', (ev, d) => {
      const r = el.getBoundingClientRect();
      tip.style('display', 'block').text(nom(d.equipo) + ': campeón ' + pct(+d['campeón']) + ' · final ' + pct(+d.final))
        .style('left', Math.min(ev.clientX - r.left + 12, Math.max(0, w - 250)) + 'px').style('top', (ev.clientY - r.top + 12) + 'px');
    })
    .on('mouseleave', () => tip.style('display', 'none'));
  el.replaceChildren(svg.node(), tip.node());
});

function celdaNom(r) {
  const td = document.createElement('td');
  const s = document.createElement('span'); s.className = 'rw-equipo';
  s.append(insignia(r.equipo, 'm'), nom(r.equipo)); td.append(s);
  return td;
}
function celda(texto, p, color) {
  const td = document.createElement('td'); td.textContent = texto;
  if (p != null) calor(td, p, color); return td;
}

dash.draw('tabla_camino', (tb) => {
  const t = filas('torneo');
  if (!t) { tb.replaceChildren(); return; }
  const rows = [...t].sort((a, b) => b['campeón'] - a['campeón']);
  tb.replaceChildren(...rows.map((r) => {
    const tr = document.createElement('tr'); tr.dataset.key = r.equipo;
    tr.append(celdaNom(r), celda(r.grupo));
    ['octavos', 'cuartos', 'semis', 'final'].forEach((k) => tr.append(celda(pct(+r[k]), +r[k], 'var(--rw-heat)')));
    const c = celda(pct(+r['campeón']), Math.min(1, +r['campeón'] * 1.6), 'var(--rw-gold)'); c.style.fontWeight = 600; tr.append(c);
    if (+r.octavos < 0.5) tr.className = 'rw-out';
    return tr;
  }));
});

dash.draw('grupo', (tb) => {
  const t = filas('grupos');
  if (!t) { tb.replaceChildren(); return; }
  const rows = t.filter((r) => r.grupo === tb.dataset.g).sort((a, b) => b['avanza (total)'] - a['avanza (total)']);
  tb.replaceChildren(...rows.map((r) => {
    const tr = document.createElement('tr'); tr.dataset.key = r.equipo;
    tr.append(celdaNom(r));
    ['1º', '2º', '3º'].forEach((k) => tr.append(celda(pct(+r[k]), +r[k] * 0.8, 'var(--rw-heat)')));
    const a = celda(pct(+r['avanza (total)']), +r['avanza (total)'], 'var(--rw-heat)'); a.style.fontWeight = 600; tr.append(a);
    if (+r['avanza (total)'] < 0.5) tr.className = 'rw-out';
    return tr;
  }));
});

dash.draw('tabla_partidos', (tb) => {
  const t = filas('partidos_x');
  if (!t) { tb.replaceChildren(); return; }
  tb.replaceChildren(...t.map((r) => {
    const tr = document.createElement('tr'); tr.dataset.key = r.partido;
    const ln = celda(nom(r.local)), vn = celda(nom(r.visita));
    ln.style.textAlign = 'left'; vn.style.textAlign = 'left';
    const bal = document.createElement('td'); const sp = document.createElement('span'); sp.className = 'rw-split';
    const i1 = document.createElement('i');
    i1.style.width = (r.p_local * 100) + '%'; i1.style.background = col(r.local)[2];
    sp.append(i1); bal.append(sp); bal.style.textAlign = 'center';
    tr.append(celda(fechaCorta(d3.utcParse('%Y-%m-%d')(r.fecha))), celda(r.grupo), ln, vn,
      celda(pct(r.p_local), r.p_local * 0.45, 'var(--rw-heat)'), bal, celda(pct(r.p_visita), r.p_visita * 0.45, 'var(--rw-heat)'));
    return tr;
  }));
});

function opciones(sel, clave, porDefecto) {
  const t = filas('torneo');
  if (!t) { sel.replaceChildren(); return; }
  const eqs = t.map((r) => r.equipo).sort((a, b) => nom(a).localeCompare(nom(b), 'es'));
  sel.replaceChildren(...eqs.map((e) => new Option(nom(e), e)));
  sel.value = dash.params()[clave] || porDefecto;
  sel.onchange = () => dash.setParams({[clave]: sel.value});
}
dash.draw('sel_a', (sel) => opciones(sel, 'ea', 'NZL'));
dash.draw('sel_b', (sel) => opciones(sel, 'eb', 'RSA'));

function par() { const p = dash.params(); return [p.ea || 'NZL', p.eb || 'RSA']; }
function pGana(c, a, b) { return c ? c.find((r) => r.a === a && r.b === b) : null; }

dash.draw('cruce', (el) => {
  const c = filas('cruces'); const [a, b] = par();
  if (!c) { el.replaceChildren(); return; }
  if (a === b) { el.replaceChildren('Elegí dos selecciones distintas.'); return; }
  const ab = pGana(c, a, b), ba = pGana(c, b, a);
  if (!ab || !ba) { el.replaceChildren(); return; }
  const lado = (eq, v, donde) => {
    const d = document.createElement('div'); d.className = 'rw-lado';
    const n = document.createElement('div'); n.className = 'rw-nom'; n.textContent = nom(eq);
    const big = document.createElement('div'); big.className = 'rw-big';
    big.append(marcado(pct(+v), 'cruces', 'p_a_gana', donde));
    big.style.color = col(eq)[2];
    d.append(insignia(eq, 'g'), n, big); return d;
  };
  const x = document.createElement('div'); x.className = 'rw-x'; x.textContent = 'contra';
  el.replaceChildren(lado(a, ab.p_a_gana, 'a=' + a + '&b=' + b), x, lado(b, ba.p_a_gana, 'a=' + b + '&b=' + a));
});
dash.draw('barra_cruce', (el) => {
  const c = filas('cruces'); const [a, b] = par();
  const ab = c && a !== b ? pGana(c, a, b) : null;
  if (!ab) { el.replaceChildren(); return; }
  const p = +ab.p_a_gana;
  const i1 = document.createElement('i'), i2 = document.createElement('i');
  i1.style.width = (p * 100) + '%'; i1.style.background = col(a)[2];
  i2.style.width = ((1 - p) * 100) + '%'; i2.style.background = col(b)[2];
  el.replaceChildren(i1, i2);
});

let _t; window.addEventListener('resize', () => { clearTimeout(_t); _t = setTimeout(_redraw, 120); });
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', _redraw); else _redraw();

(function () {
  const root = document.documentElement, btn = document.getElementById('themeToggle');
  const sistema = () => matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  function aplicar(tema) {
    root.setAttribute('data-theme', tema);
    btn.textContent = tema === 'dark' ? '☀️' : '🌙';
    btn.title = tema === 'dark' ? 'Pasar a tema claro' : 'Pasar a tema oscuro';
    if (typeof _redraw === 'function') _redraw();
  }
  let guardado = null; try { guardado = localStorage.getItem('tema'); } catch (e) {}
  aplicar(guardado || sistema());
  btn.addEventListener('click', () => {
    const nuevo = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    aplicar(nuevo); try { localStorage.setItem('tema', nuevo); } catch (e) {}
  });
})();

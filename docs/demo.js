import { animate, createTimeline, stagger, svg, utils, onScroll } from './vendor/anime.esm.min.js';

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const NS = 'http://www.w3.org/2000/svg';
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
// ?still=<step> freezes the explainer on a step (used to make screenshots)
const still = new URLSearchParams(location.search).get('still');

/* ---------- copy button + tabs ---------- */
$$('[data-copy]').forEach(b => b.addEventListener('click', async () => {
  try { await navigator.clipboard.writeText(b.dataset.copy); b.textContent = 'Copied'; }
  catch { b.textContent = 'Select & copy'; }
  setTimeout(() => (b.textContent = 'Copy'), 1500);
}));
$$('.tab').forEach(t => t.addEventListener('click', () => {
  $$('.tab').forEach(x => { x.setAttribute('aria-selected', x === t); $('#' + x.getAttribute('aria-controls')).hidden = x !== t; });
}));

/* ---------- data: a population and its front (ZDT1-like, seeded) ---------- */
const rand = utils.createSeededRandom(11, 0, 1, 5);
const X0 = 50, X1 = 540, Y0 = 330, Y1 = 20;           // plot box
const px = f1 => X0 + 18 + f1 * (X1 - X0 - 36);
const py = f2 => Y0 - 14 - (f2 / 1.6) * (Y0 - Y1 - 28);

const sols = [];
for (let i = 0; i < 26; i++) {                         // the front: f2 = 1 - sqrt(f1)
  const f1 = (i / 25) ** 1.15;
  sols.push([f1, 1 - Math.sqrt(f1)]);
}
for (let i = 0; i < 90; i++) {                         // dominated points above it
  const f1 = rand();
  const lift = 0.06 + rand() ** 1.6 * 0.9;
  sols.push([f1, Math.min(1.58, 1 - Math.sqrt(f1) + lift)]);
}
// non-dominated filter (same rule as paretolens)
const nd = sols.map((a, i) => !sols.some((b, j) => j !== i && b[0] <= a[0] && b[1] <= a[1] && (b[0] < a[0] || b[1] < a[1])));
const frontIdx = sols.map((_, i) => i).filter(i => nd[i]).sort((a, b) => sols[a][0] - sols[b][0]);
const F = frontIdx.map(i => sols[i]);

// normalise front to [0,1] (0 = best)
const mins = [0, 1].map(k => Math.min(...F.map(p => p[k])));
const maxs = [0, 1].map(k => Math.max(...F.map(p => p[k])));
const N = F.map(p => p.map((v, k) => (v - mins[k]) / ((maxs[k] - mins[k]) || 1)));

const kneeI = N.reduce((best, p, i) => (1 - p[0] - p[1] > 1 - N[best][0] - N[best][1] ? i : best), 0);
function topsis(w) {
  const s = w[0] + w[1] || 1, ww = w.map(v => v / s);
  const sc = N.map(p => {
    const b = Math.sqrt(ww[0] * p[0] ** 2 + ww[1] * p[1] ** 2);
    const x = Math.sqrt(ww[0] * (1 - p[0]) ** 2 + ww[1] * (1 - p[1]) ** 2);
    return x / (b + x + 1e-12);
  });
  return sc.indexOf(Math.max(...sc));
}

/* ---------- draw ---------- */
const g = $('.pop');
const dots = sols.map(([f1, f2], i) => {
  const c = document.createElementNS(NS, 'circle');
  c.setAttribute('cx', px(f1).toFixed(1)); c.setAttribute('cy', py(f2).toFixed(1));
  c.setAttribute('r', nd[i] ? 5 : 4);
  g.appendChild(c);
  return c;
});
const frontDots = frontIdx.map(i => dots[i]);
const domDots = dots.filter((_, i) => !nd[i]);
$('.front-line').setAttribute('d', 'M' + F.map(([a, b]) => `${px(a).toFixed(1)} ${py(b).toFixed(1)}`).join(' L'));

const [kx, ky] = [px(F[kneeI][0]), py(F[kneeI][1])];
$('.knee').setAttribute('cx', kx); $('.knee').setAttribute('cy', ky);
$('.knee-t').setAttribute('x', kx + 16); $('.knee-t').setAttribute('y', ky - 14);

const pick = $('.pick'), pickT = $('.pick-t');
function placePick(i, animated = true) {
  const x = px(F[i][0]), y = py(F[i][1]);
  const opts = { translateX: x, translateY: y, duration: animated ? 450 : 0, ease: 'outBack(1.4)' };
  animate(pick, opts);
  // put the label on the side away from the knee so the two never collide
  const left = i < kneeI;
  animate(pickT, { translateX: x + 18, translateY: left ? y - 16 : y + 28,
                   duration: opts.duration, ease: 'outQuad' });
}

/* ---------- weights ---------- */
const w1 = $('#w1'), w2 = $('#w2');
function onWeights() {
  $('#w1v').textContent = (+w1.value).toFixed(2);
  $('#w2v').textContent = (+w2.value).toFixed(2);
  placePick(topsis([+w1.value, +w2.value]));
}
w1.addEventListener('input', onWeights);
w2.addEventListener('input', onWeights);

/* ---------- step highlighting ---------- */
const steps = $$('.steps li');
const setStep = n => steps.forEach((li, i) => li.classList.toggle('on', i === n));

/* ---------- final state (no motion, or ?still) ---------- */
function showFinal(step = 4) {
  setStep(step);
  dots.forEach(d => { d.style.opacity = 1; });
  if (step >= 1) domDots.forEach(d => { d.style.opacity = 0.12; });
  if (step >= 1) frontDots.forEach(d => d.classList.add('front'));
  $('.front-line').style.opacity = step >= 2 ? 1 : 0;
  $('.knee').style.opacity = $('.knee-t').style.opacity = step >= 3 ? 1 : 0;
  pick.style.opacity = pickT.style.opacity = step >= 4 ? 1 : 0;
  $('#weights').style.opacity = step >= 4 ? 1 : 0.4;
  placePick(topsis([+w1.value, +w2.value]), false);
}

const line = svg.createDrawable('.front-line');
let tl;
function play() {
  tl?.revert?.();
  w1.value = 1; w2.value = 1; onWeights();
  dots.forEach(d => d.classList.remove('front'));
  utils.set(dots, { opacity: 0 });
  utils.set(['.knee', '.knee-t', pick, pickT, '#weights'], { opacity: 0 });
  utils.set('.front-line', { opacity: 1 });
  utils.set(line, { draw: '0 0' });
  placePick(topsis([1, 1]), false);

  tl = createTimeline({ defaults: { ease: 'outExpo' } })
    .call(() => setStep(0))
    .add(dots, { opacity: [0, 1], scale: [0, 1], translateY: () => [utils.random(-40, -10), 0],
                 duration: 650, delay: stagger(9, { from: 'random' }), ease: 'outBack(1.5)' })
    .call(() => setStep(1), '+=500')
    .add(domDots, { opacity: [1, 0.12], scale: [1, 0.7], duration: 700, delay: stagger(5, { from: 'random' }) })
    .call(() => frontDots.forEach(d => d.classList.add('front')), '-=600')
    .add(frontDots, { scale: [1, 1.5, 1], duration: 600, delay: stagger(25) }, '-=500')
    .call(() => setStep(2), '+=300')
    .add(line, { draw: ['0 0', '0 1'], duration: 1100, ease: 'inOutQuad' })
    .call(() => setStep(3), '+=400')
    .add('.knee', { opacity: [0, 1], scale: [2.6, 1], duration: 800, ease: 'outElastic(1, .6)' })
    .add('.knee-t', { opacity: [0, 1], translateX: [-8, 0], duration: 500 }, '-=500')
    .call(() => setStep(4), '+=700')
    .add('#weights', { opacity: [0, 1], translateY: [10, 0], duration: 600 })
    .add([pick, pickT], { opacity: [0, 1], duration: 400 }, '-=300')
    // show the pick moving, as if someone dragged the sliders
    .call(() => { w1.value = 0.15; onWeights(); }, '+=700')
    .call(() => { w1.value = 1; w2.value = 0.15; onWeights(); }, '+=1100')
    .call(() => { w2.value = 1; onWeights(); }, '+=1100');
}

if (still !== null) showFinal(Math.max(0, Math.min(4, +still || 0)));
else if (reduce) showFinal(4);
else {
  document.documentElement.classList.add('js-anim');
  // title letters
  const h1 = $('.hero h1');
  h1.innerHTML = [...h1.textContent].map(c => `<span class="ch" aria-hidden="true">${c}</span>`).join('');
  createTimeline({ defaults: { ease: 'outExpo' } })
    .add('.hero .ch', { translateY: ['0.5em', 0], opacity: [0, 1], duration: 900, delay: stagger(40) })
    .add('.hero .reveal', { translateY: [14, 0], opacity: [0, 1], duration: 800, delay: stagger(100) }, '-=600');
  // explainer starts when it scrolls into view
  utils.set(dots, { opacity: 0 });
  onScroll({ target: '#demo', enter: 'end-=20% start', onEnter: () => { if (!tl) play(); } });
  animate('#reports .reveal', { opacity: [0, 1], translateY: [24, 0], duration: 800, ease: 'outExpo', delay: stagger(110),
    autoplay: onScroll({ target: '#reports', enter: 'end-=10% start' }) });
}
$('#replay').addEventListener('click', () => { if (reduce) showFinal(4); else play(); });

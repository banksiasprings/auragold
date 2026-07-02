#!/usr/bin/env node
// v42 anomaly-gate — offline test harness.
//   1. SYNTAX GATE: node --check every inline <script> block in index.html (catches the
//      catastrophic failure mode — one typo that breaks the whole single-file PWA).
//   2. MATH: extract the pure gate-statistics block from index.html and assert it against
//      known values (probit, chi-square survival, diagonal Mahalanobis, baseline mean/var).
//   3. CALIBRATION QUALITY: extract the quality ladder and assert reject/warn/ok verdicts.
// The functions are extracted from the shipped source (not copied) so the test tracks real code.
const fs = require('fs');
const path = require('path');
const cp = require('child_process');
const os = require('os');

const HTML = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
let pass = 0, fail = 0;
const ok = (name, cond, extra) => { (cond ? pass++ : fail++); console.log(`${cond ? 'PASS' : 'FAIL'}  ${name}${extra != null && !cond ? '  → ' + extra : ''}`); };
const near = (a, b, tol) => Math.abs(a - b) <= tol;

// ---------------------------------------------------------------- 1. SYNTAX GATE
(function syntaxGate() {
  const blocks = [];
  const re = /<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/gi;
  let m, i = 0;
  while ((m = re.exec(HTML))) { blocks.push(m[1]); }
  ok('syntax: found inline script blocks', blocks.length >= 1, blocks.length);
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'agsyn-'));
  blocks.forEach((code, idx) => {
    const f = path.join(tmp, `block_${idx}.js`);
    fs.writeFileSync(f, code);
    try { cp.execSync(`node --check ${f}`, { stdio: 'pipe' }); ok(`syntax: inline block #${idx} parses`, true); }
    catch (e) { ok(`syntax: inline block #${idx} parses`, false, String(e.stderr || e).split('\n').slice(0, 3).join(' ')); }
  });
})();

// ---------------------------------------------------------------- helpers: extract a fn/region by brace-matching
function extractFrom(startMarker, endFnName) {
  const start = HTML.indexOf(startMarker);
  if (start < 0) throw new Error('marker not found: ' + startMarker);
  const endStart = HTML.indexOf('function ' + endFnName, start);
  if (endStart < 0) throw new Error('end fn not found: ' + endFnName);
  // brace-match from the end function's opening brace
  let i = HTML.indexOf('{', endStart), depth = 0;
  for (; i < HTML.length; i++) { if (HTML[i] === '{') depth++; else if (HTML[i] === '}') { depth--; if (depth === 0) { i++; break; } } }
  return HTML.slice(start, i);
}

// ---------------------------------------------------------------- 2. MATH
let math;
try {
  const src = extractFrom('function _invNorm(p)', 'baselineStats');
  math = new Function(src + '\n;return { _invNorm, chiSqSurvival, _effVar, ANOM_RIDGE_FRAC, mahalSigma, baselineStats };')();
  ok('math: extracted stats block', true);
} catch (e) { ok('math: extracted stats block', false, e.message); math = null; }

if (math) {
  // probit (inverse standard-normal CDF) against known quantiles
  ok('probit(0.5)=0', near(math._invNorm(0.5), 0, 1e-6));
  ok('probit(0.975)≈1.959964', near(math._invNorm(0.975), 1.959963985, 1e-4), math._invNorm(0.975));
  ok('probit(0.9986501)≈3.0 (3σ)', near(math._invNorm(0.9986501), 3.0, 1e-3), math._invNorm(0.9986501));

  // chi-square survival P(χ²_k > x) against known values
  ok('chiSq survival(0,k=8)=1', near(math.chiSqSurvival(0, 8), 1, 1e-9));
  ok('chiSq survival(k=1 @3.841)≈0.05', near(math.chiSqSurvival(3.841459, 1), 0.05, 1e-3), math.chiSqSurvival(3.841459, 1));
  ok('chiSq survival(k=2 @5.991)≈0.05', near(math.chiSqSurvival(5.991465, 2), 0.05, 1e-3), math.chiSqSurvival(5.991465, 2));
  ok('chiSq survival(k=18 @18)≈0.4557', near(math.chiSqSurvival(18, 18), 0.45657, 3e-3), math.chiSqSurvival(18, 18));

  // baselineStats: mean + sample (n-1) variance of a known set
  const vecs = [[1, 10], [2, 20], [3, 30], [4, 40]];
  const st = math.baselineStats(vecs);
  ok('baselineStats mean[0]=2.5', near(st.mean[0], 2.5, 1e-9), st.mean[0]);
  ok('baselineStats mean[1]=25', near(st.mean[1], 25, 1e-9), st.mean[1]);
  ok('baselineStats var[0]=1.6667 (n-1)', near(st.var[0], 5 / 3, 1e-6), st.var[0]);
  ok('baselineStats dim=2, n=4', st.dim === 2 && st.n === 4);

  // mahalSigma: a window AT the baseline mean ⇒ ~0σ; a far window ⇒ large σ
  const base = math.baselineStats([[0, 0], [1, 1], [-1, -1], [0.5, -0.5], [-0.5, 0.5], [0.2, 0.1], [-0.2, -0.1], [0.3, -0.2]]);
  const atMean = math.mahalSigma(base.mean.slice(), base);
  ok('mahalSigma at mean is small (<0.6σ)', atMean.sigma < 0.6, atMean.sigma);
  const far = math.mahalSigma([50, -50], base);
  ok('mahalSigma far from mean is large (>4σ)', far.sigma > 4, far.sigma);
  ok('mahalSigma returns method+k', far.method === 'mahal' && far.k === 2, JSON.stringify({ m: far.method, k: far.k }));

  // _effVar: ridge floors a zero-variance feature so z-score can't explode / divide-by-zero
  ok('_effVar(mean=1,var=0) > 0 (ridge)', math._effVar(1, 0) > 0, math._effVar(1, 0));
  ok('_effVar grows with variance', math._effVar(1, 10) > math._effVar(1, 0));
}

// ---------------------------------------------------------------- 3. CALIBRATION QUALITY
let cal;
try {
  // assessBaselineQuality depends on ANOM_MIN_WINDOWS + _pctile; grab from its declaration through the fn end.
  const src = extractFrom('var ANOM_MIN_WINDOWS', 'assessBaselineQuality');
  cal = new Function(src + '\n;return { assessBaselineQuality, ANOM_MIN_WINDOWS };')();
  ok('calib: extracted quality ladder', true);
} catch (e) { ok('calib: extracted quality ladder', false, e.message); cal = null; }

if (cal) {
  const mkStats = (o) => Object.assign({ n: 100, var: new Array(18).fill(1), mean: new Array(18).fill(0.02), selfSigma: 0.7, d2: { p99: 2.0 } }, o);
  // healthy baseline
  ok('quality: healthy ⇒ ok', cal.assessBaselineQuality(mkStats({})).verdict === 'ok');
  // too few windows ⇒ reject
  ok('quality: too few windows ⇒ reject', cal.assessBaselineQuality(mkStats({ n: 10 })).verdict === 'reject');
  // 3+ dead (zero-variance) features ⇒ reject (muted mic / silence)
  ok('quality: flat features ⇒ reject', cal.assessBaselineQuality(mkStats({ var: [0, 0, 0, 0, 1].concat(new Array(13).fill(1)) })).verdict === 'reject');
  // unsteady ground (high self-σ) ⇒ warn (still usable, badged)
  ok('quality: unsteady ⇒ warn', cal.assessBaselineQuality(mkStats({ selfSigma: 2.0 })).verdict === 'warn');
  // high noise floor ⇒ warn
  ok('quality: loud floor ⇒ warn', cal.assessBaselineQuality(mkStats({ mean: [0.4].concat(new Array(17).fill(0.02)) })).verdict === 'warn');
  // reject dominates warn when both present
  ok('quality: reject beats warn', cal.assessBaselineQuality(mkStats({ n: 5, selfSigma: 2.0 })).verdict === 'reject');
}

// ---------------------------------------------------------------- 4. A/B LOGGING SHAPE + LOOP DORMANCY
try {
  const src = extractFrom('function nearestSpotId()', 'buildGateLog');
  const make = new Function('anomLiveSigma', 'activeBaseline', 'smoothedRMS', 'AG',
    src + '\n;return { nearestSpotId, buildGateLog };');
  const api = make(2.3, () => ({ id: 'act-y' }), 0.1234, { lastFix: { lat: -37.1, lng: 144.2 } });
  const g = api.buildGateLog('gate-fired', 6.7, { id: 'base-x' });
  const keys = ['timestamp', 'gate_score', 'gate_verdict', 'shadow_rms_value', 'spot_id', 'calibration_id'];
  ok('gateLog: has exactly the 6 brief fields', keys.every(k => k in g) && Object.keys(g).length === 6, Object.keys(g).join(','));
  ok('gateLog: gate_score rounded (6.7)', g.gate_score === 6.7, g.gate_score);
  ok('gateLog: verdict passthrough', g.gate_verdict === 'gate-fired');
  ok('gateLog: shadow_rms_value captured', g.shadow_rms_value === 0.1234, g.shadow_rms_value);
  ok('gateLog: spot_id ~11m grid key', g.spot_id === '-37.1000,144.2000', g.spot_id);
  ok('gateLog: calibration_id from base', g.calibration_id === 'base-x');
  const gm = api.buildGateLog('manual-ungated', null, null);
  ok('gateLog: manual falls back to live σ', gm.gate_score === 2.3, gm.gate_score);
  ok('gateLog: manual falls back to active baseline', gm.calibration_id === 'act-y');
  ok('gateLog: manual verdict', gm.gate_verdict === 'manual-ungated');
} catch (e) { ok('gateLog: extracted + shaped', false, e.message); }

try {
  const src = extractFrom('function anomLoopWanted()', 'anomLoopWanted');
  const mk = (gate, running, panel) => new Function('acfg', 'running', 'panelVisible',
    src + '\n;return anomLoopWanted();')({ anomalyGate: gate }, running, () => panel);
  // The core byte-identity guarantee: gate OFF + no panel ⇒ loop is NOT wanted ⇒ parked ⇒ zero anomaly code.
  ok('dormancy: gate off + no panel ⇒ parked', mk(false, true, false) === false);
  ok('dormancy: gate off + not running + no panel ⇒ parked', mk(false, false, false) === false);
  ok('dormancy: gate on + running ⇒ active', mk(true, true, false) === true);
  ok('dormancy: gate on + NOT running ⇒ parked (nothing to score)', mk(true, false, false) === false);
  ok('dormancy: panel open ⇒ active (tuning chip)', mk(false, false, true) === true);
} catch (e) { ok('dormancy: extracted anomLoopWanted', false, e.message); }

// ---------------------------------------------------------------- summary
console.log(`\n${pass}/${pass + fail} passed` + (fail ? `  (${fail} FAILED)` : ''));
process.exit(fail ? 1 : 0);

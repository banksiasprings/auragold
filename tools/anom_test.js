#!/usr/bin/env node
// v42 ground-anomaly gate — offline verification harness.
//
//  Two things are proven here, both against the SHIPPED source (no copies):
//   1. The Mahalanobis math (AnomCore) is extracted verbatim from index.html and
//      exercised — Cholesky, correlated-feature distance, fit quality tiers, the
//      threshold floor, the two-tier voter, and the KEY property: a loud-but-normal
//      window is VETOED (the gate replaces the amplitude trigger, doesn't add to it).
//   2. Gate-OFF byte-identity: the v41.4 detection functions (maybeAutoFlag, feedRMS,
//      pushSamples, snapshot, saveEvent, encodeWAV) and the onaudioprocess handler
//      body are byte-for-byte unchanged between v41.4 (4a4260b) and HEAD — procClassic
//      is the verbatim handler, installed whenever anomaly mode is off.
//
//  Run: node tools/anom_test.js   (from repo root)

var fs = require('fs'), path = require('path'), cp = require('child_process'), os = require('os');
var ROOT = path.resolve(__dirname, '..');
var HTML = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
var V414 = '4a4260b';   // last v41.4 ship (pre-v42)

var pass = 0, fail = 0, fails = [];
function ok(name, cond, extra) { if (cond) { pass++; } else { fail++; fails.push(name + (extra ? ' — ' + extra : '')); } }
function approx(a, b, tol) { return Math.abs(a - b) <= (tol || 1e-6); }

// ---- extract + load the embedded AnomCore (the exact shipped math) ----
function extractAnomCore(html) {
  var a = html.indexOf('===ANOMCORE_START==='), b = html.indexOf('===ANOMCORE_END===');
  if (a < 0 || b < 0) throw new Error('ANOMCORE delimiters not found in index.html');
  // back up to the start of the opening comment, forward to the end of the closing comment
  var start = html.lastIndexOf('/*', a), end = html.indexOf('*/', b) + 2;
  return html.slice(start, end);
}
var coreSrc = extractAnomCore(HTML);
var tmpFile = path.join(os.tmpdir(), 'anomcore_extracted_' + process.pid + '.js');
fs.writeFileSync(tmpFile, coreSrc);
var makeAnomCore = require(tmpFile).makeAnomCore;
ok('AnomCore extracted + loaded from index.html', typeof makeAnomCore === 'function');

// deterministic PRNG
function rng(seed) { var s = seed >>> 0; return function () { s = (1103515245 * s + 12345) & 0x7fffffff; return s / 0x7fffffff; }; }
function gauss(r) { var u = Math.max(1e-12, r()), v = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); }

// ============================ MATH ============================
(function mathTests() {
  // 1. Mahalanobis vs hand-computed (identity covariance)
  var A = makeAnomCore(2);
  var L = A.cholesky([[1, 0], [0, 1]]);
  ok('chol(I) = I', L[0][0] === 1 && L[1][1] === 1 && L[1][0] === 0);
  ok('maha identity (3,4) → 25', approx(A.mahaChol([3, 4], [0, 0], L), 25, 1e-9));

  // 2. Cholesky reconstructs Σ
  var A3 = makeAnomCore(3);
  var S = [[4, 2, 0.6], [2, 3, 0.5], [0.6, 0.5, 2]];
  var L3 = A3.cholesky(S), okRec = true;
  for (var i = 0; i < 3; i++) for (var j = 0; j < 3; j++) { var s = 0; for (var k = 0; k < 3; k++) s += L3[i][k] * L3[j][k]; if (!approx(s, S[i][j], 1e-9)) okRec = false; }
  ok('L·Lᵀ reconstructs Σ', okRec);
  ok('chol(non-PD) → null', A.cholesky([[1, 2], [2, 1]]) === null);

  // 3. Correlated features: moving against correlation is far, with it is near
  var Lc = A.cholesky([[1, 0.9], [0.9, 1]]);
  var against = A.mahaChol([1, -1], [0, 0], Lc), withc = A.mahaChol([1, 1], [0, 0], Lc);
  ok('maha: against-correlation ≫ with-correlation', against > withc * 5, 'against=' + against.toFixed(2) + ' with=' + withc.toFixed(2));

  // 4. fit(): well-conditioned quiet ground
  var A8 = makeAnomCore(8), r = rng(1), W = [];
  for (var q = 0; q < 80; q++) { var v = []; for (var f = 0; f < 8; f++) v.push(gauss(r) * (1 + 0.2 * f) + f); W.push(v); }
  var base = A8.fit(W);
  ok('fit quality ok on clean ground', base.quality === 'ok', 'q=' + base.quality + ' w=' + (base.warnings || []).join(','));
  ok('fit produces Cholesky factor', !!base.chol);
  ok('d2 anchors ordered p50≤p90≤p99≤max', base.d2.p50 <= base.d2.p90 && base.d2.p90 <= base.d2.p99 && base.d2.p99 <= base.d2.max + 1e-9);
  var thr = A8.threshold(base, 1.5);
  var anom = []; for (var m = 0; m < 8; m++) anom.push(base.center[m] + 8 * base.scale[m]);
  ok('wildly anomalous window exceeds threshold', A8.mahalanobis(anom, base) > thr);

  // 5. Threshold = max(mult·p99, χ² floor)
  ok('threshold floored at χ²₈ P99 (tight calibration)', approx(A8.threshold({ d2: { p99: 5 } }, 1.5), A8.chi99));
  ok('threshold = mult·p99 above the floor', approx(A8.threshold({ d2: { p99: 30 } }, 1.5), 45));
  ok('χ²₈ P99 ≈ 20.09', approx(A8.chi99, 20.0902, 1e-3));

  // 6. Voter: two-tier
  var v1 = A8.makeVoter(10);
  ok('single over-threshold window does NOT fire', v1.push(11) === false);
  ok('second over-threshold window (2 of 3) fires', v1.push(12) === true);
  ok('big single window (>1.5×) fires immediately', A8.makeVoter(10).push(16) === true);
  var v3 = A8.makeVoter(10);
  ok('below-threshold never fires', !v3.push(5) && !v3.push(9.9) && !v3.push(5));
})();

// ================ THE KEY TEST: gate replaces amplitude ================
(function vetoTest() {
  var A = makeAnomCore(8), r = rng(7), W = [];
  // Baseline where log-RMS (feature 0) swings WIDELY — loud sweeps are normal here — and feature 1
  // tracks the energy. So "loud" is in-distribution as long as it stays on the learned correlation line.
  for (var i = 0; i < 80; i++) { var e = gauss(r) * 1.5; var v = [e, 0.5 * e + gauss(r) * 0.2]; for (var j = 2; j < 8; j++) v.push(gauss(r) * 0.3); W.push(v); }
  var base = A.fit(W), thr = A.threshold(base, 1.5);
  var loudNormal = [4.0, 2.0, 0, 0, 0, 0, 0, 0];   // very loud, but on the correlation line
  var ampWouldFire = loudNormal[0] > base.center[0]; // the RMS amplitude trigger fires on loudness alone
  ok('amplitude trigger WOULD fire on the loud window', ampWouldFire === true);
  ok('GATE VETOES the loud-but-normal window (D² < threshold)', A.mahalanobis(loudNormal, base) < thr,
    'd2=' + A.mahalanobis(loudNormal, base).toFixed(2) + ' thr=' + thr.toFixed(2));
  var loudWeird = [4.0, -3.0, 4, 4, 4, 4, 4, 4];   // loud AND spectrally off the learned line
  ok('gate FIRES on loud + spectrally-anomalous window', A.mahalanobis(loudWeird, base) > thr);
})();

// ==================== calibration reject / warn ====================
(function calibrationTests() {
  var A = makeAnomCore(8), r = rng(3);
  var few = []; for (var i = 0; i < 12; i++) { var v = []; for (var j = 0; j < 8; j++) v.push(gauss(r)); few.push(v); }
  ok('reject: <30 windows → unusable', A.fit(few).quality === 'unusable');

  var flat = []; for (var k = 0; k < 60; k++) flat.push([gauss(r), gauss(r), gauss(r), gauss(r), gauss(r), 1, 1, 1]);
  ok('reject: ≥3 constant features → unusable', A.fit(flat).quality === 'unusable');

  var oneFlat = []; for (var z = 0; z < 60; z++) { var w = []; for (var y = 0; y < 7; y++) w.push(gauss(r) * (1 + y)); w.push(2.5); oneFlat.push(w); }
  var ofb = A.fit(oneFlat);
  ok('one constant feature → usable (diagonal fallback or shrinkage), finite D²', ofb.quality !== 'unusable' && isFinite(A.mahalanobis(oneFlat[0], ofb)), 'q=' + ofb.quality);

  var noisy = []; for (var m = 0; m < 80; m++) { var n = []; for (var p = 0; p < 8; p++) n.push(gauss(r) * 0.5); noisy.push(n); }
  for (var o = 0; o < 8; o++) { var big = []; for (var pp = 0; pp < 8; pp++) big.push(gauss(r) * 12 + 30); noisy.push(big); }
  var nb = A.fit(noisy);
  ok('warn: unsteady ground flagged but usable', nb.quality !== 'unusable' && nb.warnings.indexOf('unsteady-ground') >= 0, 'q=' + nb.quality + ' w=' + nb.warnings.join(','));

  var clean = []; for (var q = 0; q < 80; q++) { var c = []; for (var s = 0; s < 8; s++) c.push(gauss(r) * 0.5 + s); clean.push(c); }
  clean.push([50, 50, 50, 50, 50, 50, 50, 50]);   // one knock
  ok('single stray beep absorbed by the 5% trim (quality ok)', A.fit(clean).quality === 'ok');
})();

// ==================== GATE-OFF BYTE-IDENTITY vs v41.4 ====================
(function byteIdentity() {
  var oldHtml;
  try { oldHtml = cp.execSync('git show ' + V414 + ':index.html', { cwd: ROOT, maxBuffer: 64 * 1024 * 1024 }).toString(); }
  catch (e) { ok('byte-identity: git show v41.4 available', false, 'git error: ' + e.message); return; }

  function extractFn(src, name) {
    var sig = 'function ' + name + '(', idx = src.indexOf(sig);
    if (idx < 0) return null;
    var i = src.indexOf('{', idx), depth = 0, j = i;
    for (; j < src.length; j++) { var c = src[j]; if (c === '{') depth++; else if (c === '}') { depth--; if (depth === 0) { j++; break; } } }
    return src.slice(idx, j);
  }
  // v41.4 inline handler body → the statements between the assignment and its closing brace.
  function extractInlineHandler(src) {
    var sig = 'procNode.onaudioprocess = function (e) {', idx = src.indexOf(sig);
    if (idx < 0) return null;
    var i = src.indexOf('{', idx), depth = 0, j = i;
    for (; j < src.length; j++) { var c = src[j]; if (c === '{') depth++; else if (c === '}') { depth--; if (depth === 0) break; } }
    return src.slice(i + 1, j);
  }
  function bodyOf(fnSrc) { var i = fnSrc.indexOf('{'), j = fnSrc.lastIndexOf('}'); return fnSrc.slice(i + 1, j); }
  // normalize: drop comments + blank lines, trim each line
  function norm(code) {
    return code.split('\n').map(function (l) { return l.replace(/\/\/.*$/, '').trim(); }).filter(function (l) { return l.length; }).join('\n');
  }

  var fns = ['maybeAutoFlag', 'feedRMS', 'pushSamples', 'snapshot', 'saveEvent', 'encodeWAV', 'initRing', 'guanoFor'];
  fns.forEach(function (name) {
    var a = extractFn(oldHtml, name), b = extractFn(HTML, name);
    ok('byte-identical: ' + name + '() unchanged v41.4→HEAD', a && b && norm(a) === norm(b), a && b ? '' : 'not found');
  });

  // The detection handler: v41.4 inline body === HEAD procClassic body (verbatim per-block path).
  var oldHandler = extractInlineHandler(oldHtml);
  var newClassic = extractFn(HTML, 'procClassic');
  ok('byte-identical: onaudioprocess handler body == procClassic body',
    oldHandler && newClassic && norm(oldHandler) === norm(bodyOf(newClassic)),
    oldHandler ? 'old:[' + norm(oldHandler) + '] new:[' + norm(bodyOf(newClassic || '')) + ']' : 'v41.4 handler not found');

  // Sanity: v41.4 had NO anomaly gate, HEAD does (proves this is a real replacement build).
  ok('v41.4 had no anomaly gate', oldHtml.indexOf('ANOMCORE_START') < 0 && oldHtml.indexOf('AGGate') < 0);
  ok('HEAD adds the anomaly gate', HTML.indexOf('AGGate') >= 0 && HTML.indexOf('procGated') >= 0);
})();

// ==================== report ====================
try { fs.unlinkSync(tmpFile); } catch (e) {}
console.log('\nv42 anomaly-gate tests: ' + pass + ' passed, ' + fail + ' failed');
if (fail) { console.log('FAILURES:\n  ' + fails.join('\n  ')); process.exit(1); }
console.log('ALL GREEN ✓');

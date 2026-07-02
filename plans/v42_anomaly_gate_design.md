# v42 — Ground-Baseline Anomaly Gate: Design Document

**Status:** DRAFT — awaiting Steven's approval before build
**Author:** Fable 5 (medium) planning pass, 2026-07-02
**Builds on:** v24 audio capture · v26 ML classifier · v32 per-combo models
**Inspiration:** [nickvellios/metal-detector-ai](https://github.com/nickvellios/metal-detector-ai) — baseline-learn + statistical gate, re-imagined browser-native.

---

## 0. Correction to the brief (read this first)

The task brief says v26 "runs on every audio window" and "the classifier fires
constantly on ground noise." The code says otherwise (index.html ~4600–4614,
5060–5074): the live loop computes **only a smoothed RMS scalar**. When
`smoothedRMS ≥ acfg.threshold` (debounced 3 s), a 10 s clip is saved, and *then*
meyda features + the tf.js classifier run **once per saved clip** in a worker.

So on hot ground the thing that fires constantly is the **scalar RMS amplitude
trigger** — causing constant clip saves (~320 KB each, 500/day cap), constant
classifier scoring, storage churn, and a map full of junk auto-flags. The
classifier is downstream and innocent.

**Consequence for v42:** the anomaly gate's correct home is *replacing/upgrading
the RMS trigger criterion* inside `maybeAutoFlag()`, not sitting between a
per-window classifier and its input (no such thing exists). Everything
downstream — debounce, saveEvent, clip features, classifier, ml-discard —
stays exactly as is. The outcome Steven wants (run the GPX 6000 hotter, fewer
false fires) is unchanged; the slot-in point is simpler and safer than the
brief assumed.

One more fact that matters everywhere below: **live audio is a
`ScriptProcessor(4096)` on a 16 kHz AudioContext** (falls back to device rate,
usually 48 kHz, if the browser refuses 16 k). At 16 kHz one block = 4096
samples = **256 ms** — a natural gate window that costs nothing to frame.

---

## 1. Feature selection

### Gate feature vector — 8 dimensions per ~256 ms window

| # | Feature | Why | Cost |
|---|---------|-----|------|
| 1 | **log-RMS** | Core energy; log-compressed → closer to Gaussian, tames the huge dynamic range | already computed live (reuse `feedRMS` sums or take from meyda frame) |
| 2 | **Spectral centroid** (mean over frames) | Target "zips" shift tone vs broadband ground rumble | 1 FFT/frame via meyda |
| 3 | **Spectral flux** (mean over frames) | *The* transient detector: ground chatter is spectrally stationary; a target response is a rapid frame-to-frame spectral change | prev-frame magnitude diff, trivial |
| 4 | **Zero-crossing rate** | High-frequency proxy, no FFT needed, nearly free | trivial |
| 5 | **Spectral flatness** (mean) | Ground noise is noise-like (flat); target tones are peaked. Already in the v26 extract list | free with same FFT |
| 6–8 | **MFCC 1, 2, 3** (means) | Gross spectral-envelope shape; where cross-feature correlation lives. Skip MFCC0 (≈ log energy, duplicates RMS) | free with same FFT |

**Rejected:** spectral rolloff (highly correlated with centroid — adds a
dimension without adding information); MFCCs 4–12 (dimensionality cost; at d=8
a 15–20 s calibration gives n/d ≈ 9–12 which estimates a full covariance
comfortably with shrinkage — at d=17+ it wouldn't); full 38-dim v26 clip vector
(those are clip-level mean/std aggregates over 10 s — they don't exist per
window, and n < d(d+1)/2 guarantees a singular covariance).

### Window size: 256 ms, empirically motivated

GPX 6000 target responses at normal sweep speed are ~100–400 ms transients.
Below ~100 ms spectral stats are too noisy; above ~500 ms a transient dilutes
into ground noise. 256 ms sits in the sweet spot, is within cooee of the
reference project's 200 ms, **and equals exactly one ScriptProcessor block at
16 kHz** — no reframing buffer needed. On a 48 kHz fallback context, aggregate
blocks by elapsed time (~3 blocks ≈ 256 ms); window logic must be time-based,
never block-count-based.

Gate cadence: ~4 evaluations/s at 16 kHz. (Brief said 5 Hz on 200 ms; 3.9 Hz on
256 ms is the same animal.)

### Compute strategy & v26 reuse

There is **no live feature compute today to reuse** — v26 extraction happens
only at save time, in a worker, on the whole 10 s clip. What we reuse is the
**code and configuration**, not the compute:

- Same meyda frame config as `extractFeatures`: 512-sample frames, 256 hop,
  hanning, `Meyda.extract([...])` — so gate features and classifier features
  come from one framing convention and one library load path
  (`ensureMeydaMain()` / SW-cached).
- Gate extraction runs **inline in `onaudioprocess`** (which is main-thread
  anyway — ScriptProcessor callbacks are). ~15 frames × tens of µs per 256 ms
  block ≈ well under 1 ms/block. No worker round-trip, no postMessage churn.
  Wrap in try/catch — a gate exception must never kill capture.
- The save-time v26 clip pipeline is untouched. When the gate fires, the event
  saves and gets clip-level features + classifier verdict exactly as today.

Meyda loads lazily only when anomaly mode is armed. If it can't load (first-run
offline before SW has cached it), the gate disarms and falls back to amplitude
mode with a toast — never a dead trigger.

---

## 2. Baseline representation

**Recommendation: full covariance (d=8), stored as mean + regularized Cholesky
factor, plus the raw calibration windows.**

| Option | Storage/baseline | Inference | Verdict |
|--------|-----------------|-----------|---------|
| Per-feature mean+std (diagonal) | ~64 B | O(d) | Ignores correlations — RMS/flux/centroid are strongly correlated in ground noise. Misses correlation-space anomalies, over-fires on normal co-movement. **Fallback tier only.** |
| **Full covariance** | ~600 B (μ: 8 + L: 36 floats + scales) | O(d²) = 64 mults @ 4 Hz | Captures correlation structure; enables Mahalanobis. Trivially cheap at d=8. **✅ Recommended.** |
| GMM / 1-class SVM / isolation forest | KBs, model code | heavier | No principled threshold, hard to make robust in hand-rolled JS, nothing to gain at d=8 / n≈80. Rejected. |

**Also store the raw calibration windows** (~80 windows × 8 × Float32 ≈ 2.6 KB):
enables re-fit with different trimming/shrinkage, threshold retuning without
re-capture, merging two nearby baselines, and offline debugging of "why did
this baseline behave badly."

**Numerical target: ≤ 10 KB per baseline including raw windows and metadata;
≤ 1 MB total at the 100-baseline cap.** Against the 60 MB app budget this is
noise (one audio clip = 320 KB = 30+ baselines).

Fitting recipe (all in JS doubles):
1. Standardize each feature by a robust scale (median/IQR of the calibration
   sample) — raw units span ~5 orders of magnitude (centroid in kHz vs RMS in
   0.0x); covariance conditioning demands this.
2. Trim: fit once, drop the top 5 % of calibration windows by D², refit
   (poor-man's MCD — one stray beep or knock in the calibration won't poison it).
3. Shrinkage: Σ′ = (1−λ)Σ + λ·diag(Σ), λ = 0.1 default.
4. Cholesky-factor Σ′; store L. Mahalanobis at inference = forward-substitute,
   sum of squares — no explicit inverse, numerically stable.

---

## 3. Statistical distance metric

**Recommendation: Mahalanobis distance, computed via the stored Cholesky
factor.**

- **Mahalanobis** — handles correlated features by construction; O(d²); under a
  Gaussian baseline D² ~ χ²₈, giving a *principled* threshold scale; a single
  interpretable score. ✅
- Euclidean on z-scored features = diagonal Mahalanobis — degradation tier 1
  (see below), not the default: ground-noise features co-move, and ignoring
  that is precisely how you get false fires on hard sweeps.
- Per-feature z-score voting — weaker as a detector, but **keep it as the
  explanation layer**: when the gate fires, record the top-2 |z| features so
  the UI can say "tone jumped, energy steady" (matches the v36 verdict-first
  'Why?' pattern Steven already knows).
- One-class SVM / isolation forest — no incremental accuracy at this
  dimensionality and sample size, significant hand-rolled-JS risk, no
  closed-form threshold semantics. Rejected.

### Ill-conditioned covariance — graceful degradation ladder

1. λ = 0.1 shrinkage is always applied (fit time).
2. If Cholesky fails (non-PD) or the diagonal of L implies condition > ~1e6:
   refit with λ = 0.3, then 0.6.
3. Still bad (e.g. a constant feature — someone calibrated against silence):
   floor each per-feature std at an absolute epsilon and **fall back to
   diagonal Mahalanobis** (z-score sum-of-squares). Baseline gets a
   `quality: 'diagonal-fallback'` badge in the UI.
4. Worst case (NaNs in fit): baseline marked unusable, gate disarms, amplitude
   mode takes over, user prompted to recalibrate. **Never a crash; never a
   silent no-fire gate.**

Browser-JS numerical hygiene: everything in doubles (JS numbers); features
robust-standardized before any covariance math; log-transforms with epsilon
floors (`log(x + 1e-8)`) for RMS and flux; NaN/Inf guard on every live window —
skip the window and count it; if >10 % of windows in a minute are skipped,
disarm + toast.

---

## 4. Threshold logic

**Recommendation: static per-baseline threshold, anchored empirically to the
calibration sample — plus drift *detection* (not silent adaptation).**

- Pure theory (χ²₈ P99 ≈ 20.1, the "3σ analog") under-estimates real ground:
  noise tails are heavier than Gaussian → it would over-fire.
- Pure adaptive (rolling live percentile) **self-defeats in this domain**: walk
  onto a mineralized patch and the threshold rises to accommodate it — you go
  blind exactly where you wanted sensitivity; a slow sweep over a big deep
  target gets absorbed into "normal." Rejected as the trigger criterion.
- **Hybrid anchor:** threshold = multiplier × P99(D² of calibration windows),
  floored at the χ²₈ P99 so a pathologically tight calibration can't produce a
  hair-trigger. The calibration sample tells us where *this spot's* quiet
  ground actually sits; the multiplier is the user knob.
- **Drift detection, not adaptation:** keep a slow rolling median of live D².
  If it sits above the baseline's calibration P90 for ~2–3 minutes, ground (or
  detector settings) have changed → banner: "Ground doesn't match your
  baseline — recalibrate?" The threshold itself never silently moves. This is
  an honesty decision: silent adaptation would mask exactly the changes we
  want surfaced.

### User-facing sensitivity (no sigmas)

Slider, 5 detents, mapping to the multiplier over the P99 anchor:

| Label | Multiplier | Meaning shown to user |
|-------|-----------|----------------------|
| Loose | 1.0× | "Flags anything unusual — expect more false alarms" |
| Relaxed | 1.25× | |
| **Balanced** (default) | 1.5× | "Good starting point" |
| Firm | 2.0× | |
| Tight | 3.0× | "Only strong, clear anomalies" |

Under the slider, show a live concrete consequence: **"~N gate fires/min at
this setting (last 5 min)"** — computed by replaying the rolling D² history
against the candidate threshold. That's the number Steven actually cares about.

---

## 5. Integration with v26

### Where it slots

`maybeAutoFlag()` (index.html ~4603) currently: `mode off|amp|ml`, trigger =
`smoothedRMS ≥ acfg.threshold`, 3 s debounce, `saveEvent('auto')`, ml-mode
discard via `_autoMlGate`.

v42 adds **one new trigger criterion**, orthogonal to the verdict layer:

```
Trigger layer (pick one):        Verdict layer (unchanged):
  amp   — RMS ≥ threshold          none — keep every fired event
  gate  — anomaly D² > thr   →     ml   — classifier discards low-gold
```

Concretely: a new `afmode` value (`anomaly`), with the existing `mlCombined`
classifier-discard behaviour composing on top unchanged. Debounce, ring-buffer
snapshot, WAV save, clip feature extraction, per-combo model scoring: all
untouched downstream. **Gate toggle OFF → byte-identical v26/v32 behaviour**
(hard constraint honored).

Trigger detail — two-tier vote to catch single fast zips without firing on
one-window spikes (knocks, wind buffet):
- any single window with D² > 1.5 × thr → fire immediately;
- else ≥ 2 of the last 3 windows (≈ 768 ms) over thr → fire.
Worst-case trigger latency ≈ 1 s window-to-fire; the 10 s ring buffer means the
audio is captured regardless of trigger latency, so nothing is lost.

### Advisory vs hard-blocking

**Hard-gating for the auto-flag trigger** (that's its whole point — fewer
saves, less churn), **advisory in the UI** (live score chip, §8) so Steven can
watch it work and build trust. Two absolutes:

1. **Manual REC hits are never gated.** User override is sacred.
2. **Every fired event records `gateScore` (D²), `gateBaselineId`, and the
   top-2 z-features.** Plus a per-session shadow counter: while in anomaly
   mode, count what the plain RMS trigger *would* have fired (counterfactual
   tally, no clips saved). This makes every real field session an A/B data
   point for free (§7).

### No baseline near current location

Fall back to amplitude mode automatically, with a persistent (non-spammy)
banner: "No ground baseline within 200 m — using amplitude trigger.
**Calibrate here?**" Never a silent no-op, never a dead trigger.

### Double-compute avoidance

Gate = new lightweight inline compute on live blocks (nothing existed there
before beyond RMS). Clip-level v26 extraction unchanged at save time. Shared:
meyda library load (`ensureMeydaMain`, SW-cached), frame convention (512/256
hanning), and the MFCC configuration — so numbers are comparable and there is
one extraction idiom in the codebase, exercised two ways.

---

## 6. Baseline management

### Storage: new store in the existing shared DB

New object store `auragold_baselines` (keyPath `id`), **DB_VER 4 → 5**. Do NOT
reuse `S_MODELS` — different lifecycle (user-managed spots vs trained-model
registry), different key semantics, and mixing them risks the v32 legacy-id
back-compat that S_MODELS carries. The existing additive
`contains()`-guarded `onupgradeneeded` pattern makes the migration safe for
all existing users.

Schema (per baseline):

```js
{
  id, name,                     // auto: "Spot near <locality> — 2 Jul" (reverse-geocode offline-safe: lat/lng fallback), user-renamable
  lat, lng, acc,                // GPS at calibration
  detector, coil,               // ← baselines are per detector+coil combo, like v32 models
  sampleRate,                   // 16000 normally; guards the 48 kHz fallback case
  createdTs, durationMs, nWindows,
  featNames, featScale,         // versioned feature contract
  mean, chol,                   // μ (8) + Cholesky L (36 floats), post-shrinkage
  lambda, quality,              // shrinkage used; {ok|diagonal-fallback|unusable, warnings[]}
  d2: { p50, p90, p99, max },   // calibration D² anchors (threshold + drift detection)
  rawWindows,                   // packed Float32 blob ~2.6 KB (refit/debug)
  gateVersion: 1
}
```

**Detector+coil tagging is not optional** — a GPX 6000 baseline is meaningless
for the Gold Monster (the brief missed this; v32 established the precedent).
Auto-selection filters to the active combo first.

### Auto-selection: nearest within N = 200 m

Rationale: phone GPS accuracy is 5–15 m; Victorian goldfields mineralization
varies over tens of metres; a worked patch in one session is typically
50–300 m across. 200 m keeps a baseline valid across a patch without dragging
in the next gully's different ground. Beyond 200 m: no auto-select, prompt.
Ties: nearest wins. Manual pin ("use this baseline") overrides GPS for the
session. Make N a constant, not a setting — one less knob.

### Re-calibration prompts

| Trigger | Response |
|---------|----------|
| Moved > 200 m from active baseline | Banner + auto-fallback to amp mode (notify, never silent) |
| Live median D² > baseline P90 sustained ~2–3 min | "Ground doesn't match your baseline — recalibrate?" |
| Baseline age > 90 days at selection | Gentle nudge (moisture/seasonal ground change) |
| Detector settings changed | Undetectable from audio alone — handled by calibration-flow copy: "Recalibrate after changing sensitivity or ground balance" |

### Calibration capture

15–20 s guided capture: "**Sweep normally over quiet ground** — no targets, no
talking." Sweeping matters: the baseline must contain normal sweep-motion
ground response, not a static coil. Live quality feedback during capture, trim
+ self-consistency check after (§9). At ~4 windows/s this yields 60–80
windows — comfortably above the n ≈ 10×d floor for a stable d=8 covariance
with shrinkage.

---

## 7. Verification / evaluation plan

### Offline harness (Node, `tools/` — same pattern as the v26/v31 verification)

The v31 smoke-test clips are clip-level; the gate needs **continuous sessions**.
Build a synthetic session generator: minutes of parameterized ground noise
(quiet / mild / hot: filtered noise + slow wander + occasional pops) with v31-
style gold/junk zips injected at known timestamps. Ground truth = injection
times. The gate math (standardize → fit → Cholesky → D²) is pure JS with no
DOM dependency — extract it as a testable block and run identical code in Node.

### Metrics

| Metric | Definition | Target |
|--------|-----------|--------|
| TP rate | injected targets that fire the gate (±1 s match) | ≥ 95 % at Balanced |
| FP rate | gate fires/min on target-free hot-ground sessions | ≥ 3× fewer than the RMS trigger at matched TP |
| ROC | sweep the multiplier → TPR vs fires/min; overlay the RMS-threshold ROC on identical audio | gate curve dominates on hot ground |
| Latency | window + vote, trigger-to-save | ≤ 1 s (ring buffer makes this non-lossy) |
| CPU/battery | `onaudioprocess` handler time, gate on vs off | < 2 ms per 256 ms block on the Motorola; no measurable battery delta over a 2 h session |

End-to-end: simulate both full pipelines (RMS trigger + classifier vs gate
trigger + classifier) on the same synthetic sessions; count saved events,
classifier invocations, missed gold.

### Field evidence (free, from §5's logging)

Every real session in anomaly mode produces: gateScore on each fired event,
the shadow count of would-have-been RMS fires, and Steven's labels. That is a
running v42-vs-v26 comparison with zero extra field effort.

### The honesty gate — abandon criteria

- **Bench:** if no threshold setting achieves ≥ 95 % TP on synthetic gold
  injections while cutting fires/min by ≥ 3× vs the RMS trigger on hot-ground
  sessions, the gate doesn't pay for its complexity. Don't ship it ON; park it
  or abandon.
- **Field (stop-ship for gate-by-default):** any Steven-labelled **gold** event
  whose recorded gateScore is below the Balanced threshold — i.e. the gate
  would have suppressed real gold — is a critical failure. Investigate the
  baseline quality first; if the math is working as designed and still
  suppressing gold, loosen the default or abandon.
- Standing caveat (consistent with v24/v26/v32 memory): **nothing audio is
  "verified" until it survives Steven's real GPX 6000 hardware test.** Synthetic
  results gate the build; field results gate the default.

---

## 8. UI additions

- **Settings → Audio → new "🌏 Ground baseline" card** (below Auto-flag):
  - Baseline list: name · distance from here · age · detector combo · quality
    badge. Active baseline highlighted. Per-item: use now / rename / delete.
  - Primary button: **"Calibrate here (20 s)"** → full-screen guided capture:
    countdown, live steadiness feedback, result screen (quality verdict,
    auto-name, save/retry).
  - Sensitivity slider (Loose → Tight, §4) + live "~N fires/min" hint.
- **Trigger mode:** extend the existing `afmode` radio group with
  "🌏 Ground anomaly *(needs baseline)*" — disabled with an inline hint until a
  baseline exists for the current combo.
- **Live score chip** (optional, default ON while anomaly mode is armed): a
  small bar near the REC pill — current D² against threshold, green→amber→red,
  following the existing live-RMS-meter pattern (settings CSS ~line 426). Tap
  to hide. This is the advisory layer that builds trust in the hard gate.
- **First-run explainer:** one-time sheet on first selecting anomaly mode
  (reuse the v36 NPI explainer pattern): what it does, how to calibrate, what
  the slider means — three short paragraphs, no statistics vocabulary.
- **Discovery nudge:** if a session in amp mode racks up > 30 auto-flags in an
  hour, one-time toast: "Auto-flag firing a lot? Try the new Ground baseline
  gate."

---

## 9. Failure modes and edge cases

| Failure | Detection | Response |
|---------|-----------|----------|
| Noisy calibration (target/junk beep, wind, talking during capture) | Post-fit self-consistency: after trim+refit, if > ~2 % of calibration windows still exceed χ²₈ P99.9, or d2.max/d2.p50 is extreme | Warn "ground wasn't steady — retry on quieter ground"; offer keep-anyway (badged) or retry. The 5 % trim (§2) already absorbs a single stray beep |
| User walks > 200 m from baseline | GPS check on each auto-selection tick | Banner + auto-fallback to amplitude mode; never silent |
| Ground drifts (moisture, different soil in same patch) | Rolling live median D² > baseline P90 for 2–3 min | Recalibrate prompt (§4 — detect, don't adapt) |
| Numerical overflow/underflow | NaN/Inf guard per window; robust standardization; log+epsilon transforms; clamps pre-transform | Skip bad windows and count them; > 10 % skipped in a minute → disarm gate, fall back amp, toast |
| Near-singular covariance | Cholesky failure / condition estimate at fit time | Shrinkage ladder → diagonal fallback → unusable badge (§3). Never a crash |
| v26 classifier disabled or untrained | — | **Gate works standalone** as a smarter trigger — this is the *common* path early on (no GPX 6000 model trained yet). Events save with gateScore, no ml verdict. Explicitly supported |
| Meyda fails to load (offline before SW cached it) | load promise rejects | Disarm anomaly mode, fall back amp, toast. Build agent: verify meyda URL is SW-cached for the main-thread path, not just the worker fetch |
| AudioContext at 48 kHz (device refused 16 k) | `ctx.sampleRate` vs baseline `sampleRate` | Time-based window aggregation handles cadence; MFCC filterbanks differ by rate → if active baseline's rate ≠ current rate, warn + require recalibration (rare) |
| Gate code throws mid-session | try/catch around all gate work in `onaudioprocess` | Capture continues; gate disarms after repeated faults; log |
| Debounce/daily-cap interactions | — | Both stay downstream, unchanged; gate *reduces* cap pressure |

---

## 10. Recommended shipping approach

**Ship v42 with the gate OFF by default** (everyone keeps their current
`afmode`). Reasons:

1. The gate can't function without a calibration — ON-by-default would mean
   "fallback to amp with a nag banner" for every user on first run. Confusing,
   worse than opt-in.
2. It is unproven on real GPX 6000 audio until Steven's hardware test — the
   same caveat trail as v24/v26/v32. Opt-in + shadow logging *is* the A/B:
   Steven runs amp one session, anomaly the next; the logged
   gateScores + shadow counters give the comparison numbers.
3. Discovery is handled by the mode radio + the > 30-flags/hour nudge (§8).

**Migrations:** IndexedDB v4 → v5 (one additive store — the existing
`contains()`-guarded upgrade pattern is already safe). New `acfg` keys with
defaults (existing localStorage idiom, ~line 4327). Events gain nullable
additive fields `gateScore`, `gateBaselineId`, `gateWhy` — old events
unaffected. Nothing else migrates. SW cache version bump to deploy.

### Do-NOT-break list for the build agent

- **Amp + ml auto-flag paths byte-identical when the gate is off** — this is
  the toggle-off constraint and the regression baseline.
- `saveEvent` ring-buffer snapshot + WAV encode + GPS interpolation — untouched.
- The v32 per-combo model registry and the legacy `MODEL_ID` storage-id
  back-compat (`modelStorageId`, ~line 5104).
- `onaudioprocess` must never throw — all gate work wrapped; a gate fault
  degrades to amp mode, never kills capture.
- The additive `onupgradeneeded` pattern — never drop/recreate stores.
- Manual REC hits bypass the gate unconditionally.
- Meyda/tf.js stay lazy-loaded — no new cost for users who never arm the gate.
- ScriptProcessor stays — do **not** migrate to AudioWorklet in this build
  (known tech debt, separate task, out of scope).

---

## Summary for Steven

**Mahalanobis distance** (Cholesky-based, shrinkage-regularized, diagonal
fallback) over an **8-feature 256 ms window**, against a **full-covariance
baseline** (~10 KB/spot incl. raw calibration windows — ~1 MB for 100 spots,
nothing vs the 60 MB budget), stored per detector+coil in a new IndexedDB
store, auto-selected within 200 m. Default threshold: **Balanced = 1.5 × the
calibration's own P99 distance** — static per baseline, with drift *detection*
prompting recalibration rather than silent adaptation. The gate replaces the
crude RMS trigger (that's what actually fires constantly on hot ground — the
classifier only runs on saved clips), everything downstream is untouched, and
OFF = pure v26. Real risks: unproven on real GPX 6000 audio until your
hardware test; a dirty calibration could suppress faint gold — mitigated by
calibration quality checks, ungated manual hits, per-event score logging with
a shadow RMS counter (every field session becomes an A/B), and hard abandon
criteria (≥ 95 % TP at ≥ 3× fewer fires on the bench, zero suppressed
real-gold events in the field).

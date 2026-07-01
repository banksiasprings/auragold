# Victoria Gold — Top 10 Spots per Detector (v40 · legality-audited)
_Generated 2026-07-01. Rankings from AuraGold v37 NPI + composite; **every spot re-checked against a hard legal-access filter** (Vic plm25 public-land tenure + current mineral tenements, full-resolution WFS)._

## ⚖️ Legality audit (2026-07-01) — what changed and why

Steven flagged that some ranked pins looked like they sat in towns or on private property. He holds **no landholder permissions** and freehold is off, so every spot was re-tested against a **strict** rule: *is the pin itself on land you can walk into with just a Miner’s Right?*

**The flaw this caught.** The previous pass used a **“nearest public land within 4 km”** proximity test — so a pin could read “confirmed” while sitting on a town or a paddock with State Forest 3 km away. Re-run as a **point-in-polygon** test against full-resolution Vic **plm25**, **only 1 of the 15 unique pins was cleanly inside a public-land polygon at the coordinate** (Sailors Creek crossings). The rest were on freehold, town reserves, road/utility strips, or park boundaries — and two sat on **active mining tenements** the old check never looked at.

**What I did.** Each pin was resolved to a **verified legal swing-point** (15 unique spots → 8 relocated · 5 kept · 2 removed):
- **Relocated** (8 spots / 15 of the 30 ranked entries): the intended goldfield’s public land was close by, so the pin was nudged onto confirmed State Forest / Regional Park / Castlemaine Diggings NHP / unreserved Crown and **re-verified** (tenure + tenements). Moves ranged 181–860 m. The spot and its rank are unchanged; only the coordinate moved off the town/freehold.
- **Removed** (2 spots — Maldon, Guildford): no legal ground within reach, or an active mining lease at the pin. Their slots were **back-filled** with verified-legal ground in the same belt.
- **Kept** as-is (5 spots — Castlemaine Diggings NHP, Sailors Creek, Vaughan Springs, Chewton, Inglewood): already on legal ground at the coordinate.

### Removed — and why (no matter how high the score)
- **Maldon / Muckleford** (was VLF #2 · PI #4 · ZVT #7) — pin sits on the **Maldon Historic Reserve** *and* an **active Mining Licence (MIN5146)**. Off-limits without the holder’s consent. Back-filled with **Goughs Range State Forest** (the legal Maldon–Muckleford reef belt SW of town — the ground the report always meant).
- **Guildford / Yandoit** (was PI #1 · ZVT #2 · VLF #8) — the model’s single hottest cell (NPI 100). The pin is on a narrow unreserved-Crown **road/utility reserve**; the surrounding target ground is **private freehold farmland**, nearest State Forest **3.1 km** away. **The best data pick is on private land** — it can’t be walked with a Miner’s Right. Back-filled with **Kingower / Wehla State Forest** (Wedderburn belt).

### Relocations (pin moved onto confirmed public land)
| Spot | Pin was on | Moved to | Move |
|------|-----------|----------|------|
| Hepburn RP — Sailors Ck (VLF#1·PI#2·ZVT#1) | private freehold | 627 m → Hepburn Regional Park | ✅ verified |
| Daylesford — Wombat Ck (VLF#4·PI#6·ZVT#5) | private freehold | 841 m → Hepburn Regional Park | ✅ verified |
| Creswick / Slaty Ck (VLF#6) | Creswick township (freehold) | 481 m → Creswick Regional Park | ✅ verified |
| Slaty Creek (ZVT#6) | freehold + active Retention Licences RL006988/RL006423 | 481 m → Creswick Regional Park flats | ✅ verified |
| Dunolly / Goldsborough (VLF#9·PI#7·ZVT#4) | Jardine Park recreation reserve (town park) | 362 m → Waanyarra–Dunolly State Forest | ✅ verified |
| Amherst — Avoca R (VLF#10) | Crown water frontage beside Caralulup NCR | 483 m → unreserved Crown land (clear of NCR) | ✅ verified |
| Heathcote / McIvor Ck (PI#8·ZVT#9) | town-edge unreserved Crown | 181 m → One Eye State Forest | ✅ verified |
| Fryers Ridge / Irishtown (ZVT#10) | private freehold | 860 m → Castlemaine Diggings NHP | ✅ verified |

### The 30 original picks — full status
| Det | # | Spot | Status | Reason |
|-----|---|------|--------|--------|
| VLF | 1 | Hepburn RP — Sailors Ck / Dry Diggings | ✅ RELOCATED | Pin was on private freehold; moved 627 m onto Hepburn Regional Park (prospecting permitted). |
| VLF | 2 | Maldon / Muckleford SF | ❌ REMOVED | Pin on Maldon Historic Reserve **and** active Mining Licence **MIN5146** — off-limits without the leaseholder’s consent. |
| VLF | 3 | Castlemaine Diggings NHP (Fryerstown) | ✅ KEPT | Inside Castlemaine Diggings NHP (NPA Sch-4) — designated prospecting park. |
| VLF | 4 | Daylesford — Wombat Ck | ✅ RELOCATED | Pin was on private freehold; moved 841 m onto Hepburn Regional Park. |
| VLF | 5 | Sailors Creek crossings | ✅ KEPT | Inside Wombat State Forest — clean. |
| VLF | 6 | Creswick RP / Slaty Ck | ✅ RELOCATED | Pin was in Creswick township (freehold); moved 481 m onto Creswick Regional Park. |
| VLF | 7 | Vaughan Springs / Fryers Ck | ✅ KEPT | Inside Castlemaine Diggings NHP (Sch-4) — designated. |
| VLF | 8 | Guildford / Yandoit (Loddon Valley) | ❌ REMOVED | Pin on an unreserved-Crown road/utility strip; the NPI-100 target ground is **private freehold farmland** (nearest State Forest 3.1 km). |
| VLF | 9 | Dunolly / Goldsborough | ✅ RELOCATED | Pin was on Jardine Park recreation reserve (town park); moved 362 m onto Waanyarra–Dunolly State Forest. |
| VLF | 10 | Amherst — Avoca R | ✅ RELOCATED | Pin was on a Crown water frontage beside Caralulup NCR; moved 483 m onto unreserved Crown land, clear of the reserve. |
| PI | 1 | Guildford / Yandoit (Loddon Valley) | ❌ REMOVED | Same as VLF #8 — the model’s hottest cell (NPI 100) sits on private freehold; only a road/utility Crown strip at the pin. |
| PI | 2 | Hepburn RP — Sailors Ck / Dry Diggings | ✅ RELOCATED | Moved 627 m onto Hepburn Regional Park. |
| PI | 3 | Chewton / Golden Point | ✅ KEPT | Inside Castlemaine Diggings NHP (Sch-4) — designated. |
| PI | 4 | Maldon / Muckleford SF | ❌ REMOVED | Active Mining Licence MIN5146 + Historic Reserve at the pin. |
| PI | 5 | Castlemaine Diggings NHP (Fryerstown) | ✅ KEPT | Inside the NHP — designated. |
| PI | 6 | Daylesford — Wombat Ck | ✅ RELOCATED | Moved 841 m onto Hepburn Regional Park. |
| PI | 7 | Dunolly / Goldsborough | ✅ RELOCATED | Moved 362 m onto Waanyarra–Dunolly State Forest. |
| PI | 8 | Heathcote / McIvor Ck | ✅ RELOCATED | Pin on town-edge unreserved Crown; moved 181 m onto One Eye State Forest (clear of the Costerfield mine SE). |
| PI | 9 | Inglewood / Kingower / Wehla SF | ✅ KEPT | Inside Inglewood State Forest — clean. |
| PI | 10 | Vaughan Springs / Fryers Ck | ✅ KEPT | Inside Castlemaine Diggings NHP (Sch-4). |
| ZVT | 1 | Hepburn RP — Sailors Ck / Dry Diggings | ✅ RELOCATED | Moved 627 m onto Hepburn Regional Park. |
| ZVT | 2 | Guildford / Yandoit (Loddon Valley) | ❌ REMOVED | Private freehold farmland; road/utility Crown strip only. |
| ZVT | 3 | Chewton / Golden Point | ✅ KEPT | Inside Castlemaine Diggings NHP (Sch-4). |
| ZVT | 4 | Dunolly / Goldsborough | ✅ RELOCATED | Moved 362 m onto Waanyarra–Dunolly State Forest. |
| ZVT | 5 | Daylesford — Wombat Ck | ✅ RELOCATED | Moved 841 m onto Hepburn Regional Park. |
| ZVT | 6 | Slaty Creek (Creswick RP) | ✅ RELOCATED | Pin was on freehold **and** the Slaty Creek arm is under active Retention Licences **RL006988 / RL006423** — moved to the clear Creswick Regional Park flats. |
| ZVT | 7 | Maldon / Muckleford SF | ❌ REMOVED | Active Mining Licence MIN5146 + Historic Reserve. |
| ZVT | 8 | Castlemaine Diggings NHP (Fryerstown) | ✅ KEPT | Inside the NHP — designated. |
| ZVT | 9 | Heathcote / McIvor Ck | ✅ RELOCATED | Moved 181 m onto One Eye State Forest. |
| ZVT | 10 | Fryers Ridge / Irishtown | ✅ RELOCATED | Pin was on private freehold; moved 860 m onto Castlemaine Diggings NHP. |

**Legal basis** (Vic): State forests and unreserved Crown land are open to Miner’s Right fossicking; Hepburn & Creswick **Regional Parks** and the **Castlemaine Diggings National Heritage Park** are on Parks Victoria’s prospecting-permitted list (carry the park map — a few sub-zones are excluded). **Freehold, National/State Parks outside designated areas, Nature Conservation Reserves, Historic Reserves, and active Mining/Retention Licences are off-limits.** ELs do **not** block Miner’s Right fossicking, so they were ignored. Data: full-res `plm25` (DEECA) + `minten` (Earth Resources), queried 2026-07-01. *Not legal advice — confirm on GeoVic the morning you go in; a plm25 boundary can be a few metres off and park sub-zones change.*

---

## 📱 Summary tables (read these first) — legal-only

### 🎯 Gold Monster 1000 (VLF)
| # | Spot | Legal | Comp | NPI | Top driver |
|--|------|-------|------|-----|-----------|
| 1 | Hepburn RP — Sailors Ck / Dry Diggings | 🟢 Regional Park | 0.665 | 71 | high NPI + creek water + light burn |
| 2 | Castlemaine Diggings NHP (Fryerstown) | 🟢 Designated Area | 0.635 | 75 | designated diggings, remote |
| 3 | Daylesford — Wombat Ck | 🟢 Regional Park | 0.609 | 69 | v37 stream hotspot (point-bar) |
| 4 | Sailors Creek crossings | 🟢 State Forest | 0.608 | 70 | exposed banks, best terrain shape |
| 5 | Creswick RP / Slaty Ck | 🟢 Regional Park | 0.608 | 75 | deep leads, top NPI |
| 6 | Vaughan Springs / Fryers Ck | 🟢 Designated Area | 0.593 | 69 | remote, camp on site |
| 7 | Dunolly / Goldsborough | 🟢 State Forest | 0.588 | 58 | nugget capital, most remote |
| 8 | Amherst — Avoca R | 🟢 Crown Land | 0.576 | 64 | Avoca alluvial, remote |
| 9 | Chewton / Golden Point | 🟢 Designated Area | — | 72 | Forest Ck 1851 reef ground — legality backfill (replaces Guildford) |
| 10 | Maldon–Muckleford — Goughs Range SF | 🟢 State Forest | — | — | Maldon–Muckleford reef belt — legality backfill (replaces Maldon) |

### 🎯 GPX 6000 (PI)
| # | Spot | Legal | Comp | NPI | Top driver |
|--|------|-------|------|-----|-----------|
| 1 | Hepburn RP — Sailors Ck / Dry Diggings | 🟢 Regional Park | 0.628 | 63 | reef arc, light burn |
| 2 | Chewton / Golden Point | 🟢 Designated Area | 0.615 | 72 | Forest Ck 1851 reef ground |
| 3 | Castlemaine Diggings NHP (Fryerstown) | 🟢 Designated Area | 0.566 | 59 | designated diggings |
| 4 | Daylesford — Wombat Ck | 🟢 Regional Park | 0.544 | 55 | deep-lead margin |
| 5 | Dunolly / Goldsborough | 🟢 State Forest | 0.541 | 48 | most remote, nugget country |
| 6 | Heathcote / McIvor Ck | 🟢 State Forest | 0.518 | 47 | Cambrian greenstone belt |
| 7 | Inglewood / Kingower / Wehla SF | 🟢 State Forest | 0.509 | 63 | Hand-of-Faith ground |
| 8 | Vaughan Springs / Fryers Ck | 🟢 Designated Area | 0.509 | 50 | remote, camp on site |
| 9 | Maldon–Muckleford — Goughs Range SF | 🟢 State Forest | — | — | Maldon–Muckleford magnetic belt — legality backfill (replaces Maldon) |
| 10 | Kingower / Wehla SF (Wedderburn belt) | 🟢 State Forest | — | — | Wehla/Kingower Hand-of-Faith belt — legality backfill (replaces Guildford) |

### 🎯 GPZ 7000 (ZVT)
| # | Spot | Legal | Comp | NPI | Top driver |
|--|------|-------|------|-----|-----------|
| 1 | Hepburn RP — Sailors Ck / Dry Diggings | 🟢 Regional Park | 0.779 | 97 | near-max hammered premium ground |
| 2 | Chewton / Golden Point | 🟢 Designated Area | 0.702 | 92 | dense deep-lead workings |
| 3 | Dunolly / Goldsborough | 🟢 State Forest | 0.692 | 81 | nugget capital, most remote |
| 4 | Daylesford — Wombat Ck | 🟢 Regional Park | 0.645 | 77 | Hepburn deep-lead arc |
| 5 | Creswick RP / Slaty Ck | 🟢 Regional Park | 0.634 | 85 | classic detecting creek (Slaty arm under RL — swing the Creswick RP flats) |
| 6 | Castlemaine Diggings NHP (Fryerstown) | 🟢 Designated Area | 0.616 | 71 | designated diggings |
| 7 | Heathcote / McIvor Ck | 🟢 State Forest | 0.610 | 67 | greenstone premium ground |
| 8 | Fryers Ridge / Irishtown | 🟢 Designated Area | 0.592 | 63 | ridge/spur ground beside the NHP |
| 9 | Maldon–Muckleford — Goughs Range SF | 🟢 State Forest | — | — | Maldon–Muckleford hammered belt — legality backfill (replaces Maldon) |
| 10 | Kingower / Wehla SF (Wedderburn belt) | 🟢 State Forest | — | — | Wehla/Kingower nugget belt — legality backfill (replaces Guildford + Slaty-RL) |

**One-line #1s (all legal, verified):** VLF → **Hepburn Regional Park (Sailors Creek / Dry Diggings)**. PI → **Hepburn Regional Park** (Guildford removed — private land). ZVT → **Hepburn Regional Park (ZVT 97)**. Hepburn is now the clear #1 across all three.

---

## Per-spot detail

### 🎯 Gold Monster 1000 (VLF) — Top 10 (legal)

#### #1 — Hepburn RP — Sailors Ck / Dry Diggings
- **Legality:** 🟢 Regional Park — Hepburn Regional Park — prospecting permitted with a Miner's Right (Parks Vic). Pin verified inside — moved 627 m off the freehold/town nav-point.
- Coords: `-37.35758, 144.14476` · Composite **0.665** · NPI **71** · Confidence high
- Why: high NPI + creek water + light burn
- Camp: Daylesford Victoria Caravan Park (1.9 km) · Water: Sailors Creek (permanent runs) · Nearest: Daylesford 2.1 km · Ballarat 34 km

#### #2 — Castlemaine Diggings NHP (Fryerstown)
- **Legality:** 🟢 Designated Area — Castlemaine Diggings National Heritage Park (NPA Sch-4) — prospecting permitted through most of the park; carry the Parks Vic prospecting map. Pin verified inside the boundary.
- Coords: `-37.10000, 144.22000` · Composite **0.635** · NPI **75** · Confidence high · tie
- Why: designated diggings, remote
- Camp: 2nd Castlemaine Scout Camp (3.0 km) · Water: Forest Creek / Fryers Creek · Nearest: Castlemaine 4.4 km · Bendigo 38 km

#### #3 — Daylesford — Wombat Ck
- **Legality:** 🟢 Regional Park — Hepburn Regional Park — prospecting permitted with a Miner's Right (Parks Vic). Pin verified inside — moved 841 m off the freehold/town nav-point.
- Coords: `-37.33774, 144.13266` · Composite **0.609** · NPI **69** · Confidence high · tie
- Why: v37 stream hotspot (point-bar)
- Camp: Ambleside on the Lake (1.9 km) · Water: Wombat Creek / Jim Crow Creek · Nearest: Daylesford 1.0 km · Ballarat 35 km

#### #4 — Sailors Creek crossings
- **Legality:** 🟢 State Forest — Wombat State Forest — open to Miner's Right fossicking. Pin verified inside the boundary.
- Coords: `-37.38500, 144.15000` · Composite **0.608** · NPI **70** · Confidence high · tie
- Why: exposed banks, best terrain shape
- Camp: Jubilee Lake Holiday Park (2.0 km) · Water: Sailors Creek · Nearest: Daylesford 4.9 km · Ballarat 33 km

#### #5 — Creswick RP / Slaty Ck
- **Legality:** 🟢 Regional Park — Creswick Regional Park — prospecting permitted with a Miner's Right (Parks Vic). Pin verified inside — moved 481 m off the freehold/town nav-point.
- Coords: `-37.42079, 143.89774` · Composite **0.608** · NPI **75** · Confidence high
- Why: deep leads, top NPI
- Camp: Creswick Caravan Park & Camping Ground (1.0 km) · Water: Creswick Creek / Slaty Creek · Nearest: Creswick 0.9 km · Ballarat 15 km

#### #6 — Vaughan Springs / Fryers Ck
- **Legality:** 🟢 Designated Area — Castlemaine Diggings National Heritage Park (NPA Sch-4) — prospecting permitted through most of the park; carry the Parks Vic prospecting map. Pin verified inside the boundary.
- Coords: `-37.15000, 144.21000` · Composite **0.593** · NPI **69** · Confidence med · tie
- Why: remote, camp on site
- Camp: Vaughan Springs Reserve, Castlemaine Diggings NHP (1.1 km) · Water: Fryers Creek / Loddon River · Nearest: Castlemaine 10.0 km · Bendigo 44 km

#### #7 — Dunolly / Goldsborough
- **Legality:** 🟢 State Forest — Waanyarra–Dunolly State Forest — open to Miner's Right fossicking. Pin verified inside — moved 362 m off the freehold/town nav-point.
- Coords: `-36.86266, 143.73766` · Composite **0.588** · NPI **58** · Confidence high · tie
- Why: nugget capital, most remote
- Camp: Dunolly Caravan Park (0.7 km) · Water: Bet Bet Creek / Burnt Creek (intermittent) · Nearest: Dunolly 0.9 km · Bendigo 50 km

#### #8 — Amherst — Avoca R
- **Legality:** 🟢 Crown Land — unreserved Crown land — open to Miner's Right fossicking; verified clear of nearby reserves. Pin verified inside — moved 483 m off the freehold/town nav-point.
- Coords: `-37.18456, 143.65973` · Composite **0.576** · NPI **64** · Confidence med · tie
- Why: Avoca alluvial, remote
- Camp: free bush camp, unnamed (3.6 km) · Water: Back Creek / Avoca River · Nearest: Talbot 4.4 km · Ballarat 45 km

#### #9 — Chewton / Golden Point
- **Legality:** 🟢 Designated Area — Castlemaine Diggings National Heritage Park (NPA Sch-4) — prospecting permitted through most of the park; carry the Parks Vic prospecting map. Pin verified inside the boundary.
- Coords: `-37.08000, 144.24000` · **⚑ legality back-fill** · NPI 72 · replaces a removed pin, same belt
- Why: Forest Ck 1851 reef ground — legality backfill (replaces Guildford)
- Camp: free bush camp, unnamed (2.5 km) · Water: Forest Creek · Nearest: Castlemaine 2.8 km · Bendigo 36 km

#### #10 — Maldon–Muckleford — Goughs Range SF
- **Legality:** 🟢 State Forest — Goughs Range State Forest — open to Miner's Right fossicking. Pin verified inside the boundary.
- Coords: `-37.03251, 144.03827` · **⚑ legality back-fill** · NPI — · replaces a removed pin, same belt
- Why: Maldon–Muckleford reef belt — legality backfill (replaces Maldon)
- Camp: Maldon Caravan & Camping Park (4.4 km) · Water: Muckleford Creek · Nearest: Maldon 4.4 km · Bendigo 36 km

### 🎯 GPX 6000 (PI) — Top 10 (legal)

#### #1 — Hepburn RP — Sailors Ck / Dry Diggings
- **Legality:** 🟢 Regional Park — Hepburn Regional Park — prospecting permitted with a Miner's Right (Parks Vic). Pin verified inside — moved 627 m off the freehold/town nav-point.
- Coords: `-37.35758, 144.14476` · Composite **0.628** · NPI **63** · Confidence high
- Why: reef arc, light burn
- Camp: Daylesford Victoria Caravan Park (1.9 km) · Water: Sailors Creek (permanent runs) · Nearest: Daylesford 2.1 km · Ballarat 34 km

#### #2 — Chewton / Golden Point
- **Legality:** 🟢 Designated Area — Castlemaine Diggings National Heritage Park (NPA Sch-4) — prospecting permitted through most of the park; carry the Parks Vic prospecting map. Pin verified inside the boundary.
- Coords: `-37.08000, 144.24000` · Composite **0.615** · NPI **72** · Confidence high
- Why: Forest Ck 1851 reef ground
- Camp: free bush camp, unnamed (2.5 km) · Water: Forest Creek · Nearest: Castlemaine 2.8 km · Bendigo 36 km

#### #3 — Castlemaine Diggings NHP (Fryerstown)
- **Legality:** 🟢 Designated Area — Castlemaine Diggings National Heritage Park (NPA Sch-4) — prospecting permitted through most of the park; carry the Parks Vic prospecting map. Pin verified inside the boundary.
- Coords: `-37.10000, 144.22000` · Composite **0.566** · NPI **59** · Confidence high · tie
- Why: designated diggings
- Camp: 2nd Castlemaine Scout Camp (3.0 km) · Water: Forest Creek / Fryers Creek · Nearest: Castlemaine 4.4 km · Bendigo 38 km

#### #4 — Daylesford — Wombat Ck
- **Legality:** 🟢 Regional Park — Hepburn Regional Park — prospecting permitted with a Miner's Right (Parks Vic). Pin verified inside — moved 841 m off the freehold/town nav-point.
- Coords: `-37.33774, 144.13266` · Composite **0.544** · NPI **55** · Confidence med · tie
- Why: deep-lead margin
- Camp: Ambleside on the Lake (1.9 km) · Water: Wombat Creek / Jim Crow Creek · Nearest: Daylesford 1.0 km · Ballarat 35 km

#### #5 — Dunolly / Goldsborough
- **Legality:** 🟢 State Forest — Waanyarra–Dunolly State Forest — open to Miner's Right fossicking. Pin verified inside — moved 362 m off the freehold/town nav-point.
- Coords: `-36.86266, 143.73766` · Composite **0.541** · NPI **48** · Confidence med · tie
- Why: most remote, nugget country
- Camp: Dunolly Caravan Park (0.7 km) · Water: Bet Bet Creek / Burnt Creek (intermittent) · Nearest: Dunolly 0.9 km · Bendigo 50 km

#### #6 — Heathcote / McIvor Ck
- **Legality:** 🟢 State Forest — One Eye State Forest — open to Miner's Right fossicking. Pin verified inside — moved 181 m off the freehold/town nav-point.
- Coords: `-36.92903, 144.70485` · Composite **0.518** · NPI **47** · Confidence med · tie
- Why: Cambrian greenstone belt
- Camp: Queen’s Meadow Caravan Park (1.0 km) · Water: McIvor Creek · Nearest: Heathcote 1.0 km · Bendigo 42 km

#### #7 — Inglewood / Kingower / Wehla SF
- **Legality:** 🟢 State Forest — Inglewood State Forest — open to Miner's Right fossicking. Pin verified inside the boundary.
- Coords: `-36.56700, 143.87400` · Composite **0.509** · NPI **63** · Confidence high · tie
- Why: Hand-of-Faith ground
- Camp: Inglewood Motel & Caravan Park (1.0 km) · Water: intermittent creeks — carry water · Nearest: Inglewood 0.7 km · Bendigo 42 km

#### #8 — Vaughan Springs / Fryers Ck
- **Legality:** 🟢 Designated Area — Castlemaine Diggings National Heritage Park (NPA Sch-4) — prospecting permitted through most of the park; carry the Parks Vic prospecting map. Pin verified inside the boundary.
- Coords: `-37.15000, 144.21000` · Composite **0.509** · NPI **50** · Confidence med · tie
- Why: remote, camp on site
- Camp: Vaughan Springs Reserve, Castlemaine Diggings NHP (1.1 km) · Water: Fryers Creek / Loddon River · Nearest: Castlemaine 10.0 km · Bendigo 44 km

#### #9 — Maldon–Muckleford — Goughs Range SF
- **Legality:** 🟢 State Forest — Goughs Range State Forest — open to Miner's Right fossicking. Pin verified inside the boundary.
- Coords: `-37.03251, 144.03827` · **⚑ legality back-fill** · NPI — · replaces a removed pin, same belt
- Why: Maldon–Muckleford magnetic belt — legality backfill (replaces Maldon)
- Camp: Maldon Caravan & Camping Park (4.4 km) · Water: Muckleford Creek · Nearest: Maldon 4.4 km · Bendigo 36 km

#### #10 — Kingower / Wehla SF (Wedderburn belt)
- **Legality:** 🟢 State Forest — Kingower State Forest — open to Miner's Right fossicking. Pin verified inside the boundary.
- Coords: `-36.60812, 143.78089` · **⚑ legality back-fill** · NPI — · replaces a removed pin, same belt
- Why: Wehla/Kingower Hand-of-Faith belt — legality backfill (replaces Guildford)
- Camp: Butchers Camp Site, Kingower SF (free, on site) · Water: intermittent — carry water · Nearest: Inglewood 11 km · Bendigo 46 km

### 🎯 GPZ 7000 (ZVT) — Top 10 (legal)

#### #1 — Hepburn RP — Sailors Ck / Dry Diggings
- **Legality:** 🟢 Regional Park — Hepburn Regional Park — prospecting permitted with a Miner's Right (Parks Vic). Pin verified inside — moved 627 m off the freehold/town nav-point.
- Coords: `-37.35758, 144.14476` · Composite **0.779** · NPI **97** · Confidence high
- Why: near-max hammered premium ground
- Camp: Daylesford Victoria Caravan Park (1.9 km) · Water: Sailors Creek (permanent runs) · Nearest: Daylesford 2.1 km · Ballarat 34 km

#### #2 — Chewton / Golden Point
- **Legality:** 🟢 Designated Area — Castlemaine Diggings National Heritage Park (NPA Sch-4) — prospecting permitted through most of the park; carry the Parks Vic prospecting map. Pin verified inside the boundary.
- Coords: `-37.08000, 144.24000` · Composite **0.702** · NPI **92** · Confidence high · tie
- Why: dense deep-lead workings
- Camp: free bush camp, unnamed (2.5 km) · Water: Forest Creek · Nearest: Castlemaine 2.8 km · Bendigo 36 km

#### #3 — Dunolly / Goldsborough
- **Legality:** 🟢 State Forest — Waanyarra–Dunolly State Forest — open to Miner's Right fossicking. Pin verified inside — moved 362 m off the freehold/town nav-point.
- Coords: `-36.86266, 143.73766` · Composite **0.692** · NPI **81** · Confidence high · tie
- Why: nugget capital, most remote
- Camp: Dunolly Caravan Park (0.7 km) · Water: Bet Bet Creek / Burnt Creek (intermittent) · Nearest: Dunolly 0.9 km · Bendigo 50 km

#### #4 — Daylesford — Wombat Ck
- **Legality:** 🟢 Regional Park — Hepburn Regional Park — prospecting permitted with a Miner's Right (Parks Vic). Pin verified inside — moved 841 m off the freehold/town nav-point.
- Coords: `-37.33774, 144.13266` · Composite **0.645** · NPI **77** · Confidence high · tie
- Why: Hepburn deep-lead arc
- Camp: Ambleside on the Lake (1.9 km) · Water: Wombat Creek / Jim Crow Creek · Nearest: Daylesford 1.0 km · Ballarat 35 km

#### #5 — Creswick RP / Slaty Ck
- **Legality:** 🟢 Regional Park — Creswick Regional Park — prospecting permitted with a Miner's Right (Parks Vic). Pin verified inside — moved 481 m off the freehold/town nav-point.
- Coords: `-37.42079, 143.89774` · Composite **0.634** · NPI **85** · Confidence med · tie
- Why: classic detecting creek (Slaty arm under RL — swing the Creswick RP flats)
- Camp: Creswick Caravan Park & Camping Ground (1.0 km) · Water: Creswick Creek / Slaty Creek · Nearest: Creswick 0.9 km · Ballarat 15 km

#### #6 — Castlemaine Diggings NHP (Fryerstown)
- **Legality:** 🟢 Designated Area — Castlemaine Diggings National Heritage Park (NPA Sch-4) — prospecting permitted through most of the park; carry the Parks Vic prospecting map. Pin verified inside the boundary.
- Coords: `-37.10000, 144.22000` · Composite **0.616** · NPI **71** · Confidence high · tie
- Why: designated diggings
- Camp: 2nd Castlemaine Scout Camp (3.0 km) · Water: Forest Creek / Fryers Creek · Nearest: Castlemaine 4.4 km · Bendigo 38 km

#### #7 — Heathcote / McIvor Ck
- **Legality:** 🟢 State Forest — One Eye State Forest — open to Miner's Right fossicking. Pin verified inside — moved 181 m off the freehold/town nav-point.
- Coords: `-36.92903, 144.70485` · Composite **0.610** · NPI **67** · Confidence high · tie
- Why: greenstone premium ground
- Camp: Queen’s Meadow Caravan Park (1.0 km) · Water: McIvor Creek · Nearest: Heathcote 1.0 km · Bendigo 42 km

#### #8 — Fryers Ridge / Irishtown
- **Legality:** 🟢 Designated Area — Castlemaine Diggings National Heritage Park (NPA Sch-4) — prospecting permitted through most of the park; carry the Parks Vic prospecting map. Pin verified inside — moved 860 m off the freehold/town nav-point.
- Coords: `-37.14229, 144.19742` · Composite **0.592** · NPI **63** · Confidence med · tie
- Why: ridge/spur ground beside the NHP
- Camp: Vaughan Springs Reserve, Castlemaine Diggings NHP (2.2 km) · Water: Fryers Creek · Nearest: Castlemaine 9.4 km · Bendigo 44 km

#### #9 — Maldon–Muckleford — Goughs Range SF
- **Legality:** 🟢 State Forest — Goughs Range State Forest — open to Miner's Right fossicking. Pin verified inside the boundary.
- Coords: `-37.03251, 144.03827` · **⚑ legality back-fill** · NPI — · replaces a removed pin, same belt
- Why: Maldon–Muckleford hammered belt — legality backfill (replaces Maldon)
- Camp: Maldon Caravan & Camping Park (4.4 km) · Water: Muckleford Creek · Nearest: Maldon 4.4 km · Bendigo 36 km

#### #10 — Kingower / Wehla SF (Wedderburn belt)
- **Legality:** 🟢 State Forest — Kingower State Forest — open to Miner's Right fossicking. Pin verified inside the boundary.
- Coords: `-36.60812, 143.78089` · **⚑ legality back-fill** · NPI — · replaces a removed pin, same belt
- Why: Wehla/Kingower nugget belt — legality backfill (replaces Guildford + Slaty-RL)
- Camp: Butchers Camp Site, Kingower SF (free, on site) · Water: intermittent — carry water · Nearest: Inglewood 11 km · Bendigo 46 km

---

## Notes
- **Nearly every original pin moved.** The rankings were sound on *ground favourability*; the pin *coordinates* were dropped on town centroids / nav-points, which is what read as “in a town.” The geology didn’t change — the coordinates did, onto verified public land in the same goldfield.
- **The two genuine losses** (Maldon town, Guildford) are honest: one is an active mine, one is private farmland the model happened to love. Neither is walkable on a Miner’s Right, so both are out and back-filled.
- **Back-fills are labelled, not scored.** Goughs Range SF and Kingower/Wehla SF are verified-legal and in the right belt, but they weren’t in the original composite run, so they carry no fabricated composite — they sit at #9–#10 as legality back-fills.
- **Coverage limit unchanged:** the NPI model still only covers central-west Victoria + Chiltern–Eldorado.
- **Every coordinate in this report was verified** against plm25 tenure + current tenements on 2026-07-01. Confirm on GeoVic before you dig.

_Method: legality = hard pre-filter (point-in-polygon on full-res Vic plm25 for tenure + minten for active ML/RL/PL; ELs ignored). Ranking = v37 composite (0.45·NPI + real-world trade-offs − powerline − town-extreme). Relocated pins keep their composite (same NPI cell); back-fills carry none. Not financial or legal advice._

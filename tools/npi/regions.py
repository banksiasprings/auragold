#!/usr/bin/env python3
"""Shared region definitions for the NPI build (single source of truth).

Two coverage regions around Steven's 12 Victorian Goldfields trip spots. The
build grid (build_npi.REGIONS) is the tight bbox; the raster fetchers pad a
touch so resampling near the edges has data.
"""

# (name, west, south, east, north) — TIGHT build bbox (must match build_npi.REGIONS).
# Western extends south to -37.95 so Melbourne CBD + the Werribee/Newer-Volcanics basalt
# plains fall INSIDE the grid — they are the negative controls (must score low). Those
# cells are sub-floor (prior~0) so they ship as transparent/unwritten tiles, ~free.
BUILD = [
    ("Western goldfields", 142.95, -37.95, 145.15, -36.05),
    ("Chiltern-Eldorado",  146.30, -36.42, 146.72, -36.08),
]

# Padded bbox for the raster/vector fetchers (slug, w, s, e, n).
FETCH = [
    ("western",           142.90, -38.00, 145.20, -36.00),
    ("chiltern-eldorado", 146.25, -36.47, 146.77, -36.03),
]



def slug(build_name):
    """'Western goldfields' -> 'western' (the fetch-cache slug)."""
    return build_name.split()[0].lower()

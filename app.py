# app.py — Aural Alchemy | Endless Ambient MIDI Progressions
# Streamlit app (standalone) that:
# - Generates diatonic, loop-safe ambient chord progressions (NO out-of-scale, NO low-sim transitions)
# - Exports a ZIP containing: Progressions (4/8/16-bar folders) + Individual Chords library
# - Optional Re-Voicing (inversions/voicing engine)
# - Premium UI styling (Cinzel font everywhere, cyan slider, gold shimmer button, soft glows)
# - NEW: slow rotating sacred geometry mandala overlay (two layers)

import os
import re
import math
import random
import shutil
import tempfile
import base64
from zipfile import ZipFile
from collections import Counter
from typing import List, Optional

import streamlit as st
import pandas as pd
import numpy as np
import pretty_midi


# =========================================================
# APP CONFIG
# =========================================================
st.set_page_config(
    page_title="Aural Alchemy • MIDI Progressions",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="collapsed",
)

APP_TITLE = "AURAL ALCHEMY GENERATOR"
APP_SUBTITLE = "Endless Ambient MIDI Progressions Ready To Drop Into Any DAW"
DOWNLOAD_NAME = "MIDI_Progressions_Aural_Alchemy.zip"


# =========================================================
# PREMIUM CSS (Cinzel everywhere + cyan slider + shimmer + glows)
# =========================================================
st.markdown(
    r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;500;600;700&display=swap');

/* FORCE STREAMLIT THEME PRIMARY COLOR (affects slider fill + toggle ON) */
:root {
  --primary-color: #00E5FF !important;
  --primaryColor: #00E5FF !important;
  --primary-color-light: rgba(0,229,255,0.35) !important;
}

/* Streamlit containers sometimes hold the vars instead of :root */
[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
.stApp {
  --primary-color: #00E5FF !important;
  --primaryColor: #00E5FF !important;
}

html, body, [class*="css"], .stApp, .block-container,
h1, h2, h3, h4, h5, h6,
p, span, div, label,
button, .stButton>button,
[data-testid="stMetricLabel"],
[data-testid="stMetricValue"],
[data-testid="stMarkdownContainer"],
[data-testid="stText"] {
  font-family: "Cinzel", serif !important;
  letter-spacing: 0.55px !important;
}

/* ---- Page background (gradient base) ---- */
.stApp {
  background:
    radial-gradient(1200px 700px at 20% 15%, rgba(0,229,255,0.10), rgba(0,0,0,0) 60%),
    radial-gradient(1200px 700px at 85% 20%, rgba(255,215,0,0.08), rgba(0,0,0,0) 60%),
    radial-gradient(900px 600px at 50% 85%, rgba(160,120,255,0.06), rgba(0,0,0,0) 65%),
    linear-gradient(180deg, #070A10 0%, #07080E 35%, #05060A 100%);
}

/* =========================================================
   NEW: SACRED GEOMETRY OVERLAY (two layers + slow rotation)
   - Keep this ONLY (removed old .aa-geom / aaSlowSpin)
========================================================= */
.aa-geom-wrap{
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  opacity: 0.90; /* overall container strength */
}


.aa-geom-2{
  position: absolute;
  inset: -18%;
  background-repeat: no-repeat;
  background-position: center;
  background-size: min(1200px, 90vw) min(1200px, 90vw);
  will-change: transform, opacity;

  transform: translateZ(0);
  backface-visibility: hidden;
  contain: paint;


}


/* Layer 1: crisp lines, slow spin */


/* Layer 2: softer glow, reverse spin + subtle breathing */
.aa-geom-2{
  opacity: 0.18;
  filter: blur(0.9px) drop-shadow(0 0 36px rgba(255,215,0,0.10));
  animation: aaSpin2 200s linear infinite, aaBreathe 8.5s ease-in-out infinite;
}

@keyframes aaSpin1{
  0%   { transform: rotate(0deg) scale(1.02); }
  100% { transform: rotate(360deg) scale(1.02); }
}

@keyframes aaSpin2{
  0%   { transform: rotate(0deg) scale(1.04); }
  100% { transform: rotate(-360deg) scale(1.04); }
}

@keyframes aaBreathe{
  0%, 100% { opacity: 0.16; }
  50%      { opacity: 0.22; }
}

/* Header */
.aa-hero {
  position: relative;
  z-index: 2;
  margin-top: 10px;
  padding: 22px 22px 10px 22px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
  border: 1px solid rgba(255,255,255,0.10);
  box-shadow: 0 18px 60px rgba(0,0,0,0.45);
  backdrop-filter: blur(8px);
  text-align: center;
  margin-bottom: 26px;
}
.aa-title {
  font-size: clamp(30px, 7vw, 46px);
  font-weight: 700;
  letter-spacing: clamp(1px, 0.6vw, 3.2px);
  line-height: 1.05;
  margin: 0;
  padding: 0;
  white-space: normal;
  word-break: keep-all;

  background: linear-gradient(
    90deg,
    rgba(255,255,255,0.98),
    rgba(0,229,255,0.90),
    rgba(255,215,0,0.92)
  );
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  text-shadow: 0 12px 30px rgba(0,0,0,0.55);
}

}
.aa-subtitle {
  margin-top: 8px;
  font-size: 16px;
  opacity: 0.82;
  letter-spacing: 1.1px !important;
}

/* Panels */
.aa-panel {
  position: relative;
  z-index: 2;
  padding: 18px 18px 12px 18px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
  border: 1px solid rgba(255,255,255,0.10);
  box-shadow: 0 18px 60px rgba(0,0,0,0.42);
  backdrop-filter: blur(8px);
}


/* Cyan slider styling (Streamlit/BaseWeb - strong) */
[data-testid="stSlider"] div[data-baseweb="slider"] div[role="slider"]{
  background: rgba(0, 229, 255, 0.98) !important;
  border: 1px solid rgba(0,229,255,0.40) !important;
  box-shadow:
    0 0 0 6px rgba(0,229,255,0.10),
    0 10px 28px rgba(0,229,255,0.22) !important;
}
[data-testid="stSlider"] div[data-baseweb="slider"] div[role="presentation"] > div{
  background: rgba(0, 229, 255, 0.60) !important;
}
[data-testid="stSlider"] div[data-baseweb="slider"] div[role="presentation"] > div + div{
  background: rgba(255,255,255,0.10) !important;
}
[data-testid="stSlider"] *{
  accent-color: rgba(0,229,255,0.98) !important;
}

/* Toggle glow when active */
div[data-baseweb="toggle"] input:checked + div{
  box-shadow: 0 0 18px rgba(0,229,255,0.55) !important;
}

/* Button: premium + gold shimmer hover */
.stButton>button {
  background: linear-gradient(135deg, rgba(10,25,35,0.92), rgba(18,38,48,0.92), rgba(26,55,68,0.92)) !important;
  color: rgba(255,255,255,0.96) !important;
  border-radius: 14px !important;
  padding: 0.85em 2em !important;
  border: 1px solid rgba(255,255,255,0.16) !important;
  transition: transform .25s ease, box-shadow .25s ease, filter .25s ease !important;
  position: relative !important;
  overflow: hidden !important;
}
.stButton>button:hover {
  transform: translateY(-1px);
  box-shadow: 0 0 38px rgba(255,215,0,0.28), 0 18px 55px rgba(0,0,0,0.45) !important;
  filter: brightness(1.03);
}
.stButton>button::after {
  content: "";
  position: absolute;
  top: 0;
  left: -85%;
  width: 55%;
  height: 100%;
  background: linear-gradient(120deg,
    rgba(255,255,255,0) 0%,
    rgba(255,215,0,0.55) 50%,
    rgba(255,255,255,0) 100%);
  transform: skewX(-25deg);
}
.stButton>button:hover::after {
  animation: shimmer 1.2s ease;
}
@keyframes shimmer { 100% { left: 140%; } }

/* Metric cards glow */
[data-testid="stMetric"] {
  border-radius: 16px !important;
  padding: 14px 14px 10px 14px !important;
  background:
    radial-gradient(650px 220px at 50% 0%, rgba(0,229,255,0.10), rgba(0,0,0,0) 60%),
    radial-gradient(650px 220px at 50% 100%, rgba(255,215,0,0.08), rgba(0,0,0,0) 60%),
    linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02)) !important;
  border: 1px solid rgba(255,255,255,0.10) !important;
  box-shadow: 0 14px 40px rgba(0,0,0,0.38) !important;
}

/* Dataframe polish */
[data-testid="stDataFrame"] {
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.10);
  box-shadow: 0 14px 40px rgba(0,0,0,0.38);
}

/* Reduce top whitespace */
.block-container { padding-top: 1.0rem !important; }

/* Ready badge */
.aa-ready-wrap{
  display:flex;
  justify-content:center;
  margin-top: 14px;
  margin-bottom: 6px;
}
.aa-ready-badge{
  display:inline-flex;
  align-items:center;
  gap:10px;
  padding: 10px 16px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03));
  border: 1px solid rgba(255,255,255,0.14);
  box-shadow: 0 18px 60px rgba(0,0,0,0.45);
  backdrop-filter: blur(10px);
  color: rgba(255,255,255,0.92);
  letter-spacing: 0.9px;
  font-size: 13px;
}
.aa-ready-dot{
  width:10px;
  height:10px;
  border-radius:999px;
  background: rgba(0,229,255,0.95);
  box-shadow: 0 0 18px rgba(0,229,255,0.60);
}

/* Hide empty markdown paragraphs that add tiny artifacts */
div[data-testid="stMarkdownContainer"] > p:empty {
  display: none !important;
}

/* =========================
   NUCLEAR: KILL STREAMLIT RED/ORANGE PRIMARY
========================= */
[data-testid="stSlider"] * {
  --primary-color: #00E5FF !important;
  --primaryColor: #00E5FF !important;
}
[data-testid="stSlider"] div[role="slider"]{
  background-color: #00E5FF !important;
  border-color: rgba(0,229,255,0.55) !important;
  box-shadow: 0 0 0 6px rgba(0,229,255,0.10), 0 10px 28px rgba(0,229,255,0.22) !important;
}
[data-testid="stSlider"] div[data-baseweb="slider"] div[role="presentation"] div{
  background-color: rgba(0,229,255,0.60) !important;
  background: rgba(0,229,255,0.60) !important;
}
[data-testid="stSlider"] div[data-baseweb="slider"] div[role="presentation"] div:last-child{
  background-color: rgba(255,255,255,0.12) !important;
  background: rgba(255,255,255,0.12) !important;
}
[data-baseweb="toggle"] div[aria-checked="true"]{
  background-color: rgba(0,229,255,0.55) !important;
  box-shadow: 0 0 18px rgba(0,229,255,0.45) !important;
}
[data-baseweb="toggle"] div[aria-checked="true"] > div{
  background-color: #00E5FF !important;
}
</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# Geometry SVG overlay (BASE64 DATA URI)  ✅ reliable
# =========================================================
GEOM_SVG = """
<svg width="1200" height="1200" viewBox="0 0 1200 1200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="aaGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#00E5FF" stop-opacity="0.65"/>
      <stop offset="0.55" stop-color="#FFFFFF" stop-opacity="0.18"/>
      <stop offset="1" stop-color="#FFD700" stop-opacity="0.45"/>
    </linearGradient>
  </defs>

  <g fill="none" stroke="url(#aaGrad)" stroke-width="2.2" opacity="0.95">
    <circle cx="600" cy="600" r="420"/>
    <circle cx="600" cy="600" r="340" opacity="0.62"/>
    <circle cx="600" cy="600" r="260" opacity="0.50"/>
    <circle cx="600" cy="600" r="190" opacity="0.44"/>
    <circle cx="600" cy="600" r="120" opacity="0.36"/>

    <polygon 
  points="
    600,180
    988,810
    212,810
  "
  
/>

    

    <circle cx="600" cy="600" r="480" opacity="0.28"/>
    <circle cx="600" cy="600" r="520" opacity="0.22"/>
  </g>

  <g fill="none" stroke="#FFFFFF" stroke-opacity="0.22" stroke-width="1">
    <path d="M600 80 L600 1120" opacity="0.25"/>
    <path d="M80 600 L1120 600" opacity="0.25"/>
    <path d="M220 220 L980 980" opacity="0.18"/>
    <path d="M980 220 L220 980" opacity="0.18"/>
  </g>
</svg>
"""

GEOM_DATA_URI = "data:image/svg+xml;base64," + base64.b64encode(GEOM_SVG.encode("utf-8")).decode("utf-8")

st.markdown(
    f"""
<div class="aa-geom-wrap">
  <div class="aa-geom-1" style="background-image:url('{GEOM_DATA_URI}');"></div>
  <div class="aa-geom-2" style="background-image:url('{GEOM_DATA_URI}');"></div>
</div>
""",
    unsafe_allow_html=True,
)



# =========================================================
# MUSICAL DATA + SAFE CHORD DEFINITIONS (define BEFORE generator)
# =========================================================
NOTE_TO_PC = {
    "C": 0, "B#": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "Fb": 4, "E#": 5, "F": 5,
    "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11, "Cb": 11,
}

KEYS = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

SCALES = {
    "C":  ["C","D","E","F","G","A","B"],
    "Db": ["Db","Eb","F","Gb","Ab","Bb","C"],
    "D":  ["D","E","F#","G","A","B","C#"],
    "Eb": ["Eb","F","G","Ab","Bb","C","D"],
    "E":  ["E","F#","G#","A","B","C#","D#"],
    "F":  ["F","G","A","Bb","C","D","E"],
    "Gb": ["Gb","Ab","Bb","Cb","Db","Eb","F"],
    "G":  ["G","A","B","C","D","E","F#"],
    "Ab": ["Ab","Bb","C","Db","Eb","F","G"],
    "A":  ["A","B","C#","D","E","F#","G#"],
    "Bb": ["Bb","C","D","Eb","F","G","A"],
    "B":  ["B","C#","D#","E","F#","G#","A#"],
}

QUAL_TO_INTERVALS = {
    "maj":        [0,4,7],
    "min":        [0,3,7],

    "maj7":       [0,4,7,11],
    "maj9":       [0,4,7,11,14],
    "add9":       [0,4,7,14],
    "6":          [0,4,7,9],
    "6add9":      [0,4,7,9,14],

    "min7":       [0,3,7,10],
    "min9":       [0,3,7,10,14],
    "min11":      [0,3,7,10,14,17],

    "sus2":       [0,2,7],
    "sus4":       [0,5,7],
    "sus2add9":   [0,2,7,14],
    "sus4add9":   [0,5,7,14],
}
QUALITY_NOTECOUNT = {q: len(v) for q, v in QUAL_TO_INTERVALS.items()}


def _pc(note: str) -> int:
    return NOTE_TO_PC[note]


def _key_pc_set(key: str) -> set:
    return {_pc(n) for n in SCALES[key]}


def _chord_pc_set_real(root_note: str, qual: str) -> set:
    r = _pc(root_note)
    return {(r + iv) % 12 for iv in QUAL_TO_INTERVALS[qual]}


def _is_diatonic_chord(key: str, root_note: str, qual: str) -> bool:
    return _chord_pc_set_real(root_note, qual).issubset(_key_pc_set(key))


def _shared_tone_ok_loop(roots, quals, need=1, loop=True) -> bool:
    pcs = [_chord_pc_set_real(r, q) for r, q in zip(roots, quals)]
    for a, b in zip(pcs, pcs[1:]):
        if len(a & b) < need:
            return False
    if loop and len(pcs) >= 2:
        if len(pcs[-1] & pcs[0]) < need:
            return False
    return True


def _low_sim_count_loop(roots, quals, loop=True) -> int:
    pcs = [_chord_pc_set_real(r, q) for r, q in zip(roots, quals)]
    bad = 0
    for a, b in zip(pcs, pcs[1:]):
        if len(a & b) == 0:
            bad += 1
    if loop and len(pcs) >= 2 and len(pcs[-1] & pcs[0]) == 0:
        bad += 1
    return bad


def _wchoice(rng: random.Random, items_with_w):
    items = [x for x, _ in items_with_w]
    ws = [w for _, w in items_with_w]
    return rng.choices(items, weights=ws, k=1)[0]


# =========================================================
# GENERATOR SETTINGS (pack-balanced; UI only exposes N + revoicing)
# =========================================================
EXPORT_TXT = False
EXPORT_PY_TXT = False

PATTERN_MAX_REPEATS = 1
MAX_PATTERN_DUPLICATE_RATIO = 0.01  # 1%

TOTAL_BARS_DISTRIBUTION = {8: 0.40, 4: 0.35, 16: 0.25}
CHORDCOUNT_DISTRIBUTION = {4: 0.40, 3: 0.35, 2: 0.20, 5: 0.03, 6: 0.02}

MIN_SHARED_TONES = 1
ENFORCE_LOOP_OK = True
MAX_TRIES_PER_PROG = 40000

TRIAD_PROB_BASE = 0.90
BARE_SUS_PROB = 0.13

LIMIT_NOTECOUNT_JUMPS = True
MAX_BIG_JUMPS_PER_PROG = 1

SUS_WEIGHT_MULT = 0.50
SUS_UPGRADE_PROB = 0.50

MAJ_POOL = [("maj9", 10), ("maj7", 9), ("add9", 7), ("6add9", 6), ("6", 4), ("maj", 2)]
MIN_POOL = [("min9", 10), ("min7", 9), ("min11", 4), ("min", 2)]
SUS_POOL = [("sus2add9", 10), ("sus4add9", 10), ("sus2", 2), ("sus4", 2)]


def _scaled_pool(pool, mult):
    return [(q, max(1e-9, w * mult)) for q, w in pool]


SUS_POOL_SCALED = _scaled_pool(SUS_POOL, SUS_WEIGHT_MULT)

DEG_ALLOWED_BASE = {
    0: MAJ_POOL + SUS_POOL_SCALED,
    1: MIN_POOL + MAJ_POOL + SUS_POOL_SCALED,
    2: MIN_POOL + MAJ_POOL + SUS_POOL_SCALED,
    3: MAJ_POOL + MIN_POOL + SUS_POOL_SCALED,
    4: MAJ_POOL + MIN_POOL + SUS_POOL_SCALED,
    5: MIN_POOL + MAJ_POOL + SUS_POOL_SCALED,
    6: MIN_POOL + MAJ_POOL + SUS_POOL_SCALED,
}

SAFE_FALLBACK_ORDER = [
    "maj9","maj7","add9","6add9","6",
    "min9","min7","min11",
    "maj","min",
    "sus2add9","sus4add9","sus2","sus4"
]

TEMPLATES_BY_LEN = {
    2: [((0,3), 10), ((0,5), 7), ((5,3), 5), ((3,0), 4), ((0,4), 3)],
    3: [
        ((0,5,3), 14), ((0,3,4), 12), ((0,3,5), 10), ((0,5,4), 9),
        ((0,2,3), 7), ((0,2,5), 6), ((3,5,0), 5), ((5,3,0), 5),
        ((0,1,3), 3), ((0,6,3), 2),
    ],
    4: [
        ((0,5,3,4), 18), ((0,5,3,0), 12), ((0,3,4,3), 12), ((0,3,5,3), 12),
        ((0,2,5,3), 10), ((0,2,3,4), 10), ((0,1,3,4), 6), ((0,1,3,0), 5),
        ((5,3,4,0), 5), ((3,4,0,5), 4), ((0,4,3,5), 4),
    ],
    5: [((0,5,3,4,3), 4), ((0,3,0,5,3), 3), ((0,2,3,4,3), 3)],
    6: [((0,5,3,4,3,0), 3), ((0,3,0,5,3,0), 3)],
}


def _pick_template_degs(rng: random.Random, m: int) -> list:
    return list(_wchoice(rng, TEMPLATES_BY_LEN[m]))


DURATIONS = {
    (2, 4):  [([2,2], 10)],
    (3, 4):  [([2,1,1], 10), ([1,1,2], 8)],
    (4, 4):  [([1,1,1,1], 12)],

    (2, 8):  [([4,4], 12)],
    (3, 8):  [([4,2,2], 10), ([2,2,4], 9), ([2,4,2], 2), ([3,3,2], 1)],
    (4, 8):  [([2,2,2,2], 12), ([4,2,1,1], 3), ([2,1,1,4], 2), ([1,1,2,4], 2), ([4,1,1,2], 1)],
    (5, 8):  [([2,2,2,1,1], 3), ([1,2,2,2,1], 1), ([2,1,2,1,2], 7), ([2,2,1,2,1], 3)],
    (6, 8):  [([2,1,1,2,1,1], 5), ([1,1,1,1,2,2], 1), ([1,1,2,1,1,2], 4), ([2,1,2,1,1,1], 3)],

    (2,16):  [([8,8], 8)],
    (3,16):  [([8,4,4], 4), ([4,4,8], 3), ([6,6,4], 3)],
    (4,16):  [([4,4,4,4], 12), ([6,4,4,2], 4)],
    (5,16):  [([4,4,4,2,2], 3), ([2,2,4,4,4], 3), ([4,2,4,2,4], 7), ([2,4,4,4,2], 3)],
    (6,16):  [([4,2,2,4,2,2], 5), ([4,2,2,2,2,4], 4), ([2,4,2,4,2,2], 5)],
}
VALID_COMBOS = sorted(list(DURATIONS.keys()))


def _pick_durations(rng: random.Random, m: int, total: int) -> list:
    return _wchoice(rng, DURATIONS[(m, total)])


def _pick_valid_total_and_m(rng: random.Random):
    weighted = []
    for (m, total) in VALID_COMBOS:
        wt = TOTAL_BARS_DISTRIBUTION.get(total, 0.0) * CHORDCOUNT_DISTRIBUTION.get(m, 0.0)
        if wt > 0:
            weighted.append(((total, m), wt))
    if not weighted:
        raise RuntimeError("No valid (total,m) combos available.")
    (total, m) = _wchoice(rng, weighted)
    return total, m


def _pattern_fingerprint(degs, quals):
    return (tuple(degs), tuple(quals))


def _pick_quality_diatonic(rng: random.Random, key: str, deg: int) -> str:
    root = SCALES[key][deg]
    triad_boost = (rng.random() < TRIAD_PROB_BASE)
    pool = DEG_ALLOWED_BASE[deg]

    for _ in range(200):
        q = _wchoice(rng, pool)

        if q in ("sus2", "sus4") and rng.random() < SUS_UPGRADE_PROB:
            if rng.random() >= BARE_SUS_PROB:
                q = "sus2add9" if q == "sus2" else "sus4add9"

        if q in ("maj", "min") and (not triad_boost) and rng.random() < 0.85:
            continue

        if _is_diatonic_chord(key, root, q):
            return q

    for q in SAFE_FALLBACK_ORDER:
        if _is_diatonic_chord(key, root, q):
            return q
    return "maj7"


def _dedupe_inside_progression(rng: random.Random, key: str, degs: list, quals: list):
    scale = SCALES[key]
    used = set()

    for i in range(len(degs)):
        d = degs[i]
        root = scale[d]
        q = quals[i]
        sym = root + q

        if sym not in used:
            used.add(sym)
            continue

        candidate_quals = SAFE_FALLBACK_ORDER[:]
        rng.shuffle(candidate_quals)
        fixed = False
        for q2 in candidate_quals:
            if q2 == q:
                continue
            if _is_diatonic_chord(key, root, q2):
                sym2 = root + q2
                if sym2 not in used:
                    quals[i] = q2
                    used.add(sym2)
                    fixed = True
                    break
        if fixed:
            continue

        neighbor_steps = [1, -1, 2, -2, 3, -3]
        rng.shuffle(neighbor_steps)
        for stp in neighbor_steps:
            d2 = (d + stp) % 7
            root2 = scale[d2]

            if _is_diatonic_chord(key, root2, q) and (root2 + q) not in used:
                degs[i] = d2
                used.add(root2 + q)
                fixed = True
                break

            cand2 = SAFE_FALLBACK_ORDER[:]
            rng.shuffle(cand2)
            for q2 in cand2:
                if _is_diatonic_chord(key, root2, q2) and (root2 + q2) not in used:
                    degs[i] = d2
                    quals[i] = q2
                    used.add(root2 + q2)
                    fixed = True
                    break
            if fixed:
                break

        if not fixed:
            return None

    return degs, quals


def _build_progression(rng: random.Random, key: str, degs: list, total_bars: int):
    quals = [_pick_quality_diatonic(rng, key, d) for d in degs]

    ded = _dedupe_inside_progression(rng, key, degs[:], quals[:])
    if ded is None:
        return None
    degs, quals = ded

    roots = [SCALES[key][d] for d in degs]

    if any(not _is_diatonic_chord(key, r, q) for r, q in zip(roots, quals)):
        return None

    if not _shared_tone_ok_loop(roots, quals, need=1, loop=True):
        return None

    if LIMIT_NOTECOUNT_JUMPS:
        big = 0
        for a, b in zip(quals, quals[1:]):
            if abs(QUALITY_NOTECOUNT[a] - QUALITY_NOTECOUNT[b]) >= 3:
                big += 1
        if ENFORCE_LOOP_OK and len(quals) >= 2:
            if abs(QUALITY_NOTECOUNT[quals[-1]] - QUALITY_NOTECOUNT[quals[0]]) >= 3:
                big += 1
        if big > MAX_BIG_JUMPS_PER_PROG:
            return None

    chords = [r + q for r, q in zip(roots, quals)]
    durs = _pick_durations(rng, len(chords), total_bars)

    if _low_sim_count_loop(roots, quals, loop=ENFORCE_LOOP_OK) != 0:
        return None

    return chords, durs, key, degs, quals


def _pick_keys_even(n: int, rng: random.Random) -> list:
    base = n // len(KEYS)
    rem = n % len(KEYS)
    out = []
    for k in KEYS:
        out += [k] * base
    extra = KEYS[:]
    rng.shuffle(extra)
    out += extra[:rem]
    rng.shuffle(out)
    return out


def generate_progressions(n: int, seed: int):
    rng = random.Random(seed)
    keys = _pick_keys_even(n, rng)

    max_pattern_dupes = int(math.floor(n * 0.01))
    pattern_dupe_used = 0

    used_exact = set()
    pattern_counts = Counter()
    low_sim_total = 0
    qual_usage = Counter()

    out = []

    for i in range(n):
        key = keys[i]
        built = None

        for _ in range(MAX_TRIES_PER_PROG):
            total_bars, m = _pick_valid_total_and_m(rng)
            degs = _pick_template_degs(rng, m)

            res = _build_progression(rng, key, degs, total_bars)
            if res is None:
                continue

            chords, durs, _k, degs_used, quals_used = res

            ek = tuple(chords)
            if ek in used_exact:
                continue

            fp = _pattern_fingerprint(degs_used, quals_used)
            if pattern_counts[fp] >= PATTERN_MAX_REPEATS and pattern_dupe_used >= max_pattern_dupes:
                continue

            used_exact.add(ek)
            if pattern_counts[fp] >= 1:
                pattern_dupe_used += 1
            pattern_counts[fp] += 1

            roots = [SCALES[key][d] for d in degs_used]
            low_sim_total += _low_sim_count_loop(roots, quals_used, loop=ENFORCE_LOOP_OK)
            for q in quals_used:
                qual_usage[q] += 1

            built = (chords, durs, key)
            break

        if built is None:
            raise RuntimeError(f"Could not build progression {i+1}. Space too constrained.")

        out.append(built)

    return out, pattern_dupe_used, max_pattern_dupes, low_sim_total, qual_usage


# =========================================================
# CHORD -> MIDI + VOICING ENGINE
# =========================================================
NOTE_TO_SEMITONE = NOTE_TO_PC.copy()

LOW, HIGH = 48, 84
TARGET_CENTER = 60.0
IDEAL_SPAN = 12
MIN_SPAN = 8
MAX_SPAN = 19

MAX_SHARED_DEFAULT = 2
MAX_SHARED_MIN11 = 3

DISALLOW_GLUE = True
ENFORCE_NOT_RAW_WHEN_VOICING = True


def parse_root_and_bass(ch: str):
    ch = ch.strip().replace("6/9", "6add9")
    if "/" in ch:
        main, bass = ch.split("/", 1)
        bass = bass.strip()
    else:
        main, bass = ch, None

    main = main.strip()
    m = re.match(r"^([A-G](?:#|b)?)(.*)$", main)
    if not m:
        raise ValueError(f"Bad chord root in '{ch}'")

    root = m.group(1)
    rest = m.group(2).strip().replace(" ", "")
    return root, rest, bass


def chord_to_midi(chord_name: str, base_oct=3, low=LOW, high=HIGH) -> List[int]:
    root, rest, bass = parse_root_and_bass(chord_name)
    if root not in NOTE_TO_SEMITONE:
        raise ValueError(f"Bad root '{root}' in '{chord_name}'")

    quality = rest.lower()
    if quality not in QUAL_TO_INTERVALS:
        raise ValueError(f"Unrecognized chord quality: {rest}")

    root_pc = NOTE_TO_SEMITONE[root]
    root_midi = 12 * (base_oct + 1) + root_pc

    tones = QUAL_TO_INTERVALS[quality]
    notes = []
    for iv in tones:
        p = root_midi + iv
        while p < low:
            p += 12
        while p > high:
            p -= 12
        notes.append(p)

    if bass:
        if bass not in NOTE_TO_SEMITONE:
            raise ValueError(f"Bad slash bass '{bass}' in '{chord_name}'")
        bass_pc = NOTE_TO_SEMITONE[bass]
        bass_midi = 12 * base_oct + bass_pc
        while notes and bass_midi > min(notes):
            bass_midi -= 12
        notes = [bass_midi] + notes

    return sorted(set(int(x) for x in notes))


def clamp_to_range(notes):
    out = []
    for p in notes:
        while p < LOW:
            p += 12
        while p > HIGH:
            p -= 12
        out.append(p)
    return sorted(out)


def span(notes):
    return max(notes) - min(notes)


def center(notes):
    return (min(notes) + max(notes)) / 2.0


def has_glued_semitones(notes):
    s = sorted(notes)
    return any((s[i + 1] - s[i]) == 1 for i in range(len(s) - 1))


def shared_pitch_count(a, b):
    return len(set(a) & set(b))


def is_min11_name(ch_name: str) -> bool:
    s = ch_name.replace(" ", "").lower()
    return ("min11" in s)


def max_shared_allowed(prev_name, cur_name):
    return MAX_SHARED_MIN11 if (is_min11_name(prev_name) or is_min11_name(cur_name)) else MAX_SHARED_DEFAULT


def is_raw_shape(v, raw_notes):
    return sorted(v) == sorted(clamp_to_range(raw_notes))


def total_move(prev, cur):
    p = sorted(prev)
    c = sorted(cur)
    if len(p) == len(c):
        return sum(abs(c[i] - p[i]) for i in range(len(p)))
    return abs(center(c) - center(p)) * 2.0


def generate_voicing_candidates(raw_notes):
    base = clamp_to_range(raw_notes)
    base = sorted(set(base))
    shifts = (-12, 0, 12)
    candidates = set()

    def rec(i, cur):
        if i == len(base):
            v = clamp_to_range(cur)
            if len(set(v)) == len(set(base)):
                candidates.add(tuple(sorted(v)))
            return
        for s in shifts:
            rec(i + 1, cur + [base[i] + s])

    rec(0, [])

    inv = base[:]
    for _ in range(len(base) - 1):
        inv = inv[1:] + [inv[0] + 12]
        candidates.add(tuple(clamp_to_range(inv)))

    out = [list(c) for c in candidates]
    out = [v for v in out if len(set(v)) == len(set(base))]
    return out if out else [base]


def choose_best_voicing(
    prev_voicing: Optional[List[int]],
    prev_name: str,
    cur_name: str,
    raw_notes: List[int]
) -> List[int]:
    cands = generate_voicing_candidates(raw_notes)
    raw_clamped = clamp_to_range(raw_notes)

    if DISALLOW_GLUE:
        non_glue = [v for v in cands if not has_glued_semitones(v)]
        if non_glue:
            cands = non_glue

    if ENFORCE_NOT_RAW_WHEN_VOICING:
        non_raw = [v for v in cands if not is_raw_shape(v, raw_clamped)]
        if non_raw:
            cands = non_raw

    if prev_voicing is not None:
        limit = max_shared_allowed(prev_name, cur_name)
        filtered = [v for v in cands if shared_pitch_count(prev_voicing, v) <= limit]
        if filtered:
            cands = filtered

    def cost(v):
        v = sorted(v)

        reg_pen = abs(center(v) - TARGET_CENTER) * 120

        sp = span(v)
        span_pen = abs(sp - IDEAL_SPAN) * 80
        if sp < MIN_SPAN:
            span_pen += (MIN_SPAN - sp) * 700
        if sp > MAX_SPAN:
            span_pen += (sp - MAX_SPAN) * 220

        move_pen = 0 if prev_voicing is None else total_move(prev_voicing, v) * 7

        repeat_pen = 2500 if (prev_voicing is not None and sorted(prev_voicing) == v) else 0

        shared_pen = 0
        if prev_voicing is not None:
            limit = max_shared_allowed(prev_name, cur_name)
            sh = shared_pitch_count(prev_voicing, v)
            if sh > limit:
                shared_pen = (sh - limit) * 6000

        raw_pen = 100000 if (ENFORCE_NOT_RAW_WHEN_VOICING and is_raw_shape(v, raw_clamped)) else 0
        glue_pen = 20000 if (DISALLOW_GLUE and has_glued_semitones(v)) else 0

        return reg_pen + span_pen + move_pen + repeat_pen + shared_pen + raw_pen + glue_pen

    cands.sort(key=cost)
    return sorted(cands[0])


# =========================================================
# EXPORTER
# =========================================================
BPM = 85
TIME_SIG = (4, 4)
BASE_OCTAVE = 3
VELOCITY = 100

BAR_DIR = {4: "4-bar", 8: "8-bar", 16: "16-bar"}


def sec_per_bar(bpm=BPM, ts=TIME_SIG):
    return (60.0 / bpm) * ts[0]


SEC_PER_BAR = sec_per_bar()


def safe_token(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_#-]+", "", str(s))


def chord_list_token(chords):
    return "-".join(safe_token(c) for c in chords)


def validate_progressions(progressions):
    if not progressions:
        raise ValueError("No progressions generated.")
    for i, item in enumerate(progressions, start=1):
        if len(item) != 3:
            raise ValueError(f"Progression {i} must be (chords, durations, key).")
        chords, durations, key_name = item
        if len(chords) != len(durations):
            raise ValueError(f"Progression {i}: chords/durations mismatch.")
        bars = sum(durations)
        if bars not in (4, 8, 16):
            raise ValueError(f"Progression {i}: invalid bar sum {bars}.")
        for ch in chords:
            chord_to_midi(ch, base_oct=BASE_OCTAVE)


def write_progression_midi(out_root: str, idx: int, chords, durations, key_name: str, revoice: bool):
    midi = pretty_midi.PrettyMIDI(initial_tempo=BPM)
    midi.time_signature_changes = [pretty_midi.TimeSignature(TIME_SIG[0], TIME_SIG[1], 0)]
    inst = pretty_midi.Instrument(program=0)

    raw = [chord_to_midi(ch, base_oct=BASE_OCTAVE) for ch in chords]

    if revoice:
        voiced = []
        prev_v = None
        prev_name = chords[0]
        for ch_name, notes in zip(chords, raw):
            if prev_v is None:
                v = choose_best_voicing(None, ch_name, ch_name, notes)
            else:
                v = choose_best_voicing(prev_v, prev_name, ch_name, notes)
            voiced.append(v)
            prev_v = v
            prev_name = ch_name
        out_notes = voiced
    else:
        out_notes = raw

    t = 0.0
    for notes, bars in zip(out_notes, durations):
        dur = bars * SEC_PER_BAR
        for p in sorted(set(notes)):
            inst.notes.append(pretty_midi.Note(
                velocity=int(VELOCITY),
                pitch=int(p),
                start=t,
                end=t + dur
            ))
        t += dur

    midi.instruments.append(inst)

    total_bars = sum(durations)
    out_dir = os.path.join(out_root, "Progressions", BAR_DIR[total_bars])
    os.makedirs(out_dir, exist_ok=True)

    filename = f"Prog_{idx:03d}_in_{safe_token(key_name)}_{chord_list_token(chords)}.mid"
    midi.write(os.path.join(out_dir, filename))


def write_single_chord_midi(out_root: str, chord_name: str, revoice: bool, length_bars=4):
    dur = length_bars * SEC_PER_BAR
    midi = pretty_midi.PrettyMIDI(initial_tempo=BPM)
    midi.time_signature_changes = [pretty_midi.TimeSignature(TIME_SIG[0], TIME_SIG[1], 0)]
    inst = pretty_midi.Instrument(program=0)

    raw = chord_to_midi(chord_name, base_oct=BASE_OCTAVE)
    notes = choose_best_voicing(None, chord_name, chord_name, raw) if revoice else raw

    for p in sorted(set(notes)):
        inst.notes.append(pretty_midi.Note(
            velocity=int(VELOCITY),
            pitch=int(p),
            start=0.0,
            end=dur
        ))

    midi.instruments.append(inst)

    chords_dir = os.path.join(out_root, "Chords")
    os.makedirs(chords_dir, exist_ok=True)
    midi.write(os.path.join(chords_dir, f"{safe_token(chord_name)}.mid"))


def zip_pack(out_root: str, zip_path: str):
    with ZipFile(zip_path, "w") as z:
        for root, _, files in os.walk(out_root):
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, out_root)
                z.write(full, arcname=rel)


def build_pack(progressions, revoice: bool) -> tuple[str, int]:
    validate_progressions(progressions)

    workdir = tempfile.mkdtemp(prefix="aa_midi_")
    prog_root = os.path.join(workdir, "Pack")
    os.makedirs(prog_root, exist_ok=True)

    unique_chords = set()
    for i, (chords, durations, key_name) in enumerate(progressions, start=1):
        write_progression_midi(prog_root, i, chords, durations, key_name, revoice=revoice)
        unique_chords.update(chords)

    for ch in sorted(unique_chords):
        write_single_chord_midi(prog_root, ch, revoice=revoice, length_bars=4)

    zip_path = os.path.join(workdir, DOWNLOAD_NAME)
    zip_pack(prog_root, zip_path)

    return zip_path, len(unique_chords)


# =========================================================
# UI HELPERS
# =========================================================
def make_rows(progressions):
    rows = []
    for i, (chords, durs, key) in enumerate(progressions, start=1):
        rows.append({
            "#": i,
            "Key": key,
            "Bars": int(sum(durs)),
            "Chords": " – ".join(chords),
        })
    return rows


# =========================================================
# HERO
# =========================================================
st.markdown(
    f"""
<div class="aa-hero">
  <div class="aa-title">{APP_TITLE}</div>
  <div class="aa-subtitle">{APP_SUBTITLE}</div>
</div>
""",
    unsafe_allow_html=True,
)

# =========================================================
# MAIN PANEL
# =========================================================
sp_left, sp_center, sp_right = st.columns([1, 2, 1])
with sp_center:
    n_progressions = st.slider(
        "Progressions to Generate",
        min_value=1,
        max_value=100,
        value=10,
        help="Generates a balanced mix of 4, 8, and 16-bar chord loops in different keys."
    )
    revoice = st.toggle(
        "Re-Voicing",
        value=False,
        help="Smooth voicings + inversions for a more original feel."
    )

btn_left, btn_center, btn_right = st.columns([1, 2, 1])
with btn_center:
    generate_clicked = st.button("Generate Progressions", use_container_width=True)


# =========================================================
# RUN GENERATION
# =========================================================
if generate_clicked:
    try:
        with st.spinner("Generating progressions…"):
            seed = int(np.random.randint(1, 2_000_000_000))

            progressions, pattern_dupe_used, pattern_dupe_max, low_sim_total, qual_usage = generate_progressions(
                n=int(n_progressions),
                seed=seed
            )

            if low_sim_total != 0:
                raise RuntimeError("Safety check failed: low-sim transitions detected.")

            zip_path, chord_count = build_pack(progressions, revoice=bool(revoice))

            st.session_state.progressions = progressions
            st.session_state.zip_path = zip_path
            st.session_state.progression_count = len(progressions)
            st.session_state.chord_count = chord_count

        st.markdown(
            """
            <div class="aa-ready-wrap">
              <div class="aa-ready-badge"><span class="aa-ready-dot"></span>READY</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    except Exception as e:
        st.session_state.pop("zip_path", None)
        st.session_state.pop("progressions", None)
        st.session_state.progression_count = 0
        st.session_state.chord_count = 0
        st.error(f"Error: {e}")


# =========================================================
# SUMMARY + DOWNLOAD + TABLE
# =========================================================
if "progressions" in st.session_state and st.session_state.get("zip_path"):

    

    a, b = st.columns(2)
    a.metric("Progressions Generated", int(st.session_state.get("progression_count", 0)))
    b.metric("Individual Chords Generated", int(st.session_state.get("chord_count", 0)))

    try:
        with open(st.session_state.zip_path, "rb") as f:
            zip_bytes = f.read()

        dl_left, dl_center, dl_right = st.columns([1, 2, 1])
        with dl_center:
            st.download_button(
                label="Download MIDI Progressions",
                data=zip_bytes,
                file_name=DOWNLOAD_NAME,
                mime="application/zip",
                use_container_width=True
            )
    except Exception as e:
        st.error(f"Could not read ZIP for download: {e}")

    rows = make_rows(st.session_state.progressions)
    df = pd.DataFrame(rows)

    st.markdown("### Progressions List")
    st.dataframe(df, use_container_width=True, hide_index=True)

  





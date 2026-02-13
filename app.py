# app.py  Aural Alchemy | Endless Ambient MIDI Progressions
# Streamlit app (standalone) that:
# - Generates diatonic, loop-safe ambient chord progressions
# - Exports a ZIP containing: Progressions (4/8/16-bar folders) + Individual Chords library
# - Optional Re-Voicing (inversions/voicing engine)
# - Premium UI styling (Cinzel font everywhere, cyan slider, gold shimmer button, soft glows)
# - Sacred geometry mandala overlay (two layers + slow rotation)
# - ADVANCED: Chord Type Balance sliders (optional, can be disabled via flag)
# - ADVANCED: Reset sliders to default (50)
# - ZIP name: adds "_Revoiced" when re-voicing is enabled

import os
import re
import math
import random
import tempfile
import base64
from zipfile import ZipFile
from collections import Counter
from typing import List, Optional, Dict, Tuple

import streamlit as st
import pandas as pd
import numpy as np
import pretty_midi


# =========================================================
# FEATURE FLAGS (DEV ONLY)
# =========================================================
# Master toggle: disables chord-balance feature entirely (no UI + no weighting).
ENABLE_CHORD_BALANCE_FEATURE = True


# =========================================================
# APP CONFIG
# =========================================================
st.set_page_config(
    page_title="Aural Alchemy • MIDI Progressions",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="collapsed",
)

APP_TITLE_LINE1 = "AURAL ALCHEMY"
APP_TITLE_LINE2 = "MIDI GENERATOR"
APP_SUBTITLE = "Endless Ambient MIDI Progressions"
DOWNLOAD_NAME = "MIDI_Progressions_Aural_Alchemy.zip"


# =========================================================
# PREMIUM CSS (Cinzel everywhere + cyan slider + shimmer + glows)
# + Fix expander header glitching and slider value wrapping
# =========================================================
st.markdown(
    r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;500;600;700&display=swap');

/* FORCE STREAMLIT THEME PRIMARY COLOR */
:root {
  --primary-color: #00E5FF !important;
  --primaryColor: #00E5FF !important;
  --primary-color-light: rgba(0,229,255,0.35) !important;
}
[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
.stApp {
  --primary-color: #00E5FF !important;
  --primaryColor: #00E5FF !important;
}

html, body, [class*="css"], .stApp, .block-container,
h1, h2, h3, h4, h5, h6,
p, label,
button, .stButton>button,
[data-testid="stMetricLabel"],
[data-testid="stMetricValue"],
[data-testid="stMarkdownContainer"],
[data-testid="stText"] {
  font-family: "Cinzel", serif !important;
  letter-spacing: 0.55px !important;
}

/* ✅ Restore Streamlit/BaseWeb icon fonts (prevents ARROW_* text showing) */
[data-baseweb="icon"], 
[data-baseweb="icon"] *,
svg, svg * {
  font-family: "Material Icons", "Material Symbols Outlined", system-ui, sans-serif !important;
  letter-spacing: 0 !important;
  text-transform: none !important;
}


/* ---- Page background ---- */
.stApp {
  background:
    radial-gradient(1200px 700px at 20% 15%, rgba(0,229,255,0.10), rgba(0,0,0,0) 60%),
    radial-gradient(1200px 700px at 85% 20%, rgba(255,215,0,0.08), rgba(0,0,0,0) 60%),
    radial-gradient(900px 600px at 50% 85%, rgba(160,120,255,0.06), rgba(0,0,0,0) 65%),
    linear-gradient(180deg, #070A10 0%, #07080E 35%, #05060A 100%);
}

/* =========================================================
   SACRED GEOMETRY OVERLAY (two layers + slow rotation)
========================================================= */
.aa-geom-wrap{
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  opacity: 0.90;
}
.aa-geom-1,
.aa-geom-2{
  position: absolute;
  inset: -18%;
  background-repeat: no-repeat;
  background-position: center;
  background-size: min(1000px, 85vw) min(1000px, 85vw);
  will-change: transform, opacity;
  transform: translateZ(0);
  backface-visibility: hidden;
  contain: paint;
}
.aa-geom-1{
  opacity: 0.20;
  animation: aaSpin1 700s linear infinite;
}
.aa-geom-2{
  opacity: 0.18;
  animation: aaSpin2 660s linear infinite, aaBreathe 8.5s ease-in-out infinite;
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
.aa-title-second{
  display:block;
  margin-top: 6px;
  background: linear-gradient(
    90deg,
    rgba(255,255,255,0.98),
    rgba(0,229,255,0.90),
    rgba(255,215,0,0.92)
  );
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  font-size: 38px;
  letter-spacing: 2.5px;
}
.aa-subtitle {
  margin-top: 18px;
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

/* Cyan slider styling */
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
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  text-align: center !important;
  white-space: nowrap !important;
  word-break: keep-all !important;
  overflow-wrap: normal !important;
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


/* Metrics */
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
.block-container { padding-top: 3.5rem !important; }

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

/* Hide empty markdown paragraphs */
div[data-testid="stMarkdownContainer"] > p:empty { display: none !important; }

/* Fix expander header "overposting" glitch */
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary *{
  letter-spacing: 0px !important;
  text-transform: none !important;
  line-height: 1.25 !important;
}

/* FIX: slider tooltip numbers splitting vertically */
[data-testid="stSlider"] div[data-baseweb="slider"] [role="tooltip"],
[data-testid="stSlider"] div[data-baseweb="slider"] [role="tooltip"] *{
  white-space: nowrap !important;
  word-break: keep-all !important;
  overflow-wrap: normal !important;
  letter-spacing: 0px !important;
}
[data-testid="stSlider"] div[data-baseweb="slider"] [role="tooltip"]{
  min-width: 2.6em !important;
  text-align: center !important;
}
</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# Geometry SVG overlay (BASE64 DATA URI)
# IMPORTANT: only ONE triangle (one polygon)
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
    <polygon points="600,220 929.1,790 270.9,790" opacity="0.90"/>
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

# Second layer SVG WITHOUT triangle
GEOM_SVG_NO_TRIANGLE = GEOM_SVG.replace(
    '<polygon points="600,220 929.1,790 270.9,790" opacity="0.90"/>',
    ''
)

GEOM_DATA_URI = "data:image/svg+xml;base64," + base64.b64encode(GEOM_SVG.encode("utf-8")).decode("utf-8")
GEOM_DATA_URI_NO_TRIANGLE = "data:image/svg+xml;base64," + base64.b64encode(GEOM_SVG_NO_TRIANGLE.encode("utf-8")).decode("utf-8")

st.markdown(
    f"""
<div class="aa-geom-wrap">
  <div class="aa-geom-1" style="background-image:url('{GEOM_DATA_URI}');"></div>
  <div class="aa-geom-2" style="background-image:url('{GEOM_DATA_URI_NO_TRIANGLE}');"></div>
</div>
""",
    unsafe_allow_html=True,
)


# =========================================================
# MUSICAL DATA + SAFE CHORD DEFINITIONS
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
# GENERATOR SETTINGS
# =========================================================
PATTERN_MAX_REPEATS = 1
MAX_PATTERN_DUPLICATE_RATIO = 0.01  # 1%

TOTAL_BARS_DISTRIBUTION = {8: 0.40, 4: 0.35, 16: 0.25}
CHORDCOUNT_DISTRIBUTION = {4: 0.40, 3: 0.35, 2: 0.20, 5: 0.03, 6: 0.02}

LIMIT_NOTECOUNT_JUMPS = True
MAX_BIG_JUMPS_PER_PROG = 1

MIN_SHARED_TONES = 1
ENFORCE_LOOP_OK = True
MAX_TRIES_PER_PROG = 40000

TRIAD_PROB_BASE = 0.30
BARE_SUS_PROB = 0.13

SUS_WEIGHT_MULT = 0.50
SUS_UPGRADE_PROB = 0

MAJ_POOL_BASE = [("maj9", 10), ("maj7", 9), ("add9", 7), ("6add9", 5), ("6", 4), ("maj", 4)]
MIN_POOL_BASE = [("min9", 10), ("min7", 9), ("min11", 4), ("min", 4)]
SUS_POOL_BASE = [("sus2add9", 3), ("sus4add9", 3), ("sus2", 3), ("sus4", 3)]


def _scaled_pool(pool, mult):
    return [(q, max(1e-9, w * mult)) for q, w in pool]


SUS_POOL_SCALED_BASE = _scaled_pool(SUS_POOL_BASE, SUS_WEIGHT_MULT)

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


# =========================================================
# CHORD TYPE BALANCE (ADVANCED) + STRICT MODE
# - Sliders are 0..100 with default 50.
# - 50 = neutral
# - 0  = disabled
# - 100 = strongly favored
#
# STRICT_SLIDERS:
# If user sets ONLY SUS >0 (others 0) => ONLY SUS chords.
# Same for any single chord type.
# If impossible under diatonic + templates + uniqueness => clean failure (no fallback).
# =========================================================
STRICT_SLIDERS = True  # ✅ True = sliders act like hard rules

ADV_ALL_QUALITIES = [
    "maj9","maj7","add9","6add9","6","maj",
    "min9","min7","min11","min",
    "sus2add9","sus4add9","sus2","sus4",
]
ADV_DEFAULT_VALUE = 50
ADV_KEY_PREFIX = "aa_adv_v1_"  # bump this if you ever change the widget set


def _balance_factor(v: int) -> float:
    v = int(max(0, min(100, v)))
    if v == 0:
        return 0.0
    if v == 50:
        return 1.0
    if v < 50:
        return max(0.02, v / 50.0)
    return 1.0 + ((v - 50) / 50.0) * 1.0


def _enabled_qualities(balance: Optional[Dict[str, int]]) -> List[str]:
    if (not ENABLE_CHORD_BALANCE_FEATURE) or (not balance):
        return ADV_ALL_QUALITIES[:]  # feature off => normal behavior
    return [q for q in ADV_ALL_QUALITIES if int(balance.get(q, ADV_DEFAULT_VALUE)) > 0]


def _build_deg_allowed(balance: Optional[Dict[str, int]], key: str) -> Dict[int, List[Tuple[str, float]]]:
    """
    Returns per-degree pools for THIS key: deg -> [(quality, weight), ...]
    Strict mode: ONLY enabled qualities, diatonic-filtered, no silent fallback.
    """
    enabled = _enabled_qualities(balance)

    if STRICT_SLIDERS and balance and len(enabled) == 0:
        raise RuntimeError("All chord-type sliders are 0. Enable at least one chord type.")

    out: Dict[int, List[Tuple[str, float]]] = {}
    for deg in range(7):
        root = SCALES[key][deg]
        items: List[Tuple[str, float]] = []

        for q in enabled:
            if _is_diatonic_chord(key, root, q):
                # weights only bias selection WITHIN enabled set
                w = 1.0
                if balance:
                    w = max(1e-9, _balance_factor(balance.get(q, ADV_DEFAULT_VALUE)))
                items.append((q, w))

        out[deg] = items

    return out


def _pick_quality_diatonic(
    rng: random.Random,
    key: str,
    deg: int,
    deg_allowed: Dict[int, List[Tuple[str, float]]]
) -> Optional[str]:
    """
    Strict: ONLY pick from deg_allowed. If empty -> None (template invalid).
    """
    pool = deg_allowed.get(deg, [])
    if not pool:
        return None
    return _wchoice(rng, pool)



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


def _build_progression(rng: random.Random, key: str, degs: list, total_bars: int, deg_allowed):
    # STRICT-safe quality picking:
    # - _pick_quality_diatonic() returns None if this degree has no allowed qualities (under strict sliders)
    # - returning None here simply rejects this template and tries another
    quals = []
    for d in degs:
        q = _pick_quality_diatonic(rng, key, d, deg_allowed=deg_allowed)
        if q is None:
            return None  # strict: this template can't work with enabled chord types
        quals.append(q)

    # =========================================================
    # RULE: Do not allow progression to start with SUS chord
    # unless SUS sliders are strongly boosted (>80)
    # =========================================================
    def is_sus(q: str) -> bool:
        return q.startswith("sus")

    sus_allowed_start = False
    if chord_balance:
        sus_keys = ["sus2", "sus4", "sus2add9", "sus4add9"]
        if any(chord_balance.get(k, ADV_DEFAULT_VALUE) > 80 for k in sus_keys):
            sus_allowed_start = True

    if is_sus(quals[0]) and not sus_allowed_start:
        return None

    # STRICT mode note:
    # _dedupe_inside_progression() should early-return (degs, quals) without mutating,
    # so your "only X chord types" rule isn't violated.
    ded = _dedupe_inside_progression(rng, key, degs[:], quals[:])
    if ded is None:
        return None
    degs, quals = ded

    roots = [SCALES[key][d] for d in degs]

    # Keep diatonic safety
    if any(not _is_diatonic_chord(key, r, q) for r, q in zip(roots, quals)):
        return None

    # Keep loop shared-tone safety
    if not _shared_tone_ok_loop(roots, quals, need=MIN_SHARED_TONES, loop=True):
        return None


    # =========================================================
    # SUS SAFETY SYSTEM (default + sus-heavy mode)
    # - Default mode keeps sus tasteful and avoids random sus fog
    # - Sus-heavy mode activates when user boosts sus sliders, allowing 100% sus
    #   while enforcing strong overlap and musical root movement
    # =========================================================

    # detect sus-heavy mode from chord_balance sliders (0..100)
    sus_keys = ["sus2", "sus4", "sus2add9", "sus4add9"]
    avg_sus_weight = 1.0
    if chord_balance:
        vals = [_balance_factor(chord_balance.get(k, ADV_DEFAULT_VALUE)) for k in sus_keys]
        avg_sus_weight = sum(vals) / len(vals)
    sus_heavy = avg_sus_weight >= 1.35

    def is_sus(q: str) -> bool:
        return q.startswith("sus")

    def is_sus4ish(q: str) -> bool:
        return q.startswith("sus4")

    def pc_interval(a: int, b: int) -> int:
        iv = abs((b - a) % 12)
        return min(iv, 12 - iv)

    m = len(quals)
    sus_count = sum(1 for q in quals if is_sus(q))
    sus4_count = sum(1 for q in quals if is_sus4ish(q))

    pcs = [_chord_pc_set_real(r, q) for r, q in zip(roots, quals)]
    root_pcs = [_pc(r) for r in roots]

    # Default mode constraints
    DEFAULT_SUS_MAX_RATIO = 0.45    # max 45% of chords in a progression can be sus
    DEFAULT_SUS4_MAX_COUNT = 1      # only 1 sus4/sus4add9 per progression
    DEFAULT_NEED_IF_SUS = 2         # shared tones when either chord is sus*
    DEFAULT_NEED_IF_SUS4 = 3        # shared tones when either chord is sus4*

    # Sus-heavy constraints
    HEAVY_NEED = 2                  # baseline shared tones
    HEAVY_NEED_IF_SUS4 = 3          # stricter when sus4 involved
    HEAVY_REQUIRE_STEP_OR_REPEAT = True

    # Allow sus4 -> sus4 only if "safe":
    # shared >= 3 OR stepwise root motion (<=2 semitones) OR same root
    ALLOW_SUS4_TO_SUS4_IF_SAFE = True

    if not sus_heavy:
        if sus_count / max(1, m) > DEFAULT_SUS_MAX_RATIO:
            return None
        if sus4_count > DEFAULT_SUS4_MAX_COUNT:
            return None

    step_moves = 0
    has_repeat_root = (len(set(root_pcs)) < len(root_pcs))

    for i in range(m):
        j = (i + 1) % m  # includes loop-back

        shared = len(pcs[i] & pcs[j])
        iv = pc_interval(root_pcs[i], root_pcs[j])

        if iv <= 2:
            step_moves += 1

        if sus_heavy:
            need = HEAVY_NEED
            if is_sus4ish(quals[i]) or is_sus4ish(quals[j]):
                need = max(need, HEAVY_NEED_IF_SUS4)
            if shared < need:
                return None

            if is_sus4ish(quals[i]) and is_sus4ish(quals[j]):
                if ALLOW_SUS4_TO_SUS4_IF_SAFE:
                    if not (shared >= 3 or iv <= 2 or roots[i] == roots[j]):
                        return None
                else:
                    return None

        else:
            need = 1
            if is_sus(quals[i]) or is_sus(quals[j]):
                need = DEFAULT_NEED_IF_SUS
            if is_sus4ish(quals[i]) or is_sus4ish(quals[j]):
                need = max(need, DEFAULT_NEED_IF_SUS4)
            if shared < need:
                return None

            if is_sus4ish(quals[i]) and is_sus4ish(quals[j]):
                if ALLOW_SUS4_TO_SUS4_IF_SAFE:
                    if not (shared >= 3 or iv <= 2 or roots[i] == roots[j]):
                        return None
                else:
                    return None

    if sus_heavy and HEAVY_REQUIRE_STEP_OR_REPEAT:
        if step_moves == 0 and (not has_repeat_root):
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


def generate_progressions(n: int, seed: int, chord_balance: Optional[Dict[str, int]] = None):
    rng = random.Random(seed)
    keys = _pick_keys_even(n, rng)
    deg_allowed = None  # built per key inside loop

    max_pattern_dupes = int(math.floor(n * MAX_PATTERN_DUPLICATE_RATIO))
    pattern_dupe_used = 0

    used_exact = set()
    pattern_counts = Counter()
    low_sim_total = 0
    qual_usage = Counter()

    out = []

    for i in range(n):
        key = keys[i]
        deg_allowed = _build_deg_allowed(chord_balance, key)  # ✅ key-aware + strict
        built = None

        for _ in range(MAX_TRIES_PER_PROG):
            total_bars, m = _pick_valid_total_and_m(rng)
            degs = _pick_template_degs(rng, m)

            res = _build_progression(rng, key, degs, total_bars, deg_allowed=deg_allowed)
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
# CHORD -> MIDI + VOICING ENGINE (SMOOTH PRO VERSION)
# - Real voice-leading distance (minimal assignment)
# - Explicit spacing rules (no weird holes/clusters unless forced)
# - Bass stability penalty (ambient/piano feel)
# - Keeps your cross-semitone repair + glue behavior
# =========================================================

NOTE_TO_SEMITONE = NOTE_TO_PC.copy()

# Range
LOW, HIGH = 48, 84

# Register target
TARGET_CENTER = 60.0

# Span targets (overall chord spread)
IDEAL_SPAN = 12
MIN_SPAN = 8
MAX_SPAN = 19

# Adjacent spacing rules (inside the chord)
MIN_ADJ_GAP = 2        # avoid tight clusters unless needed
MAX_ADJ_GAP = 9        # avoid big holes
HARD_MAX_ADJ_GAP = 12  # very likely "weird" if exceeded

# Bass stability
MAX_BASS_JUMP = 7      # semitones, larger jumps start to feel jumpy

# Shared tones safety
MAX_SHARED_DEFAULT = 2
MAX_SHARED_MIN11 = 3

# Raw-shape handling
ENFORCE_NOT_RAW_WHEN_VOICING = True
RAW_PENALTY = 1800     # raise if you want more "always different", lower if too strict

# Glue behavior (semitone clusters)
GLUE_LOW_CUTOFF = 48
GLUE_PROBABILITY = 0.30

# Resolution allowed for cross-semitone repair
ALLOW_RESOLVE_TO_THIRD = True
ALLOW_RESOLVE_TO_FIFTH = False


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


def clamp_to_range(notes: List[int]) -> List[int]:
    out = []
    for p in notes:
        while p < LOW:
            p += 12
        while p > HIGH:
            p -= 12
        out.append(int(p))
    return sorted(out)


def span(notes: List[int]) -> int:
    if not notes:
        return 0
    return int(max(notes) - min(notes))


def center(notes: List[int]) -> float:
    if not notes:
        return TARGET_CENTER
    return (min(notes) + max(notes)) / 2.0


def semitone_pairs(notes: List[int]):
    s = sorted(set(notes))
    pairs = []
    for i in range(len(s) - 1):
        if (s[i + 1] - s[i]) == 1:
            pairs.append((s[i], s[i + 1]))
    return pairs


def glue_ok(notes: List[int], rng: random.Random) -> bool:
    pairs = semitone_pairs(notes)
    if not pairs:
        return True

    # If any semitone cluster is too low, avoid it (mud)
    for a, b in pairs:
        if a < GLUE_LOW_CUTOFF or b < GLUE_LOW_CUTOFF:
            return False

    # Otherwise, allow some clusters (glue) probabilistically
    return rng.random() < GLUE_PROBABILITY


def shared_pitch_count(a: List[int], b: List[int]) -> int:
    return len(set(a) & set(b))


def is_min11_name(ch_name: str) -> bool:
    s = ch_name.replace(" ", "").lower()
    return ("min11" in s)


def max_shared_allowed(prev_name: str, cur_name: str) -> int:
    return MAX_SHARED_MIN11 if (is_min11_name(prev_name) or is_min11_name(cur_name)) else MAX_SHARED_DEFAULT


def is_raw_shape(v: List[int], raw_notes: List[int]) -> bool:
    return sorted(v) == sorted(clamp_to_range(raw_notes))


def allowed_resolution_pcs(key: str) -> set:
    pcs = set()
    tonic = NOTE_TO_PC[SCALES[key][0]]
    pcs.add(tonic)

    if ALLOW_RESOLVE_TO_THIRD:
        third = NOTE_TO_PC[SCALES[key][2]]
        pcs.add(third)

    if ALLOW_RESOLVE_TO_FIFTH:
        fifth = NOTE_TO_PC[SCALES[key][4]]
        pcs.add(fifth)

    return pcs


def bad_cross_semitone_indices(prev_notes: List[int], cur_notes: List[int], allowed_target_pcs: set) -> List[int]:
    prev_set = set(prev_notes)
    bad = []
    for i, n in enumerate(list(cur_notes)):
        if (n - 1) in prev_set or (n + 1) in prev_set:
            if (n % 12) not in allowed_target_pcs:
                bad.append(i)
    return bad


def repair_cross_semitones(prev_notes: List[int], cur_notes: List[int], allowed_target_pcs: set, max_iters: int = 8) -> List[int]:
    v = sorted(list(cur_notes))

    for _ in range(max_iters):
        bad_idxs = bad_cross_semitone_indices(prev_notes, v, allowed_target_pcs)
        if not bad_idxs:
            break

        changed_any = False
        for idx in bad_idxs:
            n = v[idx]
            options = []

            for delta in (+12, -12):
                n2 = n + delta
                if n2 < LOW or n2 > HIGH:
                    continue
                if n2 in v:
                    continue

                test = v[:]
                test[idx] = n2
                test = sorted(test)

                remaining = len(bad_cross_semitone_indices(prev_notes, test, allowed_target_pcs))
                options.append((remaining, abs(center(test) - TARGET_CENTER), span(test), test))

            if options:
                options.sort(key=lambda x: (x[0], x[1], x[2]))
                v = options[0][3]
                changed_any = True

        if not changed_any:
            break

    return v


def adjacent_gaps(notes: List[int]) -> List[int]:
    v = sorted(notes)
    if len(v) < 2:
        return []
    return [v[i + 1] - v[i] for i in range(len(v) - 1)]


def spacing_penalty(notes: List[int]) -> float:
    gaps = adjacent_gaps(notes)
    if not gaps:
        return 0.0

    pen = 0.0
    for g in gaps:
        # Too tight
        if g < MIN_ADJ_GAP:
            pen += (MIN_ADJ_GAP - g) * 900.0
        # Too open
        if g > MAX_ADJ_GAP:
            pen += (g - MAX_ADJ_GAP) * 420.0
        # Extremely open = almost always weird
        if g > HARD_MAX_ADJ_GAP:
            pen += (g - HARD_MAX_ADJ_GAP) * 1200.0
    return pen


def bass_penalty(prev: Optional[List[int]], cur: List[int]) -> float:
    if prev is None or not prev:
        return 0.0
    b0 = min(prev)
    b1 = min(cur)
    jump = abs(b1 - b0)
    if jump <= MAX_BASS_JUMP:
        return 0.0
    return (jump - MAX_BASS_JUMP) * 260.0


def _min_assignment_move(prev: List[int], cur: List[int]) -> float:
    """
    Real voice-leading distance.
    For equal sizes: minimal assignment between voices (permutations).
    For different sizes: nearest-neighbor distance sum (stable, small n).
    """
    p = sorted(prev)
    c = sorted(cur)
    if not p or not c:
        return 0.0

    if len(p) != len(c):
        total = 0.0
        for x in c:
            total += min(abs(x - y) for y in p)
        return float(total)

    import itertools
    best = None
    for perm in itertools.permutations(c):
        s = 0.0
        for i in range(len(p)):
            s += abs(perm[i] - p[i])
        if best is None or s < best:
            best = s
    return float(best if best is not None else 0.0)


def generate_voicing_candidates(raw_notes: List[int]) -> List[List[int]]:
    """
    Candidate generation that prefers musical shapes:
    - inversions
    - controlled open voicings (shift top or bottom voices)
    - gentle recenters
    Avoids per-note octave chaos that creates weird spacing.
    """
    base = sorted(set(clamp_to_range(raw_notes)))
    n = len(base)
    if n == 0:
        return []

    candidates = set()

    def add_candidate(v):
        v = sorted(set(clamp_to_range(v)))
        if len(v) == n:
            candidates.add(tuple(v))

    # Base
    add_candidate(base)

    # Inversions
    inv = base[:]
    for _ in range(n - 1):
        inv = inv[1:] + [inv[0] + 12]
        add_candidate(inv)

    # Controlled open voicings
    for k in range(1, n):
        # shift top k up
        v1 = base[:]
        for i in range(n - k, n):
            v1[i] += 12
        add_candidate(v1)

        # shift bottom k down
        v2 = base[:]
        for i in range(0, k):
            v2[i] -= 12
        add_candidate(v2)

    # Gentle recenter variants
    for shift in (-12, 0, 12):
        add_candidate([x + shift for x in base])

    out = [list(c) for c in candidates]
    return out if out else [base]


def choose_best_voicing(
    prev_voicing: Optional[List[int]],
    prev_name: str,
    cur_name: str,
    raw_notes: List[int],
    key_name: str,
    rng: random.Random
) -> List[int]:
    raw_clamped = clamp_to_range(raw_notes)
    cands = generate_voicing_candidates(raw_notes)

    # Glue filter (optional musical color)
    filtered = [v for v in cands if glue_ok(v, rng)]
    if filtered:
        cands = filtered

    # Repair cross-semitone clashes vs previous chord
    if prev_voicing is not None:
        allowed_pcs = allowed_resolution_pcs(key_name)
        cands = [repair_cross_semitones(prev_voicing, v, allowed_pcs) for v in cands]
    # ✅ Re-filter glue AFTER repair (prevents new low semitone clusters)
    filtered = [v for v in cands if glue_ok(v, rng)]
    if filtered:
        cands = filtered
    

    # Shared pitch cap
    if prev_voicing is not None:
        limit = max_shared_allowed(prev_name, cur_name)
        filtered = [v for v in cands if shared_pitch_count(prev_voicing, v) <= limit]
        if filtered:
            cands = filtered

    def cost(v: List[int]) -> float:
        v = sorted(v)

        # Register
        reg_pen = abs(center(v) - TARGET_CENTER) * 120.0

        # Span
        sp = span(v)
        span_pen = abs(sp - IDEAL_SPAN) * 80.0
        if sp < MIN_SPAN:
            span_pen += (MIN_SPAN - sp) * 700.0
        if sp > MAX_SPAN:
            span_pen += (sp - MAX_SPAN) * 220.0

        # Internal spacing
        space_pen = spacing_penalty(v)

        # Movement (real voice-leading)
        move_pen = 0.0 if prev_voicing is None else _min_assignment_move(prev_voicing, v) * 3.2

        # Bass stability
        b_pen = bass_penalty(prev_voicing, v)

        # Avoid exact repeats
        repeat_pen = 900.0 if (prev_voicing is not None and sorted(prev_voicing) == v) else 0.0

        # Penalize raw shape when voicing is enabled
        raw_pen = 0.0
        if ENFORCE_NOT_RAW_WHEN_VOICING and is_raw_shape(v, raw_clamped):
            raw_pen = RAW_PENALTY

        # Cross-semitone leftover (hard penalty)
        cross_pen = 0.0
        if prev_voicing is not None:
            allowed_pcs = allowed_resolution_pcs(key_name)
            bad_left = len(bad_cross_semitone_indices(prev_voicing, v, allowed_pcs))
            cross_pen = bad_left * 25000.0

        return reg_pen + span_pen + space_pen + move_pen + b_pen + repeat_pen + raw_pen + cross_pen

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


def write_progression_midi(out_root: str, idx: int, chords, durations, key_name: str, revoice: bool, seed: int):
    midi = pretty_midi.PrettyMIDI(initial_tempo=BPM)
    midi.time_signature_changes = [pretty_midi.TimeSignature(TIME_SIG[0], TIME_SIG[1], 0)]
    inst = pretty_midi.Instrument(program=0)

    raw = [chord_to_midi(ch, base_oct=BASE_OCTAVE) for ch in chords]

    if revoice:
        voiced = []
        prev_v = None
        prev_name = chords[0]
        rng = random.Random(seed + idx)

        for ch_name, notes in zip(chords, raw):
            if prev_v is None:
                v = choose_best_voicing(None, ch_name, ch_name, notes, key_name, rng)
            else:
                v = choose_best_voicing(prev_v, prev_name, ch_name, notes, key_name, rng)

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

    rv_tag = "_Revoiced" if revoice else ""
    filename = f"Prog_{idx:03d}_in_{safe_token(key_name)}_{chord_list_token(chords)}{rv_tag}.mid"
    midi.write(os.path.join(out_dir, filename))


def write_single_chord_midi(out_root: str, chord_name: str, revoice: bool, length_bars=4):
    dur = length_bars * SEC_PER_BAR
    midi = pretty_midi.PrettyMIDI(initial_tempo=BPM)
    midi.time_signature_changes = [pretty_midi.TimeSignature(TIME_SIG[0], TIME_SIG[1], 0)]
    inst = pretty_midi.Instrument(program=0)

    raw = chord_to_midi(chord_name, base_oct=BASE_OCTAVE)
    if revoice:
        rng = random.Random()
        notes = choose_best_voicing(None, chord_name, chord_name, raw, "C", rng)
    else:
        notes = raw

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
    rv_tag = "_Revoiced" if revoice else ""
    midi.write(os.path.join(chords_dir, f"{safe_token(chord_name)}{rv_tag}.mid"))


def zip_pack(out_root: str, zip_path: str):
    with ZipFile(zip_path, "w") as z:
        for root, _, files in os.walk(out_root):
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, out_root)
                z.write(full, arcname=rel)


def build_pack(progressions, revoice: bool, seed: int) -> tuple[str, int, str]:
    validate_progressions(progressions)

    workdir = tempfile.mkdtemp(prefix="aa_midi_")
    prog_root = os.path.join(workdir, "Pack")
    os.makedirs(prog_root, exist_ok=True)

    unique_chords = set()
    for i, (chords, durations, key_name) in enumerate(progressions, start=1):
        write_progression_midi(prog_root, i, chords, durations, key_name, revoice=revoice, seed=seed)
        unique_chords.update(chords)

    for ch in sorted(unique_chords):
        write_single_chord_midi(prog_root, ch, revoice=revoice, length_bars=4)

    base = DOWNLOAD_NAME[:-4] if DOWNLOAD_NAME.lower().endswith(".zip") else DOWNLOAD_NAME
    final_zip_name = f"{base}_Revoiced.zip" if revoice else DOWNLOAD_NAME

    zip_path = os.path.join(workdir, final_zip_name)
    zip_pack(prog_root, zip_path)

    return zip_path, len(unique_chords), final_zip_name


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
# ADVANCED SETTINGS (UI + STATE)
# =========================================================
# DEV ONLY: disable the slider feature here (not in the UI)
ENABLE_CHORD_TYPE_SLIDERS = True

ADV_QUALITIES = [
    ("maj9", "MAJ9"), ("maj7", "MAJ7"), ("add9", "ADD9"), ("6add9", "6ADD9"), ("6", "6"), ("maj", "MAJ"),
    ("min9", "MIN9"), ("min7", "MIN7"), ("min11", "MIN11"), ("min", "MIN"),
    ("sus2add9", "SUS2ADD9"), ("sus4add9", "SUS4ADD9"), ("sus2", "SUS2"), ("sus4", "SUS4"),
]


def ensure_adv_defaults():
    if not (ENABLE_CHORD_BALANCE_FEATURE and ENABLE_CHORD_TYPE_SLIDERS):
        return
    for qual, _ in ADV_QUALITIES:
        st.session_state.setdefault(f"{ADV_KEY_PREFIX}{qual}", ADV_DEFAULT_VALUE)


def read_adv_balance() -> Optional[Dict[str, int]]:
    if not (ENABLE_CHORD_BALANCE_FEATURE and ENABLE_CHORD_TYPE_SLIDERS):
        return None
    out = {}
    for qual, _ in ADV_QUALITIES:
        out[qual] = int(st.session_state.get(f"{ADV_KEY_PREFIX}{qual}", ADV_DEFAULT_VALUE))
    return out


def reset_adv_defaults():
    if not (ENABLE_CHORD_BALANCE_FEATURE and ENABLE_CHORD_TYPE_SLIDERS):
        return
    for qual, _ in ADV_QUALITIES:
        st.session_state[f"{ADV_KEY_PREFIX}{qual}"] = ADV_DEFAULT_VALUE


# =========================================================
# HERO
# =========================================================
st.markdown(
    f"""
<div class="aa-hero">
  <div class="aa-title">
    {APP_TITLE_LINE1}<br>
    <span class="aa-title-second">{APP_TITLE_LINE2}</span>
  </div>
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
        help="Generates a balanced mix of 4, 8, and 16-bar chord loops in different keys.",
    )
    seed_input = st.text_input(
        "Seed (optional)",
        value="",
        help="Enter a number to regenerate the exact same result."
    )

    revoice = st.toggle(
        "Re-Voicing",
        value=False,
        help="Repositions the notes within each chord for smoother movement and a more original sound.",
    )

    # ADVANCED SETTINGS UI (single render, no duplicates)
    if ENABLE_CHORD_BALANCE_FEATURE and ENABLE_CHORD_TYPE_SLIDERS:
        ensure_adv_defaults()

        with st.expander("ADVANCED SETTINGS", expanded=False):
            st.caption("Chord type balance: 0 disables. 50 is default. 100 strongly favors.")
        
            cL, cM, cR = st.columns([1, 2, 1])
            with cM:
                if st.button("Default", use_container_width=False, key="aa_reset_defaults"):
                    reset_adv_defaults()
                    st.rerun()

            st.markdown("### MAJOR FAMILY")
            c1, c2 = st.columns(2)
            majors = [x for x in ADV_QUALITIES if x[0] in ("maj9","maj7","add9","6add9","6","maj")]
            for i, (qual, label) in enumerate(majors):
                with (c1 if i % 2 == 0 else c2):
                    st.slider(label, 0, 100, key=f"{ADV_KEY_PREFIX}{qual}")

            st.markdown("### MINOR FAMILY")
            c1, c2 = st.columns(2)
            minors = [x for x in ADV_QUALITIES if x[0] in ("min9","min7","min11","min")]
            for i, (qual, label) in enumerate(minors):
                with (c1 if i % 2 == 0 else c2):
                    st.slider(label, 0, 100, key=f"{ADV_KEY_PREFIX}{qual}")

            st.markdown("### SUS FAMILY")
            c1, c2 = st.columns(2)
            suss = [x for x in ADV_QUALITIES if x[0] in ("sus2add9","sus4add9","sus2","sus4")]
            for i, (qual, label) in enumerate(suss):
                with (c1 if i % 2 == 0 else c2):
                    st.slider(label, 0, 100, key=f"{ADV_KEY_PREFIX}{qual}")

    generate_clicked = st.button("Generate Progressions", use_container_width=True)


# =========================================================
# RUN GENERATION
# =========================================================
if generate_clicked:
    try:
        with st.spinner("Generating progressions…"):
            if seed_input.strip().isdigit():
                seed = int(seed_input)
            else:
                seed = int(np.random.randint(1, 2_000_000_000))

            chord_balance = read_adv_balance() if ENABLE_CHORD_BALANCE_FEATURE else None

            progressions, pattern_dupe_used, pattern_dupe_max, low_sim_total, qual_usage = generate_progressions(
                n=int(n_progressions),
                seed=seed,
                chord_balance=chord_balance,
            )

            if low_sim_total != 0:
                raise RuntimeError("Safety check failed: low-sim transitions detected.")

            zip_path, chord_count, final_zip_name = build_pack(progressions, revoice=bool(revoice), seed=seed)

            st.session_state["progressions"] = progressions
            st.session_state["zip_path"] = zip_path
            st.session_state["progression_count"] = len(progressions)
            st.session_state["chord_count"] = chord_count
            st.session_state["final_zip_name"] = final_zip_name

        st.markdown(
            """
            <div class="aa-ready-wrap">
              <div class="aa-ready-badge"><span class="aa-ready-dot"></span>READY</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    except Exception as e:
        st.session_state.pop("zip_path", None)
        st.session_state.pop("progressions", None)
        st.session_state["progression_count"] = 0
        st.session_state["chord_count"] = 0
        st.error(f"Error: {e}")


# =========================================================
# SUMMARY + DOWNLOAD + TABLE
# =========================================================
if "progressions" in st.session_state and st.session_state.get("zip_path"):
    a, b = st.columns(2)
    a.metric("Progressions Generated", int(st.session_state.get("progression_count", 0)))
    b.metric("Individual Chords Generated", int(st.session_state.get("chord_count", 0)))

    try:
        with open(st.session_state["zip_path"], "rb") as f:
            zip_bytes = f.read()

        st.download_button(
            label="Download MIDI Progressions",
            data=zip_bytes,
            file_name=st.session_state.get("final_zip_name", DOWNLOAD_NAME),
            mime="application/zip",
            use_container_width=True,
        )
    except Exception as e:
        st.error(f"Could not read ZIP for download: {e}")

    rows = make_rows(st.session_state["progressions"])
    df = pd.DataFrame(rows)

    st.markdown("### Progressions List")
    st.dataframe(df, use_container_width=True, hide_index=True)





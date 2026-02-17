# app.py  Aural Alchemy | Endless Ambient MIDI Progressions
# Streamlit app (standalone) that:
# - Generates diatonic, loop-safe ambient chord progressions
# - Exports a ZIP containing: Progressions (4/8/16-bar folders) + Individual Chords library
# - Optional Re-Voicing (inversions/voicing engine)
# - Premium UI styling (Cinzel font everywhere, cyan slider, gold shimmer button, soft glows)
# - Sacred geometry overlay (two layers + slow rotation)
# - ADVANCED: Chord Type Balance sliders (optional, can be disabled via flag)
# - ADVANCED: Reset sliders to default (50)
# - ADVANCED: Voicing Profile selector (Default / Tight / Wide / Deep Low Ambient)
# - BANLIST: Upload a .txt with progressions to exclude (ordered match, start matters)
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
ENABLE_CHORD_BALANCE_FEATURE = True
ENABLE_CHORD_TYPE_SLIDERS = True


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

/* Restore Streamlit/BaseWeb icon fonts (prevents ARROW_* text showing) */
[data-baseweb="icon"], 
[data-baseweb="icon"] *,
svg, svg * {
  font-family: "Material Icons", "Material Symbols Outlined", system-ui, sans-serif !important;
  letter-spacing: 0 !important;
  text-transform: none !important;
}

/* Page background */
.stApp {
  background:
    radial-gradient(1200px 700px at 20% 15%, rgba(0,229,255,0.10), rgba(0,0,0,0) 60%),
    radial-gradient(1200px 700px at 85% 20%, rgba(255,215,0,0.08), rgba(0,0,0,0) 60%),
    radial-gradient(900px 600px at 50% 85%, rgba(160,120,255,0.06), rgba(0,0,0,0) 65%),
    linear-gradient(180deg, #070A10 0%, #07080E 35%, #05060A 100%);
}

/* =========================================================
   GEOMETRY OVERLAY (two layers + slow rotation)
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

/* Button */
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

/* Fix expander header glitch */
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary *{
  letter-spacing: 0px !important;
  text-transform: none !important;
  line-height: 1.25 !important;
}

/* Fix slider tooltip numbers splitting vertically */
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
# BANLIST (TXT UPLOAD) - SMART EXTRACTOR + ordered matching
# Extracts chord progressions from messy txt (headers, notes, bullets)
# Start matters (ordered match) by default
# =========================================================
BANLIST_STATE_KEY = "aa_banlist_v2"  # bump to avoid stale session_state issues


def _norm_dash(s: str) -> str:
    # Normalize different dash chars to "-"
    return (s or "").replace("–", "-").replace("—", "-").replace("−", "-")


def _normalize_quality(q: str) -> str:
    q = (q or "").strip().replace(" ", "")
    q = q.replace("6/9", "6add9").replace("6\\9", "6add9")
    q_low = q.lower()

    # maj6 -> 6
    if q_low in ("maj6", "ma6"):
        return "6"

    # keep maj* as-is
    if q_low.startswith("maj"):
        return q_low

    # m shorthand
    if q_low == "m":
        return "min"

    # m7/m9/m11 shorthand
    if q_low.startswith("m") and len(q_low) > 1 and q_low[1].isdigit():
        return "min" + q_low[1:]

    # min* already ok
    if q_low.startswith("min"):
        return q_low

    # sus / add9 / 6 / 6add9 etc
    return q_low


def _normalize_chord_token(tok: str) -> str:
    """
    Normalizes a chord token like:
      'C min7' -> 'Cmin7'
      'Bb 6/9' -> 'Bb6add9'
    Returns "" if invalid.
    """
    t = (tok or "").strip()
    if not t:
        return ""

    t = _norm_dash(t)
    t = t.replace(" ", "")
    t = t.replace("6/9", "6add9").replace("6\\9", "6add9")
    t = re.sub(r"[,\.;]+$", "", t)

    m = re.match(r"^([A-G](?:#|b)?)(.*)$", t)
    if not m:
        return ""

    root = m.group(1)
    rest = m.group(2)

    # normalize root case (C, Db, F#)
    root = root[0].upper() + (root[1:] if len(root) > 1 else "")
    if root not in NOTE_TO_PC:
        return ""

    qual = _normalize_quality(rest)
    if qual not in QUAL_TO_INTERVALS:
        return ""

    return f"{root}{qual}"


def _is_meta_line(line: str) -> bool:
    """
    Optional: keep meta skipping for common headers,
    but smart extraction would ignore them anyway.
    """
    s = (line or "").strip()
    if not s:
        return False

    s_up = s.upper()

    # PACK headers
    if re.match(r"^PACK\s*\d+\s*$", s_up) or s_up.startswith("PACK"):
        return True

    # bar section headers
    if s_up in ("4-BAR", "8-BAR", "16-BAR"):
        return True
    if re.match(r"^\s*(4|8|16)\s*-\s*BAR\s*$", s_up):
        return True

    return False


# ---------------------------------------------------------
# SMART CHORD EXTRACTION
# ---------------------------------------------------------
def _build_quality_regex() -> str:
    # Longest first to avoid partial matches (sus2add9 before sus2, etc)
    quals_sorted = sorted(list(QUAL_TO_INTERVALS.keys()), key=len, reverse=True)
    return r"(?:%s)" % "|".join(re.escape(q) for q in quals_sorted)


_QUAL_REGEX = _build_quality_regex()

# Finds chords anywhere: Root + optional accidental + quality
# Examples it catches: Cmin7, Dbmaj9, F#sus2add9, Bb6add9, Gadd9, Amin
_CHORD_TOKEN_RE = re.compile(
    rf"\b([A-G])([#b]?)\s*({_QUAL_REGEX})\b",
    flags=re.IGNORECASE
)


def _extract_chords_anywhere(line: str) -> List[str]:
    """
    Extract valid chords from messy text.
    Returns normalized chord tokens like ['Cmin7','Fsus2','Bbmaj7'].
    """
    s = _norm_dash(line or "")
    s = s.replace("6/9", "6add9").replace("6\\9", "6add9")

    out: List[str] = []
    for m in _CHORD_TOKEN_RE.finditer(s):
        root = (m.group(1) + m.group(2)).replace(" ", "")
        qual = (m.group(3) or "").replace(" ", "")

        token = _normalize_chord_token(f"{root}{qual}")
        if token:
            out.append(token)

    # collapse immediate duplicates while keeping order
    if out:
        dedup = [out[0]]
        for c in out[1:]:
            if c != dedup[-1]:
                dedup.append(c)
        out = dedup

    return out


def _extract_progressions_from_line(line: str) -> List[Tuple[str, ...]]:
    """
    Simple heuristic:
    If a line contains 2+ valid chords, treat the full sequence as one progression.
    """
    chords = _extract_chords_anywhere(line)
    if len(chords) >= 2:
        return [tuple(chords)]
    return []


def load_banlist_from_txt_bytes(data: bytes) -> Tuple[set, Dict[str, int], List[str]]:
    """
    Smarter loader:
    - Scans each line and extracts chords anywhere in the text
    - Stores progressions with 2+ chords
    - Ignores the rest automatically
    """
    try:
        text = data.decode("utf-8", errors="ignore")
    except Exception:
        text = str(data)

    banned_set: set = set()
    stats = {
        "added": 0,
        "invalid": 0,
        "empty": 0,
        "ignored_meta": 0,
        "lines_with_chords": 0,
    }
    bad_examples: List[str] = []

    for raw in text.splitlines():
        line = (raw or "").strip()
        if not line:
            stats["empty"] += 1
            continue

        if _is_meta_line(line):
            stats["ignored_meta"] += 1
            continue

        progs = _extract_progressions_from_line(line)
        if not progs:
            # If it looks like it tried to be chords but we couldn't parse, log it.
            low = line.lower()
            looks_chordish = any(x in low for x in ("maj", "min", "sus", "add", "6"))
            has_note_letter = re.search(r"\b[A-G][#b]?\b", line) is not None
            if looks_chordish and has_note_letter:
                stats["invalid"] += 1
                if len(bad_examples) < 10:
                    bad_examples.append(line[:160])
            continue

        stats["lines_with_chords"] += 1
        for prog in progs:
            if len(prog) >= 2:
                banned_set.add(tuple(prog))
                stats["added"] += 1
            else:
                stats["invalid"] += 1

    return banned_set, stats, bad_examples


def progression_is_banned(chords: List[str], banned_set: set) -> bool:
    """
    ORDERED match (start matters).
    """
    if not banned_set or not chords:
        return False

    norm = tuple(_normalize_chord_token(c) for c in chords)
    if any(not x for x in norm):
        return False

    return norm in banned_set



# =========================================================
# GENERATOR SETTINGS
# =========================================================
PATTERN_MAX_REPEATS = 1
MAX_PATTERN_DUPLICATE_RATIO = 0.01

TOTAL_BARS_DISTRIBUTION = {8: 0.40, 4: 0.35, 16: 0.25}
CHORDCOUNT_DISTRIBUTION = {4: 0.40, 3: 0.35, 2: 0.20, 5: 0.03, 6: 0.02}

LIMIT_NOTECOUNT_JUMPS = True
MAX_BIG_JUMPS_PER_PROG = 1

MIN_SHARED_TONES = 1
ENFORCE_LOOP_OK = True
MAX_TRIES_PER_PROG = 40000

# Pools (main control for maj/min/sus flavor)
MAJ_POOL_BASE = [("maj9", 10), ("maj7", 9), ("add9", 7), ("6add9", 5), ("6", 4), ("maj", 3)]
MIN_POOL_BASE = [("min9", 10), ("min7", 9), ("min11", 4), ("min", 3)]
SUS_POOL_BASE = [("sus2add9", 1), ("sus4add9", 1), ("sus2", 2), ("sus4", 2)]

SAFE_FALLBACK_ORDER = [
    "maj9", "maj7", "add9", "6add9", "6",
    "min9", "min7", "min11",
    "maj", "min",
    "sus2add9", "sus4add9", "sus2", "sus4"
]

TEMPLATES_BY_LEN = {
    2: [((0, 3), 10), ((0, 5), 7), ((5, 3), 5), ((3, 0), 4), ((0, 4), 3)],
    3: [
        ((0, 5, 3), 14), ((0, 3, 4), 12), ((0, 3, 5), 10), ((0, 5, 4), 9),
        ((0, 2, 3), 7), ((0, 2, 5), 6), ((3, 5, 0), 5), ((5, 3, 0), 5),
        ((0, 1, 3), 3), ((0, 6, 3), 2),
    ],
    4: [
        ((0, 5, 3, 4), 18), ((0, 5, 3, 0), 12), ((0, 3, 4, 3), 12), ((0, 3, 5, 3), 12),
        ((0, 2, 5, 3), 10), ((0, 2, 3, 4), 10), ((0, 1, 3, 4), 6), ((0, 1, 3, 0), 5),
        ((5, 3, 4, 0), 5), ((3, 4, 0, 5), 4), ((0, 4, 3, 5), 4),
    ],
    5: [((0, 5, 3, 4, 3), 4), ((0, 3, 0, 5, 3), 3), ((0, 2, 3, 4, 3), 3)],
    6: [((0, 5, 3, 4, 3, 0), 3), ((0, 3, 0, 5, 3, 0), 3)],
}


def _pick_template_degs(rng: random.Random, m: int) -> list:
    return list(_wchoice(rng, TEMPLATES_BY_LEN[m]))


DURATIONS = {
    (2, 4): [([2, 2], 10)],
    (3, 4): [([2, 1, 1], 10), ([1, 1, 2], 8)],
    (4, 4): [([1, 1, 1, 1], 12)],

    (2, 8): [([4, 4], 12)],
    (3, 8): [([4, 2, 2], 10), ([2, 2, 4], 9), ([2, 4, 2], 2), ([3, 3, 2], 1)],
    (4, 8): [([2, 2, 2, 2], 12), ([4, 2, 1, 1], 1), ([2, 1, 1, 4], 1), ([1, 1, 2, 4], 0), ([4, 1, 1, 2], 1)],
    (5, 8): [([2, 2, 2, 1, 1], 3), ([1, 2, 2, 2, 1], 1), ([2, 1, 2, 1, 2], 7), ([2, 2, 1, 2, 1], 3)],
    (6, 8): [([2, 1, 1, 2, 1, 1], 5), ([1, 1, 1, 1, 2, 2], 1), ([1, 1, 2, 1, 1, 2], 4), ([2, 1, 2, 1, 1, 1], 3)],

    (2, 16): [([8, 8], 8)],
    (3, 16): [([8, 4, 4], 4), ([4, 4, 8], 3), ([6, 6, 4], 3)],
    (4, 16): [([4, 4, 4, 4], 12), ([6, 4, 4, 2], 4)],
    (5, 16): [([4, 4, 4, 2, 2], 3), ([2, 2, 4, 4, 4], 3), ([4, 2, 4, 2, 4], 7), ([2, 4, 4, 4, 2], 3)],
    (6, 16): [([4, 2, 2, 4, 2, 2], 5), ([4, 2, 2, 2, 2, 4], 4), ([2, 4, 2, 4, 2, 2], 5)],
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
# =========================================================
STRICT_SLIDERS = True

ADV_ALL_QUALITIES = [
    "maj9", "maj7", "add9", "6add9", "6", "maj",
    "min9", "min7", "min11", "min",
    "sus2add9", "sus4add9", "sus2", "sus4",
]
ADV_DEFAULT_VALUE = 50
ADV_KEY_PREFIX = "aa_adv_v1_"


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
        return ADV_ALL_QUALITIES[:]
    return [q for q in ADV_ALL_QUALITIES if int(balance.get(q, ADV_DEFAULT_VALUE)) > 0]


def _build_deg_allowed(balance: Optional[Dict[str, int]], key: str) -> Dict[int, List[Tuple[str, float]]]:
    enabled = _enabled_qualities(balance)

    if STRICT_SLIDERS and balance and len(enabled) == 0:
        raise RuntimeError("All chord-type sliders are 0. Enable at least one chord type.")

    out: Dict[int, List[Tuple[str, float]]] = {}
    for deg in range(7):
        root = SCALES[key][deg]
        items: List[Tuple[str, float]] = []

        for q in enabled:
            if _is_diatonic_chord(key, root, q):
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


def _build_progression(rng: random.Random, key: str, degs: list, total_bars: int, deg_allowed, chord_balance):
    quals = []
    for d in degs:
        q = _pick_quality_diatonic(rng, key, d, deg_allowed=deg_allowed)
        if q is None:
            return None
        quals.append(q)

    def is_sus(q: str) -> bool:
        return q.startswith("sus")

    sus_allowed_start = False
    if chord_balance:
        sus_keys = ["sus2", "sus4", "sus2add9", "sus4add9"]
        if any(chord_balance.get(k, ADV_DEFAULT_VALUE) > 80 for k in sus_keys):
            sus_allowed_start = True

    if is_sus(quals[0]) and not sus_allowed_start:
        return None

    ded = _dedupe_inside_progression(rng, key, degs[:], quals[:])
    if ded is None:
        return None
    degs, quals = ded

    roots = [SCALES[key][d] for d in degs]

    if any(not _is_diatonic_chord(key, r, q) for r, q in zip(roots, quals)):
        return None

    if not _shared_tone_ok_loop(roots, quals, need=MIN_SHARED_TONES, loop=True):
        return None

    # SUS SAFETY SYSTEM
    sus_keys = ["sus2", "sus4", "sus2add9", "sus4add9"]
    avg_sus_weight = 1.0
    if chord_balance:
        vals = [_balance_factor(chord_balance.get(k, ADV_DEFAULT_VALUE)) for k in sus_keys]
        avg_sus_weight = sum(vals) / len(vals)
    sus_heavy = avg_sus_weight >= 1.35

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

    DEFAULT_SUS_MAX_RATIO = 0.45
    DEFAULT_SUS4_MAX_COUNT = 1
    DEFAULT_NEED_IF_SUS = 2
    DEFAULT_NEED_IF_SUS4 = 3

    HEAVY_NEED = 2
    HEAVY_NEED_IF_SUS4 = 3
    HEAVY_REQUIRE_STEP_OR_REPEAT = True

    ALLOW_SUS4_TO_SUS4_IF_SAFE = True

    if not sus_heavy:
        if sus_count / max(1, m) > DEFAULT_SUS_MAX_RATIO:
            return None
        if sus4_count > DEFAULT_SUS4_MAX_COUNT:
            return None

    step_moves = 0
    has_repeat_root = (len(set(root_pcs)) < len(root_pcs))

    for i in range(m):
        j = (i + 1) % m

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


def generate_progressions(
    n: int,
    seed: int,
    chord_balance: Optional[Dict[str, int]] = None,
    ban_set: Optional[set] = None,
):
    rng = random.Random(seed)
    keys = _pick_keys_even(n, rng)

    max_pattern_dupes = int(math.floor(n * MAX_PATTERN_DUPLICATE_RATIO))
    pattern_dupe_used = 0

    used_exact = set()
    pattern_counts = Counter()
    low_sim_total = 0
    qual_usage = Counter()

    out = []
    ban_set = ban_set or set()

    for i in range(n):
        key = keys[i]
        deg_allowed = _build_deg_allowed(chord_balance, key)
        built = None

        for _ in range(MAX_TRIES_PER_PROG):
            total_bars, m = _pick_valid_total_and_m(rng)
            degs = _pick_template_degs(rng, m)

            res = _build_progression(
                rng,
                key,
                degs,
                total_bars,
                deg_allowed=deg_allowed,
                chord_balance=chord_balance
            )
            if res is None:
                continue

            chords, durs, _k, degs_used, quals_used = res

            if ban_set and progression_is_banned(chords, ban_set):
                continue

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
# EDIT FRIENDLY "ONE PLACE" FOR OCTAVE / RANGE / VOICING
# =========================================================
# MIDI note reference:
# C2=36, E2=40, C3=48, E3=52, C4=60
VOICING_PROFILE_KEY = "aa_voicing_profile_v1"

VOICING_PROFILES = {
    # You can change these numbers anytime.
    "Default": {
        "global_low": 33,      # allow deep lows in engine; penalties keep it safe
        "global_high": 84,

        "bass_soft_min": 40,   # preferred bass zone (E2)
        "bass_soft_max": 52,   # (E3)
        "bass_hard_min": 36,   # hard floor (C2)
        "bass_hard_max": 60,   # hard ceiling (G3-ish)
        "bass_center": 46,     # gravity center for bass (Bb2)
        "max_bass_jump": 7,    # semitones

        "target_center": 60.0, # chord register center (C4)
        "ideal_span": 12,
        "min_span": 8,
        "max_span": 18,

        "min_adj_gap": 2,
        "max_adj_gap": 9,
        "hard_max_adj_gap": 12,

        "max_register_jump": 7,  # whole-chord center jump between chords (semitones)
    },
    "Tight": {
        "global_low": 33,
        "global_high": 84,

        "bass_soft_min": 41,
        "bass_soft_max": 52,
        "bass_hard_min": 38,
        "bass_hard_max": 55,
        "bass_center": 47,
        "max_bass_jump": 6,

        "target_center": 60.0,
        "ideal_span": 9,
        "min_span": 7,
        "max_span": 14,

        "min_adj_gap": 2,
        "max_adj_gap": 7,
        "hard_max_adj_gap": 10,

        "max_register_jump": 6,
    },
    "Wide": {
        "global_low": 33,
        "global_high": 84,

        "bass_soft_min": 40,
        "bass_soft_max": 52,
        "bass_hard_min": 36,
        "bass_hard_max": 55,
        "bass_center": 46,
        "max_bass_jump": 7,

        "target_center": 62.0,
        "ideal_span": 16,
        "min_span": 10,
        "max_span": 22,

        "min_adj_gap": 2,
        "max_adj_gap": 11,
        "hard_max_adj_gap": 14,

        "max_register_jump": 8,
    },
    "Deep Low Ambient": {
        "global_low": 33,
        "global_high": 84,

        "bass_soft_min": 36,  # C2
        "bass_soft_max": 48,  # C3
        "bass_hard_min": 33,  # A1-ish rare
        "bass_hard_max": 52,  # E3
        "bass_center": 42,    # F#2
        "max_bass_jump": 5,

        "target_center": 58.0,
        "ideal_span": 12,
        "min_span": 8,
        "max_span": 18,

        "min_adj_gap": 2,
        "max_adj_gap": 9,
        "hard_max_adj_gap": 12,

        "max_register_jump": 6,
    },
}


def get_voicing_profile_name() -> str:
    name = st.session_state.get(VOICING_PROFILE_KEY, "Default")
    return name if name in VOICING_PROFILES else "Default"


def get_voicing_profile() -> dict:
    return VOICING_PROFILES[get_voicing_profile_name()]


# =========================================================
# CHORD -> MIDI + VOICING ENGINE (HARD-SAFE, NO SUB-FLOOR)
# (PATCH: DEFAULT = VOICE-LED TIGHT, + WIDE + LOW MODES)
# =========================================================

NOTE_TO_SEMITONE = NOTE_TO_PC.copy()

# -------------------------
# HARD GLOBAL PITCH LIMITS
# -------------------------
ABS_NOTE_FLOOR = 40
ABS_NOTE_CEIL  = 88

BASS_PREF_MIN = 40
BASS_PREF_MAX = 52

BASS_HARD_MIN = ABS_NOTE_FLOOR
BASS_HARD_MAX = 60

MAX_BASS_JUMP = 7

TARGET_CENTER = 60.0

IDEAL_SPAN = 12
MIN_SPAN   = 8
MAX_SPAN   = 18

MIN_ADJ_GAP = 2
MAX_ADJ_GAP = 9
HARD_MAX_ADJ_GAP = 12

MAX_SHARED_DEFAULT = 2
MAX_SHARED_MIN11   = 3

ENFORCE_NOT_RAW_WHEN_VOICING = True
RAW_PENALTY = 1200

GLUE_LOW_CUTOFF  = 44
GLUE_PROBABILITY = 0.35

ALLOW_RESOLVE_TO_THIRD = True
ALLOW_RESOLVE_TO_FIFTH = False


# -------------------------
# NEW: VOICING MODES
# -------------------------
# Default is the new "tight voice-leading melt" behavior.
VOICING_MODE = "default"  # "default" | "wide" | "low"

# A profile is just weights + range targets for scoring.
# Movement dominates in default/low, less so in wide.
VOICING_PROFILES = {
    "default": dict(
        lo=48, hi=76,
        target_center=60.0,
        ideal_span=12, min_span=8, max_span=18,
        w_move=220.0,         # BIG: minimize total motion hard
        w_leap=260.0,         # punish big single-voice jumps
        w_center=70.0,        # mild register pull
        w_span=55.0,          # keep compact
        w_top=35.0,           # avoid too-bright top
        w_shared_bonus=180.0  # reward shared pitch classes
    ),
    "wide": dict(
        lo=48, hi=88,
        target_center=66.0,
        ideal_span=18, min_span=10, max_span=28,
        w_move=95.0,          # less strict motion
        w_leap=120.0,
        w_center=55.0,
        w_span=25.0,          # allow wider
        w_top=10.0,           # allow brighter top
        w_shared_bonus=70.0
    ),
    "low": dict(
        lo=40, hi=72,
        target_center=54.0,
        ideal_span=12, min_span=8, max_span=18,
        w_move=240.0,         # same melt, even stricter
        w_leap=300.0,
        w_center=120.0,       # strong pull lower
        w_span=60.0,
        w_top=110.0,          # strong anti-brightness
        w_shared_bonus=200.0
    ),
}


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


def _force_into_range_by_octaves(p: int, lo: int, hi: int) -> int:
    while p < lo:
        p += 12
    while p > hi:
        p -= 12
    return int(p)


def _sanitize_notes_strict(notes: List[int]) -> List[int]:
    v = [int(x) for x in notes]
    out = []
    used = set()
    for p in sorted(v):
        p = _force_into_range_by_octaves(p, ABS_NOTE_FLOOR, ABS_NOTE_CEIL)

        while p in used and (p + 12) <= ABS_NOTE_CEIL:
            p += 12
        while p in used and (p - 12) >= ABS_NOTE_FLOOR:
            p -= 12

        used.add(p)
        out.append(p)

    out = sorted(out)

    if out and min(out) < ABS_NOTE_FLOOR:
        shift = 0
        while min(out) + shift < ABS_NOTE_FLOOR:
            shift += 12
        out = [p + shift for p in out]
        out = [min(p, ABS_NOTE_CEIL) for p in out]
        out = sorted(set(out))
        out = sorted([_force_into_range_by_octaves(p, ABS_NOTE_FLOOR, ABS_NOTE_CEIL) for p in out])

    return out


def _prefer_bass_zone(notes: List[int]) -> List[int]:
    if not notes:
        return notes

    v = sorted(notes)
    pref_center = (BASS_PREF_MIN + BASS_PREF_MAX) / 2.0
    options = []
    for k in range(-4, 5):
        vv = [p + 12 * k for p in v]
        if min(vv) < ABS_NOTE_FLOOR or max(vv) > ABS_NOTE_CEIL:
            continue
        bb = min(vv)
        if bb < BASS_HARD_MIN or bb > BASS_HARD_MAX:
            continue

        dist = 0.0
        if bb < BASS_PREF_MIN:
            dist += (BASS_PREF_MIN - bb) * 25.0
        elif bb > BASS_PREF_MAX:
            dist += (bb - BASS_PREF_MAX) * 25.0
        dist += abs(bb - pref_center) * 2.0
        options.append((dist, vv))

    if options:
        options.sort(key=lambda x: x[0])
        v = options[0][1]

    return _sanitize_notes_strict(v)


def chord_to_midi(chord_name: str, base_oct=3) -> List[int]:
    root, rest, bass = parse_root_and_bass(chord_name)

    if root not in NOTE_TO_SEMITONE:
        raise ValueError(f"Bad root '{root}' in '{chord_name}'")

    quality = rest.lower()
    if quality not in QUAL_TO_INTERVALS:
        raise ValueError(f"Unrecognized chord quality: {rest}")

    root_pc = NOTE_TO_SEMITONE[root]
    root_midi = 12 * (base_oct + 1) + root_pc

    tones = QUAL_TO_INTERVALS[quality]
    notes = [root_midi + iv for iv in tones]

    if bass:
        if bass not in NOTE_TO_SEMITONE:
            raise ValueError(f"Bad slash bass '{bass}' in '{chord_name}'")
        bass_pc = NOTE_TO_SEMITONE[bass]
        bass_midi = 12 * (base_oct + 1) + bass_pc
        notes = [bass_midi] + notes

    notes = _sanitize_notes_strict(notes)
    notes = _prefer_bass_zone(notes)
    return notes


def span(notes: List[int]) -> int:
    return int(max(notes) - min(notes)) if notes else 0


def center(notes: List[int]) -> float:
    return (min(notes) + max(notes)) / 2.0 if notes else TARGET_CENTER


def adjacent_gaps(notes: List[int]) -> List[int]:
    v = sorted(notes)
    return [v[i + 1] - v[i] for i in range(len(v) - 1)] if len(v) >= 2 else []


def semitone_pairs(notes: List[int]):
    s = sorted(set(notes))
    return [(s[i], s[i + 1]) for i in range(len(s) - 1) if (s[i + 1] - s[i]) == 1]


def glue_ok(notes: List[int], rng: random.Random) -> bool:
    pairs = semitone_pairs(notes)
    if not pairs:
        return True
    for a, b in pairs:
        if a < GLUE_LOW_CUTOFF or b < GLUE_LOW_CUTOFF:
            return False
    return rng.random() < GLUE_PROBABILITY


def shared_pitch_count(a: List[int], b: List[int]) -> int:
    return len(set(a) & set(b))


def is_min11_name(ch_name: str) -> bool:
    return ("min11" in ch_name.replace(" ", "").lower())


def max_shared_allowed(prev_name: str, cur_name: str) -> int:
    return MAX_SHARED_MIN11 if (is_min11_name(prev_name) or is_min11_name(cur_name)) else MAX_SHARED_DEFAULT


def is_raw_shape(v: List[int], raw_notes: List[int]) -> bool:
    return sorted(v) == sorted(raw_notes)


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
                if n2 < ABS_NOTE_FLOOR or n2 > ABS_NOTE_CEIL:
                    continue
                if n2 in v:
                    continue
                test = v[:]
                test[idx] = n2
                test = sorted(test)
                remaining = len(bad_cross_semitone_indices(prev_notes, test, allowed_target_pcs))
                options.append((remaining, abs(center(test) - TARGET_CENTER), span(test),
                                abs(min(test) - ((BASS_PREF_MIN + BASS_PREF_MAX) / 2.0)), test))
            if options:
                options.sort(key=lambda x: (x[0], x[1], x[2], x[3]))
                v = options[0][4]
                changed_any = True

        if not changed_any:
            break

    return _sanitize_notes_strict(v)


def spacing_penalty(notes: List[int]) -> float:
    gaps = adjacent_gaps(notes)
    pen = 0.0
    for g in gaps:
        if g < MIN_ADJ_GAP:
            pen += (MIN_ADJ_GAP - g) * 900.0
        if g > MAX_ADJ_GAP:
            pen += (g - MAX_ADJ_GAP) * 420.0
        if g > HARD_MAX_ADJ_GAP:
            pen += (g - HARD_MAX_ADJ_GAP) * 1200.0
    return pen


def bass_penalty(prev: Optional[List[int]], cur: List[int]) -> float:
    if not prev:
        return 0.0
    b0 = min(prev)
    b1 = min(cur)
    jump = abs(b1 - b0)
    if jump <= MAX_BASS_JUMP:
        return 0.0
    return (jump - MAX_BASS_JUMP) * 260.0


def _min_assignment_move(prev: List[int], cur: List[int]) -> float:
    # Stable matching: sort both. (Permutation solver is expensive and overkill here.)
    p = sorted(prev)
    c = sorted(cur)
    if not p or not c:
        return 0.0
    m = min(len(p), len(c))
    return float(sum(abs(c[i] - p[i]) for i in range(m)))


def _shared_pc_count(prev: List[int], cur: List[int]) -> int:
    return len(set([n % 12 for n in prev]) & set([n % 12 for n in cur]))


def _max_single_leap(prev: List[int], cur: List[int]) -> int:
    p = sorted(prev)
    c = sorted(cur)
    m = min(len(p), len(c))
    if m == 0:
        return 0
    return int(max(abs(c[i] - p[i]) for i in range(m)))


def generate_voicing_candidates(raw_notes: List[int], mode: str) -> List[List[int]]:
    """
    Generates candidates and lets the scoring decide.
    Still:
    - never below ABS_NOTE_FLOOR
    - never above ABS_NOTE_CEIL
    - bass must remain inside hard clamp
    """
    prof = VOICING_PROFILES.get(mode, VOICING_PROFILES["default"])

    base = _sanitize_notes_strict(raw_notes)
    n = len(base)
    if n == 0:
        return []

    candidates = set()

    def add(v):
        v = _sanitize_notes_strict(v)
        if len(v) != n:
            return
        b = min(v)
        if b < BASS_HARD_MIN or b > BASS_HARD_MAX:
            return
        if min(v) < ABS_NOTE_FLOOR or max(v) > ABS_NOTE_CEIL:
            return
        candidates.add(tuple(sorted(v)))

    # Start from base, register into bass zone
    add(_prefer_bass_zone(base))

    # Inversions + octave placement
    inv = base[:]
    for _ in range(n - 1):
        inv = inv[1:] + [inv[0] + 12]
        add(_prefer_bass_zone(inv))

    # Whole chord octave shifts (more options for wide/low via profile range)
    for shift in (-24, -12, 0, 12, 24):
        v = [x + shift for x in base]
        v = _sanitize_notes_strict(v)
        # keep within profile range loosely (scoring will do the rest)
        if v and (min(v) < prof["lo"] - 12 or max(v) > prof["hi"] + 12):
            continue
        add(_prefer_bass_zone(v))

    # Spread variants
    # Default/low: mild spread only. Wide: allow more.
    max_k = min(2, n - 1) if mode in ("default", "low") else min(3, n - 1)
    for k in range(1, max_k + 1):
        v_up = base[:]
        for i in range(n - k, n):
            v_up[i] += 12
        add(_prefer_bass_zone(v_up))

        v_dn = base[:]
        for i in range(0, k):
            v_dn[i] -= 12
        add(_prefer_bass_zone(v_dn))

    out = [list(c) for c in candidates]
    return out if out else [_prefer_bass_zone(base)]


def choose_best_voicing(
    prev_voicing: Optional[List[int]],
    prev_name: str,
    cur_name: str,
    raw_notes: List[int],
    key_name: str,
    rng: random.Random
) -> List[int]:

    mode = VOICING_MODE  # NEW: default/wide/low
    prof = VOICING_PROFILES.get(mode, VOICING_PROFILES["default"])

    raw_clean = _prefer_bass_zone(_sanitize_notes_strict(raw_notes))
    cands = generate_voicing_candidates(raw_clean, mode)

    # Glue filter (keep your behavior)
    filtered = [v for v in cands if glue_ok(v, rng)]
    if filtered:
        cands = filtered

    # Repair cross-semitones (keep your behavior)
    if prev_voicing is not None:
        allowed_pcs = allowed_resolution_pcs(key_name)
        cands = [repair_cross_semitones(prev_voicing, v, allowed_pcs) for v in cands]

    # Shared tone cap (keep your behavior)
    if prev_voicing is not None:
        limit = max_shared_allowed(prev_name, cur_name)
        filtered = [v for v in cands if shared_pitch_count(prev_voicing, v) <= limit]
        if filtered:
            cands = filtered

    def cost(v: List[int]) -> float:
        v = _prefer_bass_zone(_sanitize_notes_strict(v))

        if not v:
            return 1e12
        if min(v) < ABS_NOTE_FLOOR:
            return 1e12
        if max(v) > ABS_NOTE_CEIL:
            return 1e12

        # Bass preference penalty (unchanged)
        b = min(v)
        bass_pref_pen = 0.0
        if b < BASS_PREF_MIN:
            bass_pref_pen += (BASS_PREF_MIN - b) * 300.0
        elif b > BASS_PREF_MAX:
            bass_pref_pen += (b - BASS_PREF_MAX) * 300.0

        # Mode-aware register + span targets
        reg_pen = abs(center(v) - prof["target_center"]) * prof["w_center"]
        sp = span(v)

        span_pen = abs(sp - prof["ideal_span"]) * prof["w_span"]
        if sp < prof["min_span"]:
            span_pen += (prof["min_span"] - sp) * 1200.0
        if sp > prof["max_span"]:
            span_pen += (sp - prof["max_span"]) * 800.0

        # Keep your spacing + bass jump penalty
        space_pen = spacing_penalty(v)
        b_pen = bass_penalty(prev_voicing, v)

        # NEW: Default voice-leading melt
        move_pen = 0.0
        leap_pen = 0.0
        shared_bonus = 0.0

        if prev_voicing is not None:
            move_pen = _min_assignment_move(prev_voicing, v) * prof["w_move"]
            # punish any single voice that leaps too much (beyond 5 semitones)
            worst = _max_single_leap(prev_voicing, v)
            if worst > 5:
                leap_pen = ((worst - 5) ** 2) * prof["w_leap"]
            # reward shared pitch classes (not exact pitches)
            shared = _shared_pc_count(prev_voicing, v)
            shared_bonus = -shared * prof["w_shared_bonus"]

        # NEW: top note brightness control
        top = max(v)
        top_pen = 0.0
        # penalize top being close to ceiling; stronger in low mode
        if top > (prof["hi"] - 6):
            top_pen = (top - (prof["hi"] - 6)) * prof["w_top"]

        # Avoid exact repeats (keep)
        repeat_pen = 900.0 if (prev_voicing is not None and sorted(prev_voicing) == sorted(v)) else 0.0

        # Avoid “raw” if desired (keep)
        raw_pen = 0.0
        if ENFORCE_NOT_RAW_WHEN_VOICING and is_raw_shape(v, raw_clean):
            raw_pen = RAW_PENALTY

        return (bass_pref_pen + reg_pen + span_pen + space_pen +
                move_pen + leap_pen + shared_bonus + top_pen +
                b_pen + repeat_pen + raw_pen)

    cands.sort(key=cost)
    best = cands[0] if cands else raw_clean
    best = _prefer_bass_zone(_sanitize_notes_strict(best))
    return best

# =========================================================
# GLOBAL TIMING + EXPORT SETTINGS
# =========================================================

BPM = 85
TIME_SIG = (4, 4)
BASE_OCTAVE = 3
VELOCITY = 100

BAR_DIR = {
    4: "4-bar",
    8: "8-bar",
    16: "16-bar"
}

def sec_per_bar(bpm=BPM, ts=TIME_SIG):
    return (60.0 / bpm) * ts[0]

SEC_PER_BAR = sec_per_bar()




# =========================================================
# EXPORTER (PATCH 3: HARD REGISTER LOCK + REGISTER OPTIMIZER)
# =========================================================

# IMPORTANT:
# MIDI numbers are identical in every DAW. Only the octave labels differ.
# So we enforce safety by MIDI note numbers only.

# Make sure these exist above this exporter section in your file:
# BPM, TIME_SIG, BASE_OCTAVE, VELOCITY, SEC_PER_BAR, BAR_DIR
# chord_to_midi(), choose_best_voicing(), _min_assignment_move()

def safe_token(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_#-]+", "", str(s))


def chord_list_token(chords):
    return "-".join(safe_token(c) for c in chords)


# =========================================================
# GLOBAL REGISTER LOCK (edit these any time)
# =========================================================
BASS_MIN_MIDI = 40     # bass must not be below this
BASS_MAX_MIDI = 52     # bass should not be above this (we pull down if safe)

NOTE_MIN_MIDI = 40     # absolute floor for ANY note (hard ban below this)
NOTE_MAX_MIDI = 88     # soft ceiling (keeps voicings from flying too high)

MAX_OCTAVE_SHIFTS = 6  # safety cap so we never loop forever


# =========================================================
# GLOBAL TRANSPOSE (MASTER OCTAVE SHIFT)
# =========================================================
GLOBAL_TRANSPOSE = 12   # 12 = +1 octave, 0 = off


def _shift_octaves(notes: List[int], octs: int) -> List[int]:
    return [int(n + 12 * octs) for n in notes]


def _enforce_register(notes: List[int]) -> List[int]:
    """
    Hard guarantees:
    1) No note below NOTE_MIN_MIDI, ever.
    2) Bass (min note) forced into BASS_MIN_MIDI..BASS_MAX_MIDI using whole-chord octave shifts.
    3) Keep top under NOTE_MAX_MIDI when possible.
    """
    if not notes:
        return []

    v = sorted(set(int(n) for n in notes))

    # 1) Absolute floor. Push up by octaves until safe.
    for _ in range(MAX_OCTAVE_SHIFTS):
        if min(v) >= NOTE_MIN_MIDI:
            break
        v = sorted(set(_shift_octaves(v, +1)))

    # If still below floor after cap, hard clamp by pushing all offending notes up
    if min(v) < NOTE_MIN_MIDI:
        fixed = []
        for n in v:
            while n < NOTE_MIN_MIDI:
                n += 12
            fixed.append(n)
        v = sorted(set(fixed))

    # 2) Force bass into requested window by shifting whole chord.
    for _ in range(MAX_OCTAVE_SHIFTS):
        if min(v) >= BASS_MIN_MIDI:
            break
        v = sorted(set(_shift_octaves(v, +1)))

    for _ in range(MAX_OCTAVE_SHIFTS):
        if min(v) <= BASS_MAX_MIDI:
            break
        candidate = sorted(set(_shift_octaves(v, -1)))
        if min(candidate) >= NOTE_MIN_MIDI:
            v = candidate
        else:
            break

    # 3) Ceiling control.
    for _ in range(MAX_OCTAVE_SHIFTS):
        if max(v) <= NOTE_MAX_MIDI:
            break
        candidate = sorted(set(_shift_octaves(v, -1)))
        if min(candidate) < NOTE_MIN_MIDI:
            break
        v = candidate

    # Final hard floor re-check
    for _ in range(MAX_OCTAVE_SHIFTS):
        if min(v) >= NOTE_MIN_MIDI:
            break
        v = sorted(set(_shift_octaves(v, +1)))

    if min(v) < NOTE_MIN_MIDI:
        fixed = []
        for n in v:
            while n < NOTE_MIN_MIDI:
                n += 12
            fixed.append(n)
        v = sorted(set(fixed))

    return v


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
            _ = _enforce_register(chord_to_midi(ch))


# =========================================================
# REGISTER OPTIMIZER (shared PCs + adjacency wins when needed)
# =========================================================
def _oct_shift(notes: List[int], k: int) -> List[int]:
    return [int(n + 12 * k) for n in notes]


def _pcset(notes: List[int]) -> set:
    return {int(p) % 12 for p in notes}


def _shared_pitch_class(prev: List[int], cur: List[int]) -> int:
    return len(_pcset(prev) & _pcset(cur))


def _adjacent_pc(prev: List[int], cur: List[int], dist: int = 1) -> int:
    """
    Counts how many pitch-classes in 'cur' are within +/-dist semitones
    of any pitch-class in 'prev'.
    dist=1 -> semitone adjacency
    dist=2 -> semitone + whole-tone adjacency
    """
    A = _pcset(prev)
    B = _pcset(cur)
    if not A or not B:
        return 0

    targets = set()
    for pc in A:
        for d in range(1, dist + 1):
            targets.add((pc + d) % 12)
            targets.add((pc - d) % 12)

    return len(B & targets)


def _voice_leading_cost(prev: List[int], cur: List[int]) -> float:
    return _min_assignment_move(prev, cur)


def optimize_progression_register(
    chords_notes: List[List[int]],
    search_shifts=range(-3, 4),
) -> List[List[int]]:
    """
    For each chord after the first, try octave shifts and pick the best one.

    Priority:
    - More shared pitch-classes is good
    - If shared is lower, adjacency (semi/whole tone) can win (your request)
    - Less total movement is better
    - Smaller bass jumps are better

    Always respects _enforce_register.
    """
    if not chords_notes:
        return chords_notes

    out: List[List[int]] = []
    prev = _enforce_register(chords_notes[0])
    out.append(prev)

    for cur_raw in chords_notes[1:]:
        best = None
        best_score = None

        for k in search_shifts:
            cand = _enforce_register(_oct_shift(cur_raw, k))

            shared = _shared_pitch_class(prev, cand)
            adj1 = _adjacent_pc(prev, cand, dist=1)
            adj2 = _adjacent_pc(prev, cand, dist=2)

            move = _voice_leading_cost(prev, cand)
            bass_jump = abs(min(cand) - min(prev))

            # adjacency can beat fewer shared tones:
            # nearness weights tuned so:
            # shared matters, but adj1 can overtake when shared drops by 1
            nearness = shared * 2 + adj1 * 3 + adj2 * 1

            score = (nearness, -move, -bass_jump)

            if best_score is None or score > best_score:
                best_score = score
                best = cand

        prev = best if best is not None else _enforce_register(cur_raw)
        out.append(prev)

    return out


# =========================================================
# MIDI WRITERS
# =========================================================
def write_progression_midi(
    out_root: str,
    idx: int,
    chords,
    durations,
    key_name: str,
    revoice: bool,
    seed: int
):
    midi = pretty_midi.PrettyMIDI(initial_tempo=BPM)
    midi.time_signature_changes = [pretty_midi.TimeSignature(TIME_SIG[0], TIME_SIG[1], 0)]
    inst = pretty_midi.Instrument(program=0)

    # RAW notes are always register locked
    raw = [_enforce_register(chord_to_midi(ch)) for ch in chords]

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

            v = _enforce_register(v)

            voiced.append(v)
            prev_v = v
            prev_name = ch_name

        out_notes = voiced
    else:
        out_notes = raw

    # IMPORTANT: THIS IS THE PART YOU WERE MISSING (because of duplicate function)
    out_notes = optimize_progression_register(out_notes)

    t = 0.0
    for notes, bars in zip(out_notes, durations):
        dur = bars * SEC_PER_BAR

        shifted = [int(p + GLOBAL_TRANSPOSE) for p in notes]

        for p in sorted(set(shifted)):
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


def write_single_chord_midi(
    out_root: str,
    chord_name: str,
    revoice: bool,
    length_bars=4,
    seed: int = 1337
):
    dur = length_bars * SEC_PER_BAR
    midi = pretty_midi.PrettyMIDI(initial_tempo=BPM)
    midi.time_signature_changes = [pretty_midi.TimeSignature(TIME_SIG[0], TIME_SIG[1], 0)]
    inst = pretty_midi.Instrument(program=0)

    raw = _enforce_register(chord_to_midi(chord_name))

    if revoice:
        rng = random.Random(seed)
        notes = choose_best_voicing(None, chord_name, chord_name, raw, "C", rng)
        notes = _enforce_register(notes)
    else:
        notes = raw

    notes = _enforce_register(notes)

    shifted = [int(p + GLOBAL_TRANSPOSE) for p in notes]

    for p in sorted(set(shifted)):
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
        write_progression_midi(
            prog_root,
            i,
            chords,
            durations,
            key_name,
            revoice=revoice,
            seed=seed
        )
        unique_chords.update(chords)

    for ch in sorted(unique_chords):
        write_single_chord_midi(
            prog_root,
            ch,
            revoice=revoice,
            length_bars=4,
            seed=seed + 999
        )

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
            "Chords": " - ".join(chords),
        })
    return rows


# =========================================================
# ADVANCED SETTINGS (UI + STATE)
# =========================================================
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
    st.session_state.setdefault(VOICING_PROFILE_KEY, "Default")


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
    st.session_state[VOICING_PROFILE_KEY] = "Default"


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
        max_value=200,
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

    # =========================================================
    # BANLIST (OPTIONAL)
    # =========================================================
    with st.expander("BANLIST (OPTIONAL)", expanded=False):
        st.caption("Upload a .txt with progressions to exclude (one per line). Example: Cmin-Gmin-Fmin")
        up = st.file_uploader("Upload banlist .txt", type=["txt"], label_visibility="visible")

        if up is not None:
            ban_set, stats, examples = load_banlist_from_txt_bytes(up.getvalue())
            st.session_state[BANLIST_STATE_KEY] = {
                "banned_set": ban_set,
                "stats": stats,
                "examples": examples,
            }

            st.info(
                f"Banlist loaded. Added: {stats['added']} | "
                f"Invalid lines: {stats['invalid']} | "
                f"Empty: {stats['empty']} | "
                f"Ignored meta: {stats['ignored_meta']}"
            )

            if examples:
                st.caption("Examples of invalid lines (first few):")
                for ex in examples[:6]:
                    st.code(ex)
        else:
            st.session_state.setdefault(BANLIST_STATE_KEY, {"banned_set": set(), "stats": {}, "examples": []})
            st.caption("No banlist uploaded.")

    # ADVANCED SETTINGS UI (single render, no duplicates)
    if ENABLE_CHORD_BALANCE_FEATURE and ENABLE_CHORD_TYPE_SLIDERS:
        ensure_adv_defaults()

        with st.expander("ADVANCED SETTINGS", expanded=False):
            st.caption("Chord type balance: 0 disables. 50 is default. 100 strongly favors.")

            st.markdown("### RE-VOICING STYLE")
            st.selectbox(
                "Voicing Profile",
                options=list(VOICING_PROFILES.keys()),
                key=VOICING_PROFILE_KEY,
                help="Default is balanced. Tight keeps notes closer. Wide opens the chord. Deep Low Ambient brings bass lower with smooth motion.",
            )

            cL, cM, cR = st.columns([1, 2, 1])
            with cM:
                st.button(
                    "Default",
                    use_container_width=False,
                    key="aa_reset_defaults",
                    on_click=reset_adv_defaults
                )


            st.markdown("### MAJOR FAMILY")
            c1, c2 = st.columns(2)
            majors = [x for x in ADV_QUALITIES if x[0] in ("maj9", "maj7", "add9", "6add9", "6", "maj")]
            for i, (qual, label) in enumerate(majors):
                with (c1 if i % 2 == 0 else c2):
                    st.slider(label, 0, 100, key=f"{ADV_KEY_PREFIX}{qual}")

            st.markdown("### MINOR FAMILY")
            c1, c2 = st.columns(2)
            minors = [x for x in ADV_QUALITIES if x[0] in ("min9", "min7", "min11", "min")]
            for i, (qual, label) in enumerate(minors):
                with (c1 if i % 2 == 0 else c2):
                    st.slider(label, 0, 100, key=f"{ADV_KEY_PREFIX}{qual}")

            st.markdown("### SUS FAMILY")
            c1, c2 = st.columns(2)
            suss = [x for x in ADV_QUALITIES if x[0] in ("sus2add9", "sus4add9", "sus2", "sus4")]
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
            ban_set = st.session_state.get(BANLIST_STATE_KEY, {}).get("banned_set", set())

            progressions, pattern_dupe_used, pattern_dupe_max, low_sim_total, qual_usage = generate_progressions(
                n=int(n_progressions),
                seed=seed,
                chord_balance=chord_balance,
                ban_set=ban_set,
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







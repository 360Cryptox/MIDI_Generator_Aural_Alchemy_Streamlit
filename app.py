# app.py
# Aural Alchemy — Endless Ambient MIDI Progressions (Streamlit)
# - Generates N progressions (1–100, default 10)
# - Optional Re-voicing (inversions/voicings)
# - Shows preview (first 10)
# - Exports ZIP: Progressions/*.mid + Chords/*.mid
# - Download filename always: MIDI_Progressions_Aural_Alchemy.zip

import os, re, math, time, random, shutil, tempfile
from zipfile import ZipFile
from collections import Counter
from typing import List, Optional

import pandas as pd
import streamlit as st
import pretty_midi


# ================================
# UI CONFIG + PREMIUM CSS
# ================================
st.set_page_config(
    page_title="Aural Alchemy — MIDI Progressions",
    page_icon="🌙",
    layout="centered",
)

CSS = """
<style>
/* Optional font (if you want zero external calls, remove this @import) */
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700&family=Cormorant+Garamond:wght@400;500;600&display=swap');

:root{
  --ink: rgba(248,250,255,.95);
  --muted: rgba(248,250,255,.72);
  --gold: rgba(214,182,92,.65);
  --goldSoft: rgba(214,182,92,.25);
  --glass: rgba(6,10,18,.58);
  --stroke: rgba(255,255,255,.14);
  --deep: #05070d;
  --deep2:#0a1220;
}

html, body, [class*="css"]{
  font-family: "Cormorant Garamond", serif !important;
  -webkit-font-smoothing: antialiased;
  text-rendering: geometricPrecision;
}

.stApp{
  color:var(--ink);
  background:
    radial-gradient(1400px 700px at 50% 30%, rgba(214,182,92,.08), transparent 65%),
    linear-gradient(180deg,var(--deep),var(--deep2));
  overflow:hidden;
}

/* Mandala overlay (slow + subtle) */
.stApp:before{
  content:"";
  position:fixed; inset:-10%;
  opacity:.26;
  background-image:url("data:image/svg+xml;utf8,\
  <svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 1200'>\
  <defs>\
  <pattern id='m' width='520' height='520' patternUnits='userSpaceOnUse'>\
  <g transform='translate(260 260)' fill='none' stroke='rgba(255,255,255,0.28)' stroke-width='1.05'>\
  <circle r='70'/><circle r='130'/><circle r='190' stroke-opacity='0.22'/>\
  <path d='M0 -210 L0 210' stroke-opacity='0.20'/>\
  <path d='M-210 0 L210 0' stroke-opacity='0.20'/>\
  <path d='M-148 -148 L148 148' stroke-opacity='0.18'/>\
  <path d='M148 -148 L-148 148' stroke-opacity='0.18'/>\
  <g stroke-opacity='0.16'>\
    <circle cx='0' cy='-120' r='120'/>\
    <circle cx='104' cy='-60' r='120'/>\
    <circle cx='104' cy='60' r='120'/>\
    <circle cx='0' cy='120' r='120'/>\
    <circle cx='-104' cy='60' r='120'/>\
    <circle cx='-104' cy='-60' r='120'/>\
  </g>\
  </g></pattern></defs>\
  <rect width='1200' height='1200' fill='url(%23m)'/>\
  </svg>");
  background-size: 820px 820px;
  animation: mandala 42s linear infinite;
  pointer-events:none;
  z-index:0;
}
@keyframes mandala{
  0%   { transform: rotate(0deg) scale(1.00); }
  50%  { transform: rotate(180deg) scale(1.03); }
  100% { transform: rotate(360deg) scale(1.00); }
}

.block-container{
  position:relative;
  z-index:1;
  max-width: 920px;
  padding-top: 28px;
  padding-bottom: 48px;
}

h1, h2, h3{
  font-family:"Cinzel", serif !important;
  letter-spacing: 0.8px;
}

.aa-card{
  background: var(--glass);
  border: 1px solid var(--stroke);
  border-radius: 28px;
  padding: 22px 22px 18px;
  box-shadow: 0 28px 90px rgba(0,0,0,.62);
  backdrop-filter: blur(18px);
}

.small-muted{
  color: var(--muted);
  font-size: 18px;
  letter-spacing: .4px;
  margin-top: -8px;
}

.stButton>button{
  font-family:"Cinzel", serif !important;
  font-weight: 650 !important;
  letter-spacing: 1px !important;
  border-radius: 999px !important;
  padding: 12px 18px !important;
  border: 1px solid var(--goldSoft) !important;
  background:
    radial-gradient(circle at 28% 30%, rgba(214,182,92,.34), transparent 60%),
    linear-gradient(180deg, rgba(18,22,36,.96), rgba(6,10,18,.96)) !important;
  box-shadow:
    0 14px 42px rgba(0,0,0,.55),
    inset 0 0 30px rgba(214,182,92,.14) !important;
  transition: transform .25s ease, box-shadow .25s ease, filter .25s ease;
}
.stButton>button:hover{
  transform: translateY(-2px);
  box-shadow:
    0 22px 66px rgba(0,0,0,.72),
    inset 0 0 44px rgba(214,182,92,.22) !important;
  filter: brightness(1.06);
}

[data-testid="stSlider"]{
  font-family:"Cormorant Garamond", serif !important;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

st.markdown(
    """
    <div style="text-align:center;">
      <h1 style="margin-bottom:10px;">AURAL ALCHEMY</h1>
      <div class="small-muted">Endless Ambient MIDI Progressions · Pack-Ready</div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="aa-card">', unsafe_allow_html=True)


# ================================
# MUSICAL DATA (from your notebook)
# ================================
KEYS = ["C","Db","D","Eb","E","F","Gb","G","Ab","A","Bb","B"]

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

NOTE_TO_PC = {
    "C":0,"B#":0,"C#":1,"Db":1,"D":2,"D#":3,"Eb":3,"E":4,"Fb":4,"E#":5,"F":5,
    "F#":6,"Gb":6,"G":7,"G#":8,"Ab":8,"A":9,"A#":10,"Bb":10,"B":11,"Cb":11,
}

def _pc(note): return NOTE_TO_PC[note]
def _key_pc_set(key): return {_pc(n) for n in SCALES[key]}

# Canonical chord interval formulas (moved BEFORE generator so it never KeyErrors)
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
QUALITY_NOTECOUNT = {q: len(iv) for q, iv in QUAL_TO_INTERVALS.items()}

def _chord_pc_set_real(root_note, qual):
    r = _pc(root_note)
    return {(r + iv) % 12 for iv in QUAL_TO_INTERVALS[qual]}

def _is_diatonic_chord(key, root_note, qual):
    return _chord_pc_set_real(root_note, qual).issubset(_key_pc_set(key))

def _shared_tone_ok_loop(roots, quals, need=1, loop=True):
    pcs = [_chord_pc_set_real(r, q) for r, q in zip(roots, quals)]
    for a, b in zip(pcs, pcs[1:]):
        if len(a & b) < need:
            return False
    if loop and len(pcs) >= 2:
        if len(pcs[-1] & pcs[0]) < need:
            return False
    return True

def _low_sim_count_loop(roots, quals, loop=True):
    pcs = [_chord_pc_set_real(r, q) for r, q in zip(roots, quals)]
    bad = 0
    for a, b in zip(pcs, pcs[1:]):
        if len(a & b) == 0:
            bad += 1
    if loop and len(pcs) >= 2 and len(pcs[-1] & pcs[0]) == 0:
        bad += 1
    return bad

def _wchoice(rng, items_with_w):
    items = [x for x,_ in items_with_w]
    ws    = [w for _,w in items_with_w]
    return rng.choices(items, weights=ws, k=1)[0]


# ================================
# GENERATOR SETTINGS (your notebook defaults)
# ================================
PATTERN_MAX_REPEATS = 1
MAX_PATTERN_DUPLICATE_RATIO = 0.01

TOTAL_BARS_DISTRIBUTION = {8: 0.40, 4: 0.35, 16: 0.25}
CHORDCOUNT_DISTRIBUTION = {4: 0.40, 3: 0.35, 2: 0.20, 5: 0.03, 6: 0.02}

MIN_SHARED_TONES = 1
ENFORCE_LOOP_OK  = True
MAX_TRIES_PER_PROG = 40000

TRIAD_PROB_BASE = 0.90
BARE_SUS_PROB   = 0.13

LIMIT_NOTECOUNT_JUMPS = True
MAX_BIG_JUMPS_PER_PROG = 1

SUS_WEIGHT_MULT   = 0.50
SUS_UPGRADE_PROB  = 0.50


# ================================
# DEGREE TEMPLATES
# ================================
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

def _pick_template_degs(rng, m):
    return list(_wchoice(rng, TEMPLATES_BY_LEN[m]))


# ================================
# QUALITY POOLS
# ================================
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

def _pick_quality_diatonic(rng, key, deg):
    root = SCALES[key][deg]
    triad_boost = (rng.random() < TRIAD_PROB_BASE)
    pool = DEG_ALLOWED_BASE[deg]

    for _ in range(200):
        q = _wchoice(rng, pool)

        if q in ("sus2","sus4") and rng.random() < SUS_UPGRADE_PROB:
            if rng.random() >= BARE_SUS_PROB:
                q = "sus2add9" if q == "sus2" else "sus4add9"

        if q in ("maj","min") and (not triad_boost) and rng.random() < 0.85:
            continue

        if _is_diatonic_chord(key, root, q):
            return q

    for q in SAFE_FALLBACK_ORDER:
        if _is_diatonic_chord(key, root, q):
            return q
    return "maj7"


# ================================
# DURATIONS
# ================================
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

def _pick_durations(rng, m, total):
    return _wchoice(rng, DURATIONS[(m, total)])

def _pick_valid_total_and_m(rng):
    weighted = []
    for (m, total) in VALID_COMBOS:
        wt = TOTAL_BARS_DISTRIBUTION.get(total, 0.0) * CHORDCOUNT_DISTRIBUTION.get(m, 0.0)
        if wt > 0:
            weighted.append(((total, m), wt))
    if not weighted:
        raise RuntimeError("No valid (total,m) combos available. Check DURATIONS and distributions.")
    (total, m) = _wchoice(rng, weighted)
    return total, m


# ================================
# Duplicate controls
# ================================
def _pattern_fingerprint(degs, quals):
    return (tuple(degs), tuple(quals))

def _dedupe_inside_progression(rng, key, degs, quals):
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

        cand = SAFE_FALLBACK_ORDER[:]
        rng.shuffle(cand)
        fixed = False
        for q2 in cand:
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

        neighbor_steps = [1,-1,2,-2,3,-3]
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


def _build_progression(rng, key, degs, total_bars):
    quals = [_pick_quality_diatonic(rng, key, d) for d in degs]
    ded = _dedupe_inside_progression(rng, key, degs[:], quals[:])
    if ded is None:
        return None
    degs, quals = ded

    roots = [SCALES[key][d] for d in degs]

    if any(not _is_diatonic_chord(key, r, q) for r, q in zip(roots, quals)):
        return None

    if not _shared_tone_ok_loop(roots, quals, need=MIN_SHARED_TONES, loop=ENFORCE_LOOP_OK):
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


def _pick_keys_even(n, rng):
    base = n // len(KEYS)
    rem  = n % len(KEYS)
    out = []
    for k in KEYS:
        out += [k] * base
    extra = KEYS[:]
    rng.shuffle(extra)
    out += extra[:rem]
    rng.shuffle(out)
    return out


def generate_progressions(n=10, seed=123):
    rng = random.Random(seed)
    keys = _pick_keys_even(n, rng)

    max_pattern_dupes = int(math.floor(n * MAX_PATTERN_DUPLICATE_RATIO))
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


# ================================
# CHORD -> MIDI + VOICING ENGINE (from your notebook)
# ================================
NOTE_TO_SEMITONE = {
    "C":0,"B#":0,"C#":1,"Db":1,"D":2,"D#":3,"Eb":3,"E":4,"Fb":4,"E#":5,"F":5,
    "F#":6,"Gb":6,"G":7,"G#":8,"Ab":8,"A":9,"A#":10,"Bb":10,"B":11,"Cb":11,"B#":0
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

def chord_intervals_from_symbol(rest: str):
    quality = rest.lower()
    if quality in QUAL_TO_INTERVALS:
        return QUAL_TO_INTERVALS[quality]
    raise ValueError(f"Unrecognized chord quality: {rest}")

def chord_to_midi(chord_name: str, base_oct=3, low=48, high=84) -> List[int]:
    root, rest, bass = parse_root_and_bass(chord_name)
    if root not in NOTE_TO_SEMITONE:
        raise ValueError(f"Bad root '{root}' in '{chord_name}'")
    root_pc = NOTE_TO_SEMITONE[root]
    root_midi = 12 * (base_oct + 1) + root_pc

    tones = chord_intervals_from_symbol(rest)
    notes = []
    for iv in tones:
        p = root_midi + iv
        while p < low:  p += 12
        while p > high: p -= 12
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

LOW, HIGH = 48, 84
TARGET_CENTER = 60.0
IDEAL_SPAN = 12
MIN_SPAN = 8
MAX_SPAN = 19

MAX_SHARED_DEFAULT = 2
MAX_SHARED_MIN11   = 3

DISALLOW_GLUE = True
ENFORCE_NOT_RAW_WHEN_VOICING = True

def clamp_to_range(notes):
    out = []
    for p in notes:
        while p < LOW:  p += 12
        while p > HIGH: p -= 12
        out.append(p)
    return sorted(out)

def span(notes):   return max(notes) - min(notes)
def center(notes): return (min(notes) + max(notes)) / 2.0

def has_glued_semitones(notes):
    s = sorted(notes)
    return any((s[i+1] - s[i]) == 1 for i in range(len(s)-1))

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
    p = sorted(prev); c = sorted(cur)
    n = min(len(p), len(c))
    if len(p) == len(c):
        return sum(abs(c[i] - p[i]) for i in range(n))
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

def choose_best_voicing(prev_voicing: Optional[List[int]],
                       prev_name: str,
                       cur_name: str,
                       raw_notes: List[int]) -> List[int]:
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
        if sp < MIN_SPAN: span_pen += (MIN_SPAN - sp) * 700
        if sp > MAX_SPAN: span_pen += (sp - MAX_SPAN) * 220

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


# ================================
# EXPORTER (writes to temp dir, returns zip bytes)
# ================================
BPM = 85
PACK_NAME = "MIDI_Progressions_Aural_Alchemy"
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
        raise ValueError("Progressions is empty.")

    for i, item in enumerate(progressions, start=1):
        if len(item) != 3:
            raise ValueError(f"Progression {i} must be (chords, durations, key).")
        chords, durations, key_name = item
        if len(chords) != len(durations):
            raise ValueError(f"Progression {i}: chord/duration length mismatch.")
        bars = sum(durations)
        if bars not in (4, 8, 16):
            raise ValueError(f"Progression {i}: bars sum to {bars}. Must be 4, 8, or 16.")
        for ch in chords:
            chord_to_midi(ch, base_oct=BASE_OCTAVE)

def write_progression_midi(out_dir, idx, chords, durations, key_name, revoice: bool):
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
        mode_tag = "_REVOICED"
    else:
        out_notes = raw
        mode_tag = ""

    t = 0.0
    for notes, bars in zip(out_notes, durations):
        dur = bars * SEC_PER_BAR
        for p in sorted(set(notes)):
            inst.notes.append(pretty_midi.Note(int(VELOCITY), int(p), t, t + dur))
        t += dur

    midi.instruments.append(inst)

    total_bars = sum(durations)
    bars_folder = BAR_DIR[total_bars]
    folder = os.path.join(out_dir, "Progressions", bars_folder)
    os.makedirs(folder, exist_ok=True)

    filename = f"Prog_{idx:03d}_in_{safe_token(key_name)}{mode_tag}_{chord_list_token(chords)}.mid"
    midi.write(os.path.join(folder, filename))

def write_single_chord_midi(out_dir, chord_name, revoice: bool, length_bars=4):
    dur = length_bars * SEC_PER_BAR
    midi = pretty_midi.PrettyMIDI(initial_tempo=BPM)
    midi.time_signature_changes = [pretty_midi.TimeSignature(TIME_SIG[0], TIME_SIG[1], 0)]
    inst = pretty_midi.Instrument(program=0)

    raw = chord_to_midi(chord_name, base_oct=BASE_OCTAVE)
    if revoice:
        notes = choose_best_voicing(None, chord_name, chord_name, raw)
        mode_tag = "_REVOICED"
    else:
        notes = raw
        mode_tag = ""

    for p in sorted(set(notes)):
        inst.notes.append(pretty_midi.Note(int(VELOCITY), int(p), 0.0, dur))

    midi.instruments.append(inst)
    folder = os.path.join(out_dir, "Chords")
    os.makedirs(folder, exist_ok=True)
    midi.write(os.path.join(folder, f"{safe_token(chord_name)}{mode_tag}.mid"))

def build_zip_bytes(progressions, revoice: bool) -> tuple[bytes, int]:
    validate_progressions(progressions)

    with tempfile.TemporaryDirectory() as tmp:
        unique_chords = set()

        for i, (chords, durations, key_name) in enumerate(progressions, start=1):
            write_progression_midi(tmp, i, chords, durations, key_name, revoice=revoice)
            unique_chords.update(chords)

        for ch in sorted(unique_chords):
            write_single_chord_midi(tmp, ch, revoice=revoice, length_bars=4)

        zip_path = os.path.join(tmp, f"{PACK_NAME}.zip")
        with ZipFile(zip_path, "w") as z:
            for root, _, files in os.walk(os.path.join(tmp, "Progressions")):
                for f in files:
                    full = os.path.join(root, f)
                    z.write(full, arcname=os.path.relpath(full, tmp))
            for root, _, files in os.walk(os.path.join(tmp, "Chords")):
                for f in files:
                    full = os.path.join(root, f)
                    z.write(full, arcname=os.path.relpath(full, tmp))

        with open(zip_path, "rb") as f:
            data = f.read()

    return data, len(unique_chords)


# ================================
# STREAMLIT UI
# ================================
col1, col2 = st.columns([1.2, 1.0], gap="large")
with col1:
    n_progressions = st.slider("Progressions to generate", min_value=1, max_value=100, value=10, step=1)
with col2:
    revoice = st.toggle("Re-voicing (Inversions)", value=False, help="Smoother voicings, more original MIDI.")

st.divider()

generate = st.button("Generate Pack", use_container_width=True)

# Session state
if "progressions" not in st.session_state:
    st.session_state.progressions = None
if "zip_bytes" not in st.session_state:
    st.session_state.zip_bytes = None
if "counts" not in st.session_state:
    st.session_state.counts = None

if generate:
    st.session_state.zip_bytes = None
    st.session_state.progressions = None
    st.session_state.counts = None

    prog_bar = st.progress(0, text="Generating…")

    seed = int(time.time() * 1000) ^ random.getrandbits(32)
    progressions, pattern_used, pattern_max, low_sim_total, qual_usage = generate_progressions(
        n=int(n_progressions),
        seed=int(seed),
    )

    prog_bar.progress(35, text="Preparing preview…")

    unique_chords = set()
    bar_counts = Counter()
    for chords, durs, _k in progressions:
        unique_chords.update(chords)
        bar_counts[sum(durs)] += 1

    prog_bar.progress(55, text="Exporting MIDI + building ZIP…")
    zip_bytes, chord_count = build_zip_bytes(progressions, revoice=revoice)

    prog_bar.progress(100, text="Ready ✅")

    st.session_state.progressions = progressions
    st.session_state.zip_bytes = zip_bytes
    st.session_state.counts = {
        "progressions": len(progressions),
        "chords": chord_count,
        "low_sim_total": low_sim_total,
        "bars_4": bar_counts.get(4, 0),
        "bars_8": bar_counts.get(8, 0),
        "bars_16": bar_counts.get(16, 0),
        "qualities": dict(qual_usage),
        "pattern_used": pattern_used,
        "pattern_max": pattern_max,
    }

# Output / preview
if st.session_state.progressions:
    c = st.session_state.counts or {}

    st.markdown("### Summary")
    m1, m2, m3 = st.columns(3)
    m1.metric("Progressions Generated", c.get("progressions", 0))
    m2.metric("Individual Chords Generated", c.get("chords", 0))
    m3.metric("LOW_SIM (must be 0)", c.get("low_sim_total", 0))

    st.caption(f"Bar mix: 4-bar {c.get('bars_4',0)} · 8-bar {c.get('bars_8',0)} · 16-bar {c.get('bars_16',0)}")

    st.markdown("### Preview (first 10)")
    rows = []
    for i, (chords, durs, key) in enumerate(st.session_state.progressions[:10], start=1):
        rows.append({
            "#": i,
            "Key": key,
            "Bars": sum(durs),
            "Chords": " – ".join(chords),
            "Durations": str(durs),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.divider()

    if st.session_state.zip_bytes:
        st.download_button(
            label="Download MIDI Progressions",
            data=st.session_state.zip_bytes,
            file_name="MIDI_Progressions_Aural_Alchemy.zip",
            mime="application/zip",
            use_container_width=True
        )

st.markdown("</div>", unsafe_allow_html=True)  # close aa-card

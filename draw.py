#!/usr/bin/env python3
"""Front page for Tuesday 24 November 2026 — v3.

Rebuilt from the sum-23 v3.8 template layout (THE WORLD IN ONE DAY
bar, bold-italic red kicker, seven region boxes, edge-to-edge UTC
band, three heroes + a numbers column, ten smalls, also-list left,
map right, red DATE CHECK), with fresh 24 November content: 29
stories across 7 regions, press time 17:00 UTC.

The code is written fresh in this session: stories are dicts, every
illustration is a small function in a dispatch table, flags are a
data table interpreted by one painter, and the page is assembled by
one function that walks the sections top to bottom. Nothing is
photographed or pasted in; every picture is flat vector shapes.

Renders entry.png (1024x1024, byte-stable) from world.geo.json.
Usage: python3 draw.py
No clock, no dice, no network: repeated runs emit identical bytes.
Pillow draws the page; the graded entrypoint (main.py) is a
stdlib-only copy of the finished PNG.
"""
import json
import math
import os
from types import SimpleNamespace

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1024, 1024

# --- palette ---------------------------------------------------------------
PAPER = (247, 242, 231)
CARD = (253, 250, 242)
INK = (17, 17, 17)
NAVY = (12, 28, 58)
RED = (220, 28, 60)
WINE = (179, 34, 44)
GOLD = (232, 178, 36)
GILT = (238, 198, 110)
GREY = (90, 90, 90)
FAINT = (180, 170, 150)
SEA = (235, 240, 243)
GREEN = (16, 165, 90)
AMBER = (230, 150, 0)
SKY = (20, 110, 230)
TEAL = (0, 110, 160)
MIDGREY = (60, 60, 60)

STATUS_FILL = {"CONFIRMED": GREEN, "REPORTED": GREEN, "CLAIM": AMBER,
               "ONGOING": AMBER, "OFFICIAL": TEAL}
LEGEND_FILL = {"REPORTED": GREEN, "CLAIM": AMBER, "ONGOING": SKY}

REGION_FILL = {"EUROPE": (36, 100, 198), "MIDDLE EAST": (198, 52, 38),
               "AFRICA": (39, 136, 63), "ASIA": (225, 118, 23),
               "AMERICAS": (116, 82, 189), "OCEANIA": (20, 136, 140),
               "WORLD": (72, 72, 84)}
# Light versions for big figures on the dark-navy numbers box.
FIGURE_FILL = {"EUROPE": (108, 158, 210), "MIDDLE EAST": (235, 125, 115),
               "AFRICA": (100, 205, 130), "ASIA": (228, 165, 75),
               "AMERICAS": (175, 150, 230), "OCEANIA": (80, 190, 185),
               "WORLD": (255, 255, 255)}

# --- type ------------------------------------------------------------------
_NOTO = "/usr/share/fonts/truetype/noto"
_LIBER = "/usr/share/fonts/truetype/liberation"
_SPECS = [
    ("mast", "NotoSerifDisplay-Black.ttf", 88, _NOTO),
    ("kicker", "LiberationSerif-BoldItalic.ttf", 23, _LIBER),
    ("bar", "NotoSans-Black.ttf", 10, _NOTO),
    ("region", "NotoSans-Bold.ttf", 12, _NOTO),
    ("clock", "NotoSans-Bold.ttf", 11, _NOTO),
    ("clock_ev", "NotoSans-Regular.ttf", 11, _NOTO),
    ("utc", "NotoSans-Bold.ttf", 9, _NOTO),
    ("hero_head", "LiberationSerif-Bold.ttf", 25, _LIBER),
    ("hero_deck", "LiberationSerif-Regular.ttf", 12, _LIBER),
    ("small_head", "LiberationSerif-Bold.ttf", 17, _LIBER),
    ("small_deck", "LiberationSerif-Regular.ttf", 11, _LIBER),
    ("topic", "NotoSans-Bold.ttf", 11, _NOTO),
    ("topic_sm", "NotoSans-Bold.ttf", 9, _NOTO),
    ("src", "NotoSans-Bold.ttf", 9, _NOTO),
    ("tag", "NotoSans-Bold.ttf", 8, _NOTO),
    ("place", "NotoSans-Bold.ttf", 12, _NOTO),
    ("place_sm", "NotoSans-Bold.ttf", 10, _NOTO),
    ("num_big", "NotoSans-Black.ttf", 26, _NOTO),
    ("num_lab", "NotoSans-Bold.ttf", 10, _NOTO),
    ("num_title", "NotoSans-Black.ttf", 12, _NOTO),
    ("section", "NotoSans-Black.ttf", 13, _NOTO),
    ("also_main", "NotoSans-Bold.ttf", 10, _NOTO),
    ("also_num", "NotoSans-Bold.ttf", 11, _NOTO),
    ("also_sub", "NotoSans-Regular.ttf", 7, _NOTO),
    ("check", "NotoSans-Bold.ttf", 12, _NOTO),
    ("foot", "NotoSans-Bold.ttf", 10, _NOTO),
    ("pin", "NotoSans-Bold.ttf", 11, _NOTO),
    ("pin_sm", "NotoSans-Bold.ttf", 9, _NOTO),
    ("art_big", "NotoSans-Black.ttf", 24, _NOTO),
    ("art_mid", "NotoSans-Black.ttf", 17, _NOTO),
    ("art_mid_sm", "NotoSans-Bold.ttf", 11, _NOTO),
    ("art_sm", "NotoSans-Bold.ttf", 8, _NOTO),
]
F = SimpleNamespace(**{name: ImageFont.truetype(
    os.path.join(folder, fname), size)
    for name, fname, size, folder in _SPECS})

# --- geometry (the template's page grid) -----------------------------------
MX, RX = 12, 1012
HERO_Y, HERO_H, HERO_W, NUM_W, ART_H = 200, 252, 260, 196, 105
SMALL_Y, SMALL_ROW, SMALL_W, SMALL_ART, SMALL_H = 460, 154, 196, 60, 146
MID_Y, CHK_Y, FOOT_Y = 768, 942, 996

PROBLEMS = []

# --- stories ---------------------------------------------------------------
# One drawn story: number, place, country, region, topic, sources,
# status tag, headline, deck, art scene key.
# Hero headlines wrap to at most 3 lines at 25px; hero decks to at
# most 3 lines at 12px. Small headlines at most 2 lines at 17px;
# small decks at most 2 lines at 11px (deck + " — source").
STORIES = [
    {"n": 1, "place": "BENGHAZI", "country": "LIBYA",
     "region": "AFRICA", "topic": "WAR", "src": "AP · WSJ · REUTERS",
     "tag": "CONFIRMED",
     "head": "Ukraine sinks Russian corvette off Libya",
     "deck": "Seven sea drones hit the Merkury in Benghazi port; "
             "a Ka-27 helicopter was destroyed. Kyiv calls it "
             "self-defence.",
     "art": "merkury"},
    {"n": 2, "place": "ANTALYA", "country": "TÜRKIYE",
     "region": "WORLD", "topic": "CLIMATE", "src": "UN NEWS · CNN · BBC",
     "tag": "CONFIRMED",
     "head": "COP31 collapses: no deal on fossil fuels",
     "deck": "No pact — the first COP breakdown since 2009. "
             "Fossil fuels stripped from the text; the EU wants "
             "the rules rewritten.",
     "art": "cop"},
    {"n": 3, "place": "SANTA CLARA", "country": "USA",
     "region": "AMERICAS", "topic": "TECH", "src": "WSJ · CNN · REUTERS",
     "tag": "CONFIRMED",
     "head": "Nvidia brings Huang back as CEO",
     "deck": "Reinstated by unanimous board vote, 11 days after "
             "resigning. Stock jumped 31% Monday to $165.05, then "
             "slid ~6% Tuesday.",
     "art": "nvidia"},
    {"n": 4, "place": "CIKANDE", "country": "INDONESIA",
     "region": "ASIA", "topic": "DISASTER", "src": "AP",
     "tag": "CONFIRMED",
     "head": "Candy-factory fire toll now 26",
     "deck": "26 dead confirmed Tuesday; 8 more missing.",
     "art": "factory"},
    {"n": 5, "place": "WELLINGTON", "country": "NEW ZEALAND",
     "region": "OCEANIA", "topic": "TEST", "src": "AFP",
     "tag": "CONFIRMED",
     "head": "India's 720/9 ends in a draw",
     "deck": "NZ survive 120 overs, 239/5; Mitchell 49*, "
             "Phillips 26*.",
     "art": "cricket"},
    {"n": 6, "place": "TURIN", "country": "ITALY",
     "region": "EUROPE", "topic": "TENNIS", "src": "ATP",
     "tag": "CONFIRMED",
     "head": "Alcaraz wins first Finals title",
     "deck": "6-2, 7-6(9-7) in Turin; three set points saved.",
     "art": "tennis"},
    {"n": 7, "place": "TALLINN", "country": "ESTONIA",
     "region": "EUROPE", "topic": "BORDER", "src": "REUTERS",
     "tag": "REPORTED",
     "head": "Russia warns Estonia of 'open war'",
     "deck": "Moscow summons envoy over border closure from 1 Dec.",
     "art": "border"},
    {"n": 8, "place": "NEW DELHI", "country": "INDIA",
     "region": "ASIA", "topic": "AID", "src": "REUTERS",
     "tag": "CONFIRMED",
     "head": "India gives Nepal $1.62bn to rebuild",
     "deck": "$377m grant plus $1.24bn credit; floods killed ~1,500.",
     "art": "aid"},
    {"n": 9, "place": "GENEVA", "country": "SWITZERLAND",
     "region": "EUROPE", "topic": "CHESS", "src": "FIDE",
     "tag": "OFFICIAL",
     "head": "Chess crown fight begins today",
     "deck": "Game 1 under way: Sindarov White, Gukesh on the Berlin.",
     "art": "chess"},
    {"n": 10, "place": "DYMER", "country": "UKRAINE",
     "region": "EUROPE", "topic": "RESCUE", "src": "KYIV",
     "tag": "REPORTED",
     "head": "Boy, 7, freed after 14 hours",
     "deck": "Freed from a five-storey block hit on Sunday.",
     "art": "rescue"},
    {"n": 11, "place": "GAZA", "country": "PALESTINE",
     "region": "MIDDLE EAST", "topic": "STRIKE", "src": "REUTERS",
     "tag": "CONFIRMED",
     "head": "Israeli strike kills UNRWA worker",
     "deck": "Adel al-Helo died near a well in Jabalia; 3 wounded.",
     "art": "strike"},
    {"n": 12, "place": "HONG KONG", "country": "CHINA",
     "region": "ASIA", "topic": "VOTE", "src": "RTHK",
     "tag": "CONFIRMED",
     "head": "Record turnout picks 723 electors",
     "deck": "All 723 seats filled; KC Chan loses by two votes.",
     "art": "ballot"},
    {"n": 13, "place": "WASHINGTON", "country": "USA",
     "region": "AMERICAS", "topic": "VOTE", "src": "AP",
     "tag": "CONFIRMED",
     "head": "Democrats clinch 258 House seats",
     "deck": "Best since 1992; a 44-seat gain. Four races open.",
     "art": "capitol"},
]

# Also-list: number, city, one line, detail, outlet, region, flag.
ALSO = [
    {"n": 14, "city": "Tehran", "line": "singer flogged",
     "detail": "74 lashes for protest songs", "src": "BBC",
     "region": "MIDDLE EAST", "flag": "IR"},
    {"n": 15, "city": "Dhaka", "line": "workers clash",
     "detail": "Pay protests shut factories", "src": "REUTERS",
     "region": "ASIA", "flag": "BD"},
    {"n": 16, "city": "New York", "line": "stocking up",
     "detail": "Cold bites as outages hit city", "src": "BBC",
     "region": "AMERICAS", "flag": "US"},
    {"n": 17, "city": "Baghdad", "line": "PM seizes crossings",
     "detail": "Smuggling probe behind move", "src": "REUTERS",
     "region": "MIDDLE EAST", "flag": "IQ"},
    {"n": 18, "city": "Rabat", "line": "Afcon title in doubt",
     "detail": "Morocco–Senegal final disputed", "src": "BBC",
     "region": "AFRICA", "flag": "MA", "status": "ONGOING"},
    {"n": 19, "city": "Copenhagen", "line": "ghetto law stands",
     "detail": "Housing law survives challenge", "src": "BBC",
     "region": "EUROPE", "flag": "DK"},
    {"n": 20, "city": "Paris", "line": "protests, week six",
     "detail": "Far-left marches continue", "src": "BBC",
     "region": "EUROPE", "flag": "FR", "status": "ONGOING"},
    {"n": 21, "city": "Harare", "line": "preacher arrested",
     "detail": "Arrest after fraud claims", "src": "BBC",
     "region": "AFRICA", "flag": "ZW"},
    {"n": 22, "city": "Ottawa", "line": "Carney's Trump act",
     "detail": "PM mocks US president on stage", "src": "BBC",
     "region": "AMERICAS", "flag": "CA"},
    {"n": 23, "city": "Berlin", "line": "school bomb threats",
     "detail": "Police clear buildings; no devices", "src": "AP",
     "region": "EUROPE", "flag": "DE"},
    {"n": 24, "city": "Beijing", "line": "mineral pause kept",
     "detail": "Gallium curbs eased to Jan 27", "src": "REUTERS",
     "region": "ASIA", "flag": "CN"},
    {"n": 25, "city": "Bayelsa", "line": "boat toll now 32",
     "detail": "Crane lifts wreck; toll climbs", "src": "VANGUARD",
     "region": "AFRICA", "flag": "NG", "status": "ONGOING"},
    {"n": 26, "city": "Khan Younis", "line": "infant dies",
     "detail": "Gaza winter claims youngest victim", "src": "BBC",
     "region": "MIDDLE EAST", "flag": "PS"},
    {"n": 27, "city": "Khartoum", "line": "drone strikes kill 4",
     "detail": "Attacks hit near the capital", "src": "AFP",
     "region": "AFRICA", "flag": "SD"},
    {"n": 28, "city": "London", "line": "UK sanctions Houthis",
     "detail": "Four senior figures targeted", "src": "REUTERS",
     "region": "EUROPE", "flag": "GB"},
    {"n": 29, "city": "Caracas", "line": "debt put at $237.5bn",
     "detail": "First full accounts in years", "src": "REUTERS",
     "region": "AMERICAS", "flag": "VE"},
]

# Region tallies, counted from the 29 stories by subject:
# EUROPE 8 (6, 7, 9, 10, 19, 20, 23, 28); MIDDLE EAST 4 (11, 14,
# 17, 26); AFRICA 5 (1, 18, 21, 25, 27); ASIA 5 (4, 8, 12, 15,
# 24); AMERICAS 5 (3, 13, 16, 22, 29); OCEANIA 1 (5); WORLD 1 (2).
REGIONS = [("EUROPE", 8), ("MIDDLE EAST", 4), ("AFRICA", 5),
           ("ASIA", 5), ("AMERICAS", 5), ("OCEANIA", 1), ("WORLD", 1)]

# Six numbers for the dark-navy box, one big figure per top story.
# Figure colours follow the user's rule (v3.1): dead -> red (240,90,90);
# plus -> green (80,200,120); percentage >50% -> orange, >90% ->
# orange-red (240,100,50), 100% -> dark red; sea -> blue (90,130,230).
# Any other figure keeps its story's region colour (FIGURE_FILL).
NUMBERS = [
    ("7", "sea drones sink the Merkury", (90, 130, 230)),
    ("26", "dead in the Cikande fire", (240, 90, 90)),
    ("258", "House seats for Democrats", (175, 150, 230)),
    ("$1.62bn", "India's aid to Nepal", (228, 165, 75)),
    ("+31%", "Nvidia jumps on Huang", (80, 200, 120)),
    ("98.79%", "Hong Kong turnout", (240, 100, 50)),
]

# UTC timeline, Mon 23 Nov 21:29 UTC to Tue 24 Nov 14:00 UTC.
TIMELINE = [("21:29", "Benghazi secure"),
            ("22:17", "4 killed, Khartoum"),
            ("23:25", "Boat toll 29"),
            ("00:19", "UN worker killed"),
            ("01:25", "'Ghetto law' upheld"),
            ("02:20", "India pledges $1.6bn"),
            ("14:00", "Chess game 1 begins")]

# --- the map ---------------------------------------------------------------
# Numbered pins for the 13 drawn stories; navy dots for the 16
# also-list lines. Values are (longitude, latitude).
PINS = {1: (20.1, 32.1), 2: (30.7, 36.9), 3: (-121.9, 37.4),
        4: (106.1, -6.0), 5: (174.8, -41.3), 6: (7.7, 45.1),
        7: (24.7, 59.4), 8: (77.2, 28.6), 9: (6.1, 46.2),
        10: (30.0, 50.8), 11: (34.5, 31.5), 12: (114.2, 22.3),
        13: (-77.0, 38.9)}
DOTS = {14: (51.4, 35.7), 15: (90.4, 23.8), 16: (-74.0, 40.7),
        17: (44.4, 33.3), 18: (-6.8, 34.0), 19: (12.6, 55.7),
        20: (2.35, 48.85), 21: (31.0, -17.8), 22: (-75.7, 45.4),
        23: (13.4, 52.5), 24: (116.4, 39.9), 25: (6.3, 4.9),
        26: (34.5, 31.3), 27: (32.6, 15.6), 28: (-0.1, 51.5),
        29: (-66.9, 10.5)}
# Markers that would collide are fanned out a few pixels with a thin
# leader back to the true spot.
PIN_OFF = {1: (-18, 8), 2: (12, 6), 5: (-8, 0), 6: (16, 8),
           7: (0, -12), 10: (14, -6), 11: (-14, 14)}
DOT_OFF = {16: (10, -8), 17: (-12, -14), 19: (0, -10), 20: (-10, -8),
           22: (-12, -6), 23: (0, 12), 26: (0, 12), 28: (0, -12)}
REGION_OF = {s["n"]: s["region"] for s in STORIES}


# --- small helpers ---------------------------------------------------------
def _rect(g, x0, y0, x1, y1, fill=None, out=None, wdt=1):
    g.rectangle([x0, y0, x1, y1], fill=fill, outline=out, width=wdt)


def _oval(g, x0, y0, x1, y1, fill=None, out=None, wdt=1):
    g.ellipse([x0, y0, x1, y1], fill=fill, outline=out, width=wdt)


def _disc(g, cx, cy, r, fill, out=None, wdt=1):
    g.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill,
              outline=out, width=wdt)


def _line(g, pts, fill, wdt=1):
    g.line(pts, fill=fill, width=wdt)


def _poly(g, pts, fill=None, out=None):
    g.polygon(pts, fill=fill, outline=out)


def _text(g, xy, s, font, fill, anchor=None, stroke=0, sfill=None):
    g.text(xy, s, font=font, fill=fill, anchor=anchor,
           stroke_width=stroke, stroke_fill=sfill)


def _wrap(g, text, font, width, cap=None):
    """Greedy wrap to `width` px; records a problem past `cap` lines."""
    lines, cur = [], ""
    for word in text.split():
        trial = word if not cur else cur + " " + word
        if g.textlength(trial, font=font) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    if cap is not None and len(lines) > cap:
        PROBLEMS.append("TRUNCATED (%d lines): %s" % (len(lines), text))
        lines = lines[:cap]
    return lines


def _star(g, cx, cy, outer, inner, fill):
    """Five-point star for blasts, flags and bursts."""
    pts = []
    for k in range(10):
        r = outer if k % 2 == 0 else inner
        a = math.radians(-90 + k * 36)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    g.polygon(pts, fill=fill)


def _new(w, h):
    img = Image.new("RGB", (w, h))
    return img, ImageDraw.Draw(img)


def _shrink_font(g, text, font, maxw, floor, path):
    f = font
    while g.textlength(text, font=f) > maxw and f.size > floor:
        f = ImageFont.truetype(path, f.size - 1)
    return f


# --- flags -----------------------------------------------------------------
# Each flag is a list of ops on a 16x11 canvas; one painter reads
# them all. Op forms: ("hb", y0, y1, colour) horizontal band,
# ("vb", x0, x1, colour) vertical band, ("dot", cx, cy, r, colour),
# ("tri", pts, colour), ("box", x0, y0, x1, y1, colour),
# ("star", cx, cy, r, colour), ("x", colour, w) diagonal cross.
def _flag_ops(code):
    R = (200, 16, 46)
    if code == "IR":
        return [("hb", 0, 3, (0, 122, 61)), ("hb", 4, 7, "white"),
                ("hb", 8, 11, (218, 0, 0))]
    if code == "BD":
        return [("box", 0, 0, 16, 11, (0, 106, 78)),
                ("dot", 7, 5, 4, (244, 42, 65))]
    if code == "US":
        ops = []
        for i in range(7):
            ops.append(("hb", i * 11 // 7, (i + 1) * 11 // 7,
                        (178, 34, 52) if i % 2 == 0 else "white"))
        ops.append(("box", 0, 0, 6, 6, (60, 59, 110)))
        for sx in (2, 4):
            for sy in (2, 4):
                ops.append(("dot", sx, sy, 1, "white"))
        return ops
    if code == "IQ":
        return [("hb", 0, 3, (206, 17, 38)), ("hb", 4, 7, "white"),
                ("hb", 8, 11, (0, 0, 0)),
                ("box", 3, 5, 13, 6, (0, 122, 61))]
    if code == "MA":
        return [("box", 0, 0, 16, 11, (193, 39, 45)),
                ("star", 8, 5, 4, (0, 122, 61))]
    if code == "DK":
        return [("box", 0, 0, 16, 11, (200, 16, 46)),
                ("box", 5, 0, 7, 11, "white"),
                ("box", 0, 4, 16, 6, "white")]
    if code == "FR":
        return [("vb", 0, 5, (0, 85, 164)), ("vb", 5, 11, "white"),
                ("vb", 11, 16, (239, 65, 53))]
    if code == "ZW":
        ops = []
        cols = [(0, 122, 61), (255, 210, 0), (206, 17, 38), (0, 0, 0),
                (206, 17, 38), (255, 210, 0), (0, 122, 61)]
        for i, c in enumerate(cols):
            ops.append(("hb", i * 11 // 7, (i + 1) * 11 // 7, c))
        ops.append(("tri", [(0, 0), (0, 11), (7, 5)], "white"))
        ops.append(("star", 3, 5, 2, (206, 17, 38)))
        return ops
    if code == "CA":
        return [("vb", 0, 4, (255, 0, 0)), ("vb", 4, 12, "white"),
                ("vb", 12, 16, (255, 0, 0)),
                ("dot", 8, 5, 2, (255, 0, 0))]
    if code == "DE":
        return [("hb", 0, 3, (0, 0, 0)), ("hb", 4, 7, (221, 0, 0)),
                ("hb", 8, 11, (255, 206, 0))]
    if code == "CN":
        return [("box", 0, 0, 16, 11, (222, 41, 16)),
                ("star", 4, 3, 3, (255, 222, 0)),
                ("dot", 10, 2, 1, (255, 222, 0)),
                ("dot", 12, 4, 1, (255, 222, 0)),
                ("dot", 10, 7, 1, (255, 222, 0))]
    if code == "NG":
        return [("vb", 0, 5, (0, 135, 81)), ("vb", 5, 11, "white"),
                ("vb", 11, 16, (0, 135, 81))]
    if code == "PS":
        return [("hb", 0, 3, (0, 0, 0)), ("hb", 4, 7, "white"),
                ("hb", 8, 11, (0, 122, 61)),
                ("tri", [(0, 0), (0, 11), (7, 5)], (238, 0, 0))]
    if code == "SD":
        return [("hb", 0, 3, (210, 16, 52)), ("hb", 4, 7, "white"),
                ("hb", 8, 11, (0, 0, 0)),
                ("tri", [(0, 0), (0, 11), (6, 5)], (0, 122, 61)),
                ("dot", 3, 5, 1, (255, 210, 0))]
    if code == "GB":
        return [("box", 0, 0, 16, 11, (0, 36, 125)),
                ("x", "white", 2),
                ("box", 7, 0, 9, 11, R),
                ("box", 0, 4, 16, 7, R)]
    if code == "VE":
        return [("hb", 0, 3, (255, 204, 0)), ("hb", 4, 7, (0, 56, 147)),
                ("hb", 8, 11, (207, 20, 43)),
                ("dot", 5, 5, 1, "white"), ("dot", 8, 5, 1, "white"),
                ("dot", 11, 5, 1, "white")]
    return [("box", 0, 0, 16, 11, GREY)]


def _flag(g, code, x, y, w=16, h=11):
    """Paint a small flat flag (drawn, no emoji)."""
    for op in _flag_ops(code):
        kind = op[0]
        if kind == "hb":
            _, y0, y1, col = op
            g.rectangle([x, y + y0, x + w, y + y1], fill=col)
        elif kind == "vb":
            _, x0, x1, col = op
            g.rectangle([x + x0, y, x + x1, y + h], fill=col)
        elif kind == "dot":
            _, cx, cy, r, col = op
            _disc(g, x + cx, y + cy, r, col)
        elif kind == "tri":
            _, pts, col = op
            g.polygon([(x + px, y + py) for px, py in pts], fill=col)
        elif kind == "box":
            _, x0, y0, x1, y1, col = op
            g.rectangle([x + x0, y + y0, x + x1, y + y1], fill=col)
        elif kind == "star":
            _, cx, cy, r, col = op
            _star(g, x + cx, y + cy, r, r // 2, col)
        elif kind == "x":
            _, col, wdt = op
            g.line([(x, y), (x + w, y + h)], fill=col, width=wdt)
            g.line([(x + w, y), (x, y + h)], fill=col, width=wdt)
    g.rectangle([x, y, x + w, y + h], outline=(120, 120, 120), width=1)


# --- illustrations ---------------------------------------------------------
# Each scene paints one flat vector picture. Heroes paint at
# 260x105; smalls paint at 196x80 and are shrunk to 196x60. The
# top-left corner is kept clear for the white place tag and the
# bottom-right for the status pill.
def _scene_merkury(g, w, h):
    # Russian corvette listing hard off Libya: dark sea, grey hull
    # bow-down, smoke drifting, a drone above, burst amidships.
    _rect(g, 0, 0, w, h, (20, 60, 110))
    _line(g, [(0, 58), (w, 58)], (140, 180, 210))
    _poly(g, [(40, 58), (150, 58), (160, 46), (120, 52), (60, 52)],
          (90, 95, 105))
    _rect(g, 96, 38, 118, 52, (120, 125, 135))
    _line(g, [(107, 38), (107, 28)], (120, 125, 135), 2)
    for sx, sy, sr in ((128, 30, 8), (140, 22, 10), (152, 16, 7)):
        _disc(g, sx, sy, sr, (120, 120, 126))
    _star(g, 84, 48, 8, 3, (255, 140, 40))
    for wx in range(0, w, 24):
        _line(g, [(wx, 66), (wx + 12, 66)], "white")
    _oval(g, 150, 20, 160, 26, (90, 95, 105))
    _line(g, [(142, 18), (158, 18)], (200, 200, 210), 2)


def _scene_cop(g, w, h):
    # The climate talks fail: teal hall, round globe, thermometer
    # past the mark, a torn page, a NO DEAL band bottom-left, a
    # wall clock top-right and three delegates low on the right.
    _rect(g, 0, 0, w, h, (11, 110, 110))
    _disc(g, 51, 58, 31, (30, 120, 200), out=(20, 20, 20), wdt=2)
    for a, b, c, e in ((30, 39, 52, 53), (52, 55, 74, 71),
                       (30, 59, 44, 71)):
        g.ellipse([a, b, c, e], fill=(60, 180, 90))
    _line(g, [(22, 58), (80, 58)], "white")
    _rect(g, 132, 26, 142, 74, "white", out=(20, 20, 20))
    _rect(g, 134, 28, 140, 74, (220, 30, 40))
    _disc(g, 137, 78, 11, (220, 30, 40), out=(20, 20, 20), wdt=2)
    for ty in (32, 40, 48, 56, 64):
        _line(g, [(142, ty), (147, ty)], (20, 20, 20))
    _text(g, (154, 28), "+1.5°C", F.art_mid, "white")
    _text(g, (154, 50), "LIMIT", F.art_mid_sm, "white")
    _text(g, (154, 62), "PASSED", F.art_mid_sm, "white")
    _rect(g, 228, 22, 256, 78, "white", out=(20, 20, 20), wdt=2)
    for ly in (32, 42, 52):
        _line(g, [(236, ly), (248, ly)], (60, 60, 60), 2)
    _line(g, [(228, 22), (222, 40), (230, 56), (224, 78)], RED, 3)
    _rect(g, 8, 84, 108, 102, WINE)
    _text(g, (58, 93), "NO DEAL", F.art_mid, "white", anchor="mm")
    _disc(g, 205, 14, 9, "white", out=(20, 20, 20))
    _line(g, [(205, 14), (205, 7)], (20, 20, 20))
    _line(g, [(205, 14), (210, 16)], (20, 20, 20))
    for fx, shirt in ((152, (200, 60, 40)), (168, (40, 90, 160)),
                      (184, (240, 200, 60))):
        _disc(g, fx + 6, 80, 5, (220, 180, 140))
        _poly(g, [(fx, 96), (fx + 12, 96), (fx + 10, 87), (fx + 2, 87)],
              shirt)


def _scene_nvidia(g, w, h):
    # Nvidia brings Huang back: dark board, big green AI chip with
    # gold pins, a red arrow to a red flag, a rising green chart.
    _rect(g, 0, 0, w, h, (16, 24, 44))
    for ty in range(24, h, 14):
        _line(g, [(0, ty), (w, ty)], (30, 40, 60))
    _rect(g, 30, 26, 78, 62, (16, 140, 80), out=(60, 200, 120), wdt=2)
    for px in (36, 48, 60, 72):
        _line(g, [(px, 22), (px, 26)], GOLD, 2)
        _line(g, [(px, 62), (px, 66)], GOLD, 2)
    for py in (32, 44, 56):
        _line(g, [(26, py), (30, py)], GOLD, 2)
        _line(g, [(78, py), (82, py)], GOLD, 2)
    _text(g, (54, 44), "AI", F.art_mid, "white", anchor="mm")
    _line(g, [(84, 44), (120, 30), (150, 36)], RED, 3)
    _poly(g, [(150, 36), (140, 30), (140, 42)], RED)
    _rect(g, 156, 26, 186, 46, (200, 30, 40))
    _star(g, 171, 36, 6, 2, (255, 210, 31))
    _line(g, [(100, 78), (140, 66), (175, 70), (210, 52)],
          (60, 200, 120), 3)
    _text(g, (54, 88), "+31%", F.art_mid_sm, (60, 200, 120),
          anchor="mm")


def _scene_factory(g, w, h):
    # Candy-factory fire in Cikande: sawtooth roof, fire bursting
    # through, smoke drifting right, one glowing window.
    _rect(g, 0, 0, w, h, (180, 190, 205))
    _rect(g, 0, 62, w, h, (120, 120, 126))
    _rect(g, 20, 44, 176, 62, (90, 90, 100))
    for sx in (20, 52, 84, 116, 148):
        _poly(g, [(sx, 44), (sx + 16, 32), (sx + 32, 44)], (70, 70, 80))
    _rect(g, 168, 24, 176, 44, (70, 70, 80))
    _disc(g, 98, 36, 20, (255, 140, 40))
    _disc(g, 98, 40, 10, (255, 210, 31))
    _disc(g, 99, 44, 5, (255, 120, 30))
    for sx, sy, sr in ((98, 16, 7), (112, 10, 9), (130, 8, 8),
                       (146, 12, 6)):
        _disc(g, sx, sy, sr, (90, 90, 96))
    for wx in (30, 56, 130, 156):
        _rect(g, wx, 50, wx + 10, 58, (40, 40, 50))
    _rect(g, 82, 50, 92, 58, (255, 180, 60))


def _scene_cricket(g, w, h):
    # Wellington test ends in a draw: green outfield, brown strip,
    # stumps, a bat, a red ball, and a scoreboard reading 720/9.
    _rect(g, 0, 0, w, h, (40, 130, 70))
    _rect(g, 60, 20, 140, h, (190, 170, 120))
    _line(g, [(60, 20), (60, h)], "white")
    _line(g, [(140, 20), (140, h)], "white")
    for sy in (30, 44, 58):
        _line(g, [(88, sy), (92, sy)], (230, 200, 60), 3)
        _line(g, [(108, sy), (112, sy)], (230, 200, 60), 3)
    _poly(g, [(150, 30), (158, 30), (164, 62), (156, 62)], (210, 180, 120),
          out=(120, 90, 60))
    _disc(g, 175, 44, 5, (200, 30, 40), out="white")
    _rect(g, w - 52, 14, w - 8, 36, (20, 20, 30))
    _text(g, (w - 30, 25), "720/9", F.art_mid, "white", anchor="mm")
    _text(g, (30, h - 10), "DRAW", F.art_mid_sm, "white", anchor="mm")


def _scene_tennis(g, w, h):
    # Alcaraz wins in Turin: blue court, white lines, net, gold
    # trophy and a yellow ball.
    _rect(g, 0, 0, w, h, (30, 90, 170))
    _rect(g, 20, 18, w - 20, h - 12, (60, 140, 220))
    _line(g, [(20, 52), (w - 20, 52)], "white", 2)
    _line(g, [(w // 2, 18), (w // 2, h - 12)], "white", 2)
    _line(g, [(20, h - 12), (w - 20, h - 12)], "white", 2)
    _poly(g, [(150, 30), (170, 30), (166, 52), (154, 52)], GOLD)
    _rect(g, 148, 26, 152, 34, GOLD)
    _rect(g, 168, 26, 172, 34, GOLD)
    _disc(g, 60, 34, 7, (230, 230, 40), out="white")
    _text(g, (44, 62), "6-2, 7-6", F.art_mid_sm, "white",
          anchor="mm")


def _scene_border(g, w, h):
    # Russia warns Estonia: a fence across a grey field, a red
    # warning sign, the Estonian and Russian flags on poles.
    _rect(g, 0, 0, w, h, (200, 205, 210))
    _rect(g, 0, 62, w, h, (120, 125, 110))
    for px in range(16, w, 18):
        _line(g, [(px, 26), (px, 62)], (70, 70, 80), 3)
    _line(g, [(0, 32), (w, 32)], (70, 70, 80), 2)
    _line(g, [(0, 48), (w, 48)], (70, 70, 80), 2)
    for fx, cols in ((24, ((0, 114, 187), (0, 0, 0), "white")),
                     (168, ("white", (0, 114, 187), (200, 30, 40)))):
        _line(g, [(fx, 22), (fx, 58)], (60, 60, 60), 2)
        _rect(g, fx, 22, fx + 24, 30, cols[0])
        _rect(g, fx, 30, fx + 24, 38, cols[1])
        _rect(g, fx, 38, fx + 24, 46, cols[2])
    _rect(g, 96, 58, 164, 78, (200, 30, 40), out=(120, 0, 0), wdt=2)
    _text(g, (130, 65), "CLOSED", F.art_sm, "white", anchor="mm")
    _text(g, (130, 74), "1 DEC", F.art_sm, "white", anchor="mm")


def _scene_aid(g, w, h):
    # India gives Nepal $1.62bn: a plane on the runway under a
    # pale sky, Indian and Nepali flags on poles.
    _rect(g, 0, 0, w, h, (200, 220, 235))
    _rect(g, 0, 58, w, h, (90, 90, 98))
    for dx in range(6, w, 22):
        _line(g, [(dx, 66), (dx + 11, 66)], "white", 2)
    for fx, cols in ((24, ((255, 150, 0), "white", (0, 130, 60))),
                     (164, ((200, 30, 50), (20, 60, 140), None))):
        _line(g, [(fx, 24), (fx, 58)], (60, 60, 60), 2)
        _rect(g, fx, 24, fx + 22, 32, cols[0])
        _rect(g, fx, 32, fx + 22, 40, cols[1])
        if cols[2]:
            _rect(g, fx, 40, fx + 22, 48, cols[2])
    _oval(g, 70, 44, 132, 54, (40, 90, 160))
    _poly(g, [(124, 46), (132, 38), (136, 46)], (40, 90, 160))
    _poly(g, [(84, 52), (94, 62), (98, 52)], (40, 90, 160))
    for wx in (84, 118):
        _disc(g, wx, 58, 4, (20, 20, 20))
    _text(g, (w - 6, 10), "$1.62BN", F.art_mid_sm, (20, 60, 140),
          anchor="ra")


def _scene_chess(g, w, h):
    # Gukesh v Sindarov, game 1: a chessboard, a white king and a
    # black queen facing off, a clock at the side.
    _rect(g, 0, 0, w, h, (30, 40, 70))
    bx, by, cs = 24, 12, 7
    for r in range(8):
        for c in range(8):
            col = (235, 225, 200) if (r + c) % 2 == 0 else (90, 60, 40)
            _rect(g, bx + c * cs, by + r * cs, bx + (c + 1) * cs,
                  by + (r + 1) * cs, col)
    _disc(g, bx + 2 * cs, by + 2 * cs, 5, "white", out=INK)
    _disc(g, bx + 5 * cs, by + 5 * cs, 5, (20, 20, 20), out="white")
    _text(g, (bx + 2 * cs, by + 2 * cs), "K", F.art_sm, INK,
          anchor="mm")
    _text(g, (bx + 5 * cs, by + 5 * cs), "Q", F.art_sm, "white",
          anchor="mm")
    _rect(g, 100, 18, 188, 54, "white", out=INK, wdt=2)
    _disc(g, 122, 36, 9, (240, 240, 240), out=INK)
    _disc(g, 166, 36, 9, (240, 240, 240), out=INK)
    _line(g, [(122, 36), (122, 29)], INK)
    _line(g, [(166, 36), (171, 32)], INK)
    _text(g, (120, 70), "GAME 1", F.art_mid_sm, GOLD, anchor="mm")


def _scene_rescue(g, w, h):
    # Boy freed after 14 hours in Dymer: a RESCUE, not a building.
    # Bright blue sky and a big red ladder are the focus; a rescuer
    # in orange with a yellow helmet reaches a child at the top.
    # The damaged block is only a small dark silhouette at the
    # left edge, so the scene reads nothing like the grey destroyed
    # building of the strike scene (#11).
    _rect(g, 0, 0, w, h, (110, 190, 245))
    _disc(g, 176, 14, 10, GOLD, out=INK)
    _disc(g, 28, 10, 6, "white")
    _disc(g, 36, 12, 5, "white")
    _disc(g, 120, 8, 5, "white")
    _rect(g, 0, 72, w, h, (235, 220, 190))
    _rect(g, 0, 52, 26, h, (75, 72, 85))
    _rect(g, 5, 58, 11, 64, (40, 40, 50))
    _rect(g, 15, 58, 21, 64, (40, 40, 50))
    _line(g, [(78, 80), (128, 22)], (215, 60, 25), 4)
    _line(g, [(90, 80), (140, 22)], (215, 60, 25), 4)
    for x0, x1, ry in ((86, 98, 71), (93, 105, 63), (100, 112, 54),
                       (108, 120, 45), (115, 127, 37), (123, 135, 28)):
        _line(g, [(x0, ry), (x1, ry)], (215, 60, 25), 2)
    _disc(g, 112, 34, 7, (255, 210, 31), out=INK)
    _rect(g, 105, 40, 119, 58, (240, 110, 30), out=INK)
    _rect(g, 107, 58, 111, 68, (40, 40, 50))
    _rect(g, 114, 58, 118, 68, (40, 40, 50))
    _line(g, [(118, 44), (130, 30)], (240, 110, 30), 3)
    _disc(g, 136, 15, 5, (255, 200, 150), out=INK)
    _rect(g, 131, 20, 141, 34, (20, 150, 120), out=INK)
    _line(g, [(131, 24), (124, 20)], (20, 150, 120), 2)
    _line(g, [(141, 24), (148, 20)], (20, 150, 120), 2)


def _scene_strike(g, w, h):
    # Israeli strike kills a UNRWA worker in Gaza: a damaged
    # building, smoke, a white UN flag, a red cross marker.
    _rect(g, 0, 0, w, h, (190, 185, 170))
    _rect(g, 24, 30, 120, h, (140, 130, 120))
    for wy in (38, 52, 66):
        for wx in (34, 58, 82):
            _rect(g, wx, wy, wx + 12, wy + 8, (50, 50, 55))
    _poly(g, [(24, 30), (72, 16), (120, 30)], (90, 85, 80))
    for sx, sy, sr in ((140, 22, 8), (156, 14, 10), (172, 20, 7)):
        _disc(g, sx, sy, sr, (120, 120, 126))
    _line(g, [(170, 30), (170, 62)], (60, 60, 60), 2)
    _rect(g, 170, 30, 194, 44, "white", out=(120, 120, 120))
    _text(g, (182, 37), "UN", F.art_sm, (30, 90, 170), anchor="mm")
    _rect(g, 140, 44, 172, 62, (200, 30, 40))
    _rect(g, 153, 47, 161, 59, "white")
    _rect(g, 145, 52, 169, 56, "white")


def _scene_ballot(g, w, h):
    # Record Hong Kong turnout: a ballot box, a hand dropping a
    # ballot, a 98.79% tag.
    _rect(g, 0, 0, w, h, (210, 200, 230))
    _rect(g, 40, 48, 150, h - 6, (40, 90, 170), out=INK, wdt=2)
    _rect(g, 40, 48, 150, 58, (30, 70, 140))
    _line(g, [(80, 52), (110, 52)], INK, 3)
    _poly(g, [(100, 26), (128, 26), (124, 50), (104, 50)], "white",
          out=INK)
    _text(g, (114, 38), "✓", F.art_mid, GREEN, anchor="mm")
    _text(g, (w - 6, 20), "98.79%", F.art_mid, (30, 90, 170),
          anchor="ra")
    _text(g, (w - 6, 40), "TURNOUT", F.art_mid_sm, INK, anchor="ra")
    _text(g, (95, h - 8), "723 SEATS", F.art_mid_sm, "white",
          anchor="mm")


def _scene_capitol(g, w, h):
    # Democrats clinch 258 House seats: navy hall, white dome with
    # columns and a gold cupola, a seat bar 258 blue / 177 red,
    # a flag on the right. Drawn for the 196x80 small format.
    _rect(g, 0, 0, w, h, NAVY)
    for sx, sy in ((16, 12), (60, 10), (150, 12), (180, 10)):
        _disc(g, sx, sy, 1, "white")
    _oval(g, 58, 22, 138, 56, "white")
    _rect(g, 56, 44, 140, 56, "white")
    for cx in (70, 85, 100, 115, 130):
        _line(g, [(cx, 44), (cx, 56)], NAVY, 2)
    _rect(g, 48, 56, 148, 60, "white")
    _rect(g, 86, 14, 110, 22, "white")
    _disc(g, 98, 13, 7, GOLD)
    _rect(g, 30, 64, 86, 76, (40, 90, 200))
    _rect(g, 86, 64, 132, 76, (200, 40, 50))
    _text(g, (58, 70), "258", F.art_mid_sm, "white", anchor="mm")
    _text(g, (109, 70), "177", F.art_mid_sm, "white", anchor="mm")
    _text(g, (w - 6, 8), "SINCE 1992", F.art_sm, GOLD, anchor="ra")
    _line(g, [(156, 20), (156, 60)], (200, 200, 210), 2)
    _rect(g, 156, 20, 182, 32, (200, 40, 50))
    for sy in (24, 28):
        _line(g, [(156, sy), (182, sy)], "white")
    _rect(g, 156, 20, 168, 26, (40, 60, 140))
    _disc(g, 162, 23, 1, "white")


SCENES = {"merkury": _scene_merkury, "cop": _scene_cop,
          "nvidia": _scene_nvidia, "factory": _scene_factory,
          "cricket": _scene_cricket, "tennis": _scene_tennis,
          "border": _scene_border, "aid": _scene_aid,
          "chess": _scene_chess, "rescue": _scene_rescue,
          "strike": _scene_strike, "ballot": _scene_ballot,
          "capitol": _scene_capitol}


def _paint(g, key, w, h):
    """Paint a scene at w x h and return it as an image."""
    img, d = _new(w, h)
    SCENES[key](d, w, h)
    return img


def _place_tag(g, x, y, w, story, font, boxh, discr, pad):
    """The white place box fitted to the text length only, inside
    the picture at the top-left, with the story number in a disc
    coloured by its region."""
    label = story["place"] + ", " + story["country"]
    f = _shrink_font(g, label, font, w - 40, 8,
                     os.path.join(_NOTO, "NotoSans-Bold.ttf"))
    tw = int(g.textlength(label, font=f))
    bw = pad + discr * 2 + 4 + tw + pad
    bx, by = x + pad, y + pad
    g.rectangle([bx, by, bx + bw, by + boxh], fill="white",
                outline=INK, width=1)
    _disc(g, bx + pad + discr, by + boxh // 2, discr,
          REGION_FILL[story["region"]])
    _text(g, (bx + pad + discr, by + boxh // 2), str(story["n"]),
          F.tag, "white", anchor="mm")
    _text(g, (bx + pad + discr * 2 + 4, by + boxh // 2), label, f,
          INK, anchor="lm")


def _status_pill(g, x, y, w, h, tag):
    """Status pill at the bottom-right corner of a picture."""
    pw = int(g.textlength(tag, font=F.tag)) + 10
    x1, y1 = x + w - 4, y + h - 3
    g.rounded_rectangle([x1 - pw, y1 - 12, x1, y1], radius=2,
                        fill=STATUS_FILL[tag])
    _text(g, (x1 - pw + 5, y1 - 6), tag, F.tag, "white", anchor="lm")


def _hero_card(img, g, story, x, y, w):
    """A lead card, 252 tall: 105px art with the place tag inside
    it top-left and the status pill bottom-right, a coloured
    REGION · TOPIC line, a 2–3 line 25px serif headline, a 2–3
    line 12px serif deck and a 9px source line, in a 1px ink box."""
    _rect(g, x, y, x + w, y + HERO_H, CARD)
    img.paste(_paint(g, story["art"], w, ART_H), (x, y))
    g2 = ImageDraw.Draw(img)
    _place_tag(g2, x, y, w, story, F.place, 18, 7, 4)
    _status_pill(g2, x, y, w, ART_H, story["tag"])
    ty = y + ART_H + 6
    _text(g, (x + 8, ty), "%s · %s" % (story["region"], story["topic"]),
          F.topic, REGION_FILL[story["region"]])
    hl = _wrap(g, story["head"], F.hero_head, w - 16, 3)
    dl = _wrap(g, story["deck"], F.hero_deck, w - 16, 3)
    hy = ty + 16
    for j, ln in enumerate(hl):
        _text(g, (x + 8, hy + j * 29), ln, F.hero_head, INK)
    dy = hy + len(hl) * 29 + 2
    for j, ln in enumerate(dl):
        _text(g, (x + 8, dy + j * 14), ln, F.hero_deck, MIDGREY)
    _text(g, (x + 8, y + HERO_H - 14), story["src"], F.src, GREY)
    g.rectangle([x, y, x + w, y + HERO_H], outline=INK, width=1)


def _small_card(img, g, story, x, y):
    """A small card, 146 tall: 60px mini scene with the place tag
    inside it top-left and the status pill bottom-right, a coloured
    REGION · TOPIC line, a 2-line 17px serif headline and a 2-line
    11px serif deck with its source, in a 1px ink box."""
    w = SMALL_W
    _rect(g, x, y, x + w, y + SMALL_H, CARD)
    pic = _paint(g, story["art"], w, 80).resize((w, SMALL_ART),
                                               Image.LANCZOS)
    img.paste(pic, (x, y))
    g2 = ImageDraw.Draw(img)
    _place_tag(g2, x, y, w, story, F.place_sm, 15, 6, 3)
    _status_pill(g2, x, y, w, SMALL_ART, story["tag"])
    ty = y + SMALL_ART + 5
    _text(g, (x + 8, ty), "%s · %s" % (story["region"], story["topic"]),
          F.topic_sm, REGION_FILL[story["region"]])
    hl = _wrap(g, story["head"], F.small_head, w - 16, 2)
    for j, ln in enumerate(hl):
        _text(g, (x + 8, ty + 14 + j * 20), ln, F.small_head, INK)
    dl = _wrap(g, story["deck"] + " — " + story["src"], F.small_deck,
               w - 16, 2)
    for j, ln in enumerate(dl):
        _text(g, (x + 8, ty + 15 + len(hl) * 20 + j * 12), ln,
              F.small_deck, MIDGREY)
    g.rectangle([x, y, x + w, y + SMALL_H], outline=INK, width=1)


def _numbers_panel(g, x, y):
    """The dark-navy THE DAY IN NUMBERS box, fourth column of the
    hero row: title plus six big figures, each in its NUMBERS fill
    (user colour rule, see NUMBERS), over a 10px label."""
    _rect(g, x, y, x + NUM_W, y + HERO_H, NAVY)
    _text(g, (x + 10, y + 8), "THE DAY IN NUMBERS", F.num_title, "white")
    _line(g, [(x + 10, y + 26), (x + NUM_W - 10, y + 26)],
          (80, 100, 140))
    ey = y + 30
    for value, label, fill in NUMBERS:
        fv = _shrink_font(g, value, F.num_big, NUM_W - 20, 18,
                          os.path.join(_NOTO, "NotoSans-Black.ttf"))
        _text(g, (x + 10, ey), value, fv, fill)
        _text(g, (x + 10, ey + 26), label, F.num_lab, (200, 210, 230))
        ey += 36
    g.rectangle([x, y, x + NUM_W, y + HERO_H], outline=INK, width=1)


def _inside(lon, lat, polys):
    """Ray-casting point-in-polygon against (ring, bbox) pairs."""
    for ring, (x0, x1, y0, y1) in polys:
        if not (x0 <= lon <= x1 and y0 <= lat <= y1):
            continue
        inside, n, j = False, len(ring), len(ring) - 1
        for i in range(n):
            xi, yi = ring[i]
            xj, yj = ring[j]
            if (yi > lat) != (yj > lat):
                xint = (xj - xi) * (lat - yi) / (yj - yi) + xi
                if lon < xint:
                    inside = not inside
            j = i
        if inside:
            return True
    return False


def _world_map(g, x0, y0, w, h):
    """Dotted world map: pale blue sea, land as a grid of dark
    dots (world.geo.json), navy dots for the also-list stories,
    numbered region-coloured pins for the drawn stories. Markers
    that would collide are fanned out with a thin leader back to
    their true spot."""
    with open(os.path.join(HERE, "world.geo.json")) as fh:
        geo = json.load(fh)
    polys = []
    for feat in geo["features"]:
        geom = feat["geometry"]
        rings = [geom["coordinates"]] if geom["type"] == "Polygon" \
            else geom["coordinates"]
        for ringset in rings:
            ring = ringset[0]
            xs = [p[0] for p in ring]
            ys = [p[1] for p in ring]
            polys.append((ring, (min(xs), max(xs), min(ys), max(ys))))

    def px(lon):
        return x0 + (lon + 180.0) / 360.0 * w

    def py(lat):
        return y0 + (90.0 - lat) / 180.0 * h

    _rect(g, x0, y0, x0 + w, y0 + h, SEA)
    for gy in range(2, h, 3):
        lat = 90.0 - (gy / h) * 180.0
        for gx in range(2, w, 3):
            lon = (gx / w) * 360.0 - 180.0
            if _inside(lon, lat, polys):
                _disc(g, x0 + gx, y0 + gy, 1.2, (150, 150, 150))
    for num, (lon, lat) in DOTS.items():
        tx, ty = px(lon), py(lat)
        ox, oy = DOT_OFF.get(num, (0, 0))
        if (ox, oy) != (0, 0):
            _line(g, [(tx, ty), (tx + ox, ty + oy)], INK)
        _disc(g, tx + ox, ty + oy, 2, NAVY)
    for num, (lon, lat) in PINS.items():
        tx, ty = px(lon), py(lat)
        ox, oy = PIN_OFF.get(num, (0, 0))
        if (ox, oy) != (0, 0):
            _line(g, [(tx, ty), (tx + ox, ty + oy)],
                  REGION_FILL[REGION_OF[num]])
        cx, cy = tx + ox, ty + oy
        _disc(g, cx, cy, 7, REGION_FILL[REGION_OF[num]], out="white")
        _text(g, (cx, cy), str(num), F.pin if num < 10 else F.pin_sm,
              "white", anchor="mm")


def _segs(g, x, y, parts, font):
    """Draw [(text, fill), ...] in sequence on one line."""
    cx = x
    for text, fill in parts:
        _text(g, (cx, y), text, font, fill)
        cx += int(g.textlength(text, font=font))
    return cx


def assemble():
    img, g = _new(W, H)
    _rect(g, 0, 0, W - 1, H - 1, PAPER)
    # ---- top bar 0-18: dark navy, white name left, gold count right.
    _rect(g, 0, 0, W, 18, NAVY)
    _text(g, (MX, 9), "THE WORLD IN ONE DAY", F.bar, "white",
          anchor="lm")
    _text(g, (RX, 9), "29 STORIES · 7 REGIONS · ALL FROM THIS ONE DAY",
          F.bar, GILT, anchor="rm")
    # ---- masthead: the date in a Didone at 88px, squeezed to 996
    # wide so its ink top sits at 24 (ink 24-110, 86px tall).
    title = "Tuesday 24 November 2026"
    lw = int(g.textlength(title, font=F.mast)) + 12
    layer = Image.new("RGBA", (lw, 150), (0, 0, 0, 0))
    lt = ImageDraw.Draw(layer)
    lt.text((4, 0), title, font=F.mast, fill=INK + (255,),
            stroke_width=2, stroke_fill=INK + (255,))
    ink_top = layer.getbbox()[1]
    layer = layer.resize((996, 150), Image.LANCZOS)
    img.paste(layer, (MX, 24 - ink_top), layer)
    # ---- red kicker: bold ITALIC serif, one line, stretched to
    # exactly 1000px wide, ink top y=120 (5px gap below the
    # masthead "y" descender).
    kicker = ("7 sea drones sink a Russian corvette off Libya · "
              "COP31 collapses with no deal · Nvidia brings Huang "
              "back as CEO")
    klayer = Image.new("RGBA", (1100, 60), (0, 0, 0, 0))
    kd = ImageDraw.Draw(klayer)
    kd.text((0, 0), kicker, font=F.kicker, fill=RED + (255,))
    kb = klayer.getbbox()
    kcrop = klayer.crop(kb).resize((1000, kb[3] - kb[1]), Image.LANCZOS)
    img.paste(kcrop, (MX, 119), kcrop)
    # ---- region bar 150-168: seven SEPARATE boxes, 18px tall,
    # 12px text, each sized to its text, ~7px white gaps, centred.
    by, bh, gap = 150, 18, 7
    widths = [int(g.textlength("%s %d" % (label, count), font=F.region))
              + 20 for label, count in REGIONS]
    total = sum(widths) + gap * (len(widths) - 1)
    sx = (W - total) // 2
    for (label, count), w in zip(REGIONS, widths):
        _rect(g, sx, by, sx + w, by + bh, REGION_FILL[label])
        _text(g, (sx + w / 2, by + 9), "%s %d" % (label, count),
              F.region, "white", anchor="mm")
        sx += w + gap
    # ---- UTC timeline 172-192: dark-navy band EDGE TO EDGE
    # (x 12–1012), small red UTC box 26x14 at the left, gold bold
    # times, white events, middot separators, spread across the
    # full width so the last item ends exactly at RX.
    tl_y, tl_h = 172, 20
    _rect(g, MX, tl_y, RX, tl_y + tl_h, NAVY)
    _rect(g, MX, tl_y + 3, MX + 26, tl_y + 17, RED)
    _text(g, (MX + 13, tl_y + 10), "UTC", F.utc, "white", anchor="mm")
    sep = "  ·  "
    sepw = int(g.textlength(sep, font=F.clock))
    nat = sum(int(g.textlength(tt, font=F.clock))
              + int(g.textlength(" " + ev, font=F.clock_ev))
              for tt, ev in TIMELINE) + sepw * (len(TIMELINE) - 1)
    extra = (RX - (MX + 34)) - nat
    ngap = len(TIMELINE) - 1
    tgap, rem = (extra // ngap, extra % ngap) if ngap else (0, 0)
    if extra < 0:
        PROBLEMS.append("TIMELINE OVERFLOW by %d px" % -extra)
    tx = MX + 34
    for i, (tt, ev) in enumerate(TIMELINE):
        _text(g, (tx, tl_y + tl_h // 2), tt, F.clock, GOLD, anchor="lm")
        tx += int(g.textlength(tt, font=F.clock))
        _text(g, (tx, tl_y + tl_h // 2), " " + ev, F.clock_ev, "white",
              anchor="lm")
        tx += int(g.textlength(" " + ev, font=F.clock_ev))
        if i < len(TIMELINE) - 1:
            _text(g, (tx, tl_y + tl_h // 2), sep, F.clock, GOLD,
                  anchor="lm")
            tx += sepw + tgap + (1 if i < rem else 0)
    # ---- heroes 200-452: three 260px leads, then the numbers box.
    hx = MX
    for story in STORIES[:3]:
        _hero_card(img, g, story, hx, HERO_Y, HERO_W)
        hx += HERO_W + 8
    _numbers_panel(g, hx, HERO_Y)
    # ---- smalls 460-760: two rows of five, 196 wide, 204 pitch.
    for r in range(2):
        for c in range(5):
            _small_card(img, g, STORIES[3 + r * 5 + c],
                        MX + c * 204, SMALL_Y + r * SMALL_ROW)
    # ---- also-list (left) + map (right) 768-938. Three columns:
    # 14-19, 20-24, 25-29. Each item is two lines: the main line,
    # then a small grey sub-line (detail + source) below it.
    _text(g, (MX, MID_Y), "ALSO ON TUESDAY 24 NOVEMBER", F.section, INK)
    px = 652
    for lab in ("ONGOING", "CLAIM", "REPORTED"):
        tw = int(g.textlength(lab, font=F.tag))
        pw, x0 = tw + 12, px - (tw + 12)
        g.rounded_rectangle([x0, MID_Y - 1, px, MID_Y + 13], radius=2,
                            fill=LEGEND_FILL[lab])
        _text(g, (x0 + pw / 2, MID_Y + 6), lab, F.tag, "white",
              anchor="mm")
        px = x0 - 6
    _text(g, (px - 6, MID_Y), "16 MORE STORIES", F.section, INK,
          anchor="ra")
    _line(g, [(MX, MID_Y + 16), (652, MID_Y + 16)], INK)
    col_w, col_gap, pitch = 200, 20, 24
    for item in ALSO:
        num = item["n"]
        col_i, row = (0, num - 14) if num <= 19 else \
            ((1, num - 20) if num <= 24 else (2, num - 25))
        x = MX + col_i * (col_w + col_gap)
        y = MID_Y + 18 + row * pitch
        _text(g, (x, y), "%d." % num, F.also_num,
              REGION_FILL[item["region"]])
        _flag(g, item["flag"], x + 20, y, 16, 11)
        full = "%s: %s" % (item["city"], item["line"])
        lines = _wrap(g, full, F.also_main, col_w - 40, 1)
        _text(g, (x + 40, y), lines[0] if lines else "", F.also_main,
              INK)
        _text(g, (x + 40, y + 11),
              "%s · %s" % (item["detail"], item["src"]), F.also_sub,
              GREY)
    map_x, map_w, map_h = 680, 332, 148
    _rect(g, map_x, MID_Y, map_x + map_w, MID_Y + 170, SEA)
    g.rectangle([map_x, MID_Y, map_x + map_w, MID_Y + 170],
                outline=FAINT, width=1)
    _world_map(g, map_x, MID_Y + 22, map_w, map_h)
    _text(g, (map_x + 8, MID_Y + 8), "WHERE IT HAPPENED", F.section,
          INK)
    _text(g, (RX - 8, MID_Y + 8), "pins = story numbers", F.src, GREY,
          anchor="ra")
    # ---- date check 942-992: strong red box, solid red label with
    # white bold text, 12px bold body, "Left out" and "Not yet
    # confirmed" lead-ins and every date in bold red.
    g.rectangle([MX, CHK_Y, RX, CHK_Y + 50], outline=RED, width=2)
    g.rectangle([20, CHK_Y + 3, 115, CHK_Y + 17], fill=RED)
    _text(g, (67, CHK_Y + 10), "DATE CHECK", F.src, "white",
          anchor="mm")
    _segs(g, 123, CHK_Y + 4, [
        ("Every story here happened or was first reported on "
         "Tuesday 24 November 2026 (UTC). ", INK),
        ("Left out because they happened on an earlier day:", RED),
    ], F.check)
    _segs(g, 20, CHK_Y + 18, [
        ("ICJ Myanmar ruling ", INK), ("19 Nov", RED),
        (" · Waymo ban ", INK), ("11 Nov", RED),
        (" · Fiona ", INK), ("19 Nov", RED), (".", INK),
    ], F.check)
    _segs(g, 20, CHK_Y + 32, [
        ("Not yet confirmed: ", RED),
        ("Libya's claim the Merkury was only damaged. ", INK),
        ("Tonight's real count: 7 sea drones sank the Merkury.",
         INK),
    ], F.check)
    # ---- footer 996-1018: centred sources line, then the HOW
    # SURE legend as one line.
    _text(g, (512, FOOT_Y),
          "Sources: Reuters · AP · AFP · BBC · Al Jazeera · UN News · "
          "CNN · RTHK · ATP · FIDE · Vanguard · Corrections: none",
          F.foot, GREY, anchor="ma")
    hx = 20 + int(g.textlength("HOW SURE: ", font=F.foot))
    _text(g, (20, FOOT_Y + 11), "HOW SURE: ", F.foot, RED)
    _text(g, (hx, FOOT_Y + 11),
          "REPORTED = carried by the day's wires or officials · "
          "CLAIM = one side's account, labelled as such · ONGOING "
          "= still unfolding · Scenes are drawn illustrations, not "
          "photographs.", F.foot, INK)
    return img


def main():
    img = assemble()
    out_path = os.path.join(HERE, "entry.png")
    img.save(out_path)
    print("saved", out_path, os.path.getsize(out_path), "bytes")
    if PROBLEMS:
        print("ISSUES:")
        for problem in PROBLEMS:
            print(" -", problem)
    else:
        print("no truncation")


if __name__ == "__main__":
    main()

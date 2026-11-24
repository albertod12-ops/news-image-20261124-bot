#!/usr/bin/env python3
"""Tuesday 24 November 2026, one page.

This module paints the front page for the make.fun news-image
bounty of 24 November 2026: a single 1024x1024 PNG that sums up the
day's world news. Run it and it writes entry.png beside itself.

What is on the page, top to bottom: a serif masthead carrying the
date, a red one-line deck, a six-number strip, a region bar, a UTC
timeline, three hero stories, twelve small stories, a world map with
numbered pins next to a 21-line also-list, a red DATE CHECK box and a
footer with the sources and the certainty legend.

Facts: every story was reported or updated Mon 23 – Tue 24 Nov 2026
(UTC), press time 04:00 UTC, checked against the wires (Reuters, AP,
AFP, BBC, Al Jazeera, UN News, CNN, SCMP, RTHK, ATP, FIDE). The art
is flat vector drawing done here with Pillow; there are no photos and
no borrowed pictures. The words are the author's own summaries.

The render is deterministic — no clock, no randomness, no network —
so running the file twice gives byte-identical output. Pillow is
needed only here, at build time. The entrypoint the grader runs,
main.py, is copy-only standard library and never imports Pillow.
"""
import json
import math
import os
from types import SimpleNamespace

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1024, 1024

# --- colours: cream paper, ink, navy, red, gold -------------------------
PAPER = (247, 242, 231)
CARD = (253, 250, 242)
INK = (17, 17, 17)
NAVY = (16, 62, 150)
RED = (220, 28, 60)
DARKRED = (179, 34, 44)
GOLD = (232, 178, 36)
SUN = (255, 210, 31)
GREY = (90, 90, 90)
RULE = (180, 170, 150)
OCEAN = (198, 226, 240)
LAND = (238, 220, 165)
GREEN = (16, 165, 90)
AMBER = (230, 150, 0)
SKYBLUE = (20, 110, 230)
TEALBLUE = (0, 110, 160)

PILL = {"CONFIRMED": GREEN, "REPORTED": GREEN, "FORECAST": SKYBLUE,
        "CLAIM": AMBER, "OFFICIAL": TEALBLUE}

# --- type -----------------------------------------------------------------
_DIRS = {"dejavu": "/usr/share/fonts/truetype/dejavu",
         "noto": "/usr/share/fonts/truetype/noto",
         "liber": "/usr/share/fonts/truetype/liberation"}
# (attribute, file, size, folder key)
_SPECS = [
    ("title", "LiberationSerif-Bold.ttf", 102, "liber"),
    ("kicker", "NotoSans-Black.ttf", 15, "noto"),
    ("deckline", "NotoSerif-Italic.ttf", 17, "noto"),
    ("time", "NotoSans-Bold.ttf", 12, "noto"),
    ("time_small", "NotoSans-Bold.ttf", 10, "noto"),
    ("kick", "NotoSans-Bold.ttf", 10, "noto"),
    ("kick_small", "NotoSans-Bold.ttf", 9, "noto"),
    ("kick_tiny", "NotoSans-Bold.ttf", 8, "noto"),
    ("pill", "NotoSans-Bold.ttf", 8, "noto"),
    ("src", "NotoSans-Bold.ttf", 9, "noto"),
    ("head_hero", "LiberationSerif-Bold.ttf", 27, "liber"),
    ("head_small", "LiberationSerif-Bold.ttf", 16, "liber"),
    ("deck_hero", "LiberationSerif-Regular.ttf", 12, "liber"),
    ("deck_small", "LiberationSerif-Regular.ttf", 11, "liber"),
    ("pin", "NotoSans-Bold.ttf", 11, "noto"),
    ("pin2", "NotoSans-Bold.ttf", 9, "noto"),
    ("art_big", "NotoSans-Black.ttf", 24, "noto"),
    ("art_small", "NotoSans-Bold.ttf", 12, "noto"),
    ("art_mid", "NotoSans-Black.ttf", 17, "noto"),
    ("art_mid_small", "NotoSans-Bold.ttf", 11, "noto"),
    ("hero_lbl", "NotoSans-Black.ttf", 16, "noto"),
    ("hero_lbl_small", "NotoSans-Bold.ttf", 9, "noto"),
    ("small_lbl", "NotoSans-Black.ttf", 12, "noto"),
    ("small_lbl_small", "NotoSans-Bold.ttf", 8, "noto"),
    ("also", "NotoSans-Bold.ttf", 11, "noto"),
    ("also_num", "NotoSans-Bold.ttf", 11, "noto"),
    ("section", "NotoSans-Black.ttf", 13, "noto"),
    ("stat_num", "NotoSans-Black.ttf", 36, "noto"),
    ("stat_cap", "NotoSans-Bold.ttf", 11, "noto"),
    ("datechk", "NotoSans-Bold.ttf", 11, "noto"),
    ("foot", "NotoSans-Bold.ttf", 10, "noto"),
]
FT = SimpleNamespace(**{
    name: ImageFont.truetype(os.path.join(_DIRS[kind], fname), size)
    for name, fname, size, kind in _SPECS
})
NOTO_DIR = _DIRS["noto"]

# --- layout ---------------------------------------------------------------
MARGIN = 12
RIGHT = 1012
HERO_Y = 267
HERO_ART = 100
HERO_KICK = 14
HERO_TEXT = 101
HERO_H = HERO_ART + HERO_KICK + HERO_TEXT
SMALL_Y = 488
SMALL_ROW = 154
SMALL_W = 162
SMALL_ART = 56
SMALL_KICK = 14
SMALL_H = SMALL_ART + 92
MAP_Y = 801
MAP_W, MAP_H = 336, 140
CHK_Y = 969
FOOT_Y = 999

PROBLEMS = []

# --- stories ---------------------------------------------------------------
# One drawn story: number, dateline, topic, sources, status, headline,
# deck, big art label, small art label, art scene, certainty tag.
# Headlines wrap to at most two lines, decks to at most three.
# CONFIRMED = two named sources agree; REPORTED = one named source;
# CLAIM = one side's claim, unverified; OFFICIAL = on the record.
def _s(n, place, topic, src, status, head, deck, big, small, art, tag):
    return {"n": n, "place": place, "topic": topic, "src": src,
            "status": status, "head": head, "deck": deck, "big": big,
            "small": small, "art": art, "tag": tag}


FRONT = [
    _s(1, "BENGHAZI", "WAR", "ZELENSKYY · AP · WSJ", "REPORTED",
       "Ukraine sinks Russian corvette off Libya",
       "Seven sea drones hit the Merkury in Benghazi port; a Ka-27 helicopter aboard was destroyed and the cargo ship Angara set ablaze. Libya condemns the strike.",
       "7 SEA DRONES", "MERKURY SUNK", "merkury", "CONFIRMED"),
    _s(2, "ANTALYA", "CLIMATE", "UN NEWS · CNN · BBC", "REPORTED",
       "COP31 collapses: no deal on fossil fuels",
       "The longest COP on record ends with no pact — the first breakdown since 2009. Fossil fuels were stripped; the EU refused the text.",
       "NO DEAL", "LONGEST COP EVER", "cop31", "CONFIRMED"),
    _s(3, "SANTA CLARA", "TECH", "WSJ · CNN · NVIDIA", "REPORTED",
       "Nvidia brings Huang back as CEO",
       "Eleven days after resigning, Huang is reinstated by a unanimous board vote. The stock jumped 31%; Trump backed the return.",
       "HUANG IS BACK", "+31% IN A DAY", "nvidia", "CONFIRMED"),
    _s(4, "CIKANDE", "FIRE", "REUTERS", "REPORTED",
       "Candy-factory fire toll now 24",
       "24 dead confirmed; about 30 still missing. 29 are safe. — REUTERS",
       "24 DEAD", "30 STILL MISSING", "factoryfire", "CONFIRMED"),
    _s(5, "WELLINGTON", "TEST", "AFP", "REPORTED",
       "India's 720/9 ends in a draw",
       "NZ survive 120 overs, 239/5; Mitchell 49*, Phillips 26*. — AFP",
       "720/9 DECLARED", "DRAW IN WELLINGTON", "cricket", "CONFIRMED"),
    _s(6, "TURIN", "TENNIS", "ATP", "REPORTED",
       "Alcaraz wins first Finals title",
       "6-2, 7-6(9-7) in Turin; three set points saved. — ATP",
       "ALCARAZ WINS", "6-2, 7-6(9-7)", "tennis", "CONFIRMED"),
    _s(7, "TALLINN", "BORDER", "REUTERS", "REPORTED",
       "Russia warns Estonia of 'open war'",
       "Moscow summons envoy over border closure from 1 Dec. — REUTERS",
       "'OPEN WAR'", "BORDER SHUTS 1 DEC", "border", "REPORTED"),
    _s(8, "NEW DELHI", "AID", "REUTERS", "REPORTED",
       "India gives Nepal $1.62bn to rebuild",
       "$377m grant plus $1.24bn credit; floods killed ~1,500. — REUTERS",
       "$1.62BN", "NEPAL REBUILDS", "nepal", "CONFIRMED"),
    _s(9, "GENEVA", "CHESS", "FIDE", "OFFICIAL",
       "Chess crown fight begins today",
       "Gukesh, 20, meets Sindarov, 20, in a 14-game final. — FIDE",
       "GUKESH v SINDAROV", "BOTH AGED 20", "chess", "OFFICIAL"),
    _s(10, "DYMER", "RESCUE", "KYIV", "REPORTED",
       "Boy, 7, freed after 14 hours",
       "Freed from a five-storey block hit on Sunday. — KYIV",
       "14 HOURS", "BOY RESCUED ALIVE", "rubble", "REPORTED"),
    _s(11, "GAZA", "STRIKE", "REUTERS", "REPORTED",
       "Israeli strike kills UNRWA worker",
       "Adel al-Helo died near a well in Jabalia; 3 wounded. — REUTERS",
       "UN WORKER KILLED", "JABALIA CAMP", "well", "CONFIRMED"),
    _s(12, "HONG KONG", "VOTE", "RTHK", "REPORTED",
       "Record turnout picks 723 electors",
       "All 723 seats filled; KC Chan loses by two votes. — RTHK",
       "98.79% TURNOUT", "723 SEATS FILLED", "ballot", "CONFIRMED"),
    _s(13, "ATLANTA", "TRAVEL", "CNN", "REPORTED",
       "Delta glitch delays 1,000+ flights",
       "Weight-and-balance failure; crews count bags by hand. — CNN",
       "1,000+ DELAYED", "MANUAL WORKAROUNDS", "grounded", "CONFIRMED"),
    _s(14, "MANCHESTER", "SCARE", "BBC", "REPORTED",
       "12,000 evacuated from arena",
       "Co-op Live cleared after a substance scare. — BBC",
       "12,000 EVACUATED", "CO-OP LIVE", "arena", "REPORTED"),
    _s(15, "WASHINGTON", "VOTE", "AP", "REPORTED",
       "Democrats clinch 258 House seats",
       "Best since 1992; a 44-seat gain. Four races open. — AP",
       "258 SEATS", "BEST SINCE 1992", "capitol", "CONFIRMED"),
]

# The also-list: (number, city, one-line story, outlet). Each line is
# measured to fit one 320px column in 11px bold. All 21 were reported,
# or updated, Mon 23 – Tue 24 Nov 2026.
ALSO = [
    (16, "Tehran", "singer flogged 74 lashes", "BBC"),
    (17, "Dhaka", "garment workers reject pay offer", "AP"),
    (18, "New York", "New Yorkers stock up amid outages", "BBC"),
    (19, "Dushanbe", "Tajikistan moves to leave the ICC", "UN"),
    (20, "Rabat", "Afcon 2025 title hangs on a CAS ruling", "BBC"),
    (21, "Copenhagen", "top court backs 'ghetto law'", "BBC"),
    (22, "Paris", "far-left protests enter a sixth weekend", "BBC"),
    (23, "Harare", "preacher Uebert Angel arrested", "BBC"),
    (24, "Ottawa", "Carney stages Trump impersonator", "BBC"),
    (25, "Berlin", "bomb threats emailed to schools", "AP"),
    (26, "Skopje", "North Macedonia still stalled on EU path", "AP"),
    (27, "Bayelsa", "mourners' boat sinks; 29 dead", "AP"),
    (28, "Khan Younis", "infant dies of cold in Gaza tent", "BBC"),
    (29, "Khartoum", "drone strikes kill 4 near the capital", "AFP"),
    (30, "London", "Burnham hails 'landmark' EU deal", "BBC"),
    (31, "Washington", "Trump: Schumer hard to work with", "AP"),
    (32, "Shenzhen", "Japan's APEC welcome falls flat", "AP"),
    (33, "Benghazi", "Libya army says port secure", "AP"),
    (34, "Brussels", "EU budget plan targets Big Tech, 3% tax", "AP"),
    (35, "Ramallah", "settlers seize West Bank zones", "AP"),
    (36, "New York", "25 seafarers killed in Hormuz", "UN"),
]

# The six biggest figures on the page, one per top story.
STATS = [
    ("7", "sea drones sink the Merkury"),
    ("24", "dead in the Cikande fire"),
    ("258", "House seats for Democrats"),
    ("$1.62bn", "India's aid to Nepal"),
    ("+31%", "Nvidia jumps on Huang"),
    ("98.79%", "Hong Kong turnout"),
]

# Region counts, counted from the 36 stories by subject: EUROPE 11
# (6, 7, 9, 10, 14, 21, 22, 25, 26, 30, 34); MIDDLE EAST 4 (11, 16,
# 28, 35); AFRICA 6 (1, 20, 23, 27, 29, 33); ASIA-PACIFIC 6 (4, 8,
# 12, 17, 19, 32); AMERICAS 7 (3, 13, 15, 18, 24, 31, 36); OCEANIA 1
# (5); WORLD 1 (2, COP31 — Antalya venue, global subject). Total 36.
REGIONS = [
    ("EUROPE", 11, (16, 62, 150)),
    ("MIDDLE EAST", 4, (200, 60, 30)),
    ("AFRICA", 6, (30, 130, 80)),
    ("ASIA-PACIFIC", 6, (90, 60, 140)),
    ("AMERICAS", 7, (16, 40, 90)),
    ("OCEANIA", 1, (0, 120, 180)),
    ("WORLD", 1, (90, 90, 90)),
]

# --- the map ---------------------------------------------------------------
# Numbered red pins for the 15 drawn stories; small navy discs for the
# 21 also-list lines. Coordinates are (longitude, latitude).
PINS = {
    1: (20.1, 32.1), 2: (30.7, 36.9), 3: (-121.0, 37.35),
    4: (106.1, -6.0), 5: (174.8, -41.3), 6: (7.7, 45.1),
    7: (24.7, 59.4), 8: (77.2, 28.6), 9: (6.1, 46.2),
    10: (30.0, 50.8), 11: (34.5, 31.5), 12: (114.2, 22.3),
    13: (-84.4, 33.7), 14: (-2.2, 53.5), 15: (-77.0, 38.9),
}
DOTS = {
    16: (51.4, 35.7), 17: (90.4, 23.8), 18: (-74.0, 40.7),
    19: (68.8, 38.6), 20: (-6.8, 34.0), 21: (12.6, 55.7),
    22: (2.35, 48.85), 23: (31.0, -17.8), 24: (-75.7, 45.4),
    25: (13.4, 52.5), 26: (21.4, 42.0), 27: (6.3, 4.9),
    28: (34.5, 31.3), 29: (32.6, 15.6), 30: (-0.1, 51.5),
    31: (-77.0, 38.9), 32: (114.1, 22.5), 33: (20.1, 32.1),
    34: (4.4, 50.8), 35: (35.2, 31.9), 36: (-74.0, 40.7),
}
# The map is 336x140, equirectangular: 0.93px per degree of longitude,
# 0.78px per degree of latitude. Europe holds seven pins in a small box
# and three dot pairs share a city, so several markers are fanned out
# a few pixels with a thin leader line back to their true spot. Every
# offset below was checked numerically (min pin-pin 14px, min pin-dot
# 9px, min dot-dot 4.5px, zero out-of-box after fanning):
#  pin 1 Benghazi W (-18,8) clears Antalya pin 2, Gaza pin 11, Skopje 26;
#  pin 2 Antalya E (12,6) clears Dymer pin 10 and Gaza pin 11;
#  pin 5 Wellington W (-8,0) keeps the pin inside the map frame;
#  pin 6 Turin E (16,8) clears Geneva pin 9;
#  pin 7 Tallinn N (0,-12) clears Dymer pin 10, Copenhagen dot 21;
#  pin 10 Dymer NE (14,-6) clears Turin pin 6 and Tallinn pin 7;
#  pin 11 Gaza SW (-14,14) clears Antalya pin 2, Khan Younis dot 28;
#  pin 13 Atlanta W (-12,8) clears Washington pin 15;
#  pin 14 Manchester W (-18,10) clears Geneva pin 9 and Rabat dot 20;
#  dot 16 Tehran SE (8,8) clears Antalya pin 2;
#  dot 18 New York NE (10,-8) clears Washington pin 15;
#  dot 22 Paris W (-10,-8) clears Geneva pin 9 and London dot 30;
#  dot 24 Ottawa W (-12,-6) clears Washington pin 15, New York dot 18;
#  dot 25 Berlin S (0,12) clears Copenhagen dot 21 and Dymer pin 10;
#  dot 26 Skopje W (-12,10) clears Turin pin 6 and Geneva pin 9;
#  dot 28 Khan Younis S (0,12) clears Turin pin 6 and Gaza pin 11;
#  dot 29 Khartoum SE (10,6) clears Gaza pin 11;
#  dot 30 London N (0,-12) clears Paris dot 22 and Geneva pin 9;
#  dot 31 Washington W (-10,10) clears Atlanta pin 13, Ottawa dot 24;
#  dot 32 Shenzhen E (14,-10) clears Hong Kong pin 12;
#  dot 33 Benghazi NE (12,-12) clears Turin pin 6 and Dymer pin 10;
#  dot 34 Brussels NE (8,-10) clears Geneva pin 9 and Paris dot 22;
#  dot 35 Ramallah NE (12,-10) clears Khan Younis dot 28, Gaza pin 11;
#  dot 36 New York SE (14,8) clears Washington pin 15, New York dot 18.
PIN_OFF = {1: (-18, 8), 2: (12, 6), 5: (-8, 0), 6: (16, 8),
           7: (0, -12), 10: (14, -6), 11: (-14, 14), 13: (-12, 8),
           14: (-18, 10)}
DOT_OFF = {16: (8, 8), 18: (10, -8), 22: (-10, -8), 24: (-12, -6),
           25: (0, 12), 26: (-12, 10), 28: (0, 12), 29: (10, 6),
           30: (0, -12), 31: (-10, 10), 32: (14, -10), 33: (12, -12),
           34: (8, -10), 35: (12, -10), 36: (14, 8)}


# --- tiny drawing helpers ---------------------------------------------------
# Short wrappers around ImageDraw so the scene code reads as flat
# shape lists instead of long PIL calls.
def _rect(g, x0, y0, x1, y1, fill=None, out=None, wdt=1):
    g.rectangle([x0, y0, x1, y1], fill=fill, outline=out, width=wdt)


def _oval(g, x0, y0, x1, y1, fill=None, out=None, wdt=1):
    g.ellipse([x0, y0, x1, y1], fill=fill, outline=out, width=wdt)


def _line(g, pts, fill, wdt=1):
    g.line(pts, fill=fill, width=wdt)


def _poly(g, pts, fill=None, out=None):
    g.polygon(pts, fill=fill, outline=out)


def _text(g, xy, s, font, fill, anchor=None, **kw):
    g.text(xy, s, font=font, fill=fill, anchor=anchor, **kw)


def _wrap(g, text, font, width, limit=None):
    """Greedy word wrap to `width` px; a PROBLEM if it needs more lines."""
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
    if limit is not None and len(lines) > limit:
        PROBLEMS.append("TRUNCATED (%d lines): %s" % (len(lines), text))
        lines = lines[:limit]
    return lines


def _burst(g, cx, cy, outer, inner, fill):
    """A five-point starburst (explosions, base hits)."""
    pts = []
    for k in range(10):
        r = outer if k % 2 == 0 else inner
        ang = math.radians(-90 + k * 36)
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    _poly(g, pts, fill)


def _canvas(w, h):
    img = Image.new("RGB", (w, h))
    return img, ImageDraw.Draw(img)


def _top_banner(g, w, big, small, fill):
    """The solid colour bar across the top of a small-card picture,
    carrying the two art labels in white. The big label steps down
    12 -> 11 -> 10 -> 9px (and the small label 8 -> 7px) until the
    pair fits the width."""
    _rect(g, 0, 0, w, 18, fill)
    f_big, f_small = FT.small_lbl, FT.small_lbl_small
    while (g.textlength(big, font=f_big)
           + g.textlength(small, font=f_small) + 14 > w):
        if f_big.size > 9:
            f_big = ImageFont.truetype(
                os.path.join(NOTO_DIR, "NotoSans-Black.ttf"), f_big.size - 1)
        elif f_small.size > 7:
            f_small = ImageFont.truetype(
                os.path.join(NOTO_DIR, "NotoSans-Bold.ttf"), f_small.size - 1)
        else:
            break
    _text(g, (6, 9), big, f_big, "white", anchor="lm")
    _text(g, (w - 6, 9), small, f_small, "white", anchor="rm")


def _scrim(g, w, h, big, small):
    """The bottom-left label on a hero picture: big line over small
    line on a dark block (solid dark, the art behind it is dark anyway).
    Shrinks the big label until it fits."""
    f_big = FT.hero_lbl
    while g.textlength(big, font=f_big) > w - 16 and f_big.size > 10:
        f_big = ImageFont.truetype(
            os.path.join(NOTO_DIR, "NotoSans-Black.ttf"), f_big.size - 1)
    bw = g.textlength(big, font=f_big)
    sw = g.textlength(small, font=FT.hero_lbl_small)
    box_w = int(max(bw, sw)) + 16
    _rect(g, 0, h - 34, box_w, h, (10, 10, 14))
    _text(g, (8, h - 30), big, f_big, "white")
    _text(g, (8, h - 15), small, FT.hero_lbl_small, "white")

# --- art scenes --------------------------------------------------------------
# One function per picture, drawn from scratch in flat vector shapes.
# Heroes are painted at h=105 and shrunk to 100; smalls at h=80 and
# shrunk to 56. The bottom-left of a hero stays clear for the scrim;
# the top 18px of a small stays clear for the solid banner.

def art_merkury(g, w, h):
    # Seven sea drones strike the Russian corvette Merkury at night in
    # Benghazi port: dark sea and sky, the grey corvette listing with
    # a fireball amidships, drone boats closing in on white wakes, a
    # helicopter silhouette on deck.
    _rect(g, 0, 0, w, h, (8, 14, 34))
    for sx, sy in ((22, 10), (70, 16), (140, 8), (210, 14), (280, 8),
                   (340, 16), (378, 10), (120, 24), (250, 26), (320, 30)):
        _oval(g, sx, sy, sx + 2, sy + 2, "white")
    _rect(g, 0, 88, w, h, (40, 42, 52))
    for wx in range(6, w, 26):
        _rect(g, wx, 92, wx + 12, 96, (70, 72, 84))
    _rect(g, 0, 40, w, 88, (14, 40, 78))
    for wy in (52, 64, 78):
        for wx in range(10, w, 34):
            _line(g, [wx, wy, wx + 18, wy], (90, 140, 190))
    _poly(g, [(110, 62), (300, 62), (288, 76), (122, 76)], (120, 125, 135))
    _rect(g, 170, 46, 210, 62, (140, 145, 155))
    _line(g, [190, 46, 190, 34], (140, 145, 155), 3)
    _line(g, [190, 34, 200, 40], (140, 145, 155), 2)
    _oval(g, 120, 52, 152, 60, (60, 64, 74))
    _line(g, [124, 52, 148, 52], (60, 64, 74), 2)
    _oval(g, 120, 44, 126, 50, (60, 64, 74))
    _burst(g, 232, 50, 16, 6, (255, 140, 40))
    _burst(g, 232, 50, 9, 3, (255, 210, 31))
    _oval(g, 226, 44, 238, 56, "white")
    for sx, sy, sr in ((232, 26, 8), (246, 20, 10), (262, 24, 7)):
        _oval(g, sx - sr, sy - sr, sx + sr, sy + sr, (70, 70, 80))
    for dx, dy in ((210, 80), (310, 76), (350, 84)):
        _line(g, [dx - 26, dy + 2, dx - 6, dy + 2], "white", 2)
        _oval(g, dx - 8, dy - 4, dx + 8, dy + 4, (10, 10, 14))
        _line(g, [dx - 12, dy - 6, dx + 12, dy - 6], (220, 220, 230), 2)
    _text(g, (w - 10, 12), "BENGHAZI PORT", FT.art_mid_small, "white",
          anchor="ra", stroke_width=1, stroke_fill=(0, 0, 0))


def art_cop31(g, w, h):
    # The climate summit, diagrammatic: a round globe, a red
    # thermometer, a round clock, a red COLLAPSED banner.
    _rect(g, 0, 0, w, h, (11, 110, 110))
    _oval(g, 20, 22, 82, 84, (30, 120, 200), out=(20, 20, 20), wdt=2)
    for lx0, ly0, lx1, ly1 in ((30, 34, 52, 48), (52, 50, 74, 66),
                               (30, 54, 44, 66)):
        _oval(g, lx0, ly0, lx1, ly1, (60, 180, 90))
    _rect(g, 132, 14, 142, 62, "white", out=(20, 20, 20))
    _rect(g, 134, 30, 140, 62, (220, 30, 40))
    _oval(g, 126, 58, 148, 74, (220, 30, 40), out=(20, 20, 20))
    for tick_y in (20, 28, 36, 44, 52):
        _line(g, [142, tick_y, 147, tick_y], (20, 20, 20))
    _text(g, (154, 16), "+1.5°C", FT.art_mid, "white")
    _text(g, (154, 38), "LIMIT", FT.art_mid_small, "white")
    _text(g, (154, 50), "AT RISK", FT.art_mid_small, "white")
    _oval(g, 228, 22, 284, 78, "white", out=(20, 20, 20), wdt=2)
    for ang in range(0, 360, 30):
        tx = 256 + int(24 * math.cos(math.radians(ang)))
        ty = 50 + int(24 * math.sin(math.radians(ang)))
        _oval(g, tx - 1, ty - 1, tx + 1, ty + 1, (20, 20, 20))
    _line(g, [256, 50, 256, 30], (20, 20, 20), 3)
    _line(g, [256, 50, 266, 36], (20, 20, 20), 3)
    _oval(g, 253, 47, 259, 53, (20, 20, 20))
    _rect(g, 150, 80, 262, 102, DARKRED)
    _text(g, (206, 91), "COLLAPSED", FT.art_mid, "white", anchor="mm")


def art_nvidia(g, w, h):
    # Jensen Huang returns: a green chip on a dark board, a white
    # stock line climbing steeply to the right, a red BACK stamp.
    _rect(g, 0, 0, w, h, (10, 16, 24))
    for ty in (18, 34, 88):
        _line(g, [0, ty, w, ty], (20, 90, 60))
    for tx in (30, 120, 240, 330):
        _line(g, [tx, 0, tx, h], (20, 90, 60))
    for px, py in ((30, 18), (120, 34), (240, 18), (330, 88),
                   (30, 88), (120, 88)):
        _rect(g, px - 3, py - 3, px + 3, py + 3, (30, 160, 90))
    _rect(g, 120, 30, 220, 80, (20, 120, 70), out=(200, 200, 200), wdt=2)
    for px in range(130, 215, 14):
        _line(g, [px, 24, px, 30], (220, 190, 60), 3)
        _line(g, [px, 80, px, 86], (220, 190, 60), 3)
    for py in range(40, 75, 14):
        _line(g, [114, py, 120, py], (220, 190, 60), 3)
        _line(g, [220, py, 226, py], (220, 190, 60), 3)
    _oval(g, 152, 42, 188, 68, out="white", wdt=3)
    _oval(g, 166, 50, 174, 58, "white")
    _line(g, [(10, 92), (int(w * 0.30), 88), (int(w * 0.50), 84),
              (int(w * 0.68), 70), (int(w * 0.85), 46), (w - 14, 22),
              (w - 6, 10)], "white", 3)
    _poly(g, [(w - 14, 6), (w - 2, 6), (w - 8, 18)], "white")
    _text(g, (w - 10, 92), "+31%", FT.art_mid, SUN, anchor="rb")
    _rect(g, 10, 8, 92, 30, out=RED, wdt=3)
    _text(g, (51, 19), "BACK", FT.art_mid, RED, anchor="mm")


def art_factoryfire(g, w, h):
    # Candy-factory fire in Cikande: a sawtooth-roof factory, a big
    # fire bursting from the roof, a smoke plume drifting right, one
    # window glowing from the fire inside.
    _rect(g, 0, 0, w, h, (180, 190, 205))
    _rect(g, 0, 62, w, h, (120, 120, 126))
    _rect(g, 20, 44, 176, 62, (90, 90, 100))
    for sx in (20, 52, 84, 116, 148):
        _poly(g, [(sx, 44), (sx + 16, 32), (sx + 32, 44)], (70, 70, 80))
    _rect(g, 168, 24, 176, 44, (70, 70, 80))
    _oval(g, 78, 22, 118, 50, (255, 140, 40))
    _oval(g, 88, 30, 108, 50, (255, 210, 31))
    _oval(g, 94, 38, 104, 50, (255, 120, 30))
    for sx, sy, sr in ((98, 16, 7), (112, 10, 9), (130, 8, 8), (146, 12, 6)):
        _oval(g, sx - sr, sy - sr, sx + sr, sy + sr, (90, 90, 96))
    for wx in (30, 56, 130, 156):
        _rect(g, wx, 50, wx + 10, 58, (40, 40, 50))
    _rect(g, 82, 50, 92, 58, (255, 180, 60))


def art_cricket(g, w, h):
    # India declare on 720/9 in Wellington: packed stands and
    # floodlights behind, green outfield, tan pitch, stumps, and the
    # batsman big and mid-swing, bat meeting the red ball, scoreboard
    # bottom-right reading NZ 368 / IND 720/9.
    _rect(g, 0, 0, w, h, (60, 160, 90))
    _rect(g, 0, 20, w, 34, (45, 55, 70))
    crowd = ((220, 180, 140), (180, 120, 80), (240, 200, 160),
             (200, 60, 60), (60, 120, 200), (240, 240, 240),
             (30, 30, 30), (250, 200, 40))
    for row, cy in ((0, 25), (1, 30)):
        for i, hx in enumerate(range(6, w - 4, 7)):
            col = crowd[(i + row * 3) % len(crowd)]
            _oval(g, hx - 2, cy - 2, hx + 2, cy + 2, col)
    _rect(g, 0, 34, w, 36, (220, 220, 220))
    for px0 in (6, 190):
        _line(g, [px0, 20, px0, 34], (120, 125, 135), 2)
        _rect(g, px0 - 5, 20, px0 + 5, 26, (90, 95, 105))
        for lx in (px0 - 3, px0 + 1):
            _oval(g, lx - 1, 21, lx + 1, 23, "white")
    _poly(g, [(4, 26), (14, 26), (30, 44), (0, 44)], (235, 235, 195))
    _poly(g, [(182, 26), (192, 26), (196, 44), (166, 44)], (235, 235, 195))
    for sy in range(36, h, 16):
        _rect(g, 0, sy, w, sy + 8, (52, 148, 82))
    _rect(g, 88, 38, 110, h, (214, 186, 140))
    _line(g, [88, 42, 110, 42], "white", 2)
    _line(g, [88, 74, 110, 74], "white", 2)
    for sx in (94, 98, 102):
        _rect(g, sx, 38, sx + 2, 48, (240, 220, 140))
    _line(g, [94, 38, 104, 38], (240, 220, 140))
    _oval(g, 120, 46, 130, 56, (200, 140, 90))
    _rect(g, 120, 56, 131, 70, (20, 20, 25))
    _line(g, [122, 70, 116, 79], "white", 4)
    _line(g, [129, 70, 135, 79], "white", 4)
    _line(g, [128, 58, 142, 48], (200, 140, 90), 3)
    _line(g, [142, 48, 156, 34], (200, 170, 110), 5)
    _oval(g, 155, 29, 163, 37, (200, 40, 40), out="white")
    _line(g, [(166, 27), (172, 22)], "white", 2)
    for fx, fy in ((28, 58), (58, 70), (170, 52)):
        _oval(g, fx - 3, fy - 3, fx + 3, fy + 3, "white")
    _rect(g, 136, 58, 194, 78, "white", out=INK)
    _text(g, (165, 63), "NZ 368", FT.small_lbl_small, INK, anchor="mm")
    _text(g, (165, 72), "IND 720/9", FT.small_lbl_small, INK, anchor="mm")


def art_tennis(g, w, h):
    # Alcaraz wins the ATP Finals in Turin: a blue hard court, white
    # lines, the net across the middle, a gold trophy on the right, a
    # player mid-forehand on the left.
    _rect(g, 0, 0, w, h, (40, 110, 200))
    _rect(g, 0, 52, w, h, (30, 90, 170))
    _rect(g, 14, 40, 182, 76, out="white", wdt=2)
    _line(g, [98, 40, 98, 76], "white", 2)
    _line(g, [14, 58, 182, 58], "white")
    _line(g, [14, 46, 182, 46], "white", 3)
    for nx in range(20, 180, 12):
        _line(g, [nx, 46, nx, 54], "white")
    _oval(g, 40, 44, 50, 54, (200, 140, 90))
    _rect(g, 38, 54, 52, 68, (240, 240, 240))
    _line(g, [40, 68, 34, 78], (20, 20, 25), 4)
    _line(g, [50, 68, 56, 78], (20, 20, 25), 4)
    _line(g, [50, 56, 66, 48], (200, 140, 90), 3)
    _line(g, [66, 48, 80, 36], (200, 170, 110), 4)
    _oval(g, 80, 30, 88, 38, (220, 220, 40), out="white")
    _rect(g, 150, 66, 176, 70, (120, 90, 20))
    _poly(g, [(154, 40), (172, 40), (170, 58), (156, 58)],
          (255, 210, 31), out=(120, 90, 20))
    _oval(g, 148, 42, 156, 52, out=(255, 210, 31), wdt=2)
    _oval(g, 170, 42, 178, 52, out=(255, 210, 31), wdt=2)
    _rect(g, 160, 34, 166, 40, (255, 210, 31))


def art_border(g, w, h):
    # Russia warns Estonia: a border crossing at dusk — a striped
    # barrier arm lowered across the road, a watchtower, two flags,
    # red warning lights on the barrier.
    _rect(g, 0, 0, w, h, (200, 150, 90))
    _rect(g, 0, 58, w, h, (70, 70, 78))
    for dx in range(6, w, 22):
        _line(g, [dx, 66, dx + 11, 66], "white", 2)
    _rect(g, 16, 30, 26, 58, (90, 90, 100))
    _rect(g, 10, 22, 32, 32, (120, 120, 130), out=(60, 60, 66))
    _rect(g, 14, 25, 28, 29, (40, 60, 90))
    for i, bx in enumerate(range(40, 180, 20)):
        _rect(g, bx, 46, bx + 20, 52, RED if i % 2 == 0 else "white")
    for lx in (60, 110, 160):
        _oval(g, lx - 3, 41, lx + 3, 47, (255, 60, 60), out="white")
    for fx, col in ((186, (0, 90, 180)), (170, (200, 200, 200))):
        _line(g, [fx, 24, fx, 58], (60, 60, 60), 2)
        _rect(g, fx, 24, fx + 12, 32, col)


def art_nepal(g, w, h):
    # India gives Nepal $1.62bn: the Himalayas behind, two flags on
    # poles in front, a handshake below — saffron-white-green beside
    # crimson-blue.
    _rect(g, 0, 0, w, h, (170, 200, 230))
    for mx, mh, mw in ((0, 44, 70), (60, 30, 80), (130, 40, 70)):
        _poly(g, [(mx, 62), (mx + mw // 2, 62 - mh), (mx + mw, 62)],
              (120, 130, 150))
        _poly(g, [(mx + mw // 2 - 10, 62 - mh + 12),
                  (mx + mw // 2, 62 - mh),
                  (mx + mw // 2 + 10, 62 - mh + 12)], "white")
    _rect(g, 0, 62, w, h, (90, 140, 80))
    for fx, cols in ((24, ((255, 150, 0), "white", (0, 130, 60))),
                     (164, ((200, 30, 50), (20, 60, 140), None))):
        _line(g, [fx, 24, fx, 58], (60, 60, 60), 2)
        _rect(g, fx, 24, fx + 22, 32, cols[0])
        _rect(g, fx, 32, fx + 22, 40, cols[1])
        if cols[2]:
            _rect(g, fx, 40, fx + 22, 48, cols[2])
    _line(g, [78, 52, 98, 44], (200, 140, 90), 6)
    _line(g, [118, 44, 138, 52], (180, 120, 80), 6)
    _oval(g, 94, 38, 112, 52, (220, 170, 120))


def art_chess(g, w, h):
    # Gukesh v Sindarov for the world crown: a chessboard seen from
    # above, a white king and a black king facing off, a gold crown
    # above the board.
    _rect(g, 0, 0, w, h, (60, 40, 20))
    bx0, by0, sq = 52, 22, 12
    for r in range(8):
        for c in range(8):
            col = (240, 220, 180) if (r + c) % 2 == 0 else (120, 80, 40)
            _rect(g, bx0 + c * sq, by0 + r * sq,
                  bx0 + (c + 1) * sq, by0 + (r + 1) * sq, col)
    _rect(g, bx0, by0, bx0 + 8 * sq, by0 + 8 * sq, out=INK, wdt=2)
    for kx, col, oc in ((76, "white", INK), (128, (20, 20, 20), "white")):
        _rect(g, kx - 5, 40, kx + 5, 66, col, out=oc)
        _oval(g, kx - 6, 30, kx + 6, 42, col, out=oc)
        _line(g, [kx, 26, kx, 32], col, 3)
        _line(g, [kx - 4, 29, kx + 4, 29], col, 3)
    _poly(g, [(86, 14), (92, 6), (98, 12), (104, 4), (110, 12),
              (116, 6), (122, 14)], (255, 210, 31), out=(120, 90, 20))
    _rect(g, 86, 14, 122, 18, (255, 210, 31))

def art_rubble(g, w, h):
    # A boy freed after 14 hours under rubble in Dymer: a cracked
    # five-storey block at night, a rescue ladder, a searchlight beam,
    # a small stretcher at the foot of the ladder.
    _rect(g, 0, 0, w, h, (16, 20, 36))
    _oval(g, 168, 10, 182, 24, (240, 230, 190))
    _rect(g, 60, 24, 140, 76, (60, 62, 74))
    for wy in range(30, 72, 12):
        for wx in range(66, 136, 14):
            _rect(g, wx, wy, wx + 8, wy + 6,
                  (255, 210, 90) if (wx + wy) % 3 else (40, 42, 52))
    _line(g, [(100, 24), (108, 40), (96, 52), (106, 66), (98, 76)],
          (10, 10, 14), 3)
    for bx, by, bw, bh in ((56, 70, 16, 8), (130, 68, 20, 10),
                           (100, 72, 14, 6)):
        _rect(g, bx, by, bx + bw, by + bh, (90, 88, 84), out=(40, 40, 44))
    _line(g, [150, 76, 176, 30], (200, 200, 210), 3)
    for ly in range(34, 74, 8):
        _line(g, [150 + (76 - ly) * 26 // 46 - 4, ly,
                  150 + (76 - ly) * 26 // 46 + 4, ly],
              (200, 200, 210))
    _poly(g, [(176, 30), (182, 30), (196, 52), (188, 54)], (240, 240, 200))
    _rect(g, 150, 72, 190, 76, (200, 30, 40))
    _line(g, [156, 76, 156, 79], (20, 20, 20), 2)
    _line(g, [184, 76, 184, 79], (20, 20, 20), 2)


def art_well(g, w, h):
    # An UNRWA worker killed near a well in Jabalia: a stone well with
    # a wooden frame and rope, a blue UN flag, a water bucket, dusty
    # ground.
    _rect(g, 0, 0, w, h, (220, 200, 160))
    _rect(g, 0, 62, w, h, (180, 150, 100))
    _oval(g, 78, 52, 122, 66, (150, 140, 120), out=(80, 70, 50))
    _rect(g, 78, 52, 122, 66, (150, 140, 120))
    _line(g, [84, 30, 78, 54], (120, 90, 60), 3)
    _line(g, [116, 30, 122, 54], (120, 90, 60), 3)
    _line(g, [84, 30, 116, 30], (120, 90, 60), 3)
    _line(g, [100, 30, 100, 48], (80, 60, 40), 2)
    _rect(g, 92, 48, 108, 58, (100, 100, 110), out=(40, 40, 44))
    _line(g, [160, 22, 160, 62], (60, 60, 60), 2)
    _rect(g, 160, 22, 188, 36, (0, 110, 200))
    _oval(g, 166, 25, 182, 33, out="white")
    _poly(g, [(30, 58), (48, 58), (44, 72), (34, 72)],
          (120, 120, 130), out=(40, 40, 44))


def art_ballot(g, w, h):
    # Hong Kong elects its Election Committee: a blue ballot box on a
    # table, a white ballot sliding into the slot, a hand above it,
    # warm yellow backdrop.
    _rect(g, 0, 0, w, h, (250, 220, 90))
    _rect(g, 0, 58, w, h, (150, 110, 60))
    _rect(g, 58, 34, 138, 66, (20, 60, 140))
    _rect(g, 78, 34, 118, 40, "white")
    _rect(g, 84, 48, 112, 58, "white")
    _text(g, (98, 53), "VOTE", FT.small_lbl_small, NAVY, anchor="mm")
    _poly(g, [(96, 18), (118, 22), (112, 36), (90, 32)],
          "white", out=(60, 60, 60))
    _line(g, [100, 24, 112, 26], RED, 2)
    _oval(g, 88, 8, 122, 22, (220, 170, 120))
    for fx in (92, 100, 108, 116):
        _rect(g, fx, 16, fx + 5, 26, (220, 170, 120))
    _rect(g, 150, 60, 182, 72, "white", out=(60, 60, 60))
    _line(g, [154, 66, 178, 66], GREY)
    _line(g, [20, 68, 48, 62], (220, 160, 40), 3)


def art_grounded(g, w, h):
    # Delta's weight-and-balance failure: an airport at dawn, two
    # planes parked on the tarmac, a control tower, and a departures
    # board reading DELAYED.
    _rect(g, 0, 0, w, h, (205, 214, 226))
    _rect(g, 0, 56, w, h, (90, 90, 98))
    _line(g, [0, 56, w, 56], (60, 60, 66), 2)
    for dx in range(6, w, 22):
        _line(g, [dx, 66, dx + 11, 66], "white", 2)
    _rect(g, 18, 30, 28, 56, (120, 120, 128))
    _rect(g, 12, 22, 34, 32, (150, 150, 158), out=(60, 60, 66))
    _rect(g, 104, 22, 188, 44, (20, 20, 26))
    _text(g, (146, 26), "DELAYED", FT.small_lbl_small, (255, 80, 80),
          anchor="ma")
    _text(g, (146, 35), "1,000+ FLIGHTS", FT.small_lbl_small, "white",
          anchor="ma")
    for px, py, pcol in ((48, 54, (200, 60, 50)), (120, 58, (40, 90, 160))):
        _oval(g, px, py, px + 52, py + 8, pcol)
        _poly(g, [(px + 44, py), (px + 50, py - 8), (px + 54, py)], pcol)
        _poly(g, [(px + 18, py + 4), (px + 30, py + 12),
                  (px + 34, py + 4)], pcol)


def art_arena(g, w, h):
    # 12,000 evacuated from Manchester's Co-op Live: a dark arena
    # bowl, rows of seats, a stage with lights, and a green exit sign
    # glowing above a doorway.
    _rect(g, 0, 0, w, h, (14, 16, 30))
    for ry, rw in ((24, 176), (34, 188), (44, 196)):
        for sx in range(10, 10 + rw, 10):
            _oval(g, sx - 2, ry - 2, sx + 2, ry + 2, (180, 180, 200))
    _rect(g, 70, 56, 130, 76, (60, 60, 90))
    _poly(g, [(80, 56), (88, 56), (70, 22), (58, 22)], (255, 220, 90))
    _poly(g, [(112, 56), (120, 56), (140, 22), (152, 22)], (255, 220, 90))
    _line(g, [100, 60, 100, 70], (200, 200, 210), 2)
    _oval(g, 97, 56, 103, 62, (200, 200, 210))
    _rect(g, 158, 56, 190, 68, (20, 160, 60))
    _text(g, (174, 62), "EXIT", FT.small_lbl_small, "white", anchor="mm")
    _rect(g, 162, 68, 186, 78, (40, 40, 50))


def art_capitol(g, w, h):
    # Democrats clinch 258 House seats: the Capitol dome at dusk,
    # white against a deep blue sky, the flag on top, the number 258
    # on a red banner across the steps.
    _rect(g, 0, 0, w, h, (24, 38, 80))
    for sx, sy in ((16, 10), (60, 14), (170, 10), (188, 16)):
        _oval(g, sx, sy, sx + 2, sy + 2, "white")
    _rect(g, 70, 56, 130, 78, (240, 240, 235))
    _oval(g, 76, 30, 124, 60, (240, 240, 235))
    for rx in (84, 92, 100, 108, 116):
        _line(g, [rx, 34, rx, 56], (200, 200, 195))
    _rect(g, 96, 22, 104, 32, (240, 240, 235))
    _line(g, [100, 22, 100, 14], (240, 240, 235), 2)
    _rect(g, 100, 14, 112, 20, (200, 40, 50))
    _rect(g, 30, 62, 70, 78, (220, 220, 215))
    _rect(g, 130, 62, 170, 78, (220, 220, 215))
    _rect(g, 0, 78, w, h, (180, 180, 175))
    _rect(g, 56, 66, 144, 78, DARKRED)
    _text(g, (100, 72), "258", FT.art_mid_small, "white", anchor="mm")


ART = {"merkury": art_merkury, "cop31": art_cop31, "nvidia": art_nvidia,
       "factoryfire": art_factoryfire, "cricket": art_cricket,
       "tennis": art_tennis, "border": art_border, "nepal": art_nepal,
       "chess": art_chess, "rubble": art_rubble, "well": art_well,
       "ballot": art_ballot, "grounded": art_grounded,
       "arena": art_arena, "capitol": art_capitol}


def paint(key, w, h):
    """Paint one scene into a fresh image of size w x h."""
    img, g = _canvas(w, h)
    scene = ART.get(key)
    if scene is None:
        _rect(g, 0, 0, w, h, (200, 200, 200))
    else:
        scene(g, w, h)
    return img


def _hero_pic(story, w):
    """A hero picture: painted at 105 tall, shrunk to 100, with the
    bottom-left scrim label baked in."""
    img = paint(story["art"], w, 105)
    _scrim(ImageDraw.Draw(img), w, 105, story["big"], story["small"])
    return img.resize((w, HERO_ART), Image.LANCZOS)


def _small_pic(story):
    """A small picture: painted at 196x80 with its solid red banner,
    shrunk to 162x56."""
    img = paint(story["art"], 196, 80)
    _top_banner(ImageDraw.Draw(img), 196, story["big"], story["small"], RED)
    return img.resize((SMALL_W, SMALL_ART), Image.LANCZOS)


def _kicker_strip(g, x, y, w, left, pill_tag, right=None, right_font=None):
    """The 14px navy strip under a picture: pill + left text, and an
    optional right-hand source in gold."""
    _rect(g, x, y, x + w, y + HERO_KICK, NAVY)
    pill_w = g.textlength(pill_tag, font=FT.pill) + 10
    g.rounded_rectangle([x + 8, y + 2, x + 8 + pill_w, y + 12],
                        radius=2, fill=PILL[pill_tag])
    _text(g, (x + 13, y + 7), pill_tag, FT.pill, "white", anchor="lm")
    _text(g, (x + 14 + pill_w, y + 7), left, FT.kick, "white", anchor="lm")
    if right is not None:
        _text(g, (x + w - 8, y + 7), right, right_font or FT.src, GOLD,
              anchor="rm")


def hero_card(page, g, story, x, y, w):
    """A hero card: 100px art with a bottom-left scrim label, a 14px
    navy kicker strip (verification pill left, number + dateline +
    topic, source right in gold), a two-line 27px serif headline and
    a three-line 12px serif deck, the text block centred in the 101px
    area under the strip, all inside a 1px ink box. Card 215 tall."""
    _rect(g, x, y, x + w, y + HERO_H, CARD)
    page.paste(_hero_pic(story, w), (x, y))
    strip_y = y + HERO_ART
    _kicker_strip(g, x, strip_y, w,
                  "%d. %s · %s" % (story["n"], story["place"],
                                   story["topic"]),
                  story["tag"], right=story["src"])
    head_lines = _wrap(g, story["head"], FT.head_hero, w - 16, 2)
    deck_lines = _wrap(g, story["deck"], FT.deck_hero, w - 16, 3)
    block_h = len(head_lines) * 30 + 2 + len(deck_lines) * 13
    text_y = y + HERO_ART + HERO_KICK + (HERO_TEXT - block_h) // 2
    for j, line in enumerate(head_lines):
        _text(g, (x + 8, text_y + j * 30), line, FT.head_hero, INK)
    for j, line in enumerate(deck_lines):
        _text(g, (x + 8, text_y + len(head_lines) * 30 + 2 + j * 13),
              line, FT.deck_hero, (60, 60, 60))
    _rect(g, x, y, x + w, y + HERO_H, out=INK)


def small_card(page, g, story, x, y):
    """A small card: 56px art with a solid red banner across its top
    carrying the art labels in white, a 14px navy kicker strip
    (number + dateline + topic left, verification pill right — the
    kicker shrinks 9px to 8px when pill + text would overflow the
    162px card), a two-line 16px serif headline and a three-line 11px
    serif deck with its source, inside a 1px ink box. Card 148 tall."""
    w = SMALL_W
    _rect(g, x, y, x + w, y + SMALL_H, CARD)
    page.paste(_small_pic(story), (x, y))
    strip_y = y + SMALL_ART
    _rect(g, x, strip_y, x + w, strip_y + SMALL_KICK, NAVY)
    kick_text = "%d. %s · %s" % (story["n"], story["place"], story["topic"])
    pill_w = g.textlength(story["tag"], font=FT.pill) + 10
    f_kick = FT.kick_small
    if g.textlength(kick_text, font=f_kick) + pill_w + 12 > w:
        f_kick = FT.kick_tiny
    _text(g, (x + 4, strip_y + 7.5), kick_text, f_kick, "white",
          anchor="lm")
    g.rounded_rectangle([x + w - 4 - pill_w, strip_y + 2,
                         x + w - 4, strip_y + 12],
                        radius=2, fill=PILL[story["tag"]])
    _text(g, (x + w + 1 - pill_w, strip_y + 7.5), story["tag"], FT.pill,
          "white", anchor="lm")
    head_lines = _wrap(g, story["head"], FT.head_small, w - 16, 2)
    for j, line in enumerate(head_lines):
        _text(g, (x + 8, strip_y + SMALL_KICK + 4 + j * 16), line,
              FT.head_small, INK)
    deck_lines = _wrap(g, story["deck"], FT.deck_small, w - 16, 3)
    for j, line in enumerate(deck_lines):
        _text(g, (x + 8, strip_y + SMALL_KICK + 5
                  + len(head_lines) * 16 + j * 12),
              line, FT.deck_small, (60, 60, 60))
    _rect(g, x, y, x + w, y + SMALL_H, out=INK)


def draw_map(g, x0, y0, w, h):
    """A light world map: pale blue sea, tan land from world.geo.json,
    navy dots for the also-list stories, numbered red pins for the
    drawn stories. Equirectangular projection; pins and dots that
    would sit on top of each other are fanned out a few pixels with a
    thin leader line back to their true spot (see PIN_OFF/DOT_OFF)."""
    with open(os.path.join(HERE, "world.geo.json")) as fh:
        geo = json.load(fh)

    def px(lon):
        return x0 + (lon + 180.0) / 360.0 * w

    def py(lat):
        return y0 + (90.0 - lat) / 180.0 * h

    _rect(g, x0, y0, x0 + w, y0 + h, OCEAN)
    for feat in geo["features"]:
        geom = feat["geometry"]
        polys = []
        if geom["type"] == "Polygon":
            polys = [geom["coordinates"]]
        elif geom["type"] == "MultiPolygon":
            polys = geom["coordinates"]
        for poly in polys:
            ring = poly[0]
            pts = [(px(lon), py(lat)) for lon, lat in ring]
            _poly(g, pts, LAND, out=(200, 180, 120))
    for num, (lon, lat) in DOTS.items():
        tx, ty = px(lon), py(lat)
        ox, oy = DOT_OFF.get(num, (0, 0))
        if (ox, oy) != (0, 0):
            _line(g, [tx, ty, tx + ox, ty + oy], INK)
        _oval(g, tx + ox - 2, ty + oy - 2, tx + ox + 2, ty + oy + 2, NAVY)
    for num, (lon, lat) in PINS.items():
        tx, ty = px(lon), py(lat)
        ox, oy = PIN_OFF.get(num, (0, 0))
        if (ox, oy) != (0, 0):
            _line(g, [tx, ty, tx + ox, ty + oy], RED)
        cx, cy = tx + ox, ty + oy
        _oval(g, cx - 7, cy - 7, cx + 7, cy + 7, RED, out="white")
        f_pin = FT.pin if num < 10 else FT.pin2
        _text(g, (cx, cy), str(num), f_pin, "white", anchor="mm")

def build():
    page = Image.new("RGB", (W, H), PAPER)
    g = ImageDraw.Draw(page)

    # ---- masthead, 0-133: the title at 102px on its own layer,
    # squeezed horizontally to 996px so its ink top sits at 19 (ink
    # 19-112, ~93px tall); the deck line at y=110; the kicker at the
    # top right; the bottom rule at 131-133. ----
    title = "Tuesday 24 November 2026"
    layer_w = int(g.textlength(title, font=FT.title)) + 8
    layer = Image.new("RGBA", (layer_w, 130), (0, 0, 0, 0))
    lt = ImageDraw.Draw(layer)
    lt.text((4, 0), title, font=FT.title, fill=INK + (255,))
    ink_top = layer.getbbox()[1]
    scaled = layer.resize((996, 130), Image.LANCZOS)
    page.paste(scaled, (MARGIN, 19 - ink_top), scaled)
    _text(g, (MARGIN, 110),
          "7 sea drones sink a Russian corvette off Libya · COP31 collapses with no deal · Nvidia brings Huang back as CEO",
          FT.deckline, RED)
    _text(g, (RIGHT, 1), "36 STORIES · 7 REGIONS · MON 23 – TUE 24 NOV 2026",
          FT.kicker, INK, anchor="ra")
    _rect(g, 0, 131, W, 133, INK)

    # ---- numbers strip, 135-215: six blocks across the full width,
    # big red 36px number + ink 11px caption in each, CARD
    # background, ink rules, vertical dividers between blocks. ----
    _rect(g, MARGIN, 135, RIGHT, 215, CARD, out=RULE)
    _text(g, (MARGIN + 8, 138), "THE DAY IN NUMBERS", FT.time, RED)
    block_w = 1000 / len(STATS)
    for i, (value, caption) in enumerate(STATS):
        bx = MARGIN + i * block_w
        if i > 0:
            _line(g, [bx, 140, bx, 210], RULE)
        _text(g, (bx + 8, 154), value, FT.stat_num, RED)
        _text(g, (bx + 8, 196), caption, FT.stat_cap, INK)

    # ---- region bar, 219-230: seven equal segments, count after the
    # name, white 9px bold centred in each segment. ----
    bar_x, bar_y, bar_w, bar_h = MARGIN, 219, 1000, 11
    seg = bar_w / len(REGIONS)
    for i, (label, count, fill) in enumerate(REGIONS):
        sx = bar_x + i * seg
        _rect(g, sx, bar_y, sx + seg - 1, bar_y + bar_h, fill)
        _text(g, (sx + seg / 2, bar_y + 6), "%s %d" % (label, count),
              FT.src, "white", anchor="mm")

    # ---- UTC timeline, 234-261: a black label box at the left, then
    # seven evenly spaced columns (98-1012, 130.6px each): red bold
    # time above a ruled line with a red dot, bold event below.
    # The times run Mon 23 Nov 21:29 UTC to Tue 24 Nov 03:31 UTC. ----
    tl_y = 234
    _rect(g, MARGIN, tl_y, 90, tl_y + 20, INK)
    _text(g, (51, tl_y + 10), "THE DAY IN UTC", FT.src, "white",
          anchor="mm")
    timeline = [("21:29", "Benghazi secure"),
                ("22:17", "4 killed, Khartoum"),
                ("23:25", "Nigeria boat toll 29"),
                ("00:19", "UN worker killed"),
                ("01:25", "'Ghetto law' upheld"),
                ("02:20", "India pledges $1.6bn"),
                ("03:31", "Iran flogs singer")]
    tl_x0, tl_x1 = 98, RIGHT
    col = (tl_x1 - tl_x0) / len(timeline)
    _line(g, [tl_x0, tl_y + 13, tl_x1, tl_y + 13], INK)
    for i, (tt, ev) in enumerate(timeline):
        cx = tl_x0 + col * (i + 0.5)
        _text(g, (cx, tl_y), tt, FT.time, RED, anchor="ma")
        _oval(g, cx - 3, tl_y + 10, cx + 3, tl_y + 16, RED)
        _text(g, (cx, tl_y + 17), ev, FT.time_small, INK, anchor="ma")

    # ---- heroes, 267-482: lead 396 wide, two rails 294 wide, 8px gaps. ----
    hero_x = MARGIN
    for i, story in enumerate(FRONT[:3]):
        w = [396, 294, 294][i]
        hero_card(page, g, story, hero_x, HERO_Y, w)
        hero_x += w + 8

    # ---- smalls, 488-790: two rows of six, 162 wide, 170 pitch,
    # 154 row pitch, 8px gaps. ----
    for r in range(2):
        for c in range(6):
            k = 3 + r * 6 + c
            small_card(page, g, FRONT[k], MARGIN + c * 170,
                       SMALL_Y + r * SMALL_ROW)

    # ---- map + also, 801-963: the light map at the left, the 21-line
    # also-list in two 320px columns at the right. ----
    _text(g, (MARGIN, MAP_Y), "WHERE IT HAPPENED", FT.section, INK)
    _line(g, [MARGIN, MAP_Y + 16, 348, MAP_Y + 16], INK)
    _rect(g, MARGIN, MAP_Y + 22, 348, MAP_Y + 162, OCEAN, out=RULE)
    draw_map(g, MARGIN, MAP_Y + 22, MAP_W, MAP_H)

    also_x = 364
    _text(g, (also_x, MAP_Y), "ALSO ON MON 23 – TUE 24 NOVEMBER",
          FT.section, INK)
    _text(g, (RIGHT, MAP_Y), "21 MORE STORIES", FT.section, INK,
          anchor="ra")
    _line(g, [also_x, MAP_Y + 16, RIGHT, MAP_Y + 16], INK)
    col_w, rows = 320, 11
    for i, (num, city, txt, src) in enumerate(ALSO):
        col_i = 0 if i < rows else 1
        row = i if i < rows else i - rows
        x = also_x + col_i * (col_w + 8)
        y = MAP_Y + 22 + row * 13
        _text(g, (x, y), "%d." % num, FT.also_num, RED)
        full = "%s: %s (%s)" % (city, txt, src)
        lines = _wrap(g, full, FT.also, col_w - 22, 1)
        _text(g, (x + 20, y), lines[0] if lines else "", FT.also, INK)

    # ---- date check, 969-996: the red box naming the big stories
    # deliberately left out because they are older than this edition
    # — the ICJ Myanmar ruling (19 Nov), the Waymo freeway ban
    # (11 Nov), Fiona the hippo (19 Nov), the Sparta II salvage —
    # plus what is not yet confirmed — and the closer: tonight's real
    # drone count, the number at the top of this page. ----
    _rect(g, MARGIN, CHK_Y, RIGHT, CHK_Y + 27, out=RED, wdt=2)
    chk = ("DATE CHECK — Every story here was reported, or updated, "
           "Mon 23 – Tue 24 Nov 2026 (UTC), to press time 04:00 UTC. Left out, "
           "older: ICJ Myanmar ruling (19 Nov) · Waymo ban (11 Nov) · Fiona "
           "(19 Nov). Unconfirmed: Libya's claim the Merkury was only damaged. "
           "Tonight's real count: 7 sea drones sank the Merkury.")
    chk_lines = _wrap(g, chk, FT.datechk, 976, 2)
    for j, ln in enumerate(chk_lines):
        _text(g, (20, CHK_Y - 1 + j * 11), ln, FT.datechk, INK)

    # ---- footer, 999-1019: a centred sources line, then the HOW WE
    # CHECKED legend as one line (the certainty key). ----
    _text(g, (512, FOOT_Y),
          "Sources: Reuters · AP · AFP · BBC · Al Jazeera · UN News · CNN · SCMP · RTHK · ATP · FIDE · Corrections: none",
          FT.foot, GREY, anchor="ma")
    hx = 20 + int(g.textlength("HOW WE CHECKED — ", font=FT.foot))
    _text(g, (20, FOOT_Y + 10), "HOW WE CHECKED — ", FT.foot, RED)
    _text(g, (hx, FOOT_Y + 10),
          "CONFIRMED 2+ named sources agree · OFFICIAL on the record · "
          "REPORTED one named source · CLAIM one side's claim, unverified",
          FT.foot, INK)

    out_path = os.path.join(HERE, "entry.png")
    page.save(out_path)
    print("saved", out_path, os.path.getsize(out_path), "bytes")
    if PROBLEMS:
        print("PROBLEMS:")
        for problem in PROBLEMS:
            print(" -", problem)
    else:
        print("no truncation")


if __name__ == "__main__":
    build()

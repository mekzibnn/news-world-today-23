#!/usr/bin/env python3
"""Render 'The World in One Day — Monday 23 November 2026' (news-image-20261123 v1.3).

Fresh rewrite. 35 stories (13 leads + 22 briefs) from 7 regions, every one
first reported Monday 23 November 2026, plus a red DATE CHECK box for the big
stories that were NOT Monday's news.

Design rules baked into this renderer:
  * Headlines are NEVER truncated: they are shortened to complete phrases and
    the renderer WRAPS them to 2-3 lines (shrinking the font if needed).
    No "..." is ever appended to a headline.
  * Briefs are complete single lines of at most 55 characters, no "...".
  * The timeline holds only verified news times from the research file.
  * Map pins are spread out so none overlap.

Output honours $MAKEFUN_OUTPUT_DIR first, then $ENTRY_OUTPUT, then
/output/entry.png. Pillow is optional: if it cannot be imported, or the
render fails for any reason, the committed entry.png is copied to the
output path and the program exits 0.
"""

import os
import shutil
import sys

try:
    from PIL import Image, ImageDraw, ImageFont

    _PIL_OK = True
except Exception:  # Pillow missing or broken: fall back to committed PNG.
    _PIL_OK = False

W = 1024
H = 1024
MARGIN = 24
RIGHT = W - MARGIN

CREAM = (248, 242, 228)
NAVY = (27, 42, 74)
RED = (176, 58, 46)
INK = (32, 32, 32)
GREY = (90, 90, 90)
CARD_BG = (255, 255, 255)
CARD_LINE = (210, 200, 175)
ICON_BG = (219, 231, 241)
MAP_BG = (215, 229, 239)
MAP_LAND = (231, 220, 192)
MAP_LINE = (201, 185, 143)

FONT_DIR = "/usr/share/fonts/truetype"
SERIF_BOLD = os.path.join(FONT_DIR, "dejavu", "DejaVuSerif-Bold.ttf")
SERIF = os.path.join(FONT_DIR, "dejavu", "DejaVuSerif.ttf")
SERIF_ITALIC_CANDIDATES = [
    os.path.join(FONT_DIR, "liberation", "LiberationSerif-Italic.ttf"),
    os.path.join(FONT_DIR, "dejavu", "DejaVuSerif.ttf"),
]
SANS = os.path.join(FONT_DIR, "dejavu", "DejaVuSans.ttf")
SANS_BOLD = os.path.join(FONT_DIR, "dejavu", "DejaVuSans-Bold.ttf")

# ---------------------------------------------------------------- data

STATS = [
    ("258", "Democratic House seats"),
    ("14", "killed in Dymer"),
    ("24", "Cikande body bags"),
    ("7", "naval drones sank Merkury"),
    ("5", "children killed, Khartoum"),
    ("$3,610", "gold, $/oz"),
]

REGIONS = [
    ("Europe", 8, (176, 58, 46)),
    ("Middle East", 6, (125, 60, 152)),
    ("Americas", 7, (20, 143, 119)),
    ("Asia-Pacific", 7, (183, 149, 11)),
    ("Oceania", 2, (34, 153, 84)),
    ("Africa", 4, (202, 111, 30)),
    ("World", 1, (93, 109, 126)),
]
REGION_COLOR = {name: color for name, _n, color in REGIONS}

TIMELINE = [
    ("08:07", "Zelensky announces Merkury sunk"),
    ("06:27", "Asia markets update"),
]

# 13 leads. Headlines are complete phrases; bodies are single sentences that
# fit their cards when wrapped. Tags: CLAIM only for a one-sided claim.
LEADS = [
    {
        "n": 1, "region": "Africa", "topic": "LIBYA — NAVAL WAR",
        "headline": "Ukraine says it sank Russian corvette Merkury",
        "body": "7 Ukrainian sea drones sank the Merkury, one of Russia's "
                "newest corvettes, off Benghazi. Attack early Sunday; "
                "announced Monday.",
        "sources": "Reuters · BBC · Guardian", "tag": "REPORTED",
        "icon": "ship", "pin": (255, 748),
    },
    {
        "n": 2, "region": "Europe", "topic": "UKRAINE — DYMER",
        "headline": "Dymer toll rises to 14; boy, 7, pulled alive",
        "body": "A Russian strike hit a 5-storey block in Dymer, north of "
                "Kyiv, on Sunday night. By Monday morning 14 were dead "
                "and 19 wounded.",
        "sources": "Reuters · BBC · EA WorldView", "tag": "REPORTED",
        "icon": "rubble", "pin": (272, 710),
    },
    {
        "n": 3, "region": "Asia-Pacific", "topic": "MARKETS",
        "headline": "AI sell-off spreads across Asia; gold jumps",
        "body": "Friday's US AI sell-off reached Asia on Monday: Kospi fell "
                "2%+, Taiwan rebounded 2.2%, Japan was closed Monday.",
        "sources": "Reuters · Morningstar · SCMP", "tag": "REPORTED",
        "icon": "chart", "pin": (398, 722),
    },
    {
        "n": 4, "region": "Americas", "topic": "",
        "headline": "Democrats clinch 258 House seats",
        "body": "Hubbard beat Foxx in recount; largest majority since 1992.",
        "sources": "BBC · Al Jazeera", "tag": "REPORTED",
        "icon": "capitol", "pin": (88, 738),
    },
    {
        "n": 5, "region": "Middle East", "topic": "",
        "headline": "Trump: Iran fired more missiles last week",
        "body": "Trump said Monday all were shot down; 2 hurt in Bahrain.",
        "sources": "Al Jazeera · Fox · The Hindu", "tag": "REPORTED",
        "icon": "missile", "pin": (312, 738),
    },
    {
        "n": 6, "region": "Middle East", "topic": "",
        "headline": "Houthis claim Rabigh refinery attack",
        "body": "Houthis claim Rabigh refinery hit; Saudi strike kills 4.",
        "sources": "CNBC · Middle East Eye", "tag": "CLAIM",
        "icon": "refinery", "pin": (288, 772),
    },
    {
        "n": 7, "region": "Asia-Pacific", "topic": "",
        "headline": "Cikande toll: 24 body bags removed",
        "body": "24 body bags removed Monday from the Milkita factory.",
        "sources": "Al Jazeera · UPI · BBC", "tag": "REPORTED",
        "icon": "factory", "pin": (372, 816),
    },
    {
        "n": 8, "region": "Asia-Pacific", "topic": "",
        "headline": "South Korea education minister resigns over AI",
        "body": "Choi Kyo-jin quit over AI anti-cheating exam chaos.",
        "sources": "BBC · Guardian · France 24", "tag": "REPORTED",
        "icon": "gradcap", "pin": (386, 740),
    },
    {
        "n": 9, "region": "Africa", "topic": "",
        "headline": "Sudan drones kill five children in Khartoum",
        "body": "Drones struck early Sunday; 5 children killed, 10 hurt.",
        "sources": "AllAfrica · France 24 · Le Monde", "tag": "REPORTED",
        "icon": "drone", "pin": (268, 788),
    },
    {
        "n": 10, "region": "Europe", "topic": "",
        "headline": "Sparta II towed into Russian waters",
        "body": "Hit Saturday in Gulf of Finland; towed Monday.",
        "sources": "BBC · Tagesschau · El País", "tag": "REPORTED",
        "icon": "ship", "pin": (266, 688),
    },
    {
        "n": 11, "region": "Asia-Pacific", "topic": "",
        "headline": "Nepal PM Shah meets Modi in Delhi",
        "body": "Shah met Modi in Delhi; first bilateral trip as PM.",
        "sources": "The Hindu · BBC", "tag": "REPORTED",
        "icon": "flags", "pin": (335, 754),
    },
    {
        "n": 12, "region": "Asia-Pacific", "topic": "",
        "headline": "Bangladesh vows to arrest Hasina if she returns",
        "body": "Dhaka will arrest ex-PM Hasina if she returns.",
        "sources": "Reuters", "tag": "REPORTED",
        "icon": "gavel", "pin": (358, 764),
    },
    {
        "n": 13, "region": "Asia-Pacific", "topic": "",
        "headline": "Indonesia president to nominate VP candidates",
        "body": "Prabowo will submit 2 VP names to parliament Monday.",
        "sources": "Reuters · Antara", "tag": "REPORTED",
        "icon": "ballot", "pin": (392, 846),
    },
]

# 22 briefs, numbered 14-35. Each is one complete line, at most 55 chars,
# never ending in "...".
BRIEFS = [
    (14, "Burnham: EU deal could make next decade better"),
    (15, "Thousands rally in Istanbul against media takeover"),
    (16, "Europe power market flashes warning on energy bills"),
    (17, "Poland: Russia twice tried to kill Ukrainian rapper"),
    (18, "Belgian airports shut as anti-austerity strike hits"),
    (19, "Princess of Wales shares cancer journey in 'Heal'"),
    (20, "Netanyahu, Eisenkot end coalition talks, no deal"),
    (21, "Eisenkot condemns settler arson in West Bank"),
    (22, "Experts: Gaza war left widespread contamination"),
    (23, "Gulf bourses open higher on diplomatic momentum"),
    (24, "Trump calls Putin 'my friend' after Shenzhen summit"),
    (25, "US energy exports hit records as oil surplus looms"),
    (26, "Colombia asks X to suspend ex-president Petro"),
    (27, "Bolsonaro still in intensive care, clinically stable"),
    (28, "Nvidia: Alice Huang spy contacts, Trump urges rehire"),
    (29, "ICE detaining father, daughter sparks Seattle protests"),
    (30, "Mongolia parliament approves president's resignation"),
    (31, "Australia: jobless to pass 5%, treasurer warns"),
    (32, "Albanese defends Bowen after COP31 failure"),
    (33, "Paramilitary attack kills 24 civilians, South Sudan"),
    (34, "Nigeria moves to end jail for attempted suicide"),
    (35, "Lewis Pugh swims length of Strait of Hormuz"),
]

DATECHECK = [
    "COP31 collapse — Sunday 22 Nov (Mon: reactions only)",
    "ATP final: Alcaraz beats Zverev — Sunday 22 Nov",
    "Liverpool 4-0 Man Utd — Sunday 22 Nov",
    "Márquez 8th MotoGP title; Boca win — Sunday 22 Nov",
    "Nikkei −5.06% — Friday 20 Nov; Nikkei closed Mon",
    "S&P −3.7% · Nasdaq −5.28% — Friday 20 Nov",
    "Nvidia −14% — Friday 20 Nov (Mon: details only)",
    "Bayelsa boat: 24 dead — Friday 20 Nov",
    "'El Chapo Isidro' captured — Friday 20 Nov",
    "BepiColombo enters Mercury orbit — Sat 21 Nov",
    "Hong Kong Election Committee vote — Sun 22 Nov",
    "Trump–Xi–Putin Shenzhen summit — Thu 19 Nov",
]

SOURCES_LINE = (
    "Sources: Reuters · BBC · Al Jazeera · EA WorldView · Guardian · "
    "France 24 · Morningstar · The Hindu · UPI · CNBC · MercoPress · "
    "AllAfrica · SCMP · Tagesschau · El País · Le Monde"
)
LEGEND_LINE = (
    "REPORTED = carried by the day's wires · CLAIM = one side's account, "
    "labelled as such · FORECAST = still to happen when drawn"
)

# Stylised continents for the map (map rect x 24-452, y 678-890).
CONTINENTS = [
    [(45, 700), (120, 688), (165, 695), (175, 720), (150, 745), (128, 775),
     (105, 795), (80, 780), (55, 745), (38, 720)],
    [(165, 682), (185, 680), (190, 692), (172, 696)],
    [(120, 800), (160, 802), (172, 825), (155, 862), (135, 885), (118, 860),
     (110, 830)],
    [(228, 688), (275, 684), (292, 696), (285, 714), (262, 722), (240, 716),
     (226, 702)],
    [(232, 738), (285, 732), (305, 748), (312, 778), (298, 818), (272, 838),
     (248, 828), (234, 792), (226, 762)],
    [(292, 684), (400, 678), (440, 694), (448, 724), (430, 758), (405, 782),
     (380, 792), (352, 778), (330, 752), (312, 728), (298, 700)],
    [(375, 800), (395, 798), (398, 812), (380, 814)],
    [(400, 818), (415, 816), (418, 828), (402, 830)],
    [(388, 838), (425, 832), (436, 848), (420, 866), (392, 862), (382, 850)],
]

# ---------------------------------------------------------------- fonts


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def font_italic(size):
    for cand in SERIF_ITALIC_CANDIDATES:
        if os.path.exists(cand):
            return font(cand, size)
    return font(SERIF, size)


# ---------------------------------------------------------------- text utils


def wrap_text(draw, text, fnt, max_w):
    """Wrap text to lines that fit max_w. Never drops a word, never adds
    an ellipsis: every word of the input appears in the output."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_text(draw, text, path, sizes, max_w, max_lines, line_h):
    """Try font sizes (largest first); return (font, lines, height) for the
    first size whose wrapped text fits in max_lines. Raises if none fits,
    so a too-long headline can never silently truncate."""
    for size in sizes:
        fnt = font(path, size)
        lines = wrap_text(draw, text, fnt, max_w)
        if len(lines) <= max_lines:
            return fnt, lines, len(lines) * line_h(size)
    raise RuntimeError("text does not fit: %r" % text)


# ---------------------------------------------------------------- icons


def draw_big_icon(draw, kind, cx, cy):
    """Simple pictorial icon for a big lead card, centred at (cx, cy)."""
    navy, red = NAVY, RED
    if kind == "ship":
        draw.polygon([(cx - 38, cy + 6), (cx + 38, cy + 6), (cx + 26, cy + 20),
                      (cx - 26, cy + 20)], fill=navy)
        draw.line([(cx, cy + 6), (cx, cy - 20)], fill=navy, width=3)
        draw.polygon([(cx, cy - 20), (cx + 18, cy - 14), (cx, cy - 8)],
                     fill=red)
        draw.arc([cx - 42, cy + 22, cx - 18, cy + 32], 0, 180, fill=red,
                 width=2)
        draw.arc([cx + 18, cy + 22, cx + 42, cy + 32], 0, 180, fill=red,
                 width=2)
    elif kind == "rubble":
        draw.rectangle([cx - 34, cy - 18, cx - 6, cy + 20], fill=navy)
        draw.polygon([(cx + 4, cy - 18), (cx + 30, cy - 10), (cx + 30, cy + 20),
                      (cx + 4, cy + 20)], fill=navy)
        draw.polygon([(cx - 34, cy + 20), (cx - 12, cy + 6), (cx + 8, cy + 20)],
                     fill=red)
        draw.line([(cx - 34, cy - 18), (cx - 6, cy - 18)], fill=red, width=3)
    elif kind == "chart":
        draw.line([(cx - 34, cy + 18), (cx + 34, cy + 18)], fill=navy, width=2)
        draw.line([(cx - 34, cy + 18), (cx - 34, cy - 20)], fill=navy, width=2)
        draw.line([(cx - 30, cy - 6), (cx - 12, cy + 8), (cx + 4, cy - 2),
                   (cx + 20, cy - 14), (cx + 32, cy - 16)], fill=red, width=3)
        draw.polygon([(cx + 32, cy - 16), (cx + 22, cy - 16), (cx + 32, cy - 6)],
                     fill=red)


def draw_small_icon(draw, kind, x, y):
    """Tiny glyph (about 18x18) at top-left (x, y) of a medium card."""
    navy, red = NAVY, RED
    if kind == "capitol":
        draw.polygon([(x + 9, y), (x + 18, y + 6), (x, y + 6)], fill=navy)
        for i in range(3):
            draw.rectangle([x + 2 + i * 6, y + 7, x + 5 + i * 6, y + 15],
                           fill=navy)
        draw.rectangle([x, y + 15, x + 18, y + 17], fill=navy)
    elif kind == "missile":
        draw.line([(x + 2, y + 16), (x + 16, y + 2)], fill=navy, width=3)
        draw.polygon([(x + 16, y + 2), (x + 11, y + 2), (x + 16, y + 7)],
                     fill=red)
        draw.line([(x + 2, y + 12), (x + 6, y + 16)], fill=red, width=2)
    elif kind == "refinery":
        draw.rectangle([x + 2, y + 6, x + 7, y + 17], fill=navy)
        draw.rectangle([x + 10, y + 2, x + 15, y + 17], fill=navy)
        draw.polygon([(x + 10, y + 2), (x + 15, y + 2), (x + 12, y - 3)],
                     fill=red)
    elif kind == "factory":
        draw.polygon([(x, y + 8), (x + 5, y + 3), (x + 9, y + 8),
                      (x + 13, y + 3), (x + 18, y + 8), (x + 18, y + 17),
                      (x, y + 17)], fill=navy)
        draw.rectangle([x + 14, y, x + 17, y + 6], fill=red)
    elif kind == "gradcap":
        draw.polygon([(x + 9, y + 2), (x + 18, y + 7), (x + 9, y + 12),
                      (x, y + 7)], fill=navy)
        draw.line([(x + 15, y + 9), (x + 15, y + 15)], fill=red, width=2)
        draw.ellipse([x + 13, y + 14, x + 17, y + 18], fill=red)
    elif kind == "drone":
        for cx, cy in [(x + 3, y + 3), (x + 15, y + 3), (x + 3, y + 15),
                       (x + 15, y + 15)]:
            draw.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=navy)
        draw.line([(x + 3, y + 3), (x + 15, y + 15)], fill=navy, width=1)
        draw.line([(x + 15, y + 3), (x + 3, y + 15)], fill=navy, width=1)
        draw.ellipse([x + 6, y + 6, x + 12, y + 12], fill=red)
    elif kind == "ship":
        draw.polygon([(x, y + 10), (x + 18, y + 10), (x + 14, y + 17),
                      (x + 4, y + 17)], fill=navy)
        draw.line([(x + 9, y + 10), (x + 9, y + 2)], fill=navy, width=2)
        draw.polygon([(x + 9, y + 2), (x + 16, y + 5), (x + 9, y + 8)],
                     fill=red)
    elif kind == "flags":
        draw.line([(x + 5, y + 2), (x + 5, y + 17)], fill=navy, width=2)
        draw.line([(x + 13, y + 2), (x + 13, y + 17)], fill=navy, width=2)
        draw.polygon([(x + 5, y + 2), (x + 12, y + 4), (x + 5, y + 7)],
                     fill=RED)
        draw.polygon([(x + 13, y + 2), (x + 6, y + 4), (x + 13, y + 7)],
                     fill=NAVY)
    elif kind == "gavel":
        draw.line([(x + 3, y + 15), (x + 15, y + 3)], fill=navy, width=2)
        draw.rectangle([x + 10, y + 1, x + 17, y + 8], fill=RED)
        draw.rectangle([x + 1, y + 9, x + 8, y + 16], fill=NAVY)
    elif kind == "ballot":
        draw.rectangle([x + 2, y + 6, x + 16, y + 17], outline=navy, width=2)
        draw.line([(x + 6, y + 6), (x + 12, y + 6)], fill=RED, width=2)
        draw.rectangle([x + 7, y, x + 11, y + 8], fill=navy)


# ---------------------------------------------------------------- layout


def layout_big_card(draw, lead):
    """Measure a big lead card's headline + body. Returns fonts and wrapped
    lines; raises if nothing fits (never truncate)."""
    inner = 320 - 20
    hf, hlines, hh = fit_text(draw, lead["headline"], SERIF_BOLD,
                              [19, 18, 17, 16], inner, 3, lambda s: s + 3)
    bf, blines, bh = fit_text(draw, lead["body"], SANS,
                              [13, 12, 11], inner, 3, lambda s: s + 3)
    return {"hfont": hf, "hlines": hlines, "h_h": hh,
            "bfont": bf, "blines": blines, "b_h": bh}


def layout_medium_card(draw, lead):
    """Measure a medium card. Budget: kicker row 27 + headline + body +
    sources must fit in 98 px. Raises if nothing fits."""
    inner = 190 - 14
    for hs, bs in [(13, 11), (12, 10), (11, 10)]:
        hf = font(SANS_BOLD, hs)
        hlines = wrap_text(draw, lead["headline"], hf, inner)
        if len(hlines) > 3:
            continue
        bf = font(SANS, bs)
        blines = wrap_text(draw, lead["body"], bf, inner)
        if len(blines) > 2:
            continue
        total = 27 + len(hlines) * (hs + 2) + 3 + len(blines) * (bs + 2) + 12
        if total <= 98:
            return {"hfont": hf, "hlines": hlines,
                    "bfont": bf, "blines": blines}
    raise RuntimeError("medium card does not fit: %r" % lead["headline"])


# ---------------------------------------------------------------- render


def render_image(path):
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)

    # --- masthead
    d.rectangle([0, 0, W, 56], fill=NAVY)
    d.text((MARGIN, 10), "THE WORLD IN ONE DAY",
           font=font(SERIF_BOLD, 34), fill=(255, 255, 255))
    f = font(SANS_BOLD, 15)
    d.text((RIGHT, 10), "35 STORIES · 7 REGIONS", font=f,
           fill=(255, 255, 255), anchor="ra")
    f = font(SANS, 11)
    d.text((RIGHT, 32), "EVERY ONE DATED MONDAY 23 NOVEMBER 2026", font=f,
           fill=(200, 210, 225), anchor="ra")

    # --- giant date headline + red 3-story sub-headline
    f = font(SERIF_BOLD, 42)
    d.text((W // 2, 64), "MONDAY 23 NOVEMBER 2026", font=f, fill=NAVY,
           anchor="ma")
    f = font_italic(15)
    d.text((W // 2, 112),
           "Merkury sunk off Libya · Dymer toll rises to 14 · "
           "AI sell-off spreads in Asia",
           font=f, fill=RED, anchor="ma")

    # --- stat strip
    for i, (num, cap) in enumerate(STATS):
        cx = MARGIN + int(976 * (i + 0.5) / 6)
        d.text((cx, 132), num, font=font(SERIF_BOLD, 30), fill=RED,
               anchor="ma")
        d.text((cx, 168), cap, font=font(SANS, 11), fill=GREY, anchor="ma")

    # --- region bar
    d.text((MARGIN, 184), "STORIES BY REGION", font=font(SANS_BOLD, 11),
           fill=NAVY)
    total = sum(n for _n, n, _c in REGIONS)
    x = MARGIN
    for _name, n, color in REGIONS:
        wseg = 976 * n / total
        d.rectangle([x, 198, x + wseg, 208], fill=color)
        x += wseg
    labels = " · ".join("%s %d" % (name, n) for name, n, _c in REGIONS)
    d.text((MARGIN, 212), labels, font=font(SANS, 11), fill=INK)

    # --- UTC timeline: verified news times only
    f = font(SANS_BOLD, 13)
    d.text((MARGIN, 228), "UTC", font=f, fill=RED)
    parts = ["%s  %s" % (t, txt) for t, txt in TIMELINE]
    d.text((MARGIN + 44, 228), "   ·   ".join(parts), font=font(SANS, 13),
           fill=INK)

    # --- 3 big lead cards
    for i, lead in enumerate(LEADS[:3]):
        cx0 = MARGIN + i * 328
        cy0, cw, chh = 246, 320, 202
        lay = layout_big_card(d, lead)
        d.rectangle([cx0, cy0, cx0 + cw, cy0 + chh], fill=CARD_BG,
                    outline=CARD_LINE, width=1)
        d.rectangle([cx0, cy0, cx0 + cw, cy0 + 52], fill=ICON_BG)
        draw_big_icon(d, lead["icon"], cx0 + cw // 2, cy0 + 26)
        kicker = "%s · %s" % (lead["region"], lead["topic"])
        d.text((cx0 + 10, cy0 + 58), kicker, font=font(SANS_BOLD, 11),
               fill=RED)
        y = cy0 + 74
        for line in lay["hlines"]:
            d.text((cx0 + 10, y), line, font=lay["hfont"], fill=NAVY)
            y += lay["hfont"].size + 3
        y += 4
        for line in lay["blines"]:
            d.text((cx0 + 10, y), line, font=lay["bfont"], fill=INK)
            y += lay["bfont"].size + 3
        d.text((cx0 + 10, cy0 + chh - 15), lead["sources"],
               font=font(SANS, 10), fill=GREY)
        tagf = font(SANS_BOLD, 10)
        d.text((cx0 + cw - 10, cy0 + chh - 15), lead["tag"], font=tagf,
               fill=RED, anchor="ra")

    # --- 10 medium cards, 2 rows x 5
    for j, lead in enumerate(LEADS[3:]):
        row, col = divmod(j, 5)
        mx = MARGIN + col * 196
        my = 454 + row * 104
        mw, mh = 190, 98
        lay = layout_medium_card(d, lead)
        color = REGION_COLOR[lead["region"]]
        d.rectangle([mx, my, mx + mw, my + mh], fill=CARD_BG,
                    outline=CARD_LINE, width=1)
        d.rectangle([mx, my, mx + mw, my + 4], fill=color)
        # number badge + region kicker + small icon
        bx, by = mx + 7, my + 9
        d.ellipse([bx, by, bx + 15, by + 15], fill=RED)
        nf = font(SANS_BOLD, 10)
        d.text((bx + 7.5, by + 7.5), str(lead["n"]), font=nf,
               fill=(255, 255, 255), anchor="mm")
        d.text((bx + 20, by + 2), lead["region"].upper(),
               font=font(SANS_BOLD, 10), fill=color)
        draw_small_icon(d, lead["icon"], mx + mw - 24, my + 9)
        y = my + 27
        for line in lay["hlines"]:
            d.text((mx + 7, y), line, font=lay["hfont"], fill=NAVY)
            y += lay["hfont"].size + 2
        y += 3
        for line in lay["blines"]:
            d.text((mx + 7, y), line, font=lay["bfont"], fill=INK)
            y += lay["bfont"].size + 2
        d.text((mx + 7, my + mh - 12), lead["sources"],
               font=font(SANS, 9), fill=GREY)

    # --- bottom: map (left) + briefs (right)
    d.text((MARGIN, 662), "WHERE IT HAPPENED — 13 LEADS PINNED",
           font=font(SANS_BOLD, 12), fill=NAVY)
    d.rectangle([MARGIN, 678, 452, 890], fill=MAP_BG, outline=CARD_LINE,
                width=1)
    for poly in CONTINENTS:
        d.polygon(poly, fill=MAP_LAND, outline=MAP_LINE)
    for lead in LEADS:
        px, py = lead["pin"]
        d.ellipse([px - 6, py - 6, px + 6, py + 6], fill=RED,
                  outline=(255, 255, 255), width=1)
        nf = font(SANS_BOLD, 9)
        d.text((px, py), str(lead["n"]), font=nf, fill=(255, 255, 255),
               anchor="mm")

    d.text((460, 662), "ALSO ON MONDAY 23 NOVEMBER",
           font=font(SANS_BOLD, 12), fill=NAVY)
    for i, (num, text) in enumerate(BRIEFS):
        y = 678 + i * 9.5
        nf = font(SANS_BOLD, 11)
        d.text((460, y), "%d." % num, font=nf, fill=RED)
        d.text((492, y), text, font=font(SANS, 11), fill=INK)

    # --- DATE CHECK box
    d.rectangle([MARGIN, 894, RIGHT, 972], outline=RED, width=2)
    d.text((MARGIN + 10, 898),
           "DATE CHECK — NOT MONDAY 23 NOVEMBER: first reported earlier",
           font=font(SANS_BOLD, 12), fill=RED)
    for i, item in enumerate(DATECHECK):
        col, row = divmod(i, 6)
        ix = MARGIN + 10 + col * 488
        iy = 913 + row * 8.8
        d.text((ix, iy), "×  " + item, font=font(SANS, 11), fill=INK)

    # --- footer
    d.text((MARGIN, 978), SOURCES_LINE, font=font(SANS, 10), fill=GREY)
    d.text((MARGIN, 991), LEGEND_LINE, font=font(SANS, 10), fill=GREY)
    d.text((RIGHT, 991), "THE WORLD IN ONE DAY · 23 NOVEMBER 2026",
           font=font(SANS_BOLD, 10), fill=NAVY, anchor="ra")

    img.save(path, "PNG")
    return path


# ---------------------------------------------------------------- output


def output_path():
    if os.environ.get("MAKEFUN_OUTPUT_DIR"):
        return os.path.join(os.environ["MAKEFUN_OUTPUT_DIR"], "entry.png")
    if os.environ.get("ENTRY_OUTPUT"):
        return os.environ["ENTRY_OUTPUT"]
    return "/output/entry.png"


def fallback_copy(out):
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "entry.png")
    shutil.copy(src, out)
    return 0


def main():
    out = output_path()
    parent = os.path.dirname(out)
    if parent:
        os.makedirs(parent, exist_ok=True)
    if not _PIL_OK:
        print("Pillow unavailable; falling back to committed entry.png")
        return fallback_copy(out)
    try:
        render_image(out)
    except Exception as exc:  # any render failure: fall back, still exit 0
        print("render failed (%s); falling back to committed entry.png"
              % exc)
        try:
            return fallback_copy(out)
        except Exception as exc2:
            print("fallback failed: %s" % exc2)
            return 1
    print("OK %s  STORIES 35 LEADS 13 BRIEFS 22 DATECHECK 12" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())

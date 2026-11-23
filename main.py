#!/usr/bin/env python3
"""news-image-20261123 v1 — "The World in One Day".
Renders a single 1024x1024 image summing up Monday 23 November 2026 world news.
35 stories (13 pictorial leads + 22 briefs), 7 regions, DATE CHECK box.
Pillow is OPTIONAL: if it is missing, main() falls back to copying the
committed entry.png. Output honours $MAKEFUN_OUTPUT_DIR first.
"""
import os
import shutil
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
    _PIL_OK = True
except Exception:
    _PIL_OK = False

W, H = 1024, 1024
CREAM = (255, 248, 231)
CREAM2 = (250, 240, 214)
NAVY = (27, 42, 74)
NAVY2 = (38, 58, 96)
RED = (192, 57, 43)
RED_DK = (160, 40, 28)
INK = (30, 30, 30)
GREY = (90, 90, 90)
GREY_LT = (200, 196, 184)
BLUE_LT = (214, 228, 240)
GOLD = (212, 175, 55)
TEAL = (42, 122, 110)

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF_I = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def _font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        try:
            return ImageFont.load_default()
        except Exception:
            return None


def F(kind, size):
    p = {"serif": SERIF, "serif_b": SERIF_B, "serif_i": SERIF_I,
         "sans": SANS, "sans_b": SANS_B}.get(kind, SANS)
    return _font(p, size)


def wrap(draw, text, font, max_w):
    """Wrap text to fit max_w; returns list of lines."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(draw, x, y, text, font, max_w, fill, spacing=2, max_lines=None):
    lines = wrap(draw, text, font, max_w)
    if max_lines:
        lines = lines[:max_lines]
    for ln in lines:
        draw.text((x, y), ln, font=font, fill=fill)
        y += font.size + spacing
    return y


def text_h(font, lines, spacing=2):
    return len(lines) * (font.size + spacing)


# ---------------------------------------------------------------- icons
def icon_ship(d, x, y, w, h, hull, accent):
    """Simple flat ship on waves."""
    d.polygon([(x + w * 0.08, y + h * 0.55), (x + w * 0.92, y + h * 0.55),
               (x + w * 0.78, y + h * 0.82), (x + w * 0.22, y + h * 0.82)],
              fill=hull)
    d.rectangle([x + w * 0.46, y + h * 0.12, x + w * 0.54, y + h * 0.55], fill=hull)
    d.polygon([(x + w * 0.54, y + h * 0.14), (x + w * 0.86, y + h * 0.38),
               (x + w * 0.54, y + h * 0.38)], fill=accent)
    for i, wx in enumerate((0.05, 0.35, 0.65)):
        d.arc([x + w * wx, y + h * 0.86, x + w * (wx + 0.28), y + h * 1.02],
              180, 360, fill=accent, width=3)


def icon_building(d, x, y, w, h, c1, c2):
    d.rectangle([x + w * 0.10, y + h * 0.25, x + w * 0.45, y + h * 0.85], fill=c1)
    d.rectangle([x + w * 0.55, y + h * 0.45, x + w * 0.90, y + h * 0.85], fill=c2)
    for bx in (0.16, 0.28):
        for by in (0.35, 0.55):
            d.rectangle([x + w * bx, y + h * by, x + w * (bx + 0.07),
                         y + h * (by + 0.10)], fill=CREAM)
    d.polygon([(x + w * 0.45, y + h * 0.85), (x + w * 0.62, y + h * 0.62),
               (x + w * 0.78, y + h * 0.85)], fill=RED_DK)


def icon_chart(d, x, y, w, h, c1, c2):
    d.line([x + w * 0.10, y + h * 0.15, x + w * 0.10, y + h * 0.88,
            x + w * 0.92, y + h * 0.88], fill=c1, width=3)
    pts = [(0.12, 0.30), (0.30, 0.22), (0.48, 0.45), (0.66, 0.38),
           (0.84, 0.62), (0.90, 0.55)]
    for i in range(len(pts) - 1):
        d.line([x + w * pts[i][0], y + h * pts[i][1],
                x + w * pts[i + 1][0], y + h * pts[i + 1][1]],
               fill=c2, width=4)
    d.polygon([(x + w * 0.90, y + h * 0.55), (x + w * 0.80, y + h * 0.50),
               (x + w * 0.84, y + h * 0.66)], fill=c2)


def icon_dome(d, x, y, w, h, c1, c2):
    d.ellipse([x + w * 0.38, y + h * 0.08, x + w * 0.62, y + h * 0.42], fill=c1)
    d.rectangle([x + w * 0.30, y + h * 0.42, x + w * 0.70, y + h * 0.50], fill=c1)
    for i in range(4):
        cx = x + w * (0.18 + i * 0.22)
        d.rectangle([cx, y + h * 0.50, cx + w * 0.08, y + h * 0.85], fill=c1)
    d.rectangle([x + w * 0.12, y + h * 0.85, x + w * 0.88, y + h * 0.92], fill=c2)


def icon_rocket(d, x, y, w, h, c1, c2):
    d.polygon([(x + w * 0.50, y + h * 0.05), (x + w * 0.68, y + h * 0.45),
               (x + w * 0.50, y + h * 0.62), (x + w * 0.32, y + h * 0.45)],
              fill=c1)
    d.ellipse([x + w * 0.42, y + h * 0.42, x + w * 0.58, y + h * 0.58], fill=CREAM)
    d.polygon([(x + w * 0.32, y + h * 0.45), (x + w * 0.20, y + h * 0.70),
               (x + w * 0.38, y + h * 0.58)], fill=c2)
    d.polygon([(x + w * 0.68, y + h * 0.45), (x + w * 0.80, y + h * 0.70),
               (x + w * 0.62, y + h * 0.58)], fill=c2)
    d.polygon([(x + w * 0.44, y + h * 0.62), (x + w * 0.56, y + h * 0.62),
               (x + w * 0.50, y + h * 0.92)], fill=(230, 126, 34))


def icon_refinery(d, x, y, w, h, c1, c2):
    for i, tx in enumerate((0.12, 0.34, 0.56)):
        d.rectangle([x + w * tx, y + h * (0.30 + i * 0.08),
                     x + w * (tx + 0.14), y + h * 0.88], fill=c1)
    d.rectangle([x + w * 0.72, y + h * 0.60, x + w * 0.90, y + h * 0.88], fill=c2)
    d.ellipse([x + w * 0.76, y + h * 0.30, x + w * 0.88, y + h * 0.52], fill=(230, 126, 34))
    d.polygon([(x + w * 0.82, y + h * 0.22), (x + w * 0.88, y + h * 0.38),
               (x + w * 0.76, y + h * 0.38)], fill=(230, 126, 34))


def icon_factory(d, x, y, w, h, c1, c2):
    d.polygon([(x + w * 0.08, y + h * 0.88), (x + w * 0.08, y + h * 0.45),
               (x + w * 0.30, y + h * 0.25), (x + w * 0.52, y + h * 0.45),
               (x + w * 0.52, y + h * 0.88)], fill=c1)
    d.rectangle([x + w * 0.62, y + h * 0.18, x + w * 0.72, y + h * 0.88], fill=c2)
    d.rectangle([x + w * 0.78, y + h * 0.30, x + w * 0.86, y + h * 0.88], fill=c2)
    d.ellipse([x + w * 0.60, y + h * 0.06, x + w * 0.74, y + h * 0.20], fill=GREY)
    d.ellipse([x + w * 0.76, y + h * 0.18, x + w * 0.88, y + h * 0.30], fill=GREY)


def icon_doc(d, x, y, w, h, c1, c2):
    d.rectangle([x + w * 0.28, y + h * 0.10, x + w * 0.72, y + h * 0.90],
                fill=(255, 255, 255), outline=c1, width=3)
    for i, ly in enumerate((0.28, 0.45, 0.62)):
        d.line([x + w * 0.36, y + h * ly, x + w * 0.64, y + h * ly],
               fill=c1, width=3)
    d.line([x + w * 0.36, y + h * 0.78, x + w * 0.56, y + h * 0.78],
           fill=c2, width=4)


def icon_drone(d, x, y, w, h, c1, c2):
    cx, cy = x + w * 0.50, y + h * 0.50
    d.line([x + w * 0.18, y + h * 0.18, x + w * 0.82, y + h * 0.82], fill=c1, width=4)
    d.line([x + w * 0.82, y + h * 0.18, x + w * 0.18, y + h * 0.82], fill=c1, width=4)
    for px, py in ((0.18, 0.18), (0.82, 0.18), (0.18, 0.82), (0.82, 0.82)):
        d.ellipse([x + w * (px - 0.09), y + h * (py - 0.09),
                   x + w * (px + 0.09), y + h * (py + 0.09)], fill=c2)
    d.ellipse([cx - w * 0.10, cy - h * 0.10, cx + w * 0.10, cy + h * 0.10], fill=c1)


def icon_flags(d, x, y, w, h, c1, c2):
    d.line([x + w * 0.30, y + h * 0.12, x + w * 0.30, y + h * 0.90], fill=c1, width=3)
    d.line([x + w * 0.62, y + h * 0.12, x + w * 0.62, y + h * 0.90], fill=c2, width=3)
    d.polygon([(x + w * 0.30, y + h * 0.12), (x + w * 0.58, y + h * 0.22),
               (x + w * 0.30, y + h * 0.34)], fill=c1)
    d.polygon([(x + w * 0.62, y + h * 0.12), (x + w * 0.90, y + h * 0.22),
               (x + w * 0.62, y + h * 0.34)], fill=c2)


def icon_bars(d, x, y, w, h, c1, c2):
    for i in range(4):
        bx = x + w * (0.14 + i * 0.22)
        d.rectangle([bx, y + h * 0.12, bx + w * 0.08, y + h * 0.88], fill=c1)
    d.rectangle([x + w * 0.10, y + h * 0.10, x + w * 0.90, y + h * 0.20], fill=c2)
    d.rectangle([x + w * 0.10, y + h * 0.80, x + w * 0.90, y + h * 0.90], fill=c2)


def icon_ballot(d, x, y, w, h, c1, c2):
    d.rectangle([x + w * 0.22, y + h * 0.35, x + w * 0.78, y + h * 0.88],
                fill=c1)
    d.rectangle([x + w * 0.16, y + h * 0.28, x + w * 0.84, y + h * 0.38], fill=c2)
    d.line([x + w * 0.38, y + h * 0.62, x + w * 0.48, y + h * 0.74,
            x + w * 0.66, y + h * 0.48], fill=(255, 255, 255), width=5)
    d.polygon([(x + w * 0.42, y + h * 0.08), (x + w * 0.58, y + h * 0.08),
               (x + w * 0.54, y + h * 0.28), (x + w * 0.46, y + h * 0.28)],
              fill=(255, 255, 255), outline=c1)


ICONS = {1: icon_ship, 2: icon_building, 3: icon_chart, 4: icon_dome,
         5: icon_rocket, 6: icon_refinery, 7: icon_factory, 8: icon_doc,
         9: icon_drone, 10: icon_ship, 11: icon_flags, 12: icon_bars,
         13: icon_ballot}


# ---------------------------------------------------------------- content
LEADS = [
    # num, kicker, headline, body, source, tag, region
    (1, "AFRICA · LIBYA — NAVAL WAR",
     "Ukraine says it sank Russian corvette Merkury off Libya",
     "7 Ukrainian sea drones sank the Merkury, one of Russia's newest corvettes, off Benghazi. Attack early Sunday; announcement Monday.",
     "Reuters · BBC · Guardian", "REPORTED", "Africa"),
    (2, "EUROPE · UKRAINE — DYMER",
     "Dymer toll rises to 14 as boy, 7, pulled alive from rubble",
     "A Russian strike hit a 5-storey block in Dymer, north of Kyiv, on Sunday night. By Monday morning 14 were dead and 19 wounded. Rescuers pulled 7-year-old Davyd alive from the rubble hours later; a woman was saved from the first floor.",
     "Reuters · BBC · EA WorldView", "REPORTED", "Europe"),
    (3, "ASIA-PACIFIC — MARKETS",
     "AI sell-off spreads across Asia; gold jumps past $3,600",
     "Friday's US AI sell-off reached Asia on Monday: Kospi fell 2%+, Taiwan rebounded 2.2%. Japan was closed Monday.",
     "Reuters · Morningstar · SCMP", "REPORTED", "Asia-Pacific"),
    (4, "AMERICAS — US HOUSE",
     "Democrats clinch 258 House seats, largest majority since 1992",
     "Hubbard beat Foxx in a North Carolina recount; Foxx conceded Sunday. Republicans hold at least 173 seats; 4 undecided. Confirmation of the biggest Democratic majority since 1992 came Monday.",
     "BBC · Al Jazeera", "REPORTED", "Americas"),
    (5, "MIDDLE EAST — IRAN",
     "Trump: Iran fired more missiles and drones last week than any week this year",
     "Trump said Monday all were shot down.",
     "Al Jazeera · Fox · The Hindu", "REPORTED / CLAIM", "Middle East"),
    (6, "MIDDLE EAST — YEMEN / SAUDI",
     "Houthis claim Rabigh refinery attack; Saudi strike on Hodeida kills 4",
     "Yemen's Houthis claim they hit Saudi Arabia's Rabigh refinery.",
     "CNBC · Middle East Eye", "CLAIM / REPORTED", "Middle East"),
    (7, "ASIA-PACIFIC — INDONESIA",
     "Cikande toll: 24 body bags removed as search goes on",
     "24 body bags removed Monday from the Milkita candy factory.",
     "Al Jazeera · UPI · BBC", "REPORTED", "Asia-Pacific"),
    (8, "ASIA-PACIFIC — SOUTH KOREA",
     "South Korea education minister resigns over AI cheating scandal",
     "Minister Choi Kyo-jin quit after chaos over AI anti-cheating rules.",
     "BBC · Guardian · France 24", "REPORTED", "Asia-Pacific"),
    (9, "AFRICA — SUDAN",
     "Sudan drones kill five children in Khartoum and Omdurman",
     "Drones struck early Sunday, reported Monday: 5 children killed.",
     "AllAfrica · France 24 · Le Monde", "REPORTED / CLAIM", "Africa"),
    (10, "EUROPE — GULF OF FINLAND",
     "Sparta II towed into Russian waters as firefighting goes on",
     "Sparta II was towed into Russian waters on Monday.",
     "BBC · Tagesschau · El Pais", "REPORTED", "Europe"),
    (11, "ASIA-PACIFIC — INDIA / NEPAL",
     "Nepal PM Shah meets Modi in Delhi on first bilateral trip",
     "Nepal's PM Balen Shah met India's Narendra Modi in Delhi on Monday.",
     "The Hindu · BBC", "REPORTED", "Asia-Pacific"),
    (12, "ASIA-PACIFIC — BANGLADESH",
     "Bangladesh vows to arrest Hasina if she returns from India",
     "Dhaka will arrest ex-PM Sheikh Hasina if she returns from India.",
     "Reuters", "REPORTED", "Asia-Pacific"),
    (13, "ASIA-PACIFIC — INDONESIA",
     "Indonesia president to nominate VP candidates on Monday",
     "President Prabowo Subianto will submit 2 names for vice-president to parliament on Monday, state news agency Antara reports. Parliament votes on 11 December.",
     "Reuters · Antara", "REPORTED", "Asia-Pacific"),
]

BRIEFS = [
    ("Europe", "Burnham: EU deal could make next decade 'much better'"),
    ("Europe", "Thousands rally in Istanbul against media takeover"),
    ("Europe", "Europe power market flashes warning as bills near rise"),
    ("Europe", "Poland: Russia twice tried to kill Ukrainian rapper"),
    ("Europe", "Belgian airports shut in anti-austerity strike"),
    ("Europe", "Princess of Wales shares cancer journey in 'Heal'"),
    ("Middle East", "Netanyahu–Eisenkot coalition talks end without deal"),
    ("Middle East", "Eisenkot condemns settler arson in West Bank"),
    ("Middle East", "Experts: Gaza war left widespread contamination"),
    ("Middle East", "Gulf bourses open higher on diplomatic momentum"),
    ("Americas", "Trump calls Putin 'my friend' after Shenzhen summit"),
    ("Americas", "US energy exports hit records as oil watches surplus"),
    ("Americas", "Colombia asks X to suspend ex-president Petro"),
    ("Americas", "Bolsonaro still in ICU, clinically stable"),
    ("Americas", "Nvidia: Alice Huang spy contacts; Trump urges rehire"),
    ("Americas", "ICE Seattle father-daughter video sparks protests"),
    ("Asia-Pacific", "Tata Steel to buy 26.4% of APL Apollo for $1.67bn"),
    ("Asia-Pacific", "Sensex sheds 1,430 points; Nifty below 25,400"),
    ("Asia-Pacific", "Australia: jobless rate to pass 5%, Chalmers warns"),
    ("Oceania", "Albanese defends Bowen after COP31 failure"),
    ("Asia-Pacific", "Shuri Castle hall opens to public, 7 years after fire"),
    ("World", "Lewis Pugh swims the length of the Strait of Hormuz"),
]

DATE_CHECK = [
    "COP31 collapse — Sunday 22 Nov (Monday only reactions)",
    "ATP final: Alcaraz beats Zverev — Sunday 22 Nov",
    "Liverpool 4-0 Man Utd — Sunday 22 Nov",
    "Marquez 8th MotoGP title; Boca win Sudamericana — Sun 22 Nov",
    "Nikkei -5.06% — Friday 20 Nov; Nikkei closed Monday",
    "S&P -3.7% · Nasdaq -5.28% — Friday 20 Nov (close)",
    "Nvidia -14% — Friday 20 Nov (Monday: new details only)",
    "Bayelsa boat: 24 dead — Friday 20 Nov",
    "'El Chapo Isidro' captured — Friday 20 Nov",
    "BepiColombo enters Mercury orbit — Saturday 21 Nov",
    "Hong Kong Election Committee vote — Sunday 22 Nov",
    "Trump–Xi–Putin Shenzhen summit — Thursday 19 Nov",
]

REGIONS = [("Europe", 8, (38, 58, 96)), ("Middle East", 6, (192, 57, 43)),
           ("Americas", 7, (42, 122, 110)), ("Asia-Pacific", 9, (212, 175, 55)),
           ("Oceania", 2, (120, 90, 160)), ("Africa", 2, (200, 110, 40)),
           ("World", 1, (90, 90, 90))]

STATS = [("258", "Democratic House seats"),
         ("14", "killed in Dymer"),
         ("24", "Cikande body bags"),
         ("7", "naval drones sank Merkury"),
         ("5", "children killed, Khartoum"),
         ("$3,610", "gold, $/oz")]

TIMELINE = [("08:07", "Zelensky announces Merkury sunk"),
            ("06:27", "Asia markets update"),
            ("10:26", "OneTurn day digest crawled")]

# lon/lat for the 13 lead pins (jittered where they overlap)
PINS = [(20.1, 32.1), (30.3, 50.8), (127.0, 37.5), (-77.0, 38.9),
        (56.3, 26.5), (39.0, 22.8), (106.3, -6.0), (124.0, 37.5),
        (32.5, 15.6), (24.5, 59.8), (77.2, 28.6), (90.4, 23.8),
        (109.5, -6.2)]


# ---------------------------------------------------------------- render
def render():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    M = 24  # margin

    # ---- masthead (navy band)
    d.rectangle([0, 0, W, 58], fill=NAVY)
    d.text((M, 12), "THE WORLD IN ONE DAY", font=F("serif_b", 30), fill=CREAM)
    f_small = F("sans_b", 12)
    d.text((W - M, 10), "35 STORIES  ·  7 REGIONS", font=f_small, fill=CREAM,
           anchor="ra")
    d.text((W - M, 30), "EVERY ONE DATED MONDAY 23 NOVEMBER 2026",
           font=F("sans", 11), fill=(200, 205, 220), anchor="ra")

    # ---- giant date
    d.text((W // 2, 66), "MONDAY 23 NOVEMBER 2026", font=F("serif_b", 42),
           fill=NAVY, anchor="ma")
    d.text((W // 2, 122), "Merkury sunk off Libya  ·  Dymer toll rises to 14  ·  "
           "AI sell-off spreads in Asia", font=F("serif_i", 18), fill=RED,
           anchor="ma")

    # ---- stat strip
    y0 = 152
    col_w = (W - 2 * M) / 6
    for i, (num, cap) in enumerate(STATS):
        cx = M + col_w * i + col_w / 2
        d.text((cx, y0), num, font=F("sans_b", 26), fill=RED, anchor="ma")
        lines = wrap(d, cap, F("sans", 10), col_w - 12)
        ly = y0 + 32
        for ln in lines[:2]:
            d.text((cx, ly), ln, font=F("sans", 10), fill=GREY, anchor="ma")
            ly += 12
    d.line([M, y0 + 52, W - M, y0 + 52], fill=GREY_LT, width=1)

    # ---- region bar
    y0 = 210
    d.text((M, y0), "STORIES BY REGION", font=F("sans_b", 11), fill=NAVY)
    bx, bw, bh = M, W - 2 * M, 13
    total = sum(c for _, c, _ in REGIONS)
    x = bx
    for name, cnt, col in REGIONS:
        seg = bw * cnt / total
        d.rectangle([x, y0 + 16, x + seg, y0 + 16 + bh], fill=col)
        x += seg
    d.rectangle([bx, y0 + 16, bx + bw, y0 + 16 + bh], outline=NAVY, width=1)
    legend = "  ·  ".join(f"{n} {c}" for n, c, _ in REGIONS)
    d.text((M, y0 + 34), legend, font=F("sans", 10), fill=GREY)

    # ---- UTC timeline
    y0 = 262
    d.text((M, y0), "UTC", font=F("sans_b", 11), fill=RED)
    tl = "    ".join(f"{t}  {s}" for t, s in TIMELINE)
    d.text((M + 34, y0), tl, font=F("sans", 11), fill=NAVY)
    d.line([M, y0 + 18, W - M, y0 + 18], fill=GREY_LT, width=1)

    # ---- 3 big lead cards
    y0 = 284
    card_w, card_h, gap = 320, 210, 8
    for i, (num, kicker, head, body, src, tag, region) in enumerate(LEADS[:3]):
        x = M + i * (card_w + gap)
        d.rectangle([x, y0, x + card_w, y0 + card_h], fill=(255, 255, 255),
                    outline=GREY_LT, width=1)
        # illustration strip
        d.rectangle([x, y0, x + card_w, y0 + 66], fill=BLUE_LT)
        ICONS[num](d, x + card_w / 2 - 33, y0 + 4, 66, 58, NAVY, RED)
        d.text((x + 10, y0 + 72), kicker, font=F("sans_b", 10), fill=RED)
        hy = draw_wrapped(d, x + 10, y0 + 88, head, F("serif_b", 19),
                          card_w - 20, NAVY, spacing=1, max_lines=2)
        by = draw_wrapped(d, x + 10, hy + 2, body, F("sans", 12),
                          card_w - 20, INK, spacing=1, max_lines=3)
        d.text((x + 10, y0 + card_h - 26), src, font=F("sans", 10), fill=GREY)
        d.text((x + card_w - 10, y0 + card_h - 26), tag, font=F("sans_b", 10),
               fill=RED, anchor="ra")

    # ---- 10 medium cards (2 rows x 5)
    y0 = 500
    mw, mh, mgap = 192, 100, 8
    mx0 = 16
    for i, (num, kicker, head, body, src, tag, region) in enumerate(LEADS[3:]):
        row, col = divmod(i, 5)
        x = mx0 + col * (mw + mgap)
        y = y0 + row * (mh + mgap)
        d.rectangle([x, y, x + mw, y + mh], fill=(255, 255, 255),
                    outline=GREY_LT, width=1)
        rcol = dict((n, c) for n, _, c in REGIONS).get(region, NAVY)
        d.rectangle([x, y, x + mw, y + 5], fill=rcol)
        # number badge + kicker
        d.ellipse([x + 8, y + 12, x + 26, y + 30], fill=RED)
        d.text((x + 17, y + 13), str(num), font=F("sans_b", 11),
               fill=(255, 255, 255), anchor="ma")
        d.text((x + 32, y + 14), kicker.split(" — ")[0], font=F("sans_b", 9),
               fill=RED)
        # tiny icon top-right
        ICONS[num](d, x + mw - 30, y + 10, 22, 20, NAVY2, RED)
        hy = draw_wrapped(d, x + 8, y + 34, head, F("sans_b", 12),
                          mw - 16, NAVY, spacing=0, max_lines=2)
        by = draw_wrapped(d, x + 8, hy + 1, body, F("sans", 10),
                          mw - 16, INK, spacing=0, max_lines=2)
        d.text((x + 8, y + mh - 13), src, font=F("sans", 8), fill=GREY)

    # ---- world map + briefs
    y0 = 714
    # map (left)
    d.text((M, y0), "WHERE IT HAPPENED — 13 LEADS PINNED", font=F("sans_b", 11),
           fill=NAVY)
    mx0, my0, mw, mh = M, y0 + 18, 446, 140
    d.rectangle([mx0, my0, mx0 + mw, my0 + mh], fill=BLUE_LT)
    d.rectangle([mx0, my0, mx0 + mw, my0 + mh], outline=GREY_LT, width=1)

    def proj(lon, lat):
        return (mx0 + (lon + 180) / 360 * mw,
                my0 + (85 - lat) / 145 * mh)

    continents = [
        [(-168, 66), (-140, 70), (-120, 72), (-95, 80), (-80, 73), (-55, 60),
         (-60, 45), (-75, 35), (-80, 25), (-97, 16), (-105, 20), (-115, 30),
         (-125, 40), (-140, 60), (-165, 60)],
        [(-80, 10), (-60, 10), (-50, 0), (-40, -10), (-35, -20), (-50, -30),
         (-60, -40), (-70, -50), (-75, -35), (-80, -20), (-80, -5)],
        [(-10, 36), (0, 44), (10, 45), (20, 40), (30, 36), (30, 45),
         (20, 55), (10, 58), (0, 60), (-5, 50), (-10, 45)],
        [(-17, 15), (-10, 30), (0, 35), (10, 37), (20, 32), (30, 31),
         (35, 28), (40, 20), (45, 10), (40, 0), (35, -10), (30, -20),
         (20, -30), (15, -35), (12, -25), (10, -15), (8, -5), (0, 5),
         (-8, 5), (-15, 10)],
        [(30, 36), (40, 40), (50, 45), (60, 50), (70, 55), (80, 60),
         (90, 65), (100, 70), (110, 75), (130, 72), (150, 70), (160, 65),
         (170, 60), (160, 50), (150, 45), (140, 40), (130, 35), (120, 30),
         (110, 20), (105, 10), (100, 5), (95, 10), (90, 20), (85, 25),
         (80, 15), (75, 10), (70, 20), (60, 25), (50, 30), (40, 35)],
        [(113, -22), (125, -15), (135, -12), (142, -15), (150, -22),
         (153, -28), (150, -37), (140, -38), (130, -32), (120, -30),
         (113, -25)],
    ]
    for poly in continents:
        d.polygon([proj(lon, lat) for lon, lat in poly], fill=(225, 222, 210),
                  outline=(180, 175, 160))
    placed = []
    for i, (lon, lat) in enumerate(PINS, start=1):
        px, py = proj(lon, lat)
        ox, oy = px, py
        for qx, qy in placed:
            if abs(px - qx) < 16 and abs(py - qy) < 16:
                ox, oy = px + 16, py - 12
                break
        if (ox, oy) != (px, py):
            d.line([px, py, ox, oy], fill=RED, width=1)
        d.ellipse([ox - 8, oy - 8, ox + 8, oy + 8], fill=RED,
                  outline=(255, 255, 255), width=1)
        d.text((ox, oy - 1), str(i), font=F("sans_b", 9), fill=(255, 255, 255),
               anchor="mm")
        placed.append((ox, oy))

    # briefs (right)
    bx0 = 478
    d.text((bx0, y0), "ALSO ON MONDAY 23 NOVEMBER", font=F("sans_b", 11),
           fill=NAVY)
    d.line([bx0, y0 + 16, W - M, y0 + 16], fill=GREY_LT, width=1)
    bcol_w = (W - M - bx0 - 8) // 2
    f_br = F("sans", 9)
    for i, (region, text) in enumerate(BRIEFS):
        col, row = divmod(i, 11)
        x = bx0 + col * (bcol_w + 8)
        y = y0 + 20 + row * 12
        d.text((x, y), f"{14 + i}.", font=F("sans_b", 9), fill=RED)
        # truncate to fit one line
        t = text
        while d.textlength(t, font=f_br) > bcol_w - 24 and len(t) > 10:
            t = t[:-2]
        if t != text:
            t = t.rstrip() + "…"
        d.text((x + 22, y), t, font=f_br, fill=INK)

    # ---- DATE CHECK box
    y0 = 878
    d.rectangle([M, y0, W - M, y0 + 94], outline=RED, width=2)
    d.text((M + 10, y0 + 6),
           "DATE CHECK — NOT MONDAY 23 NOVEMBER: first reported earlier",
           font=F("sans_b", 11), fill=RED)
    f_dc = F("sans", 9)
    for i, item in enumerate(DATE_CHECK):
        col, row = divmod(i, 6)
        x = M + 10 + col * 480
        y = y0 + 24 + row * 12
        d.text((x, y), "✕  " + item, font=f_dc, fill=INK)

    # ---- footer
    y0 = 980
    d.text((M, y0),
           "Sources: Reuters · BBC · Al Jazeera · EA WorldView · Guardian · "
           "France 24 · Morningstar · The Hindu · UPI · CNBC · MercoPress · "
           "AllAfrica · SCMP · Tagesschau · El Pais · Le Monde",
           font=F("sans", 9), fill=GREY)
    d.text((M, y0 + 14),
           "REPORTED = carried by the day's wires  ·  CLAIM = one side's "
           "account, labelled as such  ·  FORECAST = still to happen when drawn",
           font=F("sans", 9), fill=NAVY)
    d.text((W - M, y0 + 28), "THE WORLD IN ONE DAY · 23 NOVEMBER 2026",
           font=F("sans_b", 9), fill=GREY, anchor="ra")
    return img


# ---------------------------------------------------------------- output
def _output_path():
    d = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if d:
        return os.path.join(d, "entry.png")
    e = os.environ.get("ENTRY_OUTPUT")
    if e:
        return e
    return "/output/entry.png"


def _repo_png():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")


def _copy_committed():
    src = _repo_png()
    if not os.path.exists(src):
        alt = os.path.join(os.getcwd(), "entry.png")
        if os.path.exists(alt):
            src = alt
        else:
            return False
    out = _output_path()
    try:
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        shutil.copyfile(src, out)
        return True
    except Exception:
        return False


def main():
    if not _PIL_OK:
        return 0 if _copy_committed() else 1
    try:
        img = render()
        repo = _repo_png()
        img.save(repo, optimize=True)
        out = _output_path()
        if os.path.abspath(out) != os.path.abspath(repo):
            os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
            shutil.copyfile(repo, out)
        return 0
    except Exception:
        return 0 if _copy_committed() else 1


if __name__ == "__main__":
    sys.exit(main())

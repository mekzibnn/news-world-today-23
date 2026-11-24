#!/usr/bin/env python3
"""Fresh verifier for news-image-20261123 v1.3.

Checks (all must pass):
  (a) README has the 3 exact live make.fun badge URLs (+ bounty link,
      no shields.io).
  (b) All 35 stories present with correct numbers/dates.
  (c) No headline is truncated: every headline appears whole in main.py,
      and re-measuring with main.py's own layout functions proves each
      headline renders fully (wrapped, never cut) inside its card.
  (d) No brief ends with "..." and every brief is <= 55 chars.
  (e) Timeline contains no "OneTurn" / "crawled" / "digest".
  (f) entry.png is 1024x1024 and 170-350 KB.
  (g) main.py has no top-level Pillow import and honours $MAKEFUN_OUTPUT_DIR.
  (+) Map pins do not overlap; render fallback (Pillow/render failure)
      copies the committed entry.png and exits 0.

Usage: python3 verify.py
Exit 0 only when every check passes.
"""

import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import main as entry  # noqa: E402  (the module under test)

REPO = HERE
README = os.path.join(REPO, "README.md")
MAIN_PY = os.path.join(REPO, "main.py")
ENTRY_PNG = os.path.join(REPO, "entry.png")

PASS = []
FAIL = []


def check(name, ok, detail=""):
    (PASS if ok else FAIL).append(name)
    print("%s %s%s" % ("PASS" if ok else "FAIL", name,
                       (" — " + detail) if detail else ""))


def main_check():
    with open(MAIN_PY, encoding="utf-8") as fh:
        src = fh.read()
    with open(README, encoding="utf-8") as fh:
        readme = fh.read()

    # --- (a) exact badge URLs
    badges = [
        "https://make.fun/badge/news-image-20261123.svg",
        "https://make.fun/badge/news-image-20261123/mekzibnn/news-world-today-23/rank.svg",
        "https://make.fun/badge/news-image-20261123/mekzibnn/news-world-today-23/reward.svg",
    ]
    for url in badges:
        check("badge present: " + url, url in readme)
    check("bounty link present",
          "https://make.fun/competitions/news-image-20261123" in readme)
    check("no shields.io badges", "shields.io" not in readme)
    check("no leftover 20261122/20261124 slugs in README",
          "20261122" not in readme and "20261124" not in readme)
    check("no leftover 20261122/20261124 slugs in main.py",
          "20261122" not in src and "20261124" not in src)

    # --- (g) Pillow import rules + output-dir handling
    top_level_pil = re.findall(r"^(?:from PIL|import PIL)", src,
                               flags=re.M)
    check("no top-level Pillow import", not top_level_pil,
          str(top_level_pil) if top_level_pil else "")
    check("Pillow import guarded by try/except with _PIL_OK",
          "_PIL_OK" in src and "try:" in src)
    check("honours $MAKEFUN_OUTPUT_DIR", "MAKEFUN_OUTPUT_DIR" in src)
    check("honours $ENTRY_OUTPUT", "ENTRY_OUTPUT" in src)
    check("falls back to /output/entry.png", "/output/entry.png" in src)
    check("fallback copies committed entry.png", "shutil.copy" in src)

    # --- (e) timeline clean
    timeline_text = " ".join(t for _t, t in entry.TIMELINE)
    check("timeline has no OneTurn/crawled/digest",
          not any(w in timeline_text for w in
                  ("OneTurn", "crawled", "digest")))
    check("timeline has no OneTurn/crawled/digest in source",
          not any(w in src for w in ("OneTurn", "crawled", "digest")))
    check("timeline has exactly 2 verified items",
          len(entry.TIMELINE) == 2, str(entry.TIMELINE))
    check("timeline keeps 08:07 Merkury announcement",
          ("08:07", "Zelensky announces Merkury sunk") in entry.TIMELINE)
    check("timeline keeps 06:27 Asia markets update",
          ("06:27", "Asia markets update") in entry.TIMELINE)

    # --- (b) story counts + key facts
    check("13 leads", len(entry.LEADS) == 13, str(len(entry.LEADS)))
    check("22 briefs", len(entry.BRIEFS) == 22, str(len(entry.BRIEFS)))
    check("35 stories total",
          len(entry.LEADS) + len(entry.BRIEFS) == 35)
    check("12 DATE CHECK items", len(entry.DATECHECK) == 12)
    check("region counts sum to 35",
          sum(n for _n, n, _c in entry.REGIONS) == 35)
    counts = {n: c for n, c, _col in entry.REGIONS}
    check("Asia-Pacific 7 (not 9)", counts.get("Asia-Pacific") == 7)
    check("Africa 4 (not 2)", counts.get("Africa") == 4)
    check("Europe 8", counts.get("Europe") == 8)
    check("Middle East 6", counts.get("Middle East") == 6)
    check("Americas 7", counts.get("Americas") == 7)
    check("Oceania 2", counts.get("Oceania") == 2)
    check("World 1", counts.get("World") == 1)
    check("stat strip 258/14/24/7/5/$3,610",
          [s[0] for s in entry.STATS] ==
          ["258", "14", "24", "7", "5", "$3,610"])
    facts = ["14 were dead and 19 wounded", "7 Ukrainian sea drones",
             "Benghazi", "Dymer", "Merkury", "Rabigh", "Cikande",
             "Milkita", "Khartoum", "Sparta II", "Gulf of Finland",
             "Hasina", "Modi", "Delhi", "largest majority since 1992",
             "$3,610", "258 House seats"]
    # Facts live in the lead data (some bodies are split across source
    # lines), so check the joined headline+body text, not raw source.
    lead_text = " ".join(lead["headline"] + " " + lead["body"]
                         for lead in entry.LEADS)
    stat_text = " ".join(num for num, _cap in entry.STATS)
    for fact in facts:
        check("fact present: " + fact,
              fact in lead_text or fact in stat_text)
    check("gold is $3,610 (Monday), not $3,645",
          "$3,645" not in src)
    for item in entry.DATECHECK:
        check("DATE CHECK present: " + item[:38], item in src)

    # --- (c) headlines whole + render-fit (measured with main's own code)
    try:
        from PIL import Image, ImageDraw
    except Exception:
        print("FAIL Pillow unavailable for measurement")
        return 1
    probe = Image.new("RGB", (1024, 1024))
    d = ImageDraw.Draw(probe)
    for lead in entry.LEADS:
        hl = lead["headline"]
        check("headline %d whole in main.py" % lead["n"], hl in src)
        check("headline %d has no ellipsis" % lead["n"],
              "..." not in hl and "…" not in hl)
        try:
            if lead["n"] <= 3:
                lay = entry.layout_big_card(d, lead)
                max_lines = 3
            else:
                lay = entry.layout_medium_card(d, lead)
                max_lines = 3
            joined = " ".join(lay["hlines"])
            check("headline %d renders whole (wrap, no cut)" % lead["n"],
                  joined == hl, "lines=%r" % (lay["hlines"],))
            check("headline %d fits in %d lines" % (lead["n"], max_lines),
                  len(lay["hlines"]) <= max_lines)
            body_joined = " ".join(lay["blines"])
            check("body %d renders whole" % lead["n"],
                  body_joined == lead["body"])
        except Exception as exc:
            check("headline %d fits its card" % lead["n"], False, str(exc))

    # --- (d) briefs whole, one line, <= 55 chars, no "..."
    nums = [n for n, _t in entry.BRIEFS]
    check("brief numbers are 14-35 in order", nums == list(range(14, 36)))
    for num, text in entry.BRIEFS:
        check("brief %d <= 55 chars (%d)" % (num, len(text)),
              len(text) <= 55)
        check("brief %d has no ellipsis" % num,
              not text.endswith("...") and "…" not in text)
        check("brief %d whole in main.py" % num, text in src)

    # --- (+) map pins spread (no overlap: radius 6 -> need >= 14 px apart;
    #      require >= 18 for margin)
    pins = [lead["pin"] for lead in entry.LEADS]
    min_dist = None
    for i in range(len(pins)):
        for j in range(i + 1, len(pins)):
            dist = ((pins[i][0] - pins[j][0]) ** 2 +
                    (pins[i][1] - pins[j][1]) ** 2) ** 0.5
            min_dist = dist if min_dist is None else min(min_dist, dist)
    check("map pins spread (min gap %.1f px >= 18)" % min_dist,
          min_dist is not None and min_dist >= 18)

    # --- fresh render via subprocess
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, MAKEFUN_OUTPUT_DIR=tmp)
        proc = subprocess.run([sys.executable, MAIN_PY], env=env,
                              capture_output=True, text=True, cwd=REPO)
        check("fresh render exits 0", proc.returncode == 0,
              proc.stdout.strip() + proc.stderr.strip())
        check("fresh render prints no TRUNCATED",
              "TRUNCATED" not in proc.stdout)
        check("fresh render prints STORIES 35 LEADS 13 BRIEFS 22",
              "STORIES 35 LEADS 13 BRIEFS 22" in proc.stdout)
        out_png = os.path.join(tmp, "entry.png")
        check("fresh render writes entry.png", os.path.exists(out_png))
        if os.path.exists(out_png):
            from PIL import Image as _Image
            with _Image.open(out_png) as im:
                check("fresh render is 1024x1024", im.size == (1024, 1024),
                      str(im.size))
            size = os.path.getsize(out_png)
            check("fresh render 170-350 KB (%d KB)" % (size // 1024),
                  170 * 1024 <= size <= 350 * 1024, "%d bytes" % size)

    # --- (f) committed entry.png
    check("entry.png exists in repo", os.path.exists(ENTRY_PNG))
    if os.path.exists(ENTRY_PNG):
        from PIL import Image as _Image
        with _Image.open(ENTRY_PNG) as im:
            check("entry.png is 1024x1024", im.size == (1024, 1024),
                  str(im.size))
        size = os.path.getsize(ENTRY_PNG)
        check("entry.png 170-350 KB (%d KB)" % (size // 1024),
              170 * 1024 <= size <= 350 * 1024, "%d bytes" % size)

    # --- (+) fallback: render failure still copies committed PNG, exit 0
    with tempfile.TemporaryDirectory() as tmp:
        real_render = entry.render_image

        def _boom(_path):
            raise RuntimeError("simulated render failure")

        entry.render_image = _boom
        old_env = os.environ.get("MAKEFUN_OUTPUT_DIR")
        os.environ["MAKEFUN_OUTPUT_DIR"] = tmp
        try:
            rc = entry.main()
        finally:
            entry.render_image = real_render
            if old_env is None:
                os.environ.pop("MAKEFUN_OUTPUT_DIR", None)
            else:
                os.environ["MAKEFUN_OUTPUT_DIR"] = old_env
        out_png = os.path.join(tmp, "entry.png")
        check("fallback exits 0 on render failure", rc == 0)
        check("fallback copies committed entry.png",
              os.path.exists(out_png) and
              os.path.getsize(out_png) == os.path.getsize(ENTRY_PNG))

    print("\n%d PASS, %d FAIL" % (len(PASS), len(FAIL)))
    if FAIL:
        print("FAILED: " + "; ".join(FAIL))
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main_check())

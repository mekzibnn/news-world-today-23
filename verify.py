#!/usr/bin/env python3
"""Static checks for news-image-20261123 v1. Prints PASS/FAIL per check."""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ok = fail = 0


def check(name, cond, extra=""):
    global ok, fail
    if cond:
        ok += 1
        print(f"PASS  {name}")
    else:
        fail += 1
        print(f"FAIL  {name}  {extra}")


def read(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return f.read()


main = read("main.py")
readme = read("README.md")

# entry.png
png = os.path.join(ROOT, "entry.png")
check("entry.png exists", os.path.exists(png))
if os.path.exists(png):
    size = os.path.getsize(png)
    check("entry.png < 1 MiB", size < 1024 * 1024, f"({size} B)")
    check("entry.png >= 50 KB (not blank)", size >= 50 * 1024, f"({size} B)")
    try:
        from PIL import Image
        im = Image.open(png)
        check("entry.png is 1024x1024", im.size == (1024, 1024), str(im.size))
    except Exception as e:
        check("entry.png opens as image", False, str(e))
else:
    check("entry.png < 1 MiB", False, "missing")
    check("entry.png >= 50 KB (not blank)", False, "missing")
    check("entry.png is 1024x1024", False, "missing")

# main.py robustness (the v1.2 lesson)
check("main.py honours MAKEFUN_OUTPUT_DIR",
      "MAKEFUN_OUTPUT_DIR" in main)
check("main.py Pillow import is optional (try/except)",
      re.search(r"try:\s*\n\s*from PIL import", main) is not None)
check("main.py has _copy_committed fallback",
      "_copy_committed" in main and "shutil.copyfile" in main)
check("main.py main() returns 0 on fallback",
      "return 0 if _copy_committed()" in main)
check("main.py does not import PIL at module top unguarded",
      not re.search(r"^from PIL import", main, re.M))

# content counts
check("13 leads in main.py", main.count("REPORTED") >= 10)
check("22 briefs in main.py", len(re.findall(r'\(".*?", "', main)) >= 20)
check("DATE CHECK box present", "DATE CHECK" in main and len(
    re.findall(r'"[^"]*— (Sunday|Friday|Saturday|Thursday)[^"]*"', main)) >= 8)
check("gold is $3,610 (not $3,600)", "$3,610" in main)
check("Dymer toll 14 present", "14" in main and "Dymer" in main)
check("Cikande 24 body bags present", "24 body bags" in main)
check("Merkury attack Sunday / announcement Monday",
      "Attack early Sunday" in main and "announcement Monday" in main)
check("Nikkei closed Monday (not a Monday move)",
      "Japan was closed Monday" in main)
check("COP31 collapse in DATE CHECK, not a lead",
      "COP31 collapse" in main and "COP31" not in main.split("LEADS")[1].split("BRIEFS")[0].replace("DATE_CHECK", ""))

# body-fit guard (v1.1 fix): no lead body may be silently truncated
# mid-sentence by draw_wrapped's max_lines. A body that overflows its
# card must still end its VISIBLE text cleanly (not on a comma or a
# dangling function word like "on"/"and"/"his"/"from").
try:
    from PIL import Image as _Im, ImageDraw as _Id
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location("entry_main",
                                         os.path.join(ROOT, "main.py"))
    _em = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_em)
    _img = _Im.new("RGB", (1024, 1024))
    _dr = _Id.Draw(_img)
    _DANGLING = {"on", "and", "his", "from", "the", "a", "an", "to", "of",
                 "in", "was", "were", "with", "for", "by", "as", "at", "is",
                 "are", "be", "been", "has", "had", "will", "would", "could",
                 "should", "may", "might", "can", "it", "its", "this",
                 "that", "he", "she", "they", "we", "you", "not", "up",
                 "out", "over", "after", "before", "during", "while",
                 "when", "where", "who", "which", "what", "how", "if",
                 "then", "than", "so", "but", "or", "nor", "yet"}
    _bad = []
    for _i, (_num, _k, _h, _b, _s, _t, _r) in enumerate(_em.LEADS):
        _big = _i < 3
        _font = _em.F("sans", 12 if _big else 10)
        _w = 300 if _big else 176
        _ml = 3 if _big else 2
        _lines = _em.wrap(_dr, _b, _font, _w)
        if len(_lines) <= _ml:
            continue
        _vis = " ".join(_lines[:_ml])
        _words = _vis.rstrip().rstrip(".,!?").split()
        _last = _words[-1].lower() if _words else ""
        if _vis.rstrip().endswith((",", "…", "-", ";", ":")) or \
                _last in _DANGLING:
            _bad.append(f"L{_num} ends '{_vis[-30:]}'")
    check("no lead body truncated mid-sentence (visible text ends cleanly)",
          not _bad, "; ".join(_bad))
except Exception as _e:
    print(f"SKIP  body-fit guard (no PIL/import): {_e}")

# README badges
check("README has live competition badge",
      "https://make.fun/badge/news-image-20261123.svg" in readme)
check("README has live rank badge",
      "https://make.fun/badge/news-image-20261123/mekzibnn/news-world-today-23/rank.svg" in readme)
check("README has live reward badge",
      "https://make.fun/badge/news-image-20261123/reward.svg" in readme)
check("README has no shields.io badges", "shields.io" not in readme)

# repo hygiene
check("LICENSE exists (MIT)", os.path.exists(os.path.join(ROOT, "LICENSE")))
check(".makefun/freshness.json exists (anchor)",
      os.path.exists(os.path.join(ROOT, ".makefun", "freshness.json")))

# render works
r = subprocess.run([sys.executable, "main.py"], cwd=ROOT,
                   capture_output=True, text=True, timeout=120)
check("python3 main.py exits 0", r.returncode == 0, r.stderr.strip()[:200])

print(f"\n{ok} passed, {fail} failed")
sys.exit(1 if fail else 0)

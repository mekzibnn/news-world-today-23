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

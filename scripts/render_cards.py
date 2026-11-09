#!/usr/bin/env python3
"""Render a note card (light + dark PNG) for each post from its frontmatter.

Usage:  python scripts/render_cards.py [posts/xxx.md ...]
Needs Microsoft Edge or Chrome (headless screenshot). No pip packages.
Frontmatter fields used: title, date, series, kicker, questions (list), tags (list).
"""
import html, re, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "cards"
BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
]
# series -> (light accent, dark accent)
SERIES = {
    "AI 产品": ("#1F7A52", "#3FB07A"),
    "数据与风控": ("#2F5D8A", "#6AA6E0"),
    "和 AI 协作的方式": ("#B5651D", "#E09A4F"),
}
THEME = {
    "light": dict(bg="#F7F6F3", border="#E2E0DA", text="#24292F", muted="#8A8578", hair="#D8D5CC"),
    "dark":  dict(bg="#1C1C1A", border="#33322E", text="#E8E6E1", muted="#96917F", hair="#3A3833"),
}
ACCENT = {"light": "#1F7A52", "dark": "#4CAF82"}
W, H = 1000, 560

def parse(path):
    txt = path.read_text(encoding="utf-8")
    m = re.match(r"---\s*\n(.*?)\n---", txt, re.S)
    meta, key = {}, None
    for line in (m.group(1) if m else "").splitlines():
        if re.match(r"^\s+-\s+", line) and key:
            meta.setdefault(key, []).append(re.sub(r"^\s+-\s+", "", line).strip())
            continue
        kv = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
        if kv:
            key, val = kv.group(1), kv.group(2).strip()
            if val.startswith("[") and val.endswith("]"):
                meta[key] = [x.strip() for x in val[1:-1].split(",") if x.strip()]
            elif val:
                meta[key] = val
            else:
                meta[key] = []
    return meta


def card_html(meta, mode):
    t = THEME[mode]
    acc = ACCENT[mode]
    e = lambda s: html.escape(str(s))
    qs = "".join(
        f'<li><span class="n">{"01 02 03 04".split()[i]}</span>{e(q)}</li>'
        for i, q in enumerate(meta.get("questions", [])[:4])
    )
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0}}
html,body{{width:{W}px;height:{H}px;background:{t['bg']}}}
.card{{width:{W}px;height:{H}px;padding:56px 64px 48px;background:{t['bg']};
 border:1px solid {t['border']};border-radius:10px;font-family:"Noto Serif SC","Source Han Serif SC",SimSun,serif;color:{t['text']};
 display:flex;flex-direction:column}}
h1{{font-size:44px;line-height:1.42;font-weight:700;letter-spacing:.01em}}
.rulerow{{display:flex;align-items:center;gap:18px;margin:30px 0 30px}}
.rule{{width:64px;border:0;border-top:3px solid {acc}}}
.date{{font-size:16px;color:{t['muted']};font-family:"Microsoft YaHei",sans-serif;letter-spacing:.08em}}
.lab{{font-size:15px;letter-spacing:.2em;color:{t['muted']};font-family:"Microsoft YaHei",sans-serif}}
ul{{list-style:none;padding:0;margin-top:12px}}
li{{font-size:22px;line-height:2.05;color:{t['text']}}}
.n{{font-size:15px;color:{acc};letter-spacing:.1em;margin-right:16px;font-family:"Microsoft YaHei",sans-serif}}
</style></head><body><div class="card">
<h1>{e(meta.get('title',''))}</h1>
<div class="rulerow"><hr class="rule"><span class="date">{e(meta.get('date',''))}</span></div>
<div class="lab">这篇想回答</div><ul>{qs}</ul>
</div></body></html>"""

def main():
    browser = next((b for b in BROWSERS if Path(b).exists()), None)
    if not browser:
        sys.exit("找不到 Edge / Chrome")
    posts = [Path(a) for a in sys.argv[1:]] or sorted((ROOT / "posts").glob("*.md"))
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="cards_", dir=str(ROOT.parent / "_build") if (ROOT.parent / "_build").exists() else None))
    try:
        for p in posts:
            meta = parse(p)
            if not meta.get("questions"):
                print("跳过（缺 questions）:", p.name)
                continue
            for mode in ("light", "dark"):
                f = tmp / f"{p.stem}-{mode}.html"
                f.write_text(card_html(meta, mode), encoding="utf-8")
                png = OUT / f"{p.stem}-{mode}.png"
                subprocess.run([browser, "--headless", "--disable-gpu", "--hide-scrollbars",
                    f"--user-data-dir={tmp / 'profile'}", f"--window-size={W},{H}",
                    "--force-device-scale-factor=2", f"--screenshot={png}", f.as_uri()],
                    check=True, capture_output=True, timeout=60)
                print("OK", png)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
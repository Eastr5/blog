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
    "light": dict(bg="linear-gradient(135deg,#F4F7F5 0%,#E8F0EB 100%)", border="#D3DED8", text="#1E2B25", muted="#75877E"),
    "dark":  dict(bg="linear-gradient(135deg,#141A17 0%,#1B2721 100%)", border="#2C3B33", text="#E6EFE9", muted="#8FA89B"),
}
ACCENT = {"light": "linear-gradient(90deg,#1F7A52,#0F5132)", "dark": "linear-gradient(90deg,#4CAF82,#7FD8A6)"}
W, H = 860, 400

def parse(path):
    sidecar = ROOT / "posts" / "meta" / (path.stem + ".yaml")
    txt = sidecar.read_text(encoding="utf-8") if sidecar.exists() else path.read_text(encoding="utf-8")
    m = re.match(r"---\s*\n(.*?)\n---", "---\n" + txt + "\n---", re.S)
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
.card{{width:{W}px;height:{H}px;padding:40px 52px 36px;background:{t['bg']};
 border:1px solid {t['border']};border-radius:10px;font-family:"Noto Serif SC","Source Han Serif SC",SimSun,serif;color:{t['text']};
 display:flex;flex-direction:column}}
h1{{font-size:36px;line-height:1.5;font-weight:700;letter-spacing:.01em}}
.rulerow{{display:flex;align-items:center;gap:18px;margin:24px 0 22px}}
.rule{{width:64px;height:3px;border:0;border-radius:2px;background:{acc}}}
.date{{font-size:16px;color:{t['muted']};font-family:"Microsoft YaHei",sans-serif;letter-spacing:.08em}}
.sub{{font-size:17px;color:{t["muted"]};margin-top:10px;font-family:"Noto Serif SC",serif}}
.lab{{font-size:15px;letter-spacing:.2em;color:{t['muted']};font-family:"Microsoft YaHei",sans-serif}}
ul{{list-style:none;padding:0;margin-top:12px}}
li{{font-size:19px;line-height:1.95;color:{t['text']}}}
.n{{font-size:15px;background:{acc};-webkit-background-clip:text;background-clip:text;color:transparent;letter-spacing:.1em;margin-right:16px;font-family:"Microsoft YaHei",sans-serif}}
</style></head><body><div class="card">
<h1>{e(meta.get('title',''))}</h1>
{('<p class="sub">' + e(meta.get('subtitle','')) + '</p>') if meta.get('subtitle') else ''}
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
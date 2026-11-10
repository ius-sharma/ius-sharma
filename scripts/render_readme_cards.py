#!/usr/bin/env python3
"""
Render the profile README's cards as animated SVGs into cards/.

Theme: Orange & Warm Amber palette on Paper ("Every day, in orange").
Fonts: Instrument Serif, Geist, Geist Mono (embedded as base64 WOFF).

Live numbers come from data/contributions.json (fetch_contributions.py).
Run by .github/workflows/update-profile-cards.yml after fetch_contributions.py.
"""
import base64
import datetime
import json
import os
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
DATA = os.path.join(ROOT, "data", "contributions.json")
OUT = os.path.join(ROOT, "cards")
FONTS = os.path.join(ROOT, "fonts")

# ---- Brand Tokens (Dark Mode & Orange Theme) -------------------------------
CARD_BG = "#161b22"
CARD_BORDER = "#30363d"
TEXT_MAIN = "#f0f6fc"
TEXT_SOFT = "#c9d1d9"
MUTED = "#8b949e"
RULE = "#30363d"
ORANGE_ACCENT = "#ff7828"
ORANGE_DEEP = "#ff893b"

# Dark mode orange heatmap gradient (0 = empty, 1 = lowest, 5 = highest)
ORANGE = ["#21262d", "#5e2208", "#93370d", "#ca4e11", "#f97316", "#ff893b"]

W = 880  # Full card width (GitHub's standard README column at 100%)
BOTTOM = 12

SERIF = "'Instrument Serif', Georgia, serif"
SANS = "Geist, system-ui, -apple-system, sans-serif"
MONO = "'Geist Mono', ui-monospace, SFMono-Regular, Menlo, monospace"

FONT_FILES = {
    "serif": ("Instrument Serif", "normal", 400, "serif-400.woff"),
    "serif-i": ("Instrument Serif", "italic", 400, "serif-italic.woff"),
    "sans": ("Geist", "normal", 400, "geist-400.woff"),
    "sans-b": ("Geist", "normal", 600, "geist-600.woff"),
    "mono": ("Geist Mono", "normal", 400, "geistmono-400.woff"),
}

BASE_CSS = """
@keyframes rise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes pop{0%{opacity:0;transform:scale(.3)}70%{opacity:1;transform:scale(1.15)}100%{opacity:1;transform:none}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}
.r{opacity:0;animation:rise .8s cubic-bezier(.2,.7,.2,1) both;transform-box:fill-box}
.f{opacity:0;animation:fade .9s ease-out both}
.g{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:grow .8s cubic-bezier(.2,.7,.2,1) both}
.p{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .4s ease-out both}
.live{animation:pulse 1.6s ease-in-out infinite}
@media (prefers-reduced-motion: reduce){
  .r,.f,.g,.p,.live{animation:none!important;opacity:1!important;transform:none!important}
}
"""


def font_face(keys):
    out = []
    for k in keys:
        if k not in FONT_FILES:
            continue
        fam, style, weight, fn = FONT_FILES[k]
        font_path = os.path.join(FONTS, fn)
        if not os.path.exists(font_path):
            continue
        with open(font_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        out.append(
            f"@font-face{{font-family:'{fam}';font-style:{style};font-weight:{weight};"
            f"font-display:swap;src:url(data:font/woff;base64,{b64}) format('woff');}}"
        )
    return "\n".join(out)


def svg(w, h, body, fonts, label, bottom=BOTTOM):
    css = font_face(fonts) + BASE_CSS
    if os.environ.get("STATIC"):
        css += ".r,.f,.g,.p,.live{animation:none!important;opacity:1!important;transform:none!important}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.3f}" height="{h + bottom}" viewBox="0 0 {w:.3f} {h + bottom}" '
        f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>'
        f"<style>{css}</style>{body}</svg>"
    )


def write(name, content):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"wrote cards/{name} ({len(content) // 1024} KB)")


def d(s):
    return f'style="animation-delay:{s:.2f}s"'


def level_for(c):
    return 0 if c == 0 else 1 if c <= 3 else 2 if c <= 8 else 3 if c <= 15 else 4 if c <= 25 else 5


def heatmap(data):
    days = data["days"]
    first = datetime.date.fromisoformat(days[0]["date"])
    lead = (first.weekday() + 1) % 7  # Sunday = 0
    cell, step, gx, gy = 12, 15, 44, 96
    cells, months, seen = [], [], set()

    for i, day in enumerate(days):
        k = i + lead
        col, row = divmod(k, 7)
        date = datetime.date.fromisoformat(day["date"])
        if date.day <= 7 and (date.year, date.month) not in seen and row == 0:
            seen.add((date.year, date.month))
            months.append((col, date.strftime("%b")))
        c = day["count"]
        delay = 1.0 + col * 0.03 + row * 0.02
        cells.append(
            f'<rect class="p" style="animation-delay:{delay:.2f}s" x="{gx + col * step}" y="{gy + row * step}" '
            f'width="{cell}" height="{cell}" rx="3" fill="{ORANGE[level_for(c)]}">'
            f'<title>{day["date"]}: {c} contribution{"s" if c != 1 else ""}</title></rect>'
        )

    ncols = (len(days) + lead + 6) // 7
    right = gx + ncols * step - 3
    labels = "".join(
        f'<text x="{gx + col * step}" y="{gy + 7 * step + 16}" font-family="{MONO}" font-size="11" fill="{MUTED}">{m}</text>'
        for col, m in months if col < ncols - 12
    )

    legend_x = right - len(ORANGE) * 14
    legend = "".join(
        f'<rect x="{legend_x + i * 14}" y="{gy + 7 * step + 6}" width="11" height="11" rx="2.5" fill="{c}"/>'
        for i, c in enumerate(ORANGE)
    )
    h = gy + 7 * step + 44

    body = f"""
<rect x="0.5" y="0.5" width="{W - 1}" height="{h - 1}" rx="14" fill="{CARD_BG}" stroke="{CARD_BORDER}" stroke-width="1"/>
<text class="r" {d(0.8)} x="42" y="62" font-family="{SERIF}" font-size="34" fill="{TEXT_MAIN}">Every day, <tspan font-style="italic" fill="{ORANGE_ACCENT}">in orange</tspan></text>
<text class="f" {d(0.8)} x="{right}" y="60" text-anchor="end" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{MUTED}">REFRESHED DAILY</text>
{''.join(cells)}
<g class="f" {d(2.4)}>{labels}
<text x="{legend_x - 8}" y="{gy + 7 * step + 16}" text-anchor="end" font-family="{MONO}" font-size="11" fill="{MUTED}">less</text>
{legend}
<text x="{legend_x + len(ORANGE) * 14 + 2}" y="{gy + 7 * step + 16}" font-family="{MONO}" font-size="11" fill="{MUTED}">more</text></g>
"""
    write("heatmap.svg", svg(W, h, body, ["serif", "serif-i", "mono"],
                             f'Contribution graph: {data["total_contributions"]:,} contributions in the last year'))


def activity(data):
    h = 340
    monthly = data["monthly"][-12:]
    best = max(monthly[:-1] or monthly, key=lambda m: m["total"])
    top = max(best["total"], 1)
    x0, x1, base, maxh, gap = 40, 600, 292, 140, 10
    bw = (x1 - x0 - gap * (len(monthly) - 1)) / len(monthly)
    bars = []

    for i, m in enumerate(monthly):
        partial = i == len(monthly) - 1
        is_best = m is best
        bh = max(4, round(m["total"] / top * maxh))
        x = x0 + i * (bw + gap)
        fill = ORANGE_ACCENT if is_best else ("#282e37" if partial else "#484f58")
        label = datetime.date.fromisoformat(m["month"] + "-01").strftime("%b")
        bars.append(
            f'<rect class="g" style="animation-delay:{2.2 + i * 0.07:.2f}s" x="{x:.1f}" y="{base - bh}" '
            f'width="{bw:.1f}" height="{bh}" rx="4" fill="{fill}"><title>{label}: {m["total"]:,}</title></rect>'
            f'<text class="f" style="animation-delay:{2.2 + i * 0.07:.2f}s" x="{x + bw / 2:.1f}" y="{base + 22}" '
            f'text-anchor="middle" font-family="{MONO}" font-size="11" fill="{MUTED}">{label}</text>'
        )
        if is_best:
            bars.append(
                f'<text class="p" style="animation-delay:3.2s" x="{x + bw / 2:.1f}" y="{base - bh - 10}" '
                f'text-anchor="middle" font-family="{MONO}" font-size="11" fill="{ORANGE_ACCENT}">{m["total"]:,}</text>'
            )

    cs = data["current_streak"]["length"]
    ls = data["longest_streak"]["length"]
    streak_note = "current streak, and personal best 🔥" if cs >= ls and cs > 0 else f"current streak, longest {ls}"
    total_days = len(data["days"])
    stats = [
        (f'{cs} <tspan font-style="italic" fill="{ORANGE_ACCENT}">days</tspan>', streak_note),
        (f'{data["active_days"]}<tspan fill="#8b949e"> / {total_days}</tspan>', "days with a commit"),
        (f'{data["best_day"]["count"]}', "on the busiest day"),
    ]
    side = []
    for i, (big, small) in enumerate(stats):
        y = 104 + i * 92
        side.append(
            f'<g class="r" {d(2.6 + i * 0.15)}>'
            f'<text x="650" y="{y}" font-family="{SERIF}" font-size="40" fill="{TEXT_MAIN}">{big}</text>'
            f'<text x="650" y="{y + 24}" font-family="{SANS}" font-size="13" fill="{MUTED}">{small}</text></g>'
        )
        if i < 2:
            side.append(f'<rect class="f" {d(2.6)} x="650" y="{y + 44}" width="190" height="1" fill="{RULE}"/>')

    body = f"""
<rect x="0.5" y="0.5" width="{W - 1}" height="{h - 1}" rx="14" fill="{CARD_BG}" stroke="{CARD_BORDER}" stroke-width="1"/>
<text class="f" {d(1.9)} x="40" y="58" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{MUTED}">THE LAST 12 MONTHS ON GITHUB</text>
<text class="r" {d(2.0)} x="38" y="114" font-family="{SERIF}" font-size="52" fill="{TEXT_MAIN}">{data["total_contributions"]:,} <tspan font-style="italic" fill="{ORANGE_ACCENT}">contributions</tspan></text>
{''.join(bars)}
{''.join(side)}
"""
    write("activity.svg", svg(W, h, body, ["serif", "serif-i", "sans", "mono"],
                              f'{data["total_contributions"]:,} contributions in the last year, {cs}-day streak'))


def stack():
    h = 370
    categories = [
        ("LANGUAGES", ["JavaScript", "TypeScript", "Python", "HTML5", "CSS3"]),
        ("FRONTEND", ["Next.js", "React", "Tailwind CSS", "Vite"]),
        ("BACKEND & DB", ["Node.js", "Express.js", "MongoDB"]),
        ("AI / LLMS", ["Groq", "LLaMA", "Prompt Engineering"]),
        ("TOOLS & CLOUD", ["Git", "GitHub", "Postman", "Vercel", "Render"]),
    ]

    rows = []
    for i, (cat, items) in enumerate(categories):
        row_y = 108 + i * 48
        is_ai = cat == "AI / LLMS"
        delay = 0.5 + i * 0.12
        pills = []
        px = 200
        for item in items:
            text_len = len(item)
            pw = max(54, round(text_len * 7.5 + (32 if is_ai else 24)))
            if is_ai:
                pills.append(
                    f'<g class="r" {d(delay)}>'
                    f'<rect x="{px}" y="{row_y}" width="{pw}" height="28" rx="6" fill="#21262d" stroke="{ORANGE_ACCENT}" stroke-width="1" stroke-opacity="0.7"/>'
                    f'<circle cx="{px + 12}" cy="{row_y + 14}" r="2.5" fill="{ORANGE_ACCENT}"/>'
                    f'<text x="{px + 12 + round((pw - 12) / 2)}" y="{row_y + 18}" text-anchor="middle" font-family="{SANS}" font-size="12" font-weight="500" fill="{TEXT_MAIN}">{escape(item)}</text>'
                    f'</g>'
                )
            else:
                pills.append(
                    f'<g class="r" {d(delay)}>'
                    f'<rect x="{px}" y="{row_y}" width="{pw}" height="28" rx="6" fill="#21262d" stroke="{CARD_BORDER}" stroke-width="1"/>'
                    f'<text x="{px + round(pw / 2)}" y="{row_y + 18}" text-anchor="middle" font-family="{SANS}" font-size="12" font-weight="500" fill="{TEXT_MAIN}">{escape(item)}</text>'
                    f'</g>'
                )
            px += pw + 8

        row_divider = (
            f'<rect class="f" {d(delay)} x="42" y="{row_y + 38}" width="796" height="1" fill="{RULE}" opacity="0.3"/>'
            if i < len(categories) - 1
            else ""
        )

        rows.append(
            f'<g class="r" {d(delay)}>'
            f'<text x="44" y="{row_y + 18}" font-family="{MONO}" font-size="11" letter-spacing="1.5" font-weight="600" fill="{MUTED}">{escape(cat)}</text>'
            f'</g>'
            f'{"".join(pills)}'
            f'{row_divider}'
        )

    body = f"""
<rect x="0.5" y="0.5" width="{W - 1}" height="{h - 1}" rx="14" fill="{CARD_BG}" stroke="{CARD_BORDER}" stroke-width="1"/>
<text class="r" {d(0.3)} x="42" y="58" font-family="{SERIF}" font-size="34" fill="{TEXT_MAIN}">What I <tspan font-style="italic" fill="{ORANGE_ACCENT}">work with</tspan></text>
<text class="f" {d(0.3)} x="836" y="56" text-anchor="end" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{MUTED}">CORE TECH &amp; TOOLING</text>
<rect class="f" {d(0.4)} x="42" y="78" width="796" height="1" fill="{RULE}"/>
{''.join(rows)}
"""
    write("stack.svg", svg(W, h, body, ["serif", "serif-i", "sans", "mono"],
                           "What I work with: Languages, Frontend, Backend, AI, Tools"))


if __name__ == "__main__":
    if not os.path.exists(DATA):
        print(f"Error: {DATA} not found. Run scripts/fetch_contributions.py first.")
        exit(1)
    with open(DATA, "r", encoding="utf-8") as f:
        data = json.load(f)
    heatmap(data)
    activity(data)
    stack()
    print("Done! Rendered heatmap.svg, activity.svg, and stack.svg into cards/")

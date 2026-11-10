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
DATA_SIUU = os.path.join(ROOT, "data", "ronaldo_siuuu.txt")
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


def svg(w, h, body, fonts, label, left=0, right=0, bottom=BOTTOM):
    if left:
        body = f'<g transform="translate({left:.3f} 0)">{body}</g>'
    total_w = w + left + right
    total_h = h + bottom
    css = font_face(fonts) + BASE_CSS
    if os.environ.get("STATIC"):
        css += ".r,.f,.g,.p,.live{animation:none!important;opacity:1!important;transform:none!important}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w:.3f}" height="{total_h}" viewBox="0 0 {total_w:.3f} {total_h}" '
        f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>'
        f"<style>{css}</style>{body}</svg>"
    )


def wrap(text, n):
    words = text.split()
    lines, cur = [], []
    for w in words:
        if sum(len(x) for x in cur) + len(cur) + len(w) > n:
            lines.append(" ".join(cur))
            cur = [w]
        else:
            cur.append(w)
    if cur:
        lines.append(" ".join(cur))
    return lines


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


PROJECTS = [
    (
        "boringtools",
        "BoringTools",
        "LIVE",
        "#3fb950",
        "#132c1c",
        "100 Days, 100 Tools. Browser-first micro-utilities, no signup, no fluff.",
        "Next.js · Tailwind · Vercel",
    ),
    (
        "vakiogiri",
        "Vakiogiri",
        "TESTING",
        "#ff7828",
        "#2a1705",
        "Turns YouTube videos into viral, ready-to-post Shorts automatically.",
        "Python · FastAPI · Next.js",
    ),
    (
        "arrowgo",
        "ArrowGoPlus",
        "UP NEXT",
        "#8b949e",
        "#21262d",
        "Feature-rich Arrow puzzle game with cloud saves, leaderboards & editor.",
        "ASP.NET Core · .NET 8",
    ),
]


def project_card(i, key, title, status, st_color, st_bg, desc, stack_info):
    proj_w = 880 / 3 - 8
    proj_h = 186
    delay = 0.4 + i * 0.15

    pill_w = round(len(status) * 7.2 + 22)
    pill_x = proj_w - 20 - pill_w
    pill_y = 18

    desc_lines = wrap(desc, 30)
    desc_svg = "".join(
        f'<text x="20" y="{70 + j * 20}" font-family="{SANS}" font-size="13" fill="{MUTED}">{escape(l)}</text>'
        for j, l in enumerate(desc_lines)
    )

    body = f"""
<rect x="0.5" y="0.5" width="{proj_w - 1:.3f}" height="{proj_h - 1}" rx="14" fill="{CARD_BG}" stroke="{CARD_BORDER}" stroke-width="1"/>
<g class="r" {d(delay)}>
  <text x="20" y="36" font-family="{SANS}" font-weight="600" font-size="17" fill="{TEXT_MAIN}">{escape(title)}</text>
  <rect x="{pill_x:.3f}" y="{pill_y}" width="{pill_w}" height="22" rx="11" fill="{st_bg}" stroke="{st_color}" stroke-width="1" stroke-opacity="0.6"/>
  <circle cx="{pill_x + 9:.3f}" cy="{pill_y + 11}" r="2.5" fill="{st_color}"/>
  <text x="{pill_x + 16:.3f}" y="{pill_y + 15}" font-family="{MONO}" font-size="10" font-weight="600" letter-spacing="0.5" fill="{st_color}">{escape(status)}</text>
  {desc_svg}
  <rect x="20" y="138" width="{proj_w - 40:.3f}" height="1" fill="{RULE}" opacity="0.4"/>
  <text x="20" y="160" font-family="{MONO}" font-size="11" fill="{MUTED}">{escape(stack_info)}</text>
</g>
"""
    write(f"project-{key}.svg", svg(proj_w, proj_h, body, ["sans", "sans-b", "mono"], f"{title}: {desc}",
                                    left=4 * i, right=8 - 4 * i))


def project_title():
    h = 48
    body = (
        f'<text class="r" {d(0.2)} x="2" y="36" font-family="{SERIF}" font-size="34" fill="{TEXT_MAIN}">Featured '
        f'<tspan font-style="italic" fill="{ORANGE_ACCENT}">projects</tspan></text>'
    )
    write("title-projects.svg", svg(W, h, body, ["serif", "serif-i"], "Featured projects", bottom=0))


def beyond_code():
    w = 478
    h = 210
    pill_text = "ESPORTS FOUNDER"
    pill_w = round(len(pill_text) * 7.2 + 22)
    pill_x = w - 24 - pill_w
    body = f"""
<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="14" fill="{CARD_BG}" stroke="{CARD_BORDER}" stroke-width="1"/>
<g class="r" {d(0.2)}>
  <text x="24" y="38" font-family="{SERIF}" font-size="28" fill="{TEXT_MAIN}">Beyond <tspan font-style="italic" fill="{ORANGE_ACCENT}">code</tspan></text>
  <rect x="{pill_x}" y="18" width="{pill_w}" height="22" rx="11" fill="#2a1705" stroke="{ORANGE_ACCENT}" stroke-width="1" stroke-opacity="0.7"/>
  <circle cx="{pill_x + 9}" cy="29" r="2.5" fill="{ORANGE_ACCENT}"/>
  <text x="{pill_x + 16}" y="33" font-family="{MONO}" font-size="10" font-weight="600" letter-spacing="0.5" fill="{ORANGE_ACCENT}">{pill_text}</text>
  <rect x="24" y="56" width="430" height="1" fill="{RULE}" opacity="0.4"/>
  <text x="24" y="86" font-family="{SANS}" font-weight="600" font-size="17" fill="{TEXT_MAIN}">Founder of ODDSOCEAN</text>
  <text x="24" y="112" font-family="{SANS}" font-size="13" fill="{MUTED}">An eSports organization built for the underdogs.</text>
  <text x="24" y="132" font-family="{SANS}" font-size="13" fill="{MUTED}">Creating a gaming ecosystem where players and creators</text>
  <text x="24" y="152" font-family="{SANS}" font-size="13" fill="{MUTED}">grow, compete, and build something bigger together.</text>
  <rect x="24" y="172" width="430" height="1" fill="{RULE}" opacity="0.3"/>
  <text x="24" y="193" font-family="{MONO}" font-size="11" letter-spacing="1" fill="{ORANGE_ACCENT}">oddsocean.in &#x2197;</text>
</g>
"""
    write("beyond-code.svg", svg(w, h, body, ["serif", "serif-i", "sans", "mono"],
                                 "Beyond Code - Founder of ODDSOCEAN", right=6))


def connect():
    w = 390
    h = 210
    pill_text = "OPEN FOR TALKS"
    pill_w = round(len(pill_text) * 7.2 + 22)
    pill_x = w - 24 - pill_w
    body = f"""
<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="14" fill="{CARD_BG}" stroke="{CARD_BORDER}" stroke-width="1"/>
<g class="r" {d(0.3)}>
  <text x="24" y="38" font-family="{SERIF}" font-size="28" fill="{TEXT_MAIN}">Let&apos;s <tspan font-style="italic" fill="{ORANGE_ACCENT}">connect</tspan></text>
  <rect x="{pill_x}" y="18" width="{pill_w}" height="22" rx="11" fill="#132c1c" stroke="#3fb950" stroke-width="1" stroke-opacity="0.7"/>
  <circle cx="{pill_x + 9}" cy="29" r="2.5" fill="#3fb950"/>
  <text x="{pill_x + 16}" y="33" font-family="{MONO}" font-size="10" font-weight="600" letter-spacing="0.5" fill="#3fb950">{pill_text}</text>
  <rect x="24" y="56" width="342" height="1" fill="{RULE}" opacity="0.4"/>
  <text x="24" y="86" font-family="{SANS}" font-weight="600" font-size="17" fill="{TEXT_MAIN}">Building something real?</text>
  <text x="24" y="112" font-family="{SANS}" font-size="13" fill="{MUTED}">Not open for free-work, but always eager</text>
  <text x="24" y="132" font-family="{SANS}" font-size="13" fill="{MUTED}">to build meaningful products with good teams.</text>
  <text x="24" y="152" font-family="{SANS}" font-size="13" fill="{MUTED}">Let&apos;s talk and create value.</text>
  <rect x="24" y="172" width="342" height="1" fill="{RULE}" opacity="0.3"/>
  <text x="24" y="193" font-family="{MONO}" font-size="11" letter-spacing="1" fill="{ORANGE_ACCENT}">DROP A MESSAGE OR EMAIL &#x2197;</text>
</g>
"""
    write("connect.svg", svg(w, h, body, ["serif", "serif-i", "sans", "mono"],
                             "Let's Connect - Always open to building meaningful things", left=6))


BADGES = [
    (
        "linkedin",
        "LinkedIn",
        "M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 10.9v8.37H9.2V10.9H6.46M7.83 6.64c-.9 0-1.63.73-1.63 1.63 0 .9.73 1.63 1.63 1.63.9 0 1.63-.73 1.63-1.63 0-.9-.73-1.63-1.63-1.63",
    ),
    (
        "email",
        "Email",
        "M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z",
    ),
    (
        "instagram",
        "Instagram",
        "M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z",
    ),
    (
        "youtube",
        "YouTube",
        "M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z",
    ),
    (
        "oddsocean",
        "ODDSOCEAN",
        "M21 6H3c-1.1 0-2 .9-2 2v8c0 1.1.9 2 2 2h18c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm-10 7H8v3H6v-3H3v-2h3V8h2v3h3v2zm4.5 2c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm3-3c-.83 0-1.5-.67-1.5-1.5S17.67 9 18.5 9s1.5.67 1.5 1.5-.67 1.5-1.5 1.5z",
    ),
]


def social_badges():
    h = 32
    for key, label, path in BADGES:
        w = round(34 + len(label) * 7.5 + 14)
        body = f"""
<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="8" fill="{CARD_BG}" stroke="{CARD_BORDER}" stroke-width="1"/>
<svg x="10" y="8" width="16" height="16" viewBox="0 0 24 24" fill="{ORANGE_ACCENT}"><path d="{path}"/></svg>
<text x="32" y="20.5" font-family="{SANS}" font-weight="600" font-size="12" fill="{TEXT_MAIN}">{escape(label)}</text>
"""
        write(f"badge-{key}.svg", svg(w, h, body, ["sans", "sans-b"], f"{label} profile", bottom=0))


def cr7_quote_card():
    w = 880
    h = 430
    lines = []
    if os.path.exists(DATA_SIUU):
        with open(DATA_SIUU, "r", encoding="utf-8") as f:
            lines = [l for l in f.read().splitlines() if l.strip()]

    font_size = 2.7
    line_h = 2.92
    start_y = 26
    start_x = 525

    ascii_svg_lines = []
    for i, line in enumerate(lines):
        y = start_y + i * line_h
        ascii_svg_lines.append(
            f'<text x="{start_x}" y="{y:.2f}" font-family="{MONO}" '
            f'font-size="{font_size}" fill="{ORANGE_ACCENT}" opacity="0.92" xml:space="preserve">{escape(line)}</text>'
        )
    ascii_block = "\n".join(ascii_svg_lines)

    body = f"""
<defs>
  <radialGradient id="cr7-glow" cx="75%" cy="50%" r="45%">
    <stop offset="0%" stop-color="{ORANGE_ACCENT}" stop-opacity="0.09"/>
    <stop offset="60%" stop-color="{ORANGE_ACCENT}" stop-opacity="0.02"/>
    <stop offset="100%" stop-color="{ORANGE_ACCENT}" stop-opacity="0"/>
  </radialGradient>
  <filter id="text-shadow" x="-10%" y="-10%" width="120%" height="120%">
    <feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#000000" flood-opacity="0.7"/>
  </filter>
</defs>

<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="14" fill="{CARD_BG}" stroke="{CARD_BORDER}" stroke-width="1"/>
<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="14" fill="url(#cr7-glow)"/>

<!-- SIUU ASCII ART (Right side in glowing orange) -->
<g class="r" {d(0.35)}>
{ascii_block}
</g>

<!-- Left content with text shadow -->
<g class="r" {d(0.15)} filter="url(#text-shadow)">
  <!-- Plain CR7 IS THE GOAT (No pill/capsule, clean plain text) -->
  <g transform="translate(40 48)">
    <circle cx="4" cy="-3.5" r="3.5" fill="{ORANGE_ACCENT}"/>
    <text x="16" y="0" font-family="{MONO}" font-size="12" font-weight="600" letter-spacing="1.5" fill="{ORANGE_ACCENT}">CR7 IS THE GOAT &#x1F410;</text>
  </g>

  <!-- Single line quote spanning across the top and slightly over the pose -->
  <text x="40" y="96" font-family="{SERIF}" font-size="28" fill="{TEXT_MAIN}">Build &#x2192; Fail &#x2192; Learn &#x2192; Improve &#x2192; <tspan font-style="italic" fill="{ORANGE_ACCENT}">Repeat.</tspan></text>

  <!-- Divider -->
  <rect x="40" y="118" width="460" height="1" fill="{RULE}" opacity="0.35"/>

  <!-- Left body details / message -->
  <text x="40" y="160" font-family="{SANS}" font-weight="600" font-size="20" fill="{TEXT_MAIN}">Thanks for stopping by.</text>
  <text x="40" y="190" font-family="{SANS}" font-size="14" fill="{MUTED}">Always open to building something meaningful together.</text>
  <text x="40" y="212" font-family="{SANS}" font-size="14" fill="{MUTED}">Building in public, learning every single day.</text>

  <!-- Callout / Signature quote -->
  <rect x="40" y="246" width="440" height="74" rx="8" fill="#21262d" stroke="{CARD_BORDER}" stroke-width="1" opacity="0.8"/>
  <text x="56" y="274" font-family="{MONO}" font-size="10" font-weight="600" letter-spacing="1" fill="{ORANGE_ACCENT}">CRISTIANO RONALDO</text>
  <text x="56" y="298" font-family="{SANS}" font-size="13.5" font-weight="500" fill="{TEXT_MAIN}">&#x201C;Talent without working hard is nothing.&#x201D;</text>

  <g transform="translate(40 365)">
    <text x="0" y="0" font-family="{MONO}" font-size="11" letter-spacing="1.5" fill="{MUTED}">AYUSH SHARMA &#x00B7; <tspan fill="{ORANGE_ACCENT}">SIUUU</tspan> &#x2197;</text>
  </g>
</g>
"""
    write("quote.svg", svg(w, h, body, ["serif", "serif-i", "sans", "sans-b", "mono"],
                           "Build Fail Learn Improve Repeat - CR7 SIUU", bottom=12))


if __name__ == "__main__":
    if not os.path.exists(DATA):
        print(f"Error: {DATA} not found. Run scripts/fetch_contributions.py first.")
        exit(1)
    with open(DATA, "r", encoding="utf-8") as f:
        data = json.load(f)
    heatmap(data)
    activity(data)
    stack()
    project_title()
    for i, (key, title, status, st_color, st_bg, desc, stack_info) in enumerate(PROJECTS):
        project_card(i, key, title, status, st_color, st_bg, desc, stack_info)
    beyond_code()
    connect()
    social_badges()
    cr7_quote_card()
    print("Done! Rendered all profile cards and social badges into cards/")

from __future__ import annotations
from typing import Any, Dict, Mapping
from xml.sax.saxutils import escape

SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

# North-Indian-style fixed sign grid: houses are fixed, zodiac signs rotate through them.
# We use a simple 4x4 diamond layout that is easy to render and printable.
HOUSE_POS = {
    1:(200,45), 2:(95,75), 3:(45,150), 4:(95,225), 5:(200,255), 6:(305,225),
    7:(355,150), 8:(305,75), 9:(200,135), 10:(125,150), 11:(200,200), 12:(275,150)
}


def render_north_chart(chart: Mapping[str, Any], title: str = "Rashi Chart", highlight_houses: set[int] | None = None) -> str:
    highlight_houses = highlight_houses or set()
    lagna = int(chart.get("lagna_sign_index", 0))
    houses = {i: {"sign": (lagna + i - 1) % 12, "planets": []} for i in range(1,13)}
    for p, d in chart["planets"].items():
        houses[d["house"]]["planets"].append(p)
    w, h = 400, 310
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}">']
    parts.append('<rect x="1" y="1" width="398" height="308" fill="white" stroke="#222" stroke-width="2"/>')
    parts.append('<path d="M200 1 L399 155 L200 309 L1 155 Z" fill="none" stroke="#222" stroke-width="2"/>')
    parts.append('<path d="M1 1 L399 309 M399 1 L1 309" fill="none" stroke="#222" stroke-width="1.5"/>')
    parts.append('<path d="M200 1 L200 309 M1 155 L399 155" fill="none" stroke="#ddd" stroke-width="1"/>')
    for house, box in houses.items():
        x,y = HOUSE_POS[house]
        bg = "#eef2ff" if house in highlight_houses else "white"
        parts.append(f'<rect x="{x-42}" y="{y-18}" width="84" height="44" rx="8" fill="{bg}" fill-opacity="0.85"/>')
        parts.append(f'<text x="{x-36}" y="{y-2}" font-size="10" font-family="Arial" fill="#666">H{house}</text>')
        parts.append(f'<text x="{x-36}" y="{y+12}" font-size="11" font-family="Arial" font-weight="700">{escape(SIGNS[box["sign"]])}</text>')
        plist = ", ".join(box["planets"])
        if plist:
            parts.append(f'<text x="{x-36}" y="{y+25}" font-size="9" font-family="Arial">{escape(plist)}</text>')
    parts.append(f'<text x="200" y="23" text-anchor="middle" font-size="14" font-family="Arial" font-weight="700">{escape(title)}</text>')
    parts.append('</svg>')
    return "".join(parts)

"""Field diagrams for referee reports.
Usage:
  python3 draw.py guide OUT.png                 # blank sketch guide for the user to copy on paper
  python3 draw.py spec SPEC.json OUT_DIR        # render every diagram in SPEC["diagrams"] to OUT_DIR/<name>.png
Canvas 760x700. Field: touchlines x=90..650 (centre x=370), goal line / halfway line y=70 and y=610.
Element types: lex (solid circle, short text), opp (outline circle, short text), ref, ar (text), coach (text),
other (grey dot), ball, arrow (x1,y1,x2,y2), sight (dashed x1,y1,x2,y2), text (x,y,t[,anchor,size]).
"""
import sys, os, json, math, asyncio
from xml.sax.saxutils import escape
W, H = 760, 700
FX0, FX1, TOP, BOT = 90, 650, 70, 610
CX = (FX0 + FX1) / 2
BW, BD, GW, GD = 300, 150, 140, 55
FONT = 'font-family="Arial, Helvetica, sans-serif"'

def T(x, y, t, size=17, anchor="start", weight="normal", fill="#000"):
    return f'<text x="{x}" y="{y}" {FONT} font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{fill}">{escape(str(t))}</text>'

def field(goal_at_top=True):
    s = [f'<rect x="{FX0}" y="{TOP}" width="{FX1-FX0}" height="{BOT-TOP}" fill="none" stroke="#000" stroke-width="3"/>']
    gl, hw, d = (TOP, BOT, 1) if goal_at_top else (BOT, TOP, -1)
    by, gy = gl + d*BD, gl + d*GD
    for w, y in ((BW, by), (GW, gy)):
        s.append(f'<path d="M{CX-w/2},{gl} L{CX-w/2},{y} L{CX+w/2},{y} L{CX+w/2},{gl}" fill="none" stroke="#000" stroke-width="3"/>')
    s.append(f'<rect x="{CX-40}" y="{gl-16 if goal_at_top else gl}" width="80" height="16" fill="#fff" stroke="#000" stroke-width="3"/>')
    dx = math.sqrt(70**2 - 38**2)
    s.append(f'<path d="M{CX-dx},{by} A70,70 0 0 {0 if goal_at_top else 1} {CX+dx},{by}" fill="none" stroke="#000" stroke-width="3"/>')
    s.append(f'<path d="M{CX-110},{hw} A110,110 0 0 {1 if goal_at_top else 0} {CX+110},{hw}" fill="none" stroke="#000" stroke-width="3"/>')
    return s

def el(e):
    t = e["type"]; x = e.get("x"); y = e.get("y"); lbl = e.get("label", "")
    if t == "lex":   return f'<circle cx="{x}" cy="{y}" r="20" fill="#000"/>' + T(x, y+7, lbl, 18, "middle", "bold", "#fff")
    if t == "opp":   return f'<circle cx="{x}" cy="{y}" r="20" fill="#fff" stroke="#000" stroke-width="3"/>' + T(x, y+6, lbl, 15, "middle", "bold")
    if t == "ref":   return f'<rect x="{x-16}" y="{y-16}" width="32" height="32" fill="#000" transform="rotate(45 {x} {y})"/>' + T(x, y+6, "R", 17, "middle", "bold", "#fff")
    if t == "ar":    return f'<rect x="{x-22}" y="{y-16}" width="44" height="32" rx="6" fill="#fff" stroke="#000" stroke-width="3"/>' + T(x, y+6, lbl or "AR", 15, "middle", "bold")
    if t == "coach": return f'<rect x="{x-18}" y="{y-18}" width="36" height="36" rx="6" fill="#fff" stroke="#000" stroke-width="3"/>' + T(x, y+7, lbl or "C", 18, "middle", "bold")
    if t == "other": return f'<circle cx="{x}" cy="{y}" r="12" fill="#9a9a9a"/>'
    if t == "ball":  return f'<circle cx="{x}" cy="{y}" r="7" fill="#000"/>'
    if t == "arrow": return f'<line x1="{e["x1"]}" y1="{e["y1"]}" x2="{e["x2"]}" y2="{e["y2"]}" stroke="#000" stroke-width="{e.get("w",3)}" marker-end="url(#ah)"/>'
    if t == "sight": return f'<line x1="{e["x1"]}" y1="{e["y1"]}" x2="{e["x2"]}" y2="{e["y2"]}" stroke="#000" stroke-width="2" stroke-dasharray="8 6"/>'
    if t == "text":  return T(x, y, e["t"], e.get("size", 17), e.get("anchor", "start"))
    raise ValueError(t)

DEFS = '<defs><marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#000"/></marker></defs>'
def svg(parts, h=H):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}"><rect width="{W}" height="{h}" fill="#fff"/>{DEFS}' + ''.join(parts) + '</svg>'

def diagram(spec):
    gat = spec.get("goal_at_top", True)
    p = field(gat)
    top, bot = spec.get("top_label", "" if gat else "HALFWAY LINE"), spec.get("bottom_label", "HALFWAY LINE" if gat else "")
    if top: p.append(T(CX, TOP-24, top, 18, "middle"))
    if bot: p.append(T(CX, BOT+42, bot, 18, "middle"))
    p += [el(e) for e in spec["elements"]]
    return svg(p)

def guide():
    p = field(True)
    p.append(T(CX, TOP-24, "GOAL END (write whose goal)", 18, "middle"))
    p.append(T(CX, BOT+42, "HALFWAY LINE", 18, "middle"))
    p.append(T(FX0-10, (TOP+BOT)/2, "touchline", 15, "end"))
    leg_y = BOT + 95
    items = [("lex", "offender (#)"), ("opp", "opponent"), ("ref", "you"), ("ar", "AR1/AR2"),
             ("coach", "coach"), ("other", "blocker"), ("ball", "ball")]
    x = 60
    for t, lbl in items:
        p.append(el({"type": t, "x": x, "y": leg_y, "label": {"lex": "#", "opp": "#", "ar": "AR"}.get(t, "")}))
        p.append(T(x, leg_y + 40, lbl, 14, "middle")); x += 106
    steps = ["Copy this half-field on paper, goal at the top.",
             "Write whose goal it is. Mark the touchline the AR was on.",
             "Dot and label: you, each player involved (#), the AR, anyone blocking your view.",
             "Arrows: ball direction, push or tackle direction, coach's path.",
             "Take one photo per incident, straight on, good light."]
    y = leg_y + 85
    for i, s in enumerate(steps, 1):
        p.append(T(40, y, f"{i}. {s}", 17)); y += 26
    return svg(p, h=y + 20)

def render_any(pairs):
    try:
        asyncio.run(render(pairs))
    except Exception as e:
        try:
            import cairosvg
        except ImportError:
            sys.exit("Need Playwright with Chromium or cairosvg (pip install cairosvg) to render PNGs: %s" % e)
        for svg_path, png_path in pairs:
            cairosvg.svg2png(url=svg_path, write_to=png_path, scale=2)

async def render(pairs):
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        pg = await b.new_page(viewport={"width": W, "height": 1100}, device_scale_factor=2)
        for svg_path, png_path in pairs:
            await pg.goto("file://" + os.path.abspath(svg_path))
            await pg.locator("svg").screenshot(path=png_path)
        await b.close()

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "guide":
        out = sys.argv[2]; sp = out[:-4] + ".svg"
        open(sp, "w").write(guide()); render_any([(sp, out)]); print(out)
    elif mode == "spec":
        spec = json.load(open(sys.argv[2])); od = sys.argv[3]; os.makedirs(od, exist_ok=True); pairs = []
        for name, d in spec.get("diagrams", {}).items():
            sp = os.path.join(od, name + ".svg"); open(sp, "w").write(diagram(d)); pairs.append((sp, os.path.join(od, name + ".png")))
        render_any(pairs); print("\n".join(p for _, p in pairs))

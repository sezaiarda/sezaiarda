# Regenerates assets/*.svg. Text is converted to outlines because GitHub serves SVGs
# as <img>, where web fonts never load.
#   uv run --with fonttools --with uharfbuzz python tools/build.py
import re, pathlib, uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

HERE = pathlib.Path(__file__).parent
OUT = HERE.parent / "assets"


class Font:
    def __init__(s, f):
        path = HERE / "fonts" / f
        s.tt = TTFont(path)
        s.gs = s.tt.getGlyphSet()
        s.upm = s.tt["head"].unitsPerEm
        s.hbf = hb.Font(hb.Face(path.read_bytes()))
        s.order = s.tt.getGlyphOrder()

    def shape(s, text, size, track=0):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(s.hbf, buf, {"kern": True, "liga": True})
        k, out, x = size / s.upm, [], 0
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            out.append((s.order[info.codepoint], x + pos.x_offset * k))
            x += pos.x_advance * k + track
        return out, x - track

    def path(s, text, x, y, size, track=0, anchor="start"):
        glyphs, w = s.shape(text, size, track)
        x -= {"start": 0, "middle": w / 2, "end": w}[anchor]
        k, d = size / s.upm, []
        for g, gx in glyphs:
            pen = SVGPathPen(s.gs)
            s.gs[g].draw(TransformPen(pen, (k, 0, 0, -k, x + gx, y)))
            d.append(pen.getCommands())
        return re.sub(r"\d+\.\d+", lambda m: f"{float(m.group()):.1f}", "".join(d))


SANS, MONO, MONOB = Font("geist-300.ttf"), Font("geist-mono-400.ttf"), Font("geist-mono-500.ttf")

THEMES = {"dark": dict(fg="#e6edf3", dim="#7d8590", mute="#484f58", line="#21262d", acc="#ff8a4c"),
          "light": dict(fg="#1f2328", dim="#818b98", mute="#afb8c1", line="#eaeef2", acc="#d4541a")}

EASE = "cubic-bezier(.2,.7,.2,1)"
# `both` keeps the resting state visible for viewers that don't animate SVGs.
CSS = ("@keyframes in{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:none}}"
       f".r{{animation:in .8s {EASE} both}}")


def text(font, s, x, y, size, fill, track=0, anchor="start"):
    return f'<path fill="{fill}" d="{font.path(s, x, y, size, track, anchor)}"/>'


def svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f"<style>{CSS}</style>{body}</svg>")


def header(t):
    W, H = 880, 150
    b = f'<g class="r">{text(SANS, "arda sezai", -3, 72, 66, t["fg"], -2.4)}</g>'
    b += (f'<g class="r" style="animation-delay:.12s">'
          f'{text(MONO, "rust-first software engineer. systems, machine learning, full stack.", 0, 112, 14, t["dim"])}</g>')
    b += (f'<g class="r" style="animation-delay:.24s">'
          f'<circle cx="{W - 5}" cy="47" r="4.5" fill="{t["acc"]}">'
          '<animate attributeName="opacity" values="1;.2;1" dur="2.6s" repeatCount="indefinite"/></circle>'
          f'{text(MONO, "izmir, tr", W - 20, 51, 12, t["dim"], .5, "end")}'
          f'{text(MONO, "since 2018", W, 73, 12, t["mute"], .5, "end")}</g>')
    b += f'<rect x="0" y="{H - 1}" width="{W}" height="1" fill="{t["line"]}"/>'
    return svg(W, H, b)


ROWS = [
    ("languages", [("rust", "rust"), ("python", "python"), ("typescript", "typescript"), ("csharp", "c#"),
                   ("javascript", "javascript"), ("go", "go"), ("cplusplus", "c++"), ("openjdk", "java"),
                   ("kotlin", "kotlin"), ("swift", "swift"), ("dart", "dart"), ("gnubash", "bash")]),
    ("machine learning & data", [("pytorch", "pytorch"), ("huggingface", "hugging face"), ("polars", "polars"),
                                 ("tensorflow", "tensorflow"), ("scikitlearn", "scikit-learn"), ("opencv", "opencv"),
                                 ("pandas", "pandas"), ("numpy", "numpy"), ("jupyter", "jupyter")]),
    ("backend & apps", [("fastapi", "fastapi"), ("dotnet", ".net"), ("react", "react"), ("django", "django"),
                        ("flask", "flask"), ("nestjs", "nestjs"), ("express", "express"), ("nextdotjs", "next.js"),
                        ("vuedotjs", "vue"), ("tailwindcss", "tailwind"), ("vite", "vite"), ("flutter", "flutter")]),
    ("storage & infrastructure", [("postgresql", "postgres"), ("docker", "docker"), ("linux", "linux"),
                                  ("redis", "redis"), ("mongodb", "mongodb"), ("mysql", "mysql"), ("nginx", "nginx"),
                                  ("githubactions", "actions"), ("amazonwebservices", "aws"),
                                  ("googlecloud", "gcp"), ("git", "git")]),
]
PRIMARY = {"rust", "python", "typescript", "csharp", "pytorch", "huggingface", "polars",
           "fastapi", "dotnet", "react", "postgresql", "docker", "linux"}


def glyph(slug, fill):
    if slug == "csharp":  # not in Simple Icons; drawn as a hexagon badge to match
        hexagon = "M12 .6 21.9 6.3v11.4L12 23.4 2.1 17.7V6.3Z"
        return (f'<path d="{hexagon}" fill="none" stroke="{fill}" stroke-width="1.6" stroke-linejoin="round"/>'
                + text(MONOB, "C#", 12, 16.2, 10.5, fill, -.3, "middle"))
    src = (HERE / "icons" / f"{slug}.svg").read_text(encoding="utf-8")
    return f'<path fill="{fill}" d="{re.search(r" d=\"([^\"]+)\"", src).group(1)}"/>'


def stack(t):
    W, cell, icon = 880, 880 / 12, 26
    y, b, n = 0, "", 0
    for ri, (label, items) in enumerate(ROWS):
        b += f'<g class="r" style="animation-delay:{ri * .12:.2f}s">{text(MONO, label.upper(), 0, y + 12, 10.5, t["dim"], 1.6)}</g>'
        y += 34
        for i, (slug, name) in enumerate(items):
            on = slug in PRIMARY
            cx = i * cell + cell / 2
            s = icon / 24
            b += (f'<g class="r" style="animation-delay:{ri * .12 + i * .035:.3f}s">'
                  f'<g transform="translate({cx - icon / 2:.1f},{y}) scale({s:.3f})">{glyph(slug, t["fg"] if on else t["dim"])}</g>'
                  f'{text(MONO, name, cx, y + icon + 22, 10, t["fg"] if on else t["dim"], 0, "middle")}</g>')
            n += 1
        y += icon + 34
        if ri < len(ROWS) - 1:
            b += f'<rect x="0" y="{y}" width="{W}" height="1" fill="{t["line"]}"/>'
            y += 26
    legend = text(MONO, "bright = daily drivers", W, y + 16, 10, t["mute"], .4, "end")
    return svg(W, y + 22, b + legend)


OUT.mkdir(exist_ok=True)
for name, t in THEMES.items():
    (OUT / f"header-{name}.svg").write_text(header(t), encoding="utf-8")
    (OUT / f"stack-{name}.svg").write_text(stack(t), encoding="utf-8")
print("built", sorted(p.name for p in OUT.iterdir()))

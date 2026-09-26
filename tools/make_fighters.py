#!/usr/bin/env python3
"""Genera los retratos SVG de los luchadores en assets/.

Todos comparten la misma anatomía (pose de doble bíceps, máscara con volumen,
cinta con el nombre) y cambian colores y rasgos. Ejecutar desde la raíz:

    python3 tools/make_fighters.py
"""
import math
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
W, H = 320, 420

# ---------- piezas reutilizables ----------

MASK = "M160 50C212 50 240 90 238 140C236 186 206 222 160 226C114 222 84 186 82 140C80 90 108 50 160 50Z"
MOUTH_OPENING = "M118 182Q160 168 202 182Q200 222 160 226Q120 222 118 182Z"

EYE_PATCHES = {
    "angular": "M90 146L98 100Q130 106 150 116L154 152Q118 168 90 146Z",
    "flame": "M88 150Q84 126 100 110Q102 124 112 124Q112 104 128 94Q126 112 138 112Q146 106 154 110L154 150Q120 168 88 150Z",
    "wing": "M154 150Q126 166 96 150Q80 140 66 104Q94 118 104 108Q118 116 124 102Q140 114 152 112Z",
    "star": "M92 150L100 124L82 108L112 110L124 90L134 112L152 114L154 150Q122 166 92 150Z",
    "cat": "M154 150Q124 164 98 148Q86 140 72 112Q102 124 118 116Q138 110 152 116Z",
    "fang": "M88 128Q120 104 152 116L154 150L142 142L134 156L124 144L114 158L106 144L92 150Z",
}

EMBLEMS = {
    "diamond": '<path d="M124 262L160 326L196 262L184 350H136Z" fill="{a}" stroke="{o}" stroke-width="5" stroke-linejoin="round"/>'
               '<path d="M160 280L148 304L160 328L172 304Z" fill="{b}"/>',
    "x": '<path d="M130 270L190 340M190 270L130 340" stroke="{o}" stroke-width="22" stroke-linecap="round"/>'
         '<path d="M130 270L190 340M190 270L130 340" stroke="{a}" stroke-width="12" stroke-linecap="round"/>',
    "hourglass": '<path d="M136 274H184L166 308L184 342H136L154 308Z" fill="{a}" stroke="{o}" stroke-width="5" stroke-linejoin="round"/>',
    "horns": '<path d="M114 282Q118 322 160 326Q202 322 206 282Q188 304 160 304Q132 304 114 282Z" fill="{a}" stroke="{o}" stroke-width="5" stroke-linejoin="round"/>'
             '<circle cx="160" cy="316" r="9" fill="none" stroke="{b}" stroke-width="4"/>',
    "flame": '<path d="M160 352Q118 332 128 292Q136 306 146 306Q138 270 162 246Q162 276 178 282Q182 266 194 258Q206 300 188 330Q178 348 160 352Z" fill="{a}" stroke="{o}" stroke-width="5" stroke-linejoin="round"/>'
             '<path d="M160 338Q142 326 148 306Q156 314 162 312Q160 294 172 282Q180 310 174 326Q170 334 160 338Z" fill="{b}"/>',
    "bolt": '<path d="M170 262L136 312H158L146 354L188 298H166L180 262Z" fill="{a}" stroke="{o}" stroke-width="5" stroke-linejoin="round"/>',
    "wings": '<g id="wing-e"><path d="M160 300Q128 274 96 286Q122 296 112 304Q134 308 128 318Q148 316 160 330Z" fill="{a}" stroke="{o}" stroke-width="4" stroke-linejoin="round"/></g>'
             '<use href="#wing-e" transform="translate(320 0) scale(-1 1)"/>'
             '<circle cx="160" cy="306" r="10" fill="{b}" stroke="{o}" stroke-width="4"/>',
    "star": None,  # se genera con star_path
}


def star_path(cx, cy, r_out, r_in, points=5, rot=-90):
    pts = []
    for i in range(points * 2):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(rot + i * 180 / points)
        pts.append(f"{cx + r * math.cos(a):.1f} {cy + r * math.sin(a):.1f}")
    return "M" + "L".join(pts) + "Z"


def sparkle(x, y, s):
    return (f'M{x} {y - s}Q{x + s * .18} {y - s * .18} {x + s} {y}Q{x + s * .18} {y + s * .18} {x} {y + s}'
            f'Q{x - s * .18} {y + s * .18} {x - s} {y}Q{x - s * .18} {y - s * .18} {x} {y - s}Z')


def mirrored(content):
    return f'<g>{content}</g><g transform="translate(320 0) scale(-1 1)">{content}</g>'


def sunburst(color, opacity):
    wedges = []
    cx, cy, r = 160, 150, 460
    for i in range(0, 24, 2):
        a1, a2 = math.radians(i * 15), math.radians((i + 1) * 15)
        wedges.append(f"M{cx} {cy}L{cx + r * math.cos(a1):.0f} {cy + r * math.sin(a1):.0f}"
                      f"L{cx + r * math.cos(a2):.0f} {cy + r * math.sin(a2):.0f}Z")
    return f'<path d="{"".join(wedges)}" fill="{color}" opacity="{opacity}"/>'


# ---------- fondos temáticos ----------

def bg_curtains(c):
    fold = ('<path d="M0 0H74Q52 120 78 240Q48 330 62 420H0Z" fill="url(#curtain)"/>'
            '<path d="M22 0Q12 200 26 420M46 0Q36 200 44 420" stroke="#000" stroke-opacity=".25" stroke-width="5" fill="none"/>')
    return mirrored(fold)


def bg_scanlines(c):
    lines = "".join(f"M0 {y}H320" for y in range(6, 420, 9))
    return (f'<path d="{lines}" stroke="{c["accent"]}" stroke-opacity=".12" stroke-width="2"/>'
            '<circle cx="160" cy="140" r="120" fill="none" stroke="#ff342d" stroke-opacity=".25" stroke-width="3" stroke-dasharray="14 10"/>')


def bg_web(c):
    cx, cy = 160, 140
    spokes = "".join(f"M{cx} {cy}L{cx + 420 * math.cos(math.radians(a)):.0f} {cy + 420 * math.sin(math.radians(a)):.0f}"
                     for a in range(0, 360, 30))
    rings = ""
    for r in (60, 110, 165, 225, 290):
        pts = [f"{cx + r * math.cos(math.radians(a)):.0f} {cy + r * math.sin(math.radians(a)):.0f}" for a in range(0, 360, 30)]
        rings += "M" + "L".join(pts) + "Z"
    return f'<path d="{spokes}{rings}" fill="none" stroke="#fff" stroke-opacity=".16" stroke-width="2"/>'


def bg_smoke(c):
    puffs = [(40, 330, 60), (280, 340, 70), (70, 60, 40), (270, 70, 46), (160, 400, 80)]
    return "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#000" opacity=".22"/>' for x, y, r in puffs)


def bg_flames(c):
    return ('<path d="M44 230Q20 140 70 70Q74 116 100 124Q90 50 138 10Q136 70 160 84Q180 20 222 4Q206 70 226 108Q252 64 270 50Q304 136 276 230Z" fill="url(#aura)" opacity=".9"/>')


def bg_bolts(c):
    bolt = "M0 0L-18 34H-4L-14 64L14 24H0L10 0Z"
    spots = [(40, 60, 1.1, -12), (282, 90, 1.3, 14), (30, 250, .9, 8), (292, 280, 1, -10)]
    return "".join(f'<path d="{bolt}" transform="translate({x} {y}) scale({s}) rotate({r})" fill="#ffd230" opacity=".45"/>'
                   for x, y, s, r in spots)


def bg_streaks(c):
    lines = "".join(f"M{x} 0L{x - 140} 420" for x in range(40, 520, 38))
    return f'<path d="{lines}" stroke="#fff" stroke-opacity=".10" stroke-width="6"/>'


def bg_sparkles(c):
    spots = [(38, 50, 14), (286, 40, 18), (262, 180, 10), (30, 190, 11), (296, 300, 14), (22, 320, 9), (120, 20, 8), (210, 16, 10)]
    return f'<path d="{"".join(sparkle(x, y, s) for x, y, s in spots)}" fill="#fff" opacity=".7"/>'


BACKGROUNDS = {
    "curtains": bg_curtains, "scanlines": bg_scanlines, "web": bg_web, "smoke": bg_smoke,
    "flames": bg_flames, "bolts": bg_bolts, "streaks": bg_streaks, "sparkles": bg_sparkles,
}

# ---------- cuerpo ----------


def arms(c):
    o, skin = c["outline"], "url(#skin)"
    arm = (
        # antebrazo, muñequera y puño
        f'<path d="M40 160C30 190 26 216 30 246L80 240C84 212 88 186 86 160Z" fill="{skin}" stroke="{o}" stroke-width="6" stroke-linejoin="round"/>'
        f'<path d="M36 148Q62 160 90 148L88 170Q62 182 38 170Z" fill="{c["band"]}" stroke="{o}" stroke-width="5" stroke-linejoin="round"/>'
        f'<rect x="32" y="96" width="58" height="54" rx="22" fill="{skin}" stroke="{o}" stroke-width="6"/>'
        f'<path d="M48 99V116M61 97V116M74 99V116M36 128Q58 140 80 126" fill="none" stroke="{o}" stroke-width="4" stroke-linecap="round"/>'
        # brazo con bíceps
        f'<path d="M110 240C92 198 52 194 30 216C12 234 22 266 50 272C74 278 96 276 116 286Z" fill="{skin}" stroke="{o}" stroke-width="6" stroke-linejoin="round"/>'
        f'<path d="M42 214Q64 200 88 212" fill="none" stroke="#fff" stroke-opacity=".35" stroke-width="6" stroke-linecap="round"/>'
        f'<path d="M58 256Q76 262 96 256" fill="none" stroke="{o}" stroke-opacity=".35" stroke-width="4" stroke-linecap="round"/>'
    )
    return mirrored(arm)


def torso(c):
    o = c["outline"]
    pad = c.get("pads", "round")
    out = (f'<path d="M88 250C94 234 124 226 160 226C196 226 226 234 232 250L248 420H72Z" fill="url(#suit)" stroke="{o}" stroke-width="7" stroke-linejoin="round"/>'
           f'<path d="M112 300Q136 320 160 306Q184 320 208 300" fill="none" stroke="{o}" stroke-opacity=".35" stroke-width="5" stroke-linecap="round"/>')
    emblem = c["emblem"]
    if emblem == "star":
        out += (f'<path d="{star_path(160, 306, 44, 19)}" fill="{c["emblem_a"]}" stroke="{o}" stroke-width="5" stroke-linejoin="round"/>'
                f'<path d="{star_path(160, 306, 18, 8)}" fill="{c["emblem_b"]}"/>')
    else:
        out += EMBLEMS[emblem].format(a=c["emblem_a"], b=c["emblem_b"], o=o)
    shoulder = f'<ellipse cx="98" cy="258" rx="32" ry="28" fill="{c["pad"]}" stroke="{o}" stroke-width="6"/>'
    if pad == "spikes":
        shoulder += f'<path d="M72 246L60 222L86 238M92 232L90 206L106 230M112 234L122 212L124 238" fill="{c["pad"]}" stroke="{o}" stroke-width="5" stroke-linejoin="round"/>'
    shoulder += '<ellipse cx="88" cy="250" rx="12" ry="7" fill="#fff" opacity=".35"/>'
    out += mirrored(shoulder)
    return out


def neck(c):
    o = c["outline"]
    return (f'<path d="M120 238Q140 216 138 194H182Q180 216 200 238Q160 256 120 238Z" fill="url(#skin)" stroke="{o}" stroke-width="6" stroke-linejoin="round"/>'
            f'<path d="M136 212Q160 224 184 212" fill="none" stroke="{o}" stroke-opacity=".3" stroke-width="5"/>')

# ---------- cabeza ----------


def eyes(c):
    o = c["outline"]
    if c.get("eyes") == "glow":
        slit = f'<path d="M104 136L148 142L144 152L108 148Z" fill="#ff342d" stroke="#ffb3a8" stroke-width="2"/>'
        return (f'<path d="M86 124Q160 104 234 124L228 158Q160 142 92 158Z" fill="#15171b" stroke="{o}" stroke-width="5" stroke-linejoin="round"/>'
                + mirrored(slit) +
                '<ellipse cx="126" cy="144" rx="30" ry="10" fill="#ff342d" opacity=".35"/>'
                '<ellipse cx="194" cy="144" rx="30" ry="10" fill="#ff342d" opacity=".35"/>')
    eye = (f'<path d="M106 140Q126 122 148 138Q128 154 106 140Z" fill="#fff" stroke="{o}" stroke-width="3"/>'
           f'<circle cx="130" cy="139" r="8" fill="{c["iris"]}"/>'
           '<circle cx="131" cy="139" r="4" fill="#120708"/>'
           '<circle cx="134" cy="136" r="2.2" fill="#fff"/>')
    if c.get("lashes"):
        eye += f'<path d="M106 140L98 132M112 133L106 125M120 128L117 120" stroke="{o}" stroke-width="3" stroke-linecap="round"/>'
    brow = ('M100 124L150 136' if c["side"] == "rudo" else 'M104 124Q126 112 150 124')
    width = 6 if c.get("lashes") else 8
    eye += f'<path d="{brow}" fill="none" stroke="{o}" stroke-width="{width}" stroke-linecap="round"/>'
    return mirrored(eye)


def mouth(c):
    o = c["outline"]
    style = c["mouth"]
    if style == "snarl":
        return (f'<path d="M136 198Q160 188 184 198Q178 216 160 216Q142 216 136 198Z" fill="#6e1020" stroke="{o}" stroke-width="4" stroke-linejoin="round"/>'
                '<path d="M140 199Q160 192 180 199L178 204Q160 199 142 204Z" fill="#fff"/>'
                '<path d="M146 214L150 206L154 214M166 214L170 206L174 214" fill="#fff"/>')
    if style == "grin":
        return (f'<path d="M134 196Q160 222 186 196Q160 206 134 196Z" fill="#fff" stroke="{o}" stroke-width="4" stroke-linejoin="round"/>'
                f'<path d="M140 201Q160 210 180 201" fill="none" stroke="{o}" stroke-opacity=".4" stroke-width="2"/>')
    if style == "lips":
        return (f'<path d="M140 200Q150 192 160 197Q170 192 180 200Q172 214 160 214Q148 214 140 200Z" fill="{c.get("lip", "#c2183b")}" stroke="{o}" stroke-width="3.5" stroke-linejoin="round"/>'
                '<path d="M142 200Q160 205 178 200" fill="none" stroke="#000" stroke-opacity=".3" stroke-width="2"/>'
                '<ellipse cx="166" cy="206" rx="5" ry="2" fill="#fff" opacity=".5"/>')
    if style == "smirk":
        return (f'<path d="M138 204Q156 206 184 192Q176 212 158 212Q144 212 138 204Z" fill="{c.get("lip", "#8b0f2c")}" stroke="{o}" stroke-width="3.5" stroke-linejoin="round"/>')
    if style == "grill":
        return ""
    raise ValueError(style)


def forehead(c):
    o = c["outline"]
    kind = c.get("forehead")
    if kind == "diamond":
        return f'<path d="M160 56L176 94L160 118L144 94Z" fill="{c["accent"]}" stroke="{o}" stroke-width="5" stroke-linejoin="round"/>'
    if kind == "flame":
        return f'<path d="M122 106Q116 76 136 58Q136 82 148 88Q148 56 160 42Q172 56 172 88Q184 82 184 58Q204 76 198 106Q160 94 122 106Z" fill="{c["accent"]}" stroke="{o}" stroke-width="5" stroke-linejoin="round"/>'
    if kind == "star":
        return f'<path d="{star_path(160, 88, 30, 13)}" fill="{c["accent2"]}" stroke="{o}" stroke-width="5" stroke-linejoin="round"/>'
    if kind == "spider":
        legs = "".join(f'M160 {88}L{160 + dx} {88 + dy}' for dx, dy in [(-26, -14), (-30, 0), (-26, 14), (-18, 26), (26, -14), (30, 0), (26, 14), (18, 26)])
        return (f'<path d="{legs}" stroke="{c["accent2"]}" stroke-width="4" stroke-linecap="round"/>'
                f'<ellipse cx="160" cy="78" rx="9" ry="8" fill="{c["accent2"]}"/><ellipse cx="160" cy="96" rx="12" ry="14" fill="{c["accent2"]}"/>'
                '<path d="M155 90H165L161 96L165 102H155L159 96Z" fill="#111"/>')
    if kind == "beak":
        return f'<path d="M160 92L180 118L160 176L140 118Z" fill="{c["accent2"]}" stroke="{o}" stroke-width="5" stroke-linejoin="round"/>'
    if kind == "laces":
        return (f'<path d="M160 54V104" stroke="{o}" stroke-width="4"/>'
                f'<path d="M152 62L168 70M168 62L152 70M152 78L168 86M168 78L152 86M152 94L168 102M168 94L152 102" stroke="{c["accent2"]}" stroke-width="3" stroke-linecap="round"/>')
    return ""


def behind_head(c):
    """Rasgos detrás de la cabeza: pelo largo, coleta, cuernos, alas, cresta, cuello de capa."""
    o = c["outline"]
    out = ""
    for feat in c.get("features", []):
        if feat == "long_hair":
            out += (f'<path d="M90 110C66 180 74 262 56 306Q108 300 122 244H198Q212 300 264 306C246 262 254 180 230 110Z" fill="{c["hair"]}" stroke="{o}" stroke-width="6" stroke-linejoin="round"/>'
                    f'<path d="M84 180Q80 240 70 290M236 180Q240 240 250 290" stroke="#fff" stroke-opacity=".18" stroke-width="5" fill="none"/>')
        if feat == "ponytail":
            out += (f'<path d="M150 58Q158 8 214 14Q254 22 268 64Q240 44 216 48Q248 62 250 98Q224 62 172 62Z" fill="{c["hair"]}" stroke="{o}" stroke-width="6" stroke-linejoin="round"/>'
                    f'<path d="M180 30Q212 22 240 40" stroke="#fff" stroke-opacity=".35" stroke-width="5" fill="none" stroke-linecap="round"/>')
        if feat == "horns":
            out += mirrored(f'<path d="M106 86C80 72 58 44 64 12C76 38 98 52 126 62Z" fill="url(#bone)" stroke="{o}" stroke-width="6" stroke-linejoin="round"/>'
                            f'<path d="M72 36Q86 50 100 56M68 24Q78 34 90 40" stroke="{o}" stroke-opacity=".35" stroke-width="3" fill="none"/>')
        if feat == "wings":
            out += mirrored(f'<path d="M94 100Q40 56 12 84Q42 92 34 110Q62 108 56 128Q78 124 84 144Z" fill="url(#feather)" stroke="{o}" stroke-width="5" stroke-linejoin="round"/>'
                            f'<path d="M30 92Q56 96 74 110M46 112Q64 114 80 126" stroke="{o}" stroke-opacity=".35" stroke-width="3" fill="none"/>')
        if feat == "crest":
            out += (f'<path d="M110 84Q96 40 124 18Q128 50 144 54Q140 16 168 -2Q172 34 188 46Q198 22 216 20Q226 56 210 84Z" fill="url(#aura)" stroke="{o}" stroke-width="5" stroke-linejoin="round"/>')
        if feat == "collar":
            out += mirrored(f'<path d="M100 254Q70 196 98 150Q116 200 138 234Z" fill="{c.get("collar", c["accent2"])}" stroke="{o}" stroke-width="6" stroke-linejoin="round"/>')
        if feat == "bolts":
            out += mirrored(f'<circle cx="84" cy="148" r="11" fill="#9aa0a8" stroke="{o}" stroke-width="5"/><path d="M79 148H89" stroke="{o}" stroke-width="3"/>')
    return out


def head(c):
    o = c["outline"]
    if c.get("bare"):
        return bare_head(c)
    out = (f'<path d="{MASK}" fill="url(#mask)" stroke="{o}" stroke-width="7"/>'
           '<g clip-path="url(#headClip)">'
           '<circle cx="236" cy="204" r="112" fill="#000" opacity=".22"/>'
           '<ellipse cx="124" cy="84" rx="36" ry="17" transform="rotate(-28 124 84)" fill="#fff" opacity=".32"/>'
           '</g>')
    if c.get("mouth") == "grill":
        out += (f'<path d="{MOUTH_OPENING}" fill="#2a2d33" stroke="{o}" stroke-width="5"/>'
                '<path d="M128 192H192M126 202H194M130 212H190" stroke="#8b929c" stroke-width="4" stroke-linecap="round"/>')
    else:
        out += f'<path d="{MOUTH_OPENING}" fill="url(#skin)" stroke="{o}" stroke-width="6"/>'
        out += f'<path d="M150 172Q160 182 170 172" fill="none" stroke="{o}" stroke-opacity=".45" stroke-width="4" stroke-linecap="round"/>'
    out += forehead(c)
    patch = c.get("patch")
    if patch:
        out += mirrored(f'<path d="{EYE_PATCHES[patch]}" fill="{c["accent"]}" stroke="{o}" stroke-width="5" stroke-linejoin="round"/>')
    if c.get("forehead") == "beak":
        out += forehead(c)  # el pico va por encima de los parches
    out += eyes(c)
    out += mouth(c)
    if "nose_ring" in c.get("features", []):
        out += '<circle cx="160" cy="184" r="10" fill="none" stroke="#ffd230" stroke-width="5"/>'
    return out


def bare_head(c):
    """Cara sin máscara (Karla): pelo, flequillo, pintura de guerra."""
    o = c["outline"]
    out = (f'<path d="{MASK}" fill="url(#skin)" stroke="{o}" stroke-width="7"/>'
           '<g clip-path="url(#headClip)"><circle cx="240" cy="206" r="110" fill="#000" opacity=".16"/></g>'
           f'<path d="M84 136Q82 58 160 52Q238 58 236 136Q218 100 188 92Q194 110 182 118Q172 94 146 90Q140 108 122 112Q126 96 118 92Q100 106 84 136Z" fill="{c["hair"]}" stroke="{o}" stroke-width="6" stroke-linejoin="round"/>'
           '<path d="M118 70Q150 58 190 66" stroke="#fff" stroke-opacity=".25" stroke-width="6" fill="none" stroke-linecap="round"/>'
           f'<path d="M104 160L96 176H106L100 192L118 170H108L114 160Z" fill="{c["accent2"]}" stroke="{o}" stroke-width="2.5" stroke-linejoin="round"/>'
           f'<path d="M154 150Q156 166 150 172Q158 176 166 172" fill="none" stroke="{o}" stroke-opacity=".5" stroke-width="3.5" stroke-linecap="round"/>'
           f'<circle cx="84" cy="168" r="9" fill="none" stroke="{c["accent2"]}" stroke-width="4"/>'
           f'<circle cx="236" cy="168" r="9" fill="none" stroke="{c["accent2"]}" stroke-width="4"/>')
    out += eyes(c)
    out += mouth(c)
    return out


def banner(c):
    o = c["outline"]
    name = c["banner"]
    fit = f' textLength="{min(236, 22 * len(name))}" lengthAdjust="spacingAndGlyphs"' if len(name) > 10 else ""
    return (f'<path d="M14 366L40 358V410L14 402L26 384Z" fill="{c["banner_dark"]}" stroke="{o}" stroke-width="5" stroke-linejoin="round"/>'
            f'<path d="M306 366L280 358V410L306 402L294 384Z" fill="{c["banner_dark"]}" stroke="{o}" stroke-width="5" stroke-linejoin="round"/>'
            f'<path d="M34 352Q160 340 286 352V404Q160 392 34 404Z" fill="{c["banner_fill"]}" stroke="{o}" stroke-width="6" stroke-linejoin="round"/>'
            f'<text x="160" y="390" fill="#fff" stroke="{o}" stroke-width="5" paint-order="stroke" stroke-linejoin="round" '
            f'font-family="Impact, Anton, \'Arial Black\', sans-serif" font-weight="900" font-size="30" letter-spacing="1" text-anchor="middle"{fit}>{name}</text>')


def svg(c):
    defs = f'''
  <defs>
    <radialGradient id="bg" cx=".5" cy=".32" r=".8">
      <stop stop-color="{c["bg1"]}"/><stop offset="1" stop-color="{c["bg2"]}"/>
    </radialGradient>
    <radialGradient id="vignette" cx=".5" cy=".42" r=".7">
      <stop offset=".6" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".55"/>
    </radialGradient>
    <radialGradient id="mask" cx=".36" cy=".3" r=".85">
      <stop stop-color="{c["mask1"]}"/><stop offset=".6" stop-color="{c["mask2"]}"/><stop offset="1" stop-color="{c["mask3"]}"/>
    </radialGradient>
    <radialGradient id="skin" cx=".35" cy=".3" r=".9">
      <stop stop-color="{c["skin1"]}"/><stop offset="1" stop-color="{c["skin2"]}"/>
    </radialGradient>
    <linearGradient id="suit" x1="0" y1="0" x2="1" y2="1">
      <stop stop-color="{c["suit1"]}"/><stop offset="1" stop-color="{c["suit2"]}"/>
    </linearGradient>
    <linearGradient id="aura" x1="0" y1="1" x2="0" y2="0">
      <stop stop-color="#ff4d00"/><stop offset=".6" stop-color="#ffb000"/><stop offset="1" stop-color="#fff1a0"/>
    </linearGradient>
    <linearGradient id="bone" x1="0" y1="1" x2="0" y2="0">
      <stop stop-color="#cdbb94"/><stop offset="1" stop-color="#fffaf0"/>
    </linearGradient>
    <linearGradient id="feather" x1="1" y1="0" x2="0" y2="1">
      <stop stop-color="#ffffff"/><stop offset="1" stop-color="#9fb4cc"/>
    </linearGradient>
    <linearGradient id="curtain" x1="0" y1="0" x2="1" y2="0">
      <stop stop-color="#2a0636"/><stop offset=".6" stop-color="#6d1a86"/><stop offset="1" stop-color="#3a0a4a"/>
    </linearGradient>
    <pattern id="dots" width="9" height="9" patternUnits="userSpaceOnUse">
      <circle cx="4.5" cy="4.5" r="1.6" fill="#fff"/>
    </pattern>
    <clipPath id="headClip"><path d="{MASK}"/></clipPath>
  </defs>'''
    body = (
        '<rect width="320" height="420" fill="url(#bg)"/>'
        + sunburst("#fff", .07)
        + '<rect width="320" height="420" fill="url(#dots)" opacity=".08"/>'
        + BACKGROUNDS[c["background"]](c)
        + '<rect width="320" height="420" fill="url(#vignette)"/>'
        + arms(c)
        + torso(c)
        + behind_head(c)
        + neck(c)
        + '<ellipse cx="160" cy="232" rx="60" ry="12" fill="#000" opacity=".25"/>'
        + head(c)
        + banner(c)
    )
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title">\n'
            f'  <title id="title">{c["title"]}</title>{defs}\n  {body}\n</svg>\n')


# ---------- el elenco ----------

FIGHTERS = {
    "enmascarado-de-terciopelo": dict(
        title="El Enmascarado de Terciopelo", banner="TERCIOPELO", side="rudo",
        bg1="#1f7f86", bg2="#1a0826", background="curtains",
        mask1="#5fe3d6", mask2="#138a88", mask3="#08474d", accent="#ff7a1a", accent2="#ffd230",
        skin1="#ffd9b3", skin2="#d9a57c", suit1="#8b35b0", suit2="#2d0c40", pad="#138a88", band="#ff7a1a",
        outline="#0d1f2a", iris="#ffcf1a", patch="angular", forehead="diamond", mouth="snarl",
        emblem="diamond", emblem_a="#ff7a1a", emblem_b="#5fe3d6", features=["collar"], collar="#ff7a1a",
        banner_fill="#8b35b0", banner_dark="#4a1463"),
    "el-exterminador": dict(
        title="El Exterminador", banner="EXTERMINADOR", side="rudo",
        bg1="#6b0f18", bg2="#0b0b0e", background="scanlines",
        mask1="#f4f6f8", mask2="#9aa0a8", mask3="#3d4148", accent="#ff342d", accent2="#efb72d",
        skin1="#e0a27a", skin2="#9c6242", suit1="#34383e", suit2="#101114", pad="#6c727b", pads="spikes", band="#ff342d",
        outline="#0a0a0c", iris="#ff342d", eyes="glow", mouth="grill",
        emblem="x", emblem_a="#ff342d", emblem_b="#fff", features=["bolts"],
        banner_fill="#b3121f", banner_dark="#5c0910"),
    "la-viuda-negra": dict(
        title="La Viuda Negra", banner="VIUDA NEGRA", side="rudo",
        bg1="#4a1a6b", bg2="#07030c", background="web",
        mask1="#5b5566", mask2="#1d1a24", mask3="#060508", accent="#8e2bd6", accent2="#e2182d",
        skin1="#ffe1cc", skin2="#d9a98c", suit1="#2a2233", suit2="#050407", pad="#e2182d", band="#8e2bd6",
        outline="#050308", iris="#b44dff", patch="cat", forehead="spider", mouth="smirk", lip="#9e0f2e", lashes=True,
        emblem="hourglass", emblem_a="#e2182d", emblem_b="#fff", features=["long_hair"], hair="#141018",
        banner_fill="#e2182d", banner_dark="#6e0916"),
    "el-toro-salvaje": dict(
        title="El Toro Salvaje", banner="TORO SALVAJE", side="rudo",
        bg1="#b3361a", bg2="#1c0503", background="smoke",
        mask1="#6a2b24", mask2="#2a0c09", mask3="#0c0302", accent="#e0261b", accent2="#ffd230",
        skin1="#c98a60", skin2="#7a4a2e", suit1="#8f1d12", suit2="#2b0704", pad="#2a0c09", pads="spikes", band="#ffd230",
        outline="#120403", iris="#ff5a1a", patch="fang", forehead="laces", mouth="snarl",
        emblem="horns", emblem_a="#ffd230", emblem_b="#ffd230", features=["horns", "nose_ring"],
        banner_fill="#c7261a", banner_dark="#5e0f09"),
    "golden-fire": dict(
        title="Golden Fire", banner="GOLDEN FIRE", side="tecnico",
        bg1="#ff9a1f", bg2="#3a0a0a", background="flames",
        mask1="#ffd66b", mask2="#ff8a12", mask3="#b8420b", accent="#ffe14a", accent2="#ffd230",
        skin1="#f5c49a", skin2="#c98a60", suit1="#ffd230", suit2="#c77700", pad="#ff8a12", band="#d9263f",
        outline="#5c1406", iris="#ff7a00", patch="flame", forehead="flame", mouth="grin",
        emblem="flame", emblem_a="#d9263f", emblem_b="#ffe14a", features=["crest"],
        banner_fill="#e0520b", banner_dark="#7a2206"),
    "karla": dict(
        title="Karla", banner="KARLA", side="tecnico", bare=True,
        bg1="#11a3b8", bg2="#1d0a3a", background="bolts",
        mask1="#000", mask2="#000", mask3="#000", accent="#ffd230", accent2="#ffd230",
        skin1="#e0a07a", skin2="#a8663f", suit1="#ffd230", suit2="#e64b25", pad="#e64b25", band="#ffd230",
        outline="#1e0e24", iris="#4a2a14", mouth="lips", lip="#c2183b", lashes=True,
        emblem="bolt", emblem_a="#ffd230", emblem_b="#fff", features=["long_hair"], hair="#241126",
        banner_fill="#e64b25", banner_dark="#7a2310"),
    "halcon-plateado": dict(
        title="Halcón Plateado", banner="HALCÓN PLATEADO", side="tecnico",
        bg1="#4fb3ff", bg2="#0a1d4a", background="streaks",
        mask1="#ffffff", mask2="#b9c6d6", mask3="#5d6f86", accent="#1f6fe0", accent2="#ffc21a",
        skin1="#f3c29a", skin2="#b97d56", suit1="#2f8cff", suit2="#0b2d6b", pad="#d7e0ea", band="#ffc21a",
        outline="#08142e", iris="#1f6fe0", patch="wing", forehead="beak", mouth="grin",
        emblem="wings", emblem_a="#e6edf5", emblem_b="#ffc21a", features=["wings"],
        banner_fill="#1f6fe0", banner_dark="#0b3276"),
    "estrella-fugaz": dict(
        title="Estrella Fugaz", banner="ESTRELLA FUGAZ", side="tecnico",
        bg1="#ff5fc8", bg2="#2a0b52", background="sparkles",
        mask1="#ff9be0", mask2="#e0249c", mask3="#7a0b58", accent="#f4f6ff", accent2="#ffd230",
        skin1="#ffd9c0", skin2="#d9a07e", suit1="#ff4fb8", suit2="#6a1aa8", pad="#f4f6ff", band="#ffd230",
        outline="#2a0730", iris="#2fb6ff", patch="star", forehead="star", mouth="lips", lip="#ff2f6d", lashes=True,
        emblem="star", emblem_a="#ffd230", emblem_b="#fff7c2", features=["ponytail"], hair="#ffd230",
        banner_fill="#d61f9a", banner_dark="#6a0c4c"),
}

if __name__ == "__main__":
    for filename, config in FIGHTERS.items():
        (ASSETS / f"{filename}.svg").write_text(svg(config), encoding="utf-8")
        print("escrito", filename)

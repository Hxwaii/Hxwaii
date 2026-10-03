from html import escape
from pathlib import Path

OUT = Path(__file__).parent / "assets"
FONT = "ui-monospace,'JetBrains Mono','Cascadia Code','SF Mono',Menlo,Consolas,'Liberation Mono',monospace"

BG = "#0A0D12"
BAR = "#11161D"
LINE = "#262C36"
TEXT = "#C9D1D9"
DIM = "#6E7681"
GREEN = "#3FB950"
BLUE = "#58A6FF"
MINT = "#4ADE80"
CYAN = "#22D3EE"
AMBER = "#E3B341"
OFF = "#2A313B"
RED = "#F85149"

PROMPT = [("donnie@homelab", GREEN, 700), (":", TEXT), ("~", BLUE, 700), ("$", TEXT)]
PROMPT_LEN = len("donnie@homelab:~$ ")


def esc(s):
    return escape(s, quote=True)


def svg(w, h, title, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'font-family="{FONT}" role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>{body}</svg>\n'
    )


def grid(x0, y, segs, fs, cw=None, extra=""):
    cw = cw or fs * 0.6
    parts, col = [], 0
    for seg in segs:
        text, fill = seg[0], seg[1]
        weight = f' font-weight="{seg[2]}"' if len(seg) > 2 else ""
        i = 0
        while i < len(text):
            if text[i] == " ":
                i += 1
                continue
            j = i
            while j < len(text) and text[j] != " ":
                j += 1
            word = text[i:j]
            parts.append(
                f'<tspan x="{x0 + (col + i) * cw:.1f}" textLength="{len(word) * cw:.1f}" '
                f'lengthAdjust="spacing" fill="{fill}"{weight}>{esc(word)}</tspan>'
            )
            i = j
        col += len(text)
    return f'<text y="{y}" font-size="{fs}"{extra}>{"".join(parts)}</text>'


def hidden_until(t):
    return f'<set attributeName="opacity" to="0" begin="0s" dur="{t:.2f}s"/>' if t > 0 else ""


def fade_in(t, d=0.25):
    total = t + d
    return (
        f'<animate attributeName="opacity" values="0;0;1" keyTimes="0;{t / total:.4f};1" '
        f'dur="{total:.2f}s" fill="freeze"/>'
    )


def steps(start, n, step, x0, cw):
    times = [0] + [start + i * step for i in range(n)]
    vals = [x0] + [x0 + (i + 1) * cw for i in range(n)]
    total = times[-1] + step
    kt = ";".join(f"{t / total:.4f}" for t in times)
    return kt, vals, total


def typed_line(uid, x0, y, fs, prompt_t, cmd, t0, hide_t, step=0.075, cw=None):
    cw = cw or fs * 0.6
    cx = x0 + PROMPT_LEN * cw
    n = len(cmd)
    kt, xs, total = steps(t0, n, step, cx, cw)
    widths = ";".join(f"{x - cx + (1 if i else 0):.1f}" for i, x in enumerate(xs))
    clip = (
        f'<clipPath id="{uid}"><rect x="{cx - 1:.1f}" y="{y - fs:.1f}" width="{n * cw + 2:.1f}" height="{fs * 1.6:.1f}">'
        f'<animate attributeName="width" values="{widths}" keyTimes="{kt}" calcMode="discrete" '
        f'dur="{total:.2f}s" fill="freeze"/></rect></clipPath>'
    )
    prompt = grid(x0, y, PROMPT, fs, cw).replace("</text>", hidden_until(prompt_t) + "</text>")
    command = f'<g clip-path="url(#{uid})">{grid(cx, y, [(cmd, TEXT, 700)], fs, cw)}</g>'
    xv = ";".join(f"{x:.1f}" for x in xs)
    cursor = (
        f'<rect x="{cx:.1f}" y="{y - fs * 0.86:.1f}" width="{cw:.1f}" height="{fs * 1.12:.1f}" fill="{MINT}" opacity="0">'
        f'<set attributeName="opacity" to="0.9" begin="{prompt_t:.2f}s" dur="{hide_t - prompt_t:.2f}s"/>'
        f'<animate attributeName="x" values="{xv}" keyTimes="{kt}" calcMode="discrete" dur="{total:.2f}s" fill="freeze"/></rect>'
    )
    return clip, prompt + command + cursor


def window(w, h, title, bar=36, right=None):
    dots = "".join(
        f'<circle cx="{18 + i * 18}" cy="{bar / 2}" r="5.5" fill="{c}"/>'
        for i, c in enumerate(["#FF5F57", "#FEBC2E", "#28C840"])
    )
    right_txt = ""
    if right:
        right_txt = (
            f'<text x="{w - 32}" y="{bar / 2 + 4}" font-size="12" fill="{DIM}" text-anchor="end">{esc(right)}</text>'
            f'<path d="M{w - 25} {bar / 2 + 3} l7 -7 M{w - 23} {bar / 2 - 4} h5 v5" stroke="{DIM}" stroke-width="1.4" fill="none" stroke-linecap="round"/>'
        )
    return (
        f'<defs><clipPath id="win"><rect width="{w}" height="{h}" rx="10"/></clipPath>'
        f'<pattern id="scan" width="4" height="3" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#fff" opacity="0.022"/></pattern></defs>'
        f'<g clip-path="url(#win)"><rect width="{w}" height="{h}" fill="{BG}"/>'
        f'<rect width="{w}" height="{bar}" fill="{BAR}"/><path d="M0 {bar}.5 H{w}" stroke="{LINE}"/></g>'
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="10" fill="none" stroke="{LINE}"/>'
        f"{dots}"
        f'<text x="{w / 2}" y="{bar / 2 + 4}" font-size="12.5" fill="{DIM}" text-anchor="middle">{esc(title)}</text>'
        f"{right_txt}"
    )


def scanlines(w, h, bar=36):
    return f'<rect x="1" y="{bar + 1}" width="{w - 2}" height="{h - bar - 2}" fill="url(#scan)" pointer-events="none"/>'


def duration(seconds):
    d, rest = divmod(int(seconds), 86400)
    h, rest = divmod(rest, 3600)
    return f"{d}d {h}h" if d else f"{h}h {rest // 60}m"


def neofetch(live=None):
    w, h, fs = 840, 400, 14
    x0 = 28
    defs, body = [], []
    clip, line = typed_line("t1", x0, 72, 15, 0.0, "neofetch", 0.4, 1.1)
    defs.append(clip)
    body.append(line)
    t_out = 1.15

    rx, ry, rw = 34, 94, 238
    unit, gap = 17, 3
    rail = 15
    inner_x, inner_w = rx + rail, rw - 2 * rail
    rack_h = 8 + 13 * (unit + gap) + 5
    rack = [
        f'<rect x="{rx}" y="{ry}" width="{rw}" height="{rack_h}" rx="4" fill="#0E1218" stroke="{LINE}"/>',
        f'<rect x="{rx}" y="{ry}" width="{rail}" height="{rack_h}" rx="3" fill="#141920" stroke="{LINE}"/>',
        f'<rect x="{rx + rw - rail}" y="{ry}" width="{rail}" height="{rack_h}" rx="3" fill="#141920" stroke="{LINE}"/>',
    ]
    for k in range(13):
        uy = ry + 8 + k * (unit + gap)
        for hx in (rx + rail / 2, rx + rw - rail / 2):
            rack.append(f'<rect x="{hx - 2.5}" y="{uy + 3}" width="5" height="5" rx="1" fill="#06080B"/>')
            rack.append(f'<rect x="{hx - 2.5}" y="{uy + 10}" width="5" height="5" rx="1" fill="#06080B"/>')

    sy = ry + 8
    rack.append(f'<rect x="{inner_x + 2}" y="{sy}" width="{inner_w - 4}" height="{unit}" rx="2" fill="#12171E" stroke="{LINE}"/>')
    rack.append(f'<text x="{inner_x + 9}" y="{sy + 12}" font-size="8.5" fill="{DIM}">sw</text>')
    for p in range(24):
        col, row = p // 2, p % 2
        px = inner_x + 30 + col * 11.5
        py = sy + 3.5 + row * 6
        rack.append(f'<rect x="{px:.1f}" y="{py}" width="8" height="4.5" rx="0.8" fill="#06080B" stroke="#2C333D" stroke-width="0.6"/>')
        if p in (0, 1, 2, 3, 5, 9):
            d = 0.35 + (p * 0.173) % 0.6
            rack.append(
                f'<rect x="{px + 5.5:.1f}" y="{py + 1}" width="1.8" height="1.8" fill="{GREEN}">{hidden_until(t_out)}'
                f'<animate attributeName="opacity" values="1;0.2;1;1;0.3;1" dur="{d:.2f}s" begin="{t_out:.2f}s" repeatCount="indefinite"/></rect>'
            )
    rack.append(f'<circle cx="{inner_x + inner_w - 12}" cy="{sy + unit / 2}" r="2.6" fill="{GREEN}"/>')

    roles = {1: ("k3s", GREEN), 2: ("k3s", GREEN), 3: ("k3s", GREEN), 4: ("pve", CYAN)}
    up = {n: (live["up"].get(n, False) if live else True) for n in roles}
    for n in range(1, 13):
        uy = ry + 8 + n * (unit + gap)
        online = n in roles and up[n]
        down = n in roles and not up[n]
        rack.append(f'<rect x="{inner_x + 2}" y="{uy}" width="{inner_w - 4}" height="{unit}" rx="2" fill="{"#161C24" if n in roles else "#11151B"}" stroke="{LINE}"/>')
        label = TEXT if online else ("#C9787A" if down else "#4A525D")
        rack.append(f'<text x="{inner_x + 9}" y="{uy + 12}" font-size="8.5" fill="{label}">node-{n:02d}</text>')
        for v in range(12):
            vx = inner_x + 70 + v * 5
            rack.append(f'<rect x="{vx}" y="{uy + 5}" width="2" height="7" rx="1" fill="#0B0E13"/>')
        if down:
            rack.append(f'<text x="{inner_x + 142}" y="{uy + 12}" font-size="8.5" font-weight="700" fill="{RED}">down</text>')
            rack.append(
                f'<circle cx="{inner_x + inner_w - 12}" cy="{uy + unit / 2}" r="3" fill="{RED}">'
                f'<animate attributeName="opacity" values="1;0.25;1" dur="1.2s" repeatCount="indefinite"/></circle>'
            )
        elif online:
            tag, color = roles[n]
            t_on = t_out + 0.15 + n * 0.18
            rack.append(f'<text x="{inner_x + 142}" y="{uy + 12}" font-size="8.5" font-weight="700" fill="{color}">{tag}{fade_in(t_on, 0.2)}</text>')
            act = 0.7 + (n * 0.37) % 0.9
            rack.append(
                f'<circle cx="{inner_x + inner_w - 22}" cy="{uy + unit / 2}" r="1.8" fill="{AMBER}" opacity="0">'
                f'<animate attributeName="opacity" values="0;0.9;0;0;0.8;0;0.9;0" dur="{act:.2f}s" begin="{t_on:.2f}s" repeatCount="indefinite"/></circle>'
            )
            breathe = 2.2 + (n * 0.41) % 1.3
            rack.append(
                f'<circle cx="{inner_x + inner_w - 12}" cy="{uy + unit / 2}" r="3" fill="{color}">'
                f'<set attributeName="fill" to="{OFF}" begin="0s" dur="{t_on:.2f}s"/>'
                f'<animate attributeName="opacity" values="1;0.45;1" dur="{breathe:.2f}s" begin="{t_on:.2f}s" repeatCount="indefinite"/></circle>'
            )
        else:
            rack.append(f'<circle cx="{inner_x + inner_w - 12}" cy="{uy + unit / 2}" r="3" fill="{OFF}"/>')
    body.append(f"<g>{''.join(rack)}</g>")

    ix, lh = 306, 23
    if live:
        n_up = sum(up.values())
        k_up = sum(up[n] for n in (1, 2, 3))
        pve = live.get("pve")
        info = [
            ("Rack", [("42U · 12x HP EliteDesk 800 G1", TEXT)]),
            ("Online", [(f"{n_up} / 12 nodes", GREEN if n_up == len(roles) else AMBER, 700)]),
            ("Cluster", [("k3s HA · ", TEXT), (f"{k_up}/3", GREEN if k_up == 3 else RED, 700), (" nodes reachable", TEXT)]),
            ("Proxmox", [("node-04 · up ", TEXT), (duration(pve["uptime"]) if pve else "n/a", CYAN, 700)]),
            ("Load", [(f"CPU {pve['cpu'] * 100:.0f}% · RAM {pve['mem'] * 100:.0f}%" if pve else "n/a", TEXT)]),
            ("CPU", [("i5-4570S · 4 cores · 8 GB each", TEXT)]),
            ("Database", [("CloudNativePG · Postgres x3", TEXT)]),
            ("Ingress", [("Cloudflare Tunnel → Traefik", TEXT)]),
            ("Failover", [("~60 s · tested by pulling the plug", TEXT)]),
            ("Mounts", [("3D-printed EliteDesk sleeves", TEXT)]),
        ]
    else:
        info = [(k, [(v, TEXT)]) for k, v in [
            ("Rack", "42U · 12x HP EliteDesk 800 G1"),
            ("Online", "4 / 12 nodes"),
            ("CPU", "i5-4570S · 4 cores · 8 GB each"),
            ("Cluster", "k3s HA · 3 servers · embedded etcd"),
            ("Database", "CloudNativePG · Postgres x3"),
            ("Virt", "Proxmox VE 9 · private game hosting"),
            ("Ingress", "Cloudflare Tunnel → Traefik"),
            ("Failover", "~60 s · tested by pulling the plug"),
            ("Switch", "D-Link DGS-1224T · 24x GbE"),
            ("Mounts", "3D-printed EliteDesk sleeves"),
        ]]
    rows = [
        [("donnie", MINT, 700), ("@", TEXT), ("homelab", MINT, 700)],
        [("─" * 14, DIM)],
    ] + [[(f"{k:<10}", MINT, 700)] + v for k, v in info]
    for i, segs in enumerate(rows):
        body.append(grid(ix, 108 + i * lh, segs, fs).replace("</text>", hidden_until(t_out + i * 0.035) + "</text>"))
    by = 108 + len(rows) * lh - 6
    blocks = ["#21262D", "#F85149", GREEN, "#D29922", BLUE, "#BC8CFF", "#39C5CF", TEXT]
    for i, c in enumerate(blocks):
        body.append(f'<rect x="{ix + i * 30}" y="{by}" width="26" height="14" rx="2" fill="{c}">{hidden_until(t_out + 0.45)}</rect>')

    if live:
        stamp = f"live · {live['stamp']}"
        sx = w - 18 - len(stamp) * 7.2
        body.append(
            f'<circle cx="{sx - 10:.1f}" cy="18" r="6" fill="{GREEN}" opacity="0">'
            f'<animate attributeName="r" values="3;8" dur="1.8s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0.5;0" dur="1.8s" repeatCount="indefinite"/></circle>'
            f'<circle cx="{sx - 10:.1f}" cy="18" r="3.5" fill="{GREEN}"/>'
            + grid(sx, 22, [("live", GREEN, 700), (f" · {live['stamp']}", DIM)], 12)
        )

    return svg(w, h, "neofetch of Donnie's homelab: 42U rack with 12 HP EliteDesk nodes, k3s HA cluster and Proxmox",
               window(w, h, "donnie@homelab: ~ — neofetch") + f"<defs>{''.join(defs)}</defs>" + "".join(body) + scanlines(w, h))


def main():
    OUT.mkdir(exist_ok=True)
    (OUT / "neofetch.svg").write_text(neofetch(), encoding="utf-8")
    print(f"neofetch.svg -> {OUT}")


if __name__ == "__main__":
    main()

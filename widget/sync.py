import json
import os
import re
import sys
import urllib.error
import urllib.request
from html import unescape
from pathlib import Path

HERE = Path(__file__).resolve().parent
README = HERE.parent / "README.md"
API = "https://discord.com/api/v9"
UA = "DiscordBot (https://github.com/Hxwaii/Hxwaii, 1.0)"
LIMIT = 100
MAX_FIELDS = 30
STRING, NUMBER, MEDIA = 1, 2, 3


def load_env():
    env = HERE / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip("\"'"))


def text(s):
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def clip(s, n=LIMIT):
    if len(s) <= n:
        return s
    cut = s[:n]
    best = max(
        (m.start() for m in re.finditer(r", |; | · | - | \(", cut)
         if m.start() > n // 3 and cut[: m.start()].count("(") <= cut[: m.start()].count(")")),
        default=0,
    )
    if best:
        return cut[:best]
    return cut[: cut.rfind(" ")].rstrip(",;") + "…"


def joined(items):
    out = []
    for item in items:
        if len(" · ".join(out + [item])) > LIMIT:
            break
        out.append(item)
    return " · ".join(out)


def sections(md):
    parts = re.split(r"<h2[^>]*>(.*?)</h2>", md, flags=re.S)
    return {slug(text(parts[i])): parts[i + 1] for i in range(1, len(parts) - 1, 2)}


def github(user):
    req = urllib.request.Request(f"https://api.github.com/users/{user}", headers={"User-Agent": UA})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.load(r)
        return data.get("name") or user, data["avatar_url"] + "&s=256"
    except (urllib.error.URLError, KeyError, ValueError):
        return user, f"https://github.com/{user}.png?size=256"


def fields(md, user):
    out = []

    def add(name, value, kind=STRING):
        if value in (None, ""):
            return
        if kind == STRING:
            value = clip(str(value))
        elif kind == MEDIA:
            value = {"url": value}
        out.append({"type": kind, "name": name, "value": value})

    sec = sections(md)
    name, avatar = github(user)
    add("name", name)
    add("avatar", avatar, MEDIA)

    about = sec.get("about_me", "")
    lines = [text(x) for x in re.split(r"<br\s*/?>", re.sub(r"</?p[^>]*>", "", about)) if text(x)]
    if lines:
        add("tagline", lines[0].rstrip("."))
        add("about", " ".join(lines[1:]).rstrip("."))

    for label, alt in re.findall(r"<b>(.*?)</b></td>\s*<td>\s*<img[^>]*alt=\"([^\"]*)\"", sec.get("tech_stack", ""), re.S):
        items = [x.strip() for x in alt.split(",") if x.strip()]
        key = slug(text(label))
        add(key, joined(items))
        add(f"{key}_count", len(items), NUMBER)

    projects = [
        (re.sub(r"^\W+", "", text(n)), text(d))
        for n, d in re.findall(r"<tr>\s*<td[^>]*><b>(.*?)</b></td>\s*<td>(.*?)</td>", sec.get("projects", ""), re.S)
    ]
    if projects:
        add("projects", joined([n for n, _ in projects]))
        add("projects_count", len(projects), NUMBER)
        for i, (n, d) in enumerate(projects, 1):
            add(f"project_{i}", n)
            add(f"project_{i}_desc", d)

    lab = re.search(r"alt=\"([^\"]+)\"", sec.get("homelab", ""))
    if lab:
        summary = lab.group(1).split(": ", 1)[-1]
        add("homelab", summary)
        nodes = re.search(r"(\d+)\s+[^,]*?\bnodes\b", summary)
        if nodes:
            add("homelab_nodes", int(nodes.group(1)), NUMBER)

    for href, alt in re.findall(r"<a href=\"([^\"]+)\"><img src=\"https://img\.shields\.io/[^\"]*\" alt=\"([^\"]+)\"", md):
        add(slug(alt), re.sub(r"^https?://(www\.)?", "", href).rstrip("/"))
    add("github", f"github.com/{user}")

    if len(out) > MAX_FIELDS:
        dropped = ", ".join(f["name"] for f in out[MAX_FIELDS:])
        print(f"warning: more than {MAX_FIELDS} fields, dropping {dropped}", file=sys.stderr)
    return out[:MAX_FIELDS]


def show(data):
    width = max(len(f["name"]) for f in data)
    kinds = {STRING: "text", NUMBER: "number", MEDIA: "image"}
    for f in data:
        value = f["value"]["url"] if f["type"] == MEDIA else f["value"]
        print(f"{f['name']:<{width}}  {kinds[f['type']]:<6}  {value}")


def push(app_id, user_id, token, user, data):
    body = json.dumps({"username": user, "data": {"dynamic": data}}).encode()
    req = urllib.request.Request(
        f"{API}/applications/{app_id}/users/{user_id}/identities/0/profile",
        data=body,
        method="PATCH",
        headers={"Authorization": f"Bot {token}", "Content-Type": "application/json", "User-Agent": UA},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            print(f"discord: {r.status} ok, {len(data)} fields synced")
    except urllib.error.HTTPError as e:
        print(f"discord: {e.code} {e.read().decode(errors='replace')}", file=sys.stderr)
        sys.exit(1)


def main():
    load_env()
    md = README.read_text(encoding="utf-8")
    user = os.environ.get("GITHUB_USER") or os.environ.get("GITHUB_REPOSITORY_OWNER") or "Hxwaii"
    data = fields(md, user)
    show(data)
    if "--dry-run" in sys.argv:
        return

    found = re.search(r"discord\.com/users/(\d+)", md)
    user_id = os.environ.get("DISCORD_USER_ID") or (found and found.group(1))
    app_id = os.environ.get("DISCORD_APP_ID")
    token = os.environ.get("DISCORD_BOT_TOKEN")
    missing = [k for k, v in (("DISCORD_APP_ID", app_id), ("DISCORD_BOT_TOKEN", token), ("DISCORD_USER_ID", user_id)) if not v]
    if missing:
        sys.exit(f"missing {', '.join(missing)} (set them in widget/.env or as env vars)")
    print()
    push(app_id, user_id, token, user, data)


if __name__ == "__main__":
    main()

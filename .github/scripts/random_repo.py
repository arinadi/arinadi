#!/usr/bin/env python3
import json
import os
import random
import re
import urllib.parse
import urllib.request

OWNER = "arinadi"
README = "README.md"
START = "<!-- RANDOM_REPO:START -->"
END = "<!-- RANDOM_REPO:END -->"
TOKEN = os.environ.get("GH_TOKEN", "")


def gh(path):
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "repo-roulette")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def read_last_repo():
    try:
        with open(README, encoding="utf-8") as f:
            m = re.search(
                re.escape(START) + r".*?github\.com/" + OWNER + r"/([A-Za-z0-9_.-]+)",
                f.read(),
                re.S,
            )
        return m.group(1) if m else ""
    except FileNotFoundError:
        return ""


def main():
    repos, page = [], 1
    while True:
        data = gh(f"/users/{OWNER}/repos?per_page=100&page={page}&type=public")
        if not data:
            break
        repos += data
        if len(data) < 100:
            break
        page += 1

    candidates = [
        r
        for r in repos
        if not r["fork"]
        and not r["archived"]
        and r["name"] not in (OWNER, ".github", "arinadi.github.io")
    ]
    if not candidates:
        print("no candidates")
        return

    last = read_last_repo()
    if last in [r["name"] for r in candidates]:
        candidates = [r for r in candidates if r["name"] != last]

    repo = random.choice(candidates)
    name = repo["name"]
    lang = repo.get("language") or "misc"
    stars = repo["stargazers_count"]
    forks = repo["forks_count"]
    desc = (repo.get("description") or "No description, only vibes.").strip()
    desc = re.sub(r"[`*_#<>\[\]]", "", desc)
    if len(desc) > 60:
        desc = desc[:57].rstrip() + "..."

    def shields_escape(s):
        return urllib.parse.quote(s, safe="").replace("-", "--")

    meta = f"{lang} | stars {stars} | forks {forks}"
    badge = (
        "https://img.shields.io/badge/"
        + shields_escape(name)
        + "-"
        + shields_escape(meta)
        + "-0d1117?style=for-the-badge&logo=github&logoColor=00f2ff"
    )
    block = (
        START
        + "\n"
        + '<p align="center">\n'
        + f'  <a href="https://github.com/{OWNER}/{name}">\n'
        + f'    <img src="{badge}" alt="{name}" />\n'
        + "  </a>\n"
        + "</p>\n"
        + f'<p align="center"><i>{desc}</i></p>\n'
        + END
    )

    with open(README, encoding="utf-8") as f:
        content = f.read()
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    new = pattern.sub(block, content)
    if new == content:
        print("no change")
        return
    with open(README, "w", encoding="utf-8") as f:
        f.write(new)
    print(f"updated: {name}")


if __name__ == "__main__":
    main()
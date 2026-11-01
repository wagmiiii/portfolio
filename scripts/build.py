#!/usr/bin/env python3
"""Render the measured blocks of the portfolio page.

`index.html` is hand-written except for the regions between `<!-- NAME:START -->` and
`<!-- NAME:END -->` markers, which this script regenerates from `data/profile.json` (the prose and
the curation) and `data/measured.json` (the counts, written by `scripts/measure.py`). Nothing hits
the network here, so a rebuild is deterministic and a stale number is a diff rather than a surprise.

`--check` writes nothing and exits 1 when a region no longer matches its data, which is the gate
that keeps the page honest after a refresh.
"""

from __future__ import annotations

import argparse
import html
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

BLOCKS = (
    "META",
    "IDENTITY",
    "TELEMETRY",
    "BAND",
    "WORK",
    "OPENSOURCE",
    "STATS",
    "TIMELINE",
    "STACK",
    "CREDENTIALS",
    "PROJECTS",
    "CONTACT",
    "FOOTMETA",
)

EM_DASH = "\u2014"


def subs(measured: dict) -> dict[str, str]:
    """The placeholder map used inside profile prose."""
    orgs = measured["thirdparty_owners"] + len(measured["owned_orgs"])
    return {
        "commits": f"{measured['commits_authored']:,}",
        "merged": f"{measured['merged_enumerated']:,}",
        "repos": str(measured["repos_touched"]),
        "ext": str(measured["thirdparty_repos"]),
        "ext_repos": str(measured["thirdparty_repos"]),
        "ext_prs": str(measured["thirdparty_merged_prs"]),
        "ext_owners": str(measured["thirdparty_owners"]),
        "orgs": str(orgs),
        "authored_repos": str(measured["authored_repos"]),
        "languages": str(measured["languages"]),
        "account_since": str(measured["profile"]["since"]),
        "date": measured["fetched_at"],
        "workspaces": str(measured["workspaces"]),
        "owned_prs": str(measured["owned_org_merged_prs"]),
    }


def fill(text: str, values: dict[str, str]) -> str:
    """Substitute `{name}` placeholders, failing loudly on one that has no value."""
    missing: list[str] = []

    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values:
            missing.append(key)
            return match.group(0)
        return values[key]

    out = re.sub(r"\{([a-z_]+)\}", repl, text)
    if missing:
        raise SystemExit(f"unknown placeholder(s) {sorted(set(missing))} in: {text[:80]}")
    return out


def chips(items: list[str]) -> str:
    return "".join(f'<span class="chip">{html.escape(i)}</span>' for i in items)


def render_meta(profile: dict, measured: dict, values: dict[str, str]) -> str:
    """Head copy is generated like the rest of the page, so its counts cannot drift from the body."""
    meta = profile["identity"]["meta"]
    url = meta["url"].rstrip("/") + "/"
    image = url + meta["image"]
    text = {
        key: html.escape(fill(meta[key], values), quote=True)
        for key in ("title", "description", "og_title", "og_description")
    }
    return "\n".join(
        (
            f"<title>{text['title']}</title>",
            f'<meta name="description" content="{text["description"]}">',
            '<meta name="theme-color" content="#0a0a0a">',
            f'<link rel="canonical" href="{url}">',
            '<meta property="og:type" content="profile">',
            f'<meta property="og:url" content="{url}">',
            f'<meta property="og:title" content="{text["og_title"]}">',
            f'<meta property="og:description" content="{text["og_description"]}">',
            f'<meta property="og:image" content="{image}">',
            '<meta name="twitter:card" content="summary">',
            f'<meta name="twitter:image" content="{image}">',
        )
    )


def render_telemetry(profile: dict, measured: dict, values: dict[str, str]) -> str:
    rows = []
    for row in profile["telemetry"]:
        rows.append(
            '<div class="tel">'
            f'<span class="tel-k">{html.escape(fill(row["k"], values))}</span>'
            f'<span class="tel-v">{html.escape(fill(row["v"], values))}</span>'
            "</div>"
        )
    return "\n".join(rows)


def render_band(profile: dict, measured: dict, values: dict[str, str]) -> str:
    band = profile["band"]
    return (
        f'<span class="band-k">{html.escape(fill(band["kicker"], values))}</span>\n'
        f'      <p class="band-t">{html.escape(fill(band["title"], values))}</p>\n'
        f'      <a class="band-a" href="{html.escape(band["href"])}">'
        f'{html.escape(band["link_text"])} &rarr;</a>'
    )


def render_work(profile: dict, measured: dict, values: dict[str, str]) -> str:
    by_repo = measured["merged_by_repo"]
    latest = measured["latest_by_repo"]
    out = []
    for index, item in enumerate(profile["work"], start=1):
        merged = sum(by_repo.get(r, 0) for r in item["repos"])
        newest = max((latest.get(r, "") for r in item["repos"]), default="")
        if item.get("metrics"):
            metrics = item["metrics"]
        else:
            metrics = [
                {"value": f"{merged:,}", "label": "merged PRs"},
                {"value": str(len(item["repos"])), "label": "repositories"},
                {"value": newest or "n/a", "label": "latest merge"},
            ]
        cells = "\n".join(
            f'        <div><b>{html.escape(m["value"])}</b>'
            f"<span>{html.escape(m['label'])}</span></div>"
            for m in metrics
        )
        links = "\n".join(
            f'          <a href="{html.escape(l["href"])}">{html.escape(l["label"])} &nearr;</a>'
            for l in item["links"]
        )
        repo_links = " ".join(
            f'<a class="chip" href="https://github.com/{html.escape(r)}">{html.escape(r)}</a>'
            for r in item["repos"]
        )
        when = (
            f' <span class="chip">{html.escape(item["when"])}</span>'
            if item.get("when")
            else ""
        )
        # The front-end claim sits directly above the screenshots that evidence it.
        visuals = ""
        if item.get("frontend"):
            visuals += f'\n          <p class="work-body">{html.escape(fill(item["frontend"], values))}</p>'
        if item.get("shots"):
            figures = "\n".join(
                '          <figure class="shot">\n'
                f'            <img src="{html.escape(s["src"])}" loading="lazy" decoding="async"\n'
                f'              alt="{html.escape(s["alt"])}">\n'
                f"            <figcaption>{html.escape(s['cap'])}"
                f"<span>{html.escape(s['repo'])}</span></figcaption>\n"
                "          </figure>"
                for s in item["shots"]
            )
            visuals += f'\n          <div class="shots">\n{figures}\n          </div>'
        out.append(
            f'      <article class="work-item" id="work-{index}">\n'
            "        <div>\n"
            f'          <p class="work-role"><span class="num">[ {index:02d} ]</span> '
            f'{html.escape(fill(item["role"], values))}{when}</p>\n'
            f'          <h3 class="work-title">{html.escape(item["title"])}</h3>\n'
            f'          <p class="work-body">{html.escape(fill(item["description"], values))}</p>{visuals}\n'
            f'          <div class="chips mt">{chips(item["chips"])}</div>\n'
            f'          <p class="work-body">{repo_links}</p>\n'
            "        </div>\n"
            '        <div class="work-side">\n'
            f'          <div class="work-metrics">\n{cells}\n          </div>\n'
            '          <nav class="work-links" aria-label="'
            f'{html.escape(item["title"])} links">\n{links}\n          </nav>\n'
            "        </div>\n"
            "      </article>"
        )
    return "\n".join(out)


def render_timeline(profile: dict, measured: dict, values: dict[str, str]) -> str:
    rows = []
    for group, kind in (("experience", "role"), ("education", "edu"), ("awards", "award")):
        for row in profile[group]:
            tail = "".join(
                "\n        " + part
                for part in (
                    f'<span class="tl-note">{html.escape(row["note"])}</span>'
                    if row.get("note")
                    else "",
                    f'<p class="tl-detail">{html.escape(row["detail"])}</p>'
                    if row.get("detail")
                    else "",
                )
                if part
            )
            rows.append(
                '      <div class="tl-row">\n'
                f'        <span class="tl-when">{html.escape(row["when"])}</span>\n'
                f'        <p class="tl-what">{html.escape(row["what"])}'
                f"<span>{html.escape(row['who'])}</span></p>{tail}\n"
                "      </div>"
            )
    return "\n".join(rows)


def render_stack(profile: dict, measured: dict, values: dict[str, str]) -> str:
    out = []
    for group in profile["stack"]:
        out.append(
            '      <div class="tel tel--chips">\n'
            f'        <span class="tel-k">{html.escape(group["group"])}</span>\n'
            f'        <span class="chips">{chips(group["items"])}</span>\n'
            "      </div>"
        )
    langs = ", ".join(
        f'{l["language"]} ({l["repos"]})' for l in measured["language_counts"]
    )
    out.append(
        '      <div class="tel tel--long">\n'
        '        <span class="tel-k">Detected languages</span>\n'
        f'        <span class="tel-v">{html.escape(langs)}</span>\n'
        "      </div>"
    )
    return "\n".join(out)


def render_projects(profile: dict, measured: dict, values: dict[str, str]) -> str:
    out = []
    for project in profile["extra_projects"]:
        link = (
            f'<a class="card-link" href="{html.escape(project["href"])}">Repository &nearr;</a>'
            if project.get("href")
            else ""
        )
        out.append(
            '      <article class="card">\n'
            f'        <span class="card-k">{html.escape(project["k"])}</span>\n'
            f"        <h3>{html.escape(project['title'])}</h3>\n"
            f'        <p>{html.escape(fill(project["p"], values))}</p>\n'
            f'        <div class="chips">{chips(project["chips"])}</div>\n'
            f"        {link}\n"
            "      </article>"
        )
    return "\n".join(out)


def render_footmeta(profile: dict, measured: dict, values: dict[str, str]) -> str:
    account = html.escape(measured["account"])
    return (
        f'      <p>Counts read from <a href="https://github.com/{account}">'
        f"github.com/{account}</a> on {html.escape(measured['fetched_at'])} by "
        f"<code>scripts/measure.py</code>. Merged pull requests are counted by enumeration "
        f"({measured['merged_enumerated']}); the search endpoint reported "
        f"{measured['merged_reported_total']} at the same minute.</p>"
    )


def render_identity(profile: dict, measured: dict, values: dict[str, str]) -> str:
    ident = profile["identity"]
    kicker = "".join(
        f'<span{" class=\"live\"" if i == 0 else ""}>{html.escape(fill(k, values))}</span>'
        for i, k in enumerate(ident["kicker"])
    )
    first, second = ident["mega"]
    return (
        f'        <p class="kicker">{kicker}</p>\n'
        '        <h1 class="mega" id="page-title">'
        f"<span>{html.escape(first)}</span>"
        f'<span class="accent">{html.escape(second)}</span>'
        '<span class="cursor" aria-hidden="true"></span></h1>\n'
        f'        <p class="lede">{html.escape(fill(ident["lede"], values))}</p>'
    )


def render_opensource(profile: dict, measured: dict, values: dict[str, str]) -> str:
    return "\n".join(
        f"        <p>{html.escape(fill(paragraph, values))}</p>"
        for paragraph in profile["opensource"]["paras"]
    )


def render_stats(profile: dict, measured: dict, values: dict[str, str]) -> str:
    cells = [
        (measured["thirdparty_merged_prs"], "Merged pull requests"),
        (measured["thirdparty_repos"], "Repositories I do not own"),
        (measured["thirdparty_owners"], "Organizations and owners"),
    ]
    return "\n".join(
        f'        <div class="stat"><b>{value}</b><span>{label}</span></div>'
        for value, label in cells
    )


def render_credentials(profile: dict, measured: dict, values: dict[str, str]) -> str:
    out = []
    for cred in profile["credentials"]:
        valid = f"Valid to {cred['expires']}" if cred.get("expires") else "No expiry listed"
        out.append(
            '      <article class="card">\n'
            f'        <span class="card-k">{html.escape(cred["issuer"])} badge</span>\n'
            f"        <h3>{html.escape(cred['title'])}</h3>\n"
            f'        <p>Earned {html.escape(cred["earned"])}. {html.escape(valid)}.</p>\n'
            f'        <a class="card-link" href="{html.escape(cred["href"])}">'
            "Verify at Microsoft Learn &nearr;</a>\n"
            "      </article>"
        )
    return "\n".join(out)


def render_contact(profile: dict, measured: dict, values: dict[str, str]) -> str:
    out = []
    for cell in profile["contact"]["cells"]:
        is_email = cell.get("copy") == "email"
        id_attr = ' id="contact-email"' if is_email else ""
        value = (
            f'<a class="lv" href="{html.escape(cell["href"])}">{html.escape(cell["lv"])}</a>'
            if cell.get("href")
            else f'<span class="lv"{id_attr}>{html.escape(cell["lv"])}</span>'
        )
        button = (
            '<button class="copy js-only" type="button" data-copy="contact-email">'
            "Copy address</button>"
            if is_email
            else ""
        )
        out.append(
            "      <div class=\"contact-cell\">\n"
            + "        "
            + "\n        ".join(
                part
                for part in (
                    f'<span class="lk">{html.escape(cell["lk"])}</span>',
                    value,
                    button,
                )
                if part
            )
            + "\n      </div>"
        )
    return "\n".join(out)


RENDERERS = {
    "META": render_meta,
    "IDENTITY": render_identity,
    "TELEMETRY": render_telemetry,
    "BAND": render_band,
    "WORK": render_work,
    "OPENSOURCE": render_opensource,
    "STATS": render_stats,
    "TIMELINE": render_timeline,
    "STACK": render_stack,
    "CREDENTIALS": render_credentials,
    "PROJECTS": render_projects,
    "CONTACT": render_contact,
    "FOOTMETA": render_footmeta,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify the page without writing it")
    args = parser.parse_args(argv)

    profile = json.loads((ROOT / "data" / "profile.json").read_text())
    measured = json.loads((ROOT / "data" / "measured.json").read_text())
    values = subs(measured)
    page = ROOT / "index.html"
    text = page.read_text()

    stale: list[str] = []
    for name in BLOCKS:
        start, end = f"<!-- {name}:START -->", f"<!-- {name}:END -->"
        if start not in text or end not in text:
            raise SystemExit(f"index.html is missing the {name} markers")
        body = RENDERERS[name](profile, measured, values)
        text = re.sub(
            re.escape(start) + r"\n?.*?\n?" + re.escape(end),
            lambda m, b=body: start + "\n" + b + "\n" + end,
            text,
            count=1,
            flags=re.S,
        )

    for problem in (c for c in text if ord(c) > 126 and c != EM_DASH):
        raise SystemExit(f"non-ASCII character {problem!r} in the generated page")
    if EM_DASH in text:
        raise SystemExit("em dash in the generated page")
    if re.search(r"\{[a-z_]+\}", re.sub(r"<pre>.*?</pre>", "", text, flags=re.S)):
        raise SystemExit("an unsubstituted placeholder survived into the page")

    if args.check:
        current = (ROOT / "index.html").read_text()
        if current != text:
            print("index.html is stale; run scripts/build.py", file=sys.stderr)
            return 1
        print("index.html matches its data")
        return 0

    page.write_text(text)
    print("index.html regenerated from data/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

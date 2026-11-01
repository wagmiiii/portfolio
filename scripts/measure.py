#!/usr/bin/env python3
"""Refresh the measured numbers behind the portfolio from the GitHub API.

Writes `data/measured.json`. Every count the site publishes comes from here, and the file records
the query that produced it along with the fetch date, so a number on the page can be checked
rather than taken on trust.

`--cache-dir` reads saved API responses instead of the network, which is how the site rebuilds
offline or inside CI without spending the rate limit. `--refresh` in combination with it refetches
every response and overwrites the saved one, so the recorded provenance and the numbers move
together. Unauthenticated requests allow 60 core calls an hour and 10 search calls a minute; a full
refresh is 3 core and 8 search, so one fits and a second in the same hour does not.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import pathlib
import sys
import urllib.request

ACCOUNT = "wagmiiii"
# Orgs this account owns or co-owns. Merged pull requests in these repositories are shipped work,
# not community contributions, and the site counts them separately.
OWNED_ORGS = {"accensa", "Tollcraft", "StaffPurse"}
USER_AGENT = "portfolio-measure"


class Responses:
    """Named API responses: read from disk when recorded, from the network when not.

    With `refresh` every response is refetched and written back over the recorded copy, so the
    saved provenance and the numbers published from it cannot drift apart.
    """

    def __init__(self, directory: pathlib.Path | None, refresh: bool = False) -> None:
        self.directory = directory
        self.refresh = refresh

    def get(self, url: str, name: str) -> object:
        path = self.directory / (name + ".json") if self.directory else None
        if path is not None and path.exists() and not self.refresh:
            return json.loads(path.read_text())

        request = urllib.request.Request(
            url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}
        )
        with urllib.request.urlopen(request, timeout=40) as response:
            payload = json.loads(response.read().decode())
        if path is not None:
            path.write_text(json.dumps(payload) + "\n")
        return payload


def slug(text: str) -> str:
    """A filesystem-safe form of a query, used as the cache file name."""
    return "".join(c if c.isalnum() else "_" for c in text).strip("_")[:90]


def search(
    endpoint: str, query: str, store: Responses, enumerate_items: bool
) -> tuple[list[dict], int]:
    """Query a GitHub search endpoint. Returns the items and the reported total.

    `enumerate_items` is false when only the total is wanted, which costs one request instead of
    several and is enough for counts the site does not break down.
    """
    items: list[dict] = []
    total = 0
    pages = 10 if enumerate_items else 1
    for page in range(1, pages + 1):
        name = f"{endpoint}_{slug(query)}_p{page}"
        url = (
            f"https://api.github.com/search/{endpoint}?q={query.replace(' ', '+')}"
            f"&per_page=100&page={page}"
        )
        payload = store.get(url, name)
        batch = payload.get("items", [])
        total = payload.get("total_count", 0)
        items.extend(batch)
        if not batch or len(items) >= total:
            break
    return items, total


def repo_rels(items: list[dict]) -> collections.Counter:
    counter: collections.Counter = collections.Counter()
    for item in items:
        counter[item["repository_url"].replace("https://api.github.com/repos/", "")] += 1
    return counter


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=pathlib.Path, help="read saved responses from here")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="with --cache-dir, refetch everything and overwrite the saved responses",
    )
    parser.add_argument("--check", action="store_true", help="fail if the file on disk would change")
    args = parser.parse_args(argv)

    root = pathlib.Path(__file__).resolve().parents[1]
    store = Responses(args.cache_dir, args.refresh)

    profile = store.get(f"https://api.github.com/users/{ACCOUNT}", "user_" + ACCOUNT)
    repos: list[dict] = []
    for page in range(1, 4):
        batch = store.get(
            f"https://api.github.com/users/{ACCOUNT}/repos?per_page=100&page={page}",
            f"repos_{ACCOUNT}_p{page}",
        )
        repos.extend(batch)
        if len(batch) < 100:
            break

    merged, merged_total = search(
        "issues", f"author:{ACCOUNT} type:pr is:merged", store, enumerate_items=True
    )
    commits_total = search("commits", f"author:{ACCOUNT}", store, enumerate_items=False)[1]
    opened_total = search("issues", f"author:{ACCOUNT} type:pr", store, False)[1]
    issues_total = search("issues", f"author:{ACCOUNT} type:issue", store, False)[1]
    reviews_total = search("issues", f"reviewed-by:{ACCOUNT} type:pr", store, False)[1]

    by_repo = repo_rels(merged)
    third_party = {
        k: v
        for k, v in by_repo.items()
        if not k.startswith(ACCOUNT + "/") and k.split("/")[0] not in OWNED_ORGS
    }
    owned = {k: v for k, v in by_repo.items() if k.split("/")[0] in OWNED_ORGS}
    latest: dict[str, str] = {}
    for item in merged:
        rel = item["repository_url"].replace("https://api.github.com/repos/", "")
        latest[rel] = max(latest.get(rel, ""), item["created_at"][:10])

    langs = collections.Counter(r["language"] for r in repos if r["language"])
    measured = {
        "fetched_at": dt.datetime.now(dt.timezone.utc).date().isoformat(),
        "source": "https://api.github.com",
        "account": ACCOUNT,
        "owned_orgs": sorted(OWNED_ORGS),
        "queries": {
            "merged_prs": f"search/issues?q=author:{ACCOUNT}+type:pr+is:merged",
            "prs_opened": f"search/issues?q=author:{ACCOUNT}+type:pr",
            "issues_opened": f"search/issues?q=author:{ACCOUNT}+type:issue",
            "commits_authored": f"search/commits?q=author:{ACCOUNT}",
            "reviews": f"search/issues?q=reviewed-by:{ACCOUNT}+type:pr",
            "repos": f"users/{ACCOUNT}/repos",
        },
        "profile": {
            "name": profile.get("name"),
            "since": (profile.get("created_at") or "")[:4],
            "public_repos": profile.get("public_repos"),
        },
        "commits_authored": commits_total,
        "prs_opened": opened_total,
        "issues_opened": issues_total,
        "prs_reviewed": reviews_total,
        "merged_enumerated": len(merged),
        "merged_reported_total": merged_total,
        "repos_touched": len(by_repo),
        "authored_repos": sum(1 for r in repos if not r["fork"]),
        "workspaces": sum(1 for r in repos if r["fork"]),
        "owned_org_repos": len(owned),
        "owned_org_merged_prs": sum(owned.values()),
        "thirdparty_repos": len(third_party),
        "thirdparty_merged_prs": sum(third_party.values()),
        "thirdparty_owners": len({k.split("/")[0] for k in third_party}),
        "languages": len(langs),
        "language_counts": [{"language": k, "repos": v} for k, v in langs.most_common()],
        "merged_by_repo": {k: v for k, v in sorted(by_repo.items())},
        "latest_by_repo": {k: v for k, v in sorted(latest.items())},
        "thirdparty_rows": [
            {
                "repo": k,
                "owner": k.split("/")[0],
                "merged_prs": v,
                "latest": latest.get(k, ""),
                "html": "https://github.com/" + k,
            }
            for k, v in sorted(third_party.items(), key=lambda kv: (-kv[1], kv[0]))
        ],
        "owned_org_rows": [
            {
                "org": org,
                "repos": sorted(k for k in owned if k.split("/")[0] == org),
                "merged_prs": sum(v for k, v in owned.items() if k.split("/")[0] == org),
                "html": "https://github.com/" + org,
            }
            for org in sorted(OWNED_ORGS)
        ],
        "authored_rows": [
            {
                "name": r["name"],
                "language": r["language"] or "",
                "description": r["description"] or "",
                "pushed": r["pushed_at"][:10],
                "stars": r["stargazers_count"],
                "html": r["html_url"],
            }
            for r in sorted(
                (x for x in repos if not x["fork"]), key=lambda x: x["pushed_at"], reverse=True
            )
        ],
    }

    out = root / "data" / "measured.json"
    text = json.dumps(measured, indent=2) + "\n"
    if args.check:
        if out.exists() and out.read_text() != text:
            print("data/measured.json is stale; run scripts/measure.py", file=sys.stderr)
            return 1
        return 0
    out.write_text(text)
    print(
        f"measured.json written: {measured['merged_enumerated']} merged PRs, "
        f"{measured['repos_touched']} repositories, "
        f"{measured['thirdparty_merged_prs']} into {measured['thirdparty_repos']} not owned"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

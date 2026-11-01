# Portfolio: Ademola Ajala

The source for `https://wagmiiii.github.io/portfolio/`. A single static page, no build step at
publish time, no third-party requests, no webfonts.

The visual language is derived from the [Airlock documentation site](https://github.com/wagmiiii/airlock)
stylesheet: dark substrate, phosphor ink, one red accent, hairline compartments, a scanline tile,
and no gradients, border radius or shadows anywhere. The only green on the page is the status LED.
`assets/theme.css` carries that rule at the top of the file.

## What makes the numbers true

Every count on the page is measured from the GitHub API rather than typed in, and the footer states
the account and the date it was read. Two scripts, in order:

```sh
python3 scripts/measure.py --cache-dir data/raw   # refresh data/measured.json
python3 scripts/build.py                          # regenerate the marked regions of index.html
```

`data/raw/` holds the API responses the current numbers came from (recorded 2026-11-01), so a
rebuild is offline and deterministic. To move the numbers forward, add `--refresh`, which refetches
everything and overwrites those files so the recorded responses and the published counts stay
together:

```sh
python3 scripts/measure.py --cache-dir data/raw --refresh
```

Requests are unauthenticated: 60 core calls an hour and 10 search calls a minute. A full refresh is
3 core and 8 search, so one fits and a second in the same hour does not.

Both scripts take `--check`, which writes nothing and exits 1 when the file on disk no longer
matches its data. That is the gate to run before committing:

```sh
python3 scripts/measure.py --cache-dir data/raw --check
python3 scripts/build.py --check
```

`build.py` also refuses to write a page containing a non-ASCII character, an em dash, or a
`{placeholder}` that never resolved. HTML entities (`&rarr;`, `&mdash;`) are how the page carries
anything outside ASCII.

## Layout

| Path | What it is |
| --- | --- |
| `index.html` | The page. Hand-written outside the `<!-- NAME:START -->` markers. |
| `assets/theme.css` | The whole design system, one stylesheet. |
| `assets/site.js` | Copy-to-clipboard, the name that types itself, the mobile nav drawer and the current-section marker. The heading is the control that stops the loop: it takes focus, and Enter, Space or a click resolves the name and holds it. Without JS the copy button hides itself, the nav stays a scrolling strip, the marker never lights up, the heading is not focusable and the name is simply there. Reduced motion does the same, because the script never splits the name into characters. |
| `assets/portrait.jpg` | The headshot, cropped square and converted to grayscale at source so a photo cannot fight the palette. Used as the Open Graph image. |
| `assets/portrait-mark.jpg` | The same headshot cropped to the head, for the 40px header square. At that size a shoulder-up frame leaves a face too small to read. |
| `assets/avatar.jpg` | The avatar illustration, cropped square at 760px and desaturated at source for the same reason as the headshot. This is the figure in the hero. |
| `assets/shots/` | Product screenshots, committed rather than generated. Each is cropped to 16:10 at 1200px wide; the CSS reserves the box with `aspect-ratio` and the images carry no `width`/`height` attributes, so a new shot must be 16:10 or it will be cropped by `object-fit`. Their job is to show interface work. |
| `data/profile.json` | The curated half: prose, roles, stack, projects, contact rows. |
| `data/measured.json` | The measured half: counts, the per-repository rows they were enumerated from, and the query that produced each. |
| `data/raw/` | The API responses behind `measured.json`. |
| `cv/` | The CV PDF the "Read the CV" button points at. |

Thirteen regions of the page are generated: `META`, `IDENTITY`, `TELEMETRY`, `BAND`, `WORK`,
`OPENSOURCE`, `STATS`, `TIMELINE`, `STACK`, `CREDENTIALS`, `PROJECTS`, `CONTACT`, `FOOTMETA`.
`META` is the `<head>` copy, and it exists because the title, description and Open Graph text quote
the same counts as the body: hand-written, they were the first thing to go stale on a re-measure.
Prose in `profile.json` may reference a measured value as `{commits}`, `{merged}`, `{ext_prs}` and
so on; `build.py` fails on a placeholder with no value.

## How the counts are framed

The account holds 77 repositories and 58 of them are forks. On this page a fork is treated as what
it is: the working copy where a pull request got written. So:

- **Merged only.** Nothing counts as a contribution until it closed into a default branch the
  account does not control. Open and rejected pull requests are not published.
- **Owned and third-party are separate.** Merged work in `accensa`, `Tollcraft` and `StaffPurse` is
  shipped product, listed apart from the 107 merged pull requests into 49 repositories belonging to
  other people. They are never added into one "contributions" number.
- **Totals, not lists.** The page states a count and points at GitHub to check it, rather than
  naming 49 repositories or 19 of them. Section 03 links to a merged-pull-request search, the
  `type=source` repository filter and the `type=fork` filter, so the reader verifies the number
  against the live account. A repository list copied onto the page is a list that goes stale, and
  section 03 says exactly that.

The footer prints the enumerated merged count next to the total the search endpoint reported at the
same minute. They differ by three because the search index lags a merge; the enumeration is the
number the page uses.

## Editing

Change `data/profile.json`, then run `python3 scripts/build.py`. Editing generated regions of
`index.html` directly is wasted work: the next build overwrites them, and `--check` fails before
that happens.

Three keys on a work item are optional and the renderer omits the markup entirely when they are
absent: `when` (the chip beside the role), `frontend` (a line of prose) and `shots` (the framed
screenshot pair). StaffPurse and Airlock use none of the three.

To preview locally, any static server works:

```sh
python3 -m http.server 8000
```

`http.server` sends no `Cache-Control`, so a browser decides an image's freshness for itself and can
keep serving an old copy of a file it has already seen. Replacing an image under the same name is
therefore invisible locally until the cache expires; changing the file name is what forces the fetch.

GitHub Pages publishes from `main` at the repository root. The repository is a project pages site
under `/portfolio/`, so `sitemap.xml` and canonical URLs carry that prefix.

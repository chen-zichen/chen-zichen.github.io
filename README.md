# chen-zichen.github.io

Personal website of Zichen Chen — https://chen-zichen.github.io/

A small, hand-written static site: no framework and no build step. Every push to `master` publishes the `site/` folder to GitHub Pages (see `.github/workflows/deploy.yml`).

## Layout

```
site/                     # everything that gets published
  index.html              # homepage
  publications/
    index.html            # publication list (the <main> list and the JSON-LD are generated)
    pubs.json             # publication data, the single source for the list
  assets/img/             # images (chair-sky.jpg, og.png share image)
  robots.txt, sitemap.xml, llms.txt, llms-full.txt, favicons
tools/
  pubs/                   # publication generator
    data/scholar.json     # snapshot of the Google Scholar profile
    data/arxiv.json       # arXiv metadata (full author lists)
    build_pubs.py         # merges Scholar + arXiv + per-paper overrides -> site/publications/pubs.json
    render_pubs.py        # renders the list, JSON-LD and llms-full.txt from pubs.json
  og/                     # source for the social share image
```

## Preview locally

```bash
python3 -m http.server 8000 --directory site
```

Then open http://localhost:8000/.

## Update publications

1. Refresh `tools/pubs/data/scholar.json` from the Google Scholar profile, and `tools/pubs/data/arxiv.json` from the arXiv API for any new arXiv ids.
2. Add or adjust entries in `tools/pubs/build_pubs.py`. Scholar papers go in `E`; papers that are not on Scholar yet go in `EXTRA`. Venue overrides also live there, for example "ACL 2026" rather than "Findings of ACL 2026".
3. Regenerate:

   ```bash
   cd tools/pubs
   python3 build_pubs.py && python3 render_pubs.py
   ```

4. Commit and push to `master`.

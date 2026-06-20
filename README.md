# Europe Trip 2026

Trip planning documents and an offline iPhone web app for Joy & Jeffery Peterson's July 6–17, 2026 Europe trip.

## Trip app (GitHub Pages)

**Live app:** https://jdp71.github.io/Europe_Trip/

> **One-time setup:** If the site isn't live yet, go to [Repository Settings → Pages](https://github.com/jdp71/Europe_Trip/settings/pages) and set **Source** to **GitHub Actions**. The deploy workflow runs automatically on every push to `main`.

### Install on iPhone

1. Open the URL above in **Safari**
2. Tap **Share → Add to Home Screen**
3. Open once while online to cache all PDFs offline

## Local development

```bash
python app/build.py      # rebuild data from markdown/PDFs
python app/serve.py      # local server at http://localhost:8080
```

## Contents

- `Europe Trip Itinerary.md` — master itinerary
- `06_July/` … `17_July/` — booking PDFs and markdown notes
- `app/` — offline PWA source (built automatically on deploy)

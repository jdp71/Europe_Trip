# Europe Trip 2026

Trip planning documents and an offline iPhone web app for Joy & Jeffery Peterson's July 6–17, 2026 Europe trip.

## Trip app (GitHub Pages)

**Live app:** https://jdp71.github.io/Europe_Trip/

### Enable GitHub Pages (one-time)

1. Wait for the [Deploy workflow](https://github.com/jdp71/Europe_Trip/actions) to finish (it creates a `gh-pages` branch).
2. Go to **[Settings → Pages](https://github.com/jdp71/Europe_Trip/settings/pages)**
3. Under **Build and deployment → Source**, choose **Deploy from a branch** (not “GitHub Actions” — that option may not appear)
4. Set **Branch** to `gh-pages` and folder to **`/ (root)`**
5. Click **Save**

The site should be live within a minute or two at the URL above.

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

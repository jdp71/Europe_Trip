# Europe Trip — iPhone App

An offline-capable Progressive Web App (PWA) for your July 6–17, 2026 trip.

## Install on iPhone

1. **Build the app** (after any booking changes):
   ```
   python app/build.py
   ```

2. **Start the local server** on your computer:
   ```
   python app/serve.py
   ```

3. **On your iPhone** (same Wi-Fi as your computer):
   - Open Safari and go to the URL shown (e.g. `http://192.168.x.x:8080`)
   - Tap **Share** → **Add to Home Screen**
   - Name it "Europe Trip" and tap Add

4. **Cache for offline**: Open the app once while online. It downloads all booking PDFs and data. After that, it works without internet.

## Features

- **Days tab** — tap any day to see that day's bookings
- **All tab** — filter by hotel / transport / activity
- **PDFs tab** — open any original booking document offline
- Each item includes confirmation numbers, QR codes, maps links, phone/email, and tips

## Updating

When you add or change bookings:
1. Update the markdown/PDF in the date folder
2. Run `python app/build.py`
3. Refresh the app (or re-open) while online to update the cache

## Deploy online (optional)

For easier install without running a local server, deploy the `app/` folder to GitHub Pages, Netlify, or iCloud Drive (with a simple host). PWAs require HTTPS (or localhost) for offline caching.

# Digital business card

A static, HiHello-style card: tap-to-save contact (.vcf), call/text/email buttons,
links, a "share your info with me" form (opens the visitor's own mail/SMS app — no
backend, nothing stored), a QR code, and the browser's native Share sheet.

## Deploy (GitHub Pages, ~5 minutes)
1. Create a public repo (e.g. `card`) and push this folder to `main`.
2. Repo **Settings → Pages → Source: GitHub Actions**.
3. Edit `config.yml` — set `site_url` to `https://<user>.github.io/card/` (or your
   custom domain) and fill in your details. Commit. The workflow builds and deploys.
4. Optional photo: add a square JPEG to `assets/` and set `photo: "photo.jpg"`.
   It is also embedded in the downloaded contact, so keep it small (~600px, <150 KB).

## Before RSNA
- Open the live URL on iPhone + Android and test **Save contact** end to end.
- `qr.png` — print for a badge sticker / back of a paper card.
- `qr-lockscreen.png` — set as your phone lock screen so people can scan without
  you unlocking. `/qr.html` is a full-screen version.
- Optional: write the URL to an NFC sticker/card (NFC Tools app) for tap-to-open.
- Lock the QR target forever: if you might change hosts later, use a custom domain.

## Local preview
    pip install pyyaml segno && python build.py && open dist/index.html

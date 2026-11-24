#!/usr/bin/env python3
"""Build the static business card from config.yml into ./dist.

    pip install pyyaml segno
    python build.py            # then open dist/index.html
"""
import base64
import html
import json
import shutil
from pathlib import Path
from urllib.parse import quote

import segno
import yaml

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
ASSETS = ROOT / "assets"

cfg = yaml.safe_load((ROOT / "config.yml").read_text())
g = lambda k: (cfg.get(k) or "").strip() if isinstance(cfg.get(k, ""), str) else cfg.get(k)
e = lambda s: html.escape(s or "", quote=True)

first, last = g("first_name"), g("last_name")
full_name = f"{first} {last}".strip()
initials = (first[:1] + last[:1]).upper()
site_url = g("site_url")
accent = g("accent") or "#0b4f8a"
phone = g("phone")
tel = "".join(c for c in phone if c.isdigit() or c == "+")
if tel and not tel.startswith("+"):  # assume US/Canada for bare 10-digit numbers
    tel = "+1" + tel if len(tel) == 10 else "+" + tel
links = [l for l in (cfg.get("links") or []) if l and l.get("url")]

# ── fresh output dir ────────────────────────────────────────
if DIST.exists():
    shutil.rmtree(DIST)
DIST.mkdir()
if ASSETS.exists():
    shutil.copytree(ASSETS, DIST / "assets")

photo = g("photo")
photo_path = ASSETS / photo if photo else None
if photo_path and not photo_path.exists():
    print(f"warning: photo {photo_path} not found; using initials")
    photo_path = None


# ── vCard 3.0 (best compatibility with iOS + Android) ───────
def vesc(s):
    return (s or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def fold(line):
    out, b = [], line.encode()
    first_chunk = True
    while b:
        n = 75 if first_chunk else 74
        chunk = b[:n]
        while True:  # don't split a UTF-8 multibyte char
            try:
                s = chunk.decode()
                break
            except UnicodeDecodeError:
                chunk = chunk[:-1]
        out.append(s if first_chunk else " " + s)
        b = b[len(chunk):]
        first_chunk = False
    return "\r\n".join(out)


v = ["BEGIN:VCARD", "VERSION:3.0",
     f"N:{vesc(last)};{vesc(first)};;;", f"FN:{vesc(full_name)}"]
if g("organization"):
    v.append(f"ORG:{vesc(g('organization'))}" + (f";{vesc(g('department'))}" if g("department") else ""))
if g("title"):
    v.append(f"TITLE:{vesc(g('title'))}")
if g("email"):
    v.append(f"EMAIL;TYPE=INTERNET,WORK:{g('email')}")
if tel:
    v.append(f"TEL;TYPE=CELL,VOICE:{tel}")
if g("website"):
    v.append(f"URL;TYPE=WORK:{g('website')}")
if site_url:
    v.append(f"URL:{site_url}")
for l in links:
    v.append(f"URL:{l['url']}")
note = g("contact_note")
if note:
    v.append(f"NOTE:{vesc(note)}")
if photo_path:
    kind = "PNG" if photo_path.suffix.lower() == ".png" else "JPEG"
    small = photo_path.with_name(photo_path.stem + "-small" + photo_path.suffix)
    src = small if small.exists() else photo_path
    v.append(f"PHOTO;ENCODING=b;TYPE={kind}:" + base64.b64encode(src.read_bytes()).decode())
v.append("END:VCARD")
(DIST / "contact.vcf").write_bytes(("\r\n".join(fold(x) for x in v) + "\r\n").encode())

# ── QR codes ────────────────────────────────────────────────
qr = segno.make(site_url or "https://example.com", error="m")
qr.save(DIST / "qr.svg", scale=10, border=2, dark="#0a1a2b")
qr.save(DIST / "qr.png", scale=20, border=2, dark="#0a1a2b")          # print / badge sticker
qr.save(DIST / "qr-lockscreen.png", scale=24, border=6, dark="#0a1a2b")  # set as phone wallpaper

# ── icons (simple generic line icons) ───────────────────────
def icon(d):
    return (f'<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" '
            f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{d}</svg>')

I = {
    "mail": icon('<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>'),
    "phone": icon('<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2"/>'),
    "sms": icon('<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/>'),
    "globe": icon('<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>'),
    "link": icon('<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>'),
    "cal": icon('<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>'),
    "save": icon('<circle cx="10" cy="8" r="4"/><path d="M3 21a7 7 0 0 1 12-5M19 14v6M16 17h6"/>'),
    "share": icon('<path d="M12 3v13M7 8l5-5 5 5"/><path d="M5 13v6a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-6"/>'),
    "qr": icon('<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><path d="M14 14h3v3M21 14v.01M14 21h7v-4"/>'),
    "pin": icon('<path d="M12 21s-7-6.2-7-12a7 7 0 0 1 14 0c0 5.8-7 12-7 12z"/><circle cx="12" cy="9" r="2.5"/>'),
    "chev": icon('<path d="m9 6 6 6-6 6"/>'),
    "hand": icon('<path d="M4 12h6l2-2h4a2 2 0 0 1 0 4h-3M4 18h10l6-4"/>'),
}


def ext(url):  # open external links in a new tab
    return f'href="{e(url)}" target="_blank" rel="noopener"'


# ── page pieces ─────────────────────────────────────────────
avatar = (f'<img class="avatar" src="assets/{e(photo)}" alt="{e(full_name)}">' if photo_path
          else f'<div class="avatar initials" aria-hidden="true">{e(initials)}</div>')

quick = []
if g("email"):
    quick.append(f'<a class="q" href="mailto:{e(g("email"))}">{I["mail"]}<span>Email</span></a>')
if tel:
    quick.append(f'<a class="q" href="tel:{e(tel)}">{I["phone"]}<span>Call</span></a>')
    quick.append(f'<a class="q" href="sms:{e(tel)}">{I["sms"]}<span>Text</span></a>')
if g("website"):
    quick.append(f'<a class="q" {ext(g("website"))}>{I["globe"]}<span>Website</span></a>')

rows = []
if g("meeting_link"):
    rows.append(f'<a class="row" {ext(g("meeting_link"))}>{I["cal"]}<span>Book a meeting</span>{I["chev"]}</a>')
for l in links:
    rows.append(f'<a class="row" {ext(l["url"])}>{I["link"]}<span>{e(l.get("label") or l["url"])}</span>{I["chev"]}</a>')
if g("email"):
    rows.append(f'<a class="row" href="mailto:{e(g("email"))}">{I["mail"]}<span>{e(g("email"))}</span>{I["chev"]}</a>')
if phone:
    rows.append(f'<a class="row" href="tel:{e(tel)}">{I["phone"]}<span>{e(phone)}</span>{I["chev"]}</a>')
if g("location"):
    rows.append(f'<div class="row static">{I["pin"]}<span>{e(g("location"))}</span></div>')

org_line = " · ".join(x for x in [g("organization"), g("department")] if x)
banner = f'<div class="banner">{e(g("event_note"))}</div>' if g("event_note") else ""
desc = " — ".join(x for x in [g("title"), g("organization")] if x)
og_img = f'{site_url.rstrip("/")}/assets/{e(photo)}' if photo_path else f'{site_url.rstrip("/")}/qr.png'
js_cfg = json.dumps({"email": g("email"), "tel": tel, "name": full_name, "url": site_url})

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(full_name)}{' — ' + e(g('title')) if g('title') else ''}</title>
<meta name="description" content="{e(desc)}">
<meta name="theme-color" content="{e(accent)}">
<meta property="og:type" content="profile">
<meta property="og:title" content="{e(full_name)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{e(site_url)}">
<meta property="og:image" content="{og_img}">
<meta name="twitter:card" content="summary">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><rect width='64' height='64' rx='14' fill='{quote(accent)}'/><text x='32' y='42' font-size='28' text-anchor='middle' fill='white' font-family='sans-serif' font-weight='700'>{e(initials)}</text></svg>">
<style>
:root{{--a:{accent};--bg:#eef2f6;--card:#fff;--ink:#0f1b2a;--mute:#5b6878;--line:#e3e8ee;--chip:#f3f6f9}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0b1118;--card:#131b25;--ink:#e8eef5;--mute:#93a1b1;--line:#223041;--chip:#1a2431}}}}
*{{box-sizing:border-box}}
html,body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased}}
main{{max-width:440px;margin:0 auto;padding:0 0 calc(28px + env(safe-area-inset-bottom))}}
.card{{background:var(--card);margin:0 0 14px;border-radius:0 0 22px 22px;overflow:hidden;box-shadow:0 1px 2px rgba(0,0,0,.06)}}
@media (min-width:480px){{main{{padding-top:28px}}.card{{border-radius:22px}}}}
.hero{{height:118px;background:linear-gradient(135deg,var(--a),color-mix(in srgb,var(--a) 55%,#000));position:relative}}
.hero:after{{content:"";position:absolute;inset:0;background:radial-gradient(circle at 85% -20%,rgba(255,255,255,.22),transparent 55%)}}
.banner{{position:absolute;z-index:1;top:14px;left:50%;transform:translateX(-50%);white-space:nowrap;background:rgba(255,255,255,.16);backdrop-filter:blur(6px);color:#fff;font-size:12.5px;font-weight:600;letter-spacing:.02em;padding:5px 12px;border-radius:99px;border:1px solid rgba(255,255,255,.25)}}
.avatar{{width:112px;height:112px;border-radius:50%;object-fit:cover;display:block;margin:-62px auto 0;position:relative;border:4px solid var(--card);background:var(--chip)}}
.initials{{display:grid;place-items:center;font-size:40px;font-weight:700;color:#fff;background:linear-gradient(135deg,var(--a),color-mix(in srgb,var(--a) 60%,#000))}}
.id{{text-align:center;padding:12px 22px 4px}}
h1{{font-size:26px;line-height:1.15;margin:0;letter-spacing:-.01em}}
.pn{{font-size:14px;color:var(--mute);font-weight:500;margin-left:4px}}
.title{{margin:6px 0 0;font-weight:600}}
.org{{margin:2px 0 0;color:var(--mute);font-size:15px}}
.tag{{display:inline-block;margin-top:10px;font-size:13px;color:var(--a);background:color-mix(in srgb,var(--a) 10%,transparent);padding:4px 10px;border-radius:99px;font-weight:600}}
@media (prefers-color-scheme:dark){{.tag{{color:color-mix(in srgb,var(--a) 45%,#fff)}}}}
.save{{display:flex;align-items:center;justify-content:center;gap:10px;margin:18px 20px 0;padding:15px;border-radius:14px;background:var(--a);color:#fff;font-weight:700;font-size:17px;text-decoration:none;box-shadow:0 6px 16px color-mix(in srgb,var(--a) 35%,transparent)}}
.save svg{{width:22px;height:22px}}
.save:active{{transform:scale(.98)}}
.quick{{display:grid;grid-template-columns:repeat(auto-fit,minmax(0,1fr));gap:8px;padding:14px 20px 22px}}
.q{{display:flex;flex-direction:column;align-items:center;gap:6px;padding:12px 4px;border-radius:12px;background:var(--chip);color:var(--ink);text-decoration:none;font-size:13px;font-weight:600}}
.q svg{{width:22px;height:22px;color:var(--a)}}
@media (prefers-color-scheme:dark){{.q svg,.row svg:first-child{{color:color-mix(in srgb,var(--a) 45%,#fff)}}}}
.list{{background:var(--card);border-radius:18px;margin:0 12px 14px;overflow:hidden;box-shadow:0 1px 2px rgba(0,0,0,.06)}}
.row{{display:flex;align-items:center;gap:14px;padding:15px 16px;color:var(--ink);text-decoration:none;border-top:1px solid var(--line);font-weight:500;min-width:0}}
.row:first-child{{border-top:0}}
.row span{{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.row svg{{width:20px;height:20px;flex:none}}
.row svg:first-child{{color:var(--a)}}
.row svg:last-child{{color:var(--mute);width:16px}}
.row.static{{color:var(--mute)}}
details.list summary{{list-style:none;cursor:pointer}}
details.list summary::-webkit-details-marker{{display:none}}
details[open] summary svg:last-child{{transform:rotate(90deg)}}
form{{padding:4px 16px 16px;display:grid;gap:10px}}
input,textarea{{width:100%;font:inherit;color:var(--ink);background:var(--chip);border:1px solid var(--line);border-radius:10px;padding:11px 12px}}
textarea{{min-height:70px;resize:vertical}}
.btns{{display:flex;gap:8px}}
.btns button{{flex:1}}
button{{font:inherit;font-weight:700;border:0;border-radius:12px;padding:12px;background:var(--a);color:#fff;cursor:pointer}}
button.alt{{background:var(--chip);color:var(--ink);border:1px solid var(--line)}}
.foot{{display:flex;gap:8px;margin:0 12px}}
.foot button,.foot a{{flex:1;display:flex;align-items:center;justify-content:center;gap:8px;background:var(--card);color:var(--ink);border:1px solid var(--line);font-weight:600;font-size:15px;text-decoration:none;border-radius:14px;padding:13px}}
.foot svg{{width:20px;height:20px}}
.hint{{font-size:12.5px;color:var(--mute);margin:0}}
dialog{{border:0;border-radius:22px;padding:24px;max-width:92vw;background:#fff;color:#0f1b2a;text-align:center}}
dialog::backdrop{{background:rgba(5,12,20,.7)}}
dialog img{{width:min(76vw,340px);height:auto;display:block;margin:0 auto 8px}}
dialog p{{margin:4px 0 14px;font-weight:600}}
@media (prefers-color-scheme:dark){{.row svg:first-child{{color:color-mix(in srgb,var(--a) 45%,#fff)}}}}
</style>
</head>
<body>
<main>
  <section class="card">
    <div class="hero">{banner}</div>
    {avatar}
    <div class="id">
      <h1>{e(full_name)}{f'<span class="pn">({e(g("pronouns"))})</span>' if g("pronouns") else ''}</h1>
      {f'<p class="title">{e(g("title"))}</p>' if g("title") else ''}
      {f'<p class="org">{e(org_line)}</p>' if org_line else ''}
      {f'<span class="tag">{e(g("tagline"))}</span>' if g("tagline") else ''}
    </div>
    <a class="save" href="contact.vcf">{I["save"]}Save contact</a>
    <nav class="quick">{''.join(quick)}</nav>
  </section>

  {f'<section class="list">{"".join(rows)}</section>' if rows else ''}

  <details class="list" id="swap">
    <summary class="row">{I["hand"]}<span>Share your info with me</span>{I["chev"]}</summary>
    <form id="f" autocomplete="on">
      <input name="name" placeholder="Your name" autocomplete="name" required>
      <input name="org" placeholder="Organization" autocomplete="organization">
      <input name="email" type="email" placeholder="Email" autocomplete="email">
      <input name="phone" type="tel" placeholder="Phone" autocomplete="tel">
      <textarea name="note" placeholder="What should we follow up on?"></textarea>
      <div class="btns">
        {'<button type="submit" data-via="email">Send by email</button>' if g("email") else ''}
        {'<button type="submit" data-via="sms" class="alt">Send by text</button>' if tel else ''}
      </div>
      <p class="hint">Opens your own mail or messages app — nothing is stored on this site.</p>
    </form>
  </details>

  <div class="foot">
    <button type="button" id="qrb">{I["qr"]}Show QR</button>
    <button type="button" id="shb">{I["share"]}Share</button>
  </div>
</main>

<dialog id="qd">
  <img src="qr.svg" alt="QR code for this card" width="340" height="340">
  <p>Scan to get my card</p>
  <form method="dialog"><button>Close</button></form>
</dialog>

<script>
const C={js_cfg};
document.getElementById('qrb').onclick=()=>document.getElementById('qd').showModal();
document.getElementById('shb').onclick=async()=>{{
  const d={{title:C.name,text:C.name,url:C.url||location.href}};
  if(navigator.share){{try{{await navigator.share(d)}}catch(_){{}}}}
  else{{try{{await navigator.clipboard.writeText(d.url);alert('Link copied')}}catch(_){{prompt('Copy this link',d.url)}}}}
}};
document.getElementById('f').addEventListener('submit',ev=>{{
  ev.preventDefault();
  const f=new FormData(ev.target),via=ev.submitter&&ev.submitter.dataset.via;
  const lines=[['Name','name'],['Org','org'],['Email','email'],['Phone','phone'],['Note','note']]
    .map(([l,k])=>[l,(f.get(k)||'').trim()]).filter(x=>x[1]).map(x=>x[0]+': '+x[1]);
  const body=lines.join('\\n'),subj='Nice meeting you — '+(f.get('name')||'');
  location.href = via==='sms'
    ? 'sms:'+C.tel+(/iPhone|iPad/.test(navigator.userAgent)?'&':'?')+'body='+encodeURIComponent(body)
    : 'mailto:'+C.email+'?subject='+encodeURIComponent(subj)+'&body='+encodeURIComponent(body);
}});
</script>
</body>
</html>
"""
(DIST / "index.html").write_text(page)

# Full-screen QR page: open on your phone and hand it over / screenshot it.
(DIST / "qr.html").write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(full_name)} — QR</title>
<style>html,body{{margin:0;height:100%;background:#fff;color:#0a1a2b;font:600 18px -apple-system,Segoe UI,Roboto,sans-serif}}
body{{display:grid;place-items:center;text-align:center}}img{{width:min(86vw,86vh);height:auto}}</style></head>
<body><div><img src="qr.svg" alt="QR code"><div>{e(full_name)}</div></div></body></html>""")

(DIST / ".nojekyll").write_text("")
print(f"Built {DIST} → QR points to {site_url}")

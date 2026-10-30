#!/usr/bin/env python3
"""Baut ../index.html aus template.html: bettet Roboto (src/fonts/*.woff) als base64 ein.
Das Logo steckt bereits als data-URI im Template (Quelle: logo-white.png); paravoz.jpg (Easter Egg im Kaffee-Leaderboard) wird als %%EGG%% eingesetzt,
vendor/qrcode.js (QR-Code-Bibliothek, MIT) als %%QRLIB%%.

    python3 src/build.py
"""
import base64, pathlib
here = pathlib.Path(__file__).resolve().parent
css = []
for name, w in [('Regular', 400), ('Medium', 500), ('Bold', 700), ('Black', 900)]:
    b64 = base64.b64encode((here / 'fonts' / f'roboto-{name}.woff').read_bytes()).decode()
    css.append("@font-face{font-family:'Roboto';font-style:normal;font-weight:%d;font-display:block;src:url(data:font/woff;base64,%s) format('woff')}" % (w, b64))
egg = 'data:image/jpeg;base64,' + base64.b64encode((here / 'paravoz.jpg').read_bytes()).decode()
qrlib = (here / 'vendor' / 'qrcode.js').read_text(encoding='utf-8')   # qrcode-generator 1.4.4 (MIT), für die Kalender-QR-Codes bei Events
html = (here / 'template.html').read_text(encoding='utf-8').replace('/*FONTS*/', '\n'.join(css)).replace('%%EGG%%', egg).replace('%%QRLIB%%', qrlib)
out = here.parent / 'index.html'
out.write_text(html, encoding='utf-8')
print(f'{out} ({len(html)} Bytes)')

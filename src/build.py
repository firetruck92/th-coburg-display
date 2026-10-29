#!/usr/bin/env python3
"""Baut ../index.html aus template.html: bettet Roboto (src/fonts/*.woff) als base64 ein.
Das Logo steckt bereits als data-URI im Template (Quelle: logo-white.png).

    python3 src/build.py
"""
import base64, pathlib
here = pathlib.Path(__file__).resolve().parent
css = []
for name, w in [('Regular', 400), ('Medium', 500), ('Bold', 700), ('Black', 900)]:
    b64 = base64.b64encode((here / 'fonts' / f'roboto-{name}.woff').read_bytes()).decode()
    css.append("@font-face{font-family:'Roboto';font-style:normal;font-weight:%d;font-display:block;src:url(data:font/woff;base64,%s) format('woff')}" % (w, b64))
html = (here / 'template.html').read_text(encoding='utf-8').replace('/*FONTS*/', '\n'.join(css))
out = here.parent / 'index.html'
out.write_text(html, encoding='utf-8')
print(f'{out} ({len(html)} Bytes)')

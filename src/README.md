# src – Quellen der Anzeige

`index.html` im Repository-Root ist ein Build-Ergebnis. Nicht dort bearbeiten, sondern hier:

- `template.html` – Seite (HTML, CSS, JS), Platzhalter `/*FONTS*/` für die Schrift
- `fonts/` – Roboto (Regular, Medium, Bold, Black) als woff-Subset
- `logo-white.png` – Hochschul-Logo (im Template als data-URI eingebettet)
- `build.py` – erzeugt `../index.html`

Ablauf: `template.html` ändern → `python3 src/build.py` → `index.html` committen.

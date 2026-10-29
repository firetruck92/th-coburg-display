# th-coburg-display

Touch-Kiosk-Anzeige für den Campus der Hochschule Coburg.
Zielgerät: ET 4363L, Auflösung 1080 × 1920 (Hochformat).

## Inhalt
Eine einzelne Datei, `index.html` (HTML, CSS und JavaScript, keine Bibliotheken).
Links sechs Tabs, rechts das aktive Fenster:

- Stundenplan
- Events
- Wichtige Termine
- Mensaplan
- Profs Kontakt Informationen
- Kaffee Leaderboard

## Starten
Datei im Browser öffnen. Für den Kioskbetrieb zum Beispiel:

    chrome --kiosk index.html

Nach 2 Minuten ohne Berührung springt die Anzeige zurück auf den Stundenplan.

## Sprache
Oben rechts lässt sich zwischen Deutsch und Englisch umschalten. Nach 2 Minuten ohne
Berührung wird wieder auf Deutsch zurückgesetzt. Die englischen Texte stehen im
Wörterbuch `DICT` im `<script>`-Block.

## Logo
Das Logo der Hochschule liegt nicht im Repository. Eine weiße Version mit transparentem
Hintergrund als `logo.svg` oder `logo.png` neben `index.html` legen, dann erscheint es
automatisch oben links. Ohne Datei wird der Schriftzug angezeigt.

## Daten
Alle Inhalte sind derzeit Beispieldaten und stehen als Arrays am Anfang des
`<script>`-Blocks in `index.html` (PLAN, EVENTS, TERMINE, MENSA, PROFS, KAFFEE).
Zum Anbinden echter Quellen diese Arrays durch `fetch()`-Aufrufe ersetzen.

## Hinweis
Die Schrift Roboto ist in `index.html` eingebettet. Die Seite funktioniert daher ohne Internet.

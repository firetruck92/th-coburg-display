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

## Daten
Alle Inhalte sind derzeit Beispieldaten und stehen als Arrays am Anfang des
`<script>`-Blocks in `index.html` (PLAN, EVENTS, TERMINE, MENSA, PROFS, KAFFEE).
Zum Anbinden echter Quellen diese Arrays durch `fetch()`-Aufrufe ersetzen.

## Hinweis
Die Schrift Roboto wird von Google Fonts geladen. Für den Offline-Betrieb die Schrift lokal einbinden.

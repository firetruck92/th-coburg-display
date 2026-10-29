# th-coburg-display

Touch-Kiosk-Anzeige für den Campus der Hochschule Coburg.
Zielgerät: ET 4363L, Auflösung 1080 × 1920 (Hochformat).

## Inhalt
Eine einzelne Datei, `index.html` (HTML, CSS und JavaScript, keine Bibliotheken).
Schrift (Roboto) und Logo sind eingebettet, die Seite funktioniert ohne Internet.
Links sechs Tabs, rechts das aktive Fenster:

- Stundenplan (Montag, Dienstag, Donnerstag; Auswahl des Semesters 1 bis 7)
- Events
- Wichtige Termine
- Mensaplan
- Profs Kontakt Informationen
- Kaffee Leaderboard (mit Dialog zum Eintragen neuer Tassen)

Oben rechts lässt sich zwischen Deutsch und Englisch umschalten.

## Starten
Datei im Browser öffnen. Für den Kioskbetrieb zum Beispiel:

    chrome --kiosk index.html

Nach 2 Minuten ohne Berührung springt die Anzeige zurück auf den Stundenplan (Semester 3, Deutsch).

## Daten
Alle Inhalte sind derzeit Beispieldaten und stehen als Arrays am Anfang des
`<script>`-Blocks in `index.html` (PLAN3, MODULES, EVENTS, TERMINE, MENSA, PROFS, KDEF).
Zum Anbinden echter Quellen diese Arrays durch `fetch()`-Aufrufe ersetzen.
Die englischen Texte stehen im Wörterbuch `DICT`.

## Kaffee Leaderboard
Neue Einträge werden im Browser des Displays gespeichert (localStorage) und sind auf
anderen Geräten nicht sichtbar. "Heute" und "Woche" beginnen automatisch neu.
Für ein gemeinsames Leaderboard wird ein kleiner Server benötigt.

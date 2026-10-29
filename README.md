# th-coburg-display

Touch-Kiosk-Anzeige für den Campus der Hochschule Coburg.
Zielgerät: ET 4363L, Auflösung 1080 × 1920 (Hochformat).

## Inhalt
Eine einzelne Datei, `index.html` (HTML, CSS und JavaScript, keine Bibliotheken).
Schrift (Roboto) und Logo sind eingebettet, die Seite funktioniert ohne Internet.
Links sechs Tabs, rechts das aktive Fenster:

- Stundenplan (echte Daten aus der Excel-Zeitplanung; Auswahl des Semesters 1/3/5/7)
- Events
- Wichtige Termine
- Mensaplan
- Profs Kontakt Informationen
- Kaffee Leaderboard (mit Dialog zum Eintragen neuer Tassen)

Oben rechts lässt sich zwischen Deutsch und Englisch umschalten.

## Starten
Datei im Browser öffnen. Für den Kioskbetrieb zum Beispiel:

    chrome --kiosk index.html

Nach 2 Minuten ohne Berührung springt die Anzeige zurück auf den Stundenplan (Semester 1, Deutsch).

## Daten
Stundenplan und Wichtige Termine kommen aus `schedule.js` / `schedule.json`
(erzeugt aus der Excel-Zeitplanung). Events, Mensaplan, Profs und Kaffee sind
weiterhin Beispieldaten im `<script>`-Block von `index.html`.
Die englischen Texte stehen im Wörterbuch `DICT`.

### Stundenplan aktualisieren

    python3 tools/excel_to_json.py Zeitplanung.xlsx .

Benötigt `openpyxl`. Erzeugt `schedule.json` und `schedule.js` (rote Schrift = vorläufig,
Teams-Links werden nicht übernommen). Offline wird `schedule.js` genutzt; über http(s) lädt
die Seite `schedule.json` alle 30 Minuten neu.

## Kaffee Leaderboard
Neue Einträge werden im Browser des Displays gespeichert (localStorage) und sind auf
anderen Geräten nicht sichtbar. "Heute" und "Woche" beginnen automatisch neu.
Für ein gemeinsames Leaderboard wird ein kleiner Server benötigt.

## Kiosk-Server mit Admin-Upload (Raspberry Pi)
Im Ordner `kiosk/` liegt eine lokale Variante mit kleinem Python-Server und Admin-Seite
(`/admin`): Excel hochladen, Vorschau prüfen, übernehmen. Das Display aktualisiert sich
innerhalb einer Minute. Anleitung in `kiosk/README.md`.


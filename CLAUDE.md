# Projekt: Kiosk-Anzeige Hochschule Coburg

Uni-Projekt. Website im Kioskmodus auf einem Touch-Display (ET 4363L, Hochformat 1080×1920).
Optik wie hs-coburg.de: Rot→Orange-Verlauf, graue Fläche, weiße Karten mit runden Ecken, Roboto,
fette Großbuchstaben als Überschriften. Alles groß und touch-tauglich.

## Regeln
- **Vor jedem Push/Upload auf GitHub zuerst den Nutzer fragen und die Bestätigung abwarten.**
- Kommunikation mit dem Nutzer auf Russisch; Seitentexte deutsch (Basis) mit englischer Übersetzung.

## Aufbau
- `src/template.html` – Quelle der Seite; `python3 src/build.py` erzeugt daraus `index.html` (nicht direkt editieren).
- `index.html` – eine Datei, Roboto und Logo eingebettet, läuft offline.
- `schedule.js` / `schedule.json` – Stundenplan und Wichtige Termine (echt, aus der Excel-Zeitplanung).
- `tools/excel_to_json.py` – Excel → schedule.json/js (Blatt `WiSe26_27`).
- `server.py` + `admin.html` – lokaler Server (Raspberry Pi) mit Admin-Upload unter `/admin`, ohne Passwort;
  Standard nur localhost, `--lan` öffnet ins Netz. Sicherungen in `data/backup/` (nicht im Git).
- Start: `pip install openpyxl`, `python3 server.py`, Kiosk http://localhost:8080/.

## Seitenlogik (src/template.html)
- Feste 1080×1920-Bühne, per `transform: scale()` an den Viewport angepasst; nur helles Design.
- Zustand im Objekt `S` (tab, date, sem, mday, fak, per, lang, modal); nach 2 Min Inaktivität `fresh()`:
  Stundenplan, Semester 1, Deutsch.
- Sprache: deutscher Basistext, Wörterbuch `DICT` (de→en), Funktion `t()`.
- Events, Mensaplan, Profs und Kaffee sind **Beispieldaten** im Script. Das Kaffee-Leaderboard speichert
  nur in localStorage (`kaffee-v1`) des jeweiligen Browsers.
- Stundenplan lädt `schedule.js`; über http(s) zusätzlich jede Minute `schedule.json`.

## Excel-Konventionen (tools/excel_to_json.py)
- Semestergruppen 1/3/5/7; Spalten K:O verbunden = 5.+7. gemeinsam; Q:S = Studiengangsrelevante Termine;
  U = Allgemeines (Feiertage u. a.).
- Rote Schrift = vorläufig ("Vorläufig"); HYPERLINK → "Online" (URLs werden verworfen); tba/tbd → "Raum folgt".

## Offene Fragen
- Programmname "Wirtschaftsinformatik" und Standardsemester 1 bestätigen lassen.
- Nur Wintersemester (1/3/5/7) vorhanden; Sommer (2/4/6) fehlt.
- Echte Daten enthalten Tage außer Mo/Di/Do; sollen alle Tage gezeigt werden?
- Repo ist öffentlich und enthält Vornamen der Dozenten.
- Events, Mensa, Profs, Kaffee durch echte Quellen ersetzen (Kaffee ggf. serverseitig speichern).

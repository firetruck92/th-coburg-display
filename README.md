# th-coburg-display

Touch-Kiosk-Anzeige für den Campus der Hochschule Coburg.
Zielgerät: ET 4363L, Auflösung 1080 × 1920 (Hochformat).

## Inhalt
- `index.html` – die Anzeige (HTML, CSS, JavaScript; Roboto und Logo eingebettet, keine Bibliotheken)
- `schedule.js` / `schedule.json` – Stundenplan und Wichtige Termine (aus der Excel-Zeitplanung)
- `server.py` + `admin.html` – lokaler Server mit Admin-Seite zum Hochladen der Excel-Datei
- `tools/excel_to_json.py` – Konverter Excel → `schedule.json` / `schedule.js`

Tabs: Stundenplan, Events, Wichtige Termine, Mensaplan, Profs Kontakt Informationen, Kaffee Leaderboard.
Oben rechts Umschalter Deutsch/Englisch. Nach 2 Minuten ohne Berührung springt die Anzeige zurück
auf den Stundenplan (Semester 1, Deutsch).

## Nur ansehen
`index.html` im Browser öffnen oder über GitHub Pages. Der Stundenplan kommt aus `schedule.js`
(funktioniert auch ohne Internet).

## Raspberry Pi (mit Admin-Upload)
    sudo apt install python3-openpyxl
    python3 server.py

- Kiosk: http://localhost:8080/
- Admin: http://localhost:8080/admin (Excel hochladen, Vorschau prüfen, "Übernehmen")

Das Display lädt `schedule.json` jede Minute neu. Die letzten 10 Versionen liegen in `data/backup/`.

### Zugriff aus dem WLAN
Standardmäßig nur vom Pi selbst erreichbar. Mit `python3 server.py --lan` auch von anderen
Geräten (`http://<IP-des-Pi>:8080/admin`). Die Admin-Seite hat KEIN Passwort, also nur in
vertrauenswürdigen Netzen verwenden.

### Autostart
`/etc/systemd/system/kiosk-server.service`:

    [Unit]
    Description=Kiosk Server
    After=network.target
    [Service]
    WorkingDirectory=/home/pi/th-coburg-display
    ExecStart=/usr/bin/python3 /home/pi/th-coburg-display/server.py
    Restart=always
    User=pi
    [Install]
    WantedBy=multi-user.target

    sudo systemctl enable --now kiosk-server

Browser im Kiosk-Modus (z. B. `~/.config/autostart/kiosk.desktop`):

    chromium-browser --kiosk --noerrdialogs --disable-infobars http://localhost:8080/

## Stundenplan ohne Server aktualisieren
    python3 tools/excel_to_json.py Zeitplanung.xlsx .

Rote Schrift in Excel = vorläufig, Teams-Links werden nicht übernommen.

## Daten
Stundenplan und Wichtige Termine sind echt. Events, Mensaplan, Profs und Kaffee sind Beispieldaten
im `<script>`-Block von `index.html`. Das Kaffee Leaderboard speichert im Browser (localStorage).

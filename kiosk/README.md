# Kiosk mit Admin-Upload (Raspberry Pi)

Lokaler Server: zeigt die Kiosk-Seite und erlaubt das Hochladen der Excel-Zeitplanung.

## Einmalig einrichten
    sudo apt install python3-openpyxl
    python3 server.py

- Kiosk:  http://localhost:8080/
- Admin:  http://localhost:8080/admin  (Excel hochladen, Vorschau prüfen, "Übernehmen")

Das Display lädt `schedule.json` jede Minute neu. Die letzten 10 Versionen liegen in `data/backup/`.

## Zugriff aus dem WLAN
Standardmäßig nur vom Pi selbst erreichbar. Mit `python3 server.py --lan` auch von anderen
Geräten (`http://<IP-des-Pi>:8080/admin`). Die Admin-Seite hat KEIN Passwort, also nur in
vertrauenswürdigen Netzen verwenden.

## Autostart
`/etc/systemd/system/kiosk-server.service`:

    [Unit]
    Description=Kiosk Server
    After=network.target
    [Service]
    WorkingDirectory=/home/pi/kiosk
    ExecStart=/usr/bin/python3 /home/pi/kiosk/server.py
    Restart=always
    User=pi
    [Install]
    WantedBy=multi-user.target

    sudo systemctl enable --now kiosk-server

Browser im Kiosk-Modus (z. B. in `~/.config/autostart/kiosk.desktop`):

    chromium-browser --kiosk --noerrdialogs --disable-infobars http://localhost:8080/

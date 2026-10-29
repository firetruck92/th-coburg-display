#!/usr/bin/env python3
"""Kiosk-Server: liefert die Anzeige und eine Admin-Seite zum Hochladen der Excel-Zeitplanung.

    python3 server.py            # nur lokal erreichbar (http://localhost:8080)
    python3 server.py --lan      # auch aus dem WLAN erreichbar (Admin ohne Passwort!)
"""
import argparse, json, shutil, subprocess, sys, tempfile, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
BACKUP = DATA / 'backup'
PENDING = DATA / 'pending'
MAX_BYTES = 20 * 1024 * 1024
TYPES = {'.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
         '.json': 'application/json; charset=utf-8', '.png': 'image/png'}


def summarize(js):
    les, ev, notes = js.get('lessons', []), js.get('events', []), js.get('notes', [])
    dates = sorted(l['date'] for l in les)
    return {
        'lessons': len(les), 'events': len(ev), 'notes': len(notes),
        'first': dates[0] if dates else None, 'last': dates[-1] if dates else None,
        'semesters': js.get('meta', {}).get('semesters', []),
        'provisional': sum(1 for l in les if l.get('provisional')),
        'tbd': sum(1 for l in les if l.get('tbd')),
        'sheet': js.get('meta', {}).get('sheet'),
    }


def convert(xlsx_bytes):
    """Excel -> (summary, Ordner mit schedule.json/js). Wirft ValueError bei Fehlern."""
    if xlsx_bytes[:2] != b'PK':
        raise ValueError('Das ist keine Excel-Datei (.xlsx).')
    shutil.rmtree(PENDING, ignore_errors=True)
    PENDING.mkdir(parents=True)
    src = PENDING / 'upload.xlsx'
    src.write_bytes(xlsx_bytes)
    r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'excel_to_json.py'), str(src), str(PENDING)],
                       capture_output=True, text=True, timeout=120)
    if r.returncode != 0 or not (PENDING / 'schedule.json').exists():
        raise ValueError('Konverter-Fehler: ' + (r.stderr.strip().splitlines() or ['unbekannt'])[-1])
    js = json.loads((PENDING / 'schedule.json').read_text(encoding='utf-8'))
    s = summarize(js)
    if s['lessons'] == 0:
        raise ValueError('In der Datei wurden keine Lehrveranstaltungen gefunden.')
    return s


def apply_pending():
    if not (PENDING / 'schedule.json').exists():
        raise ValueError('Keine Vorschau vorhanden. Bitte Datei zuerst hochladen.')
    BACKUP.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime('%Y%m%d-%H%M%S')
    for name in ('schedule.json', 'schedule.js'):
        cur = ROOT / name
        if cur.exists():
            shutil.copy2(cur, BACKUP / f'{stamp}-{name}')
    # atomar ersetzen, damit der Kiosk nie eine halbe Datei liest
    for name in ('schedule.js', 'schedule.json'):
        tmp = ROOT / (name + '.tmp')
        shutil.copy2(PENDING / name, tmp)
        tmp.replace(ROOT / name)
    shutil.copy2(PENDING / 'upload.xlsx', DATA / 'zeitplanung.xlsx')
    shutil.rmtree(PENDING, ignore_errors=True)
    old = sorted(BACKUP.glob('*-schedule.json'))
    for f in old[:-10]:  # nur die letzten 10 Sicherungen behalten
        f.unlink(missing_ok=True)
        (BACKUP / f.name.replace('.json', '.js')).unlink(missing_ok=True)


def current_info():
    f = ROOT / 'schedule.json'
    if not f.exists():
        return {'exists': False}
    js = json.loads(f.read_text(encoding='utf-8'))
    s = summarize(js)
    s.update(exists=True, updated=time.strftime('%d.%m.%Y %H:%M', time.localtime(f.stat().st_mtime)))
    return s


class H(BaseHTTPRequestHandler):
    def log_message(self, fmt, *a):
        sys.stderr.write('%s %s\n' % (self.address_string(), fmt % a))

    def send(self, code, body, ctype='application/json; charset=utf-8'):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        p = self.path.split('?')[0]
        if p == '/api/status':
            return self.send(200, current_info())
        if p in ('/admin', '/admin/'):
            return self.send(200, (ROOT / 'admin.html').read_bytes(), TYPES['.html'])
        if p in ('/', '/index.html'):
            f = ROOT / 'index.html'
        elif p in ('/schedule.json', '/schedule.js'):
            f = ROOT / p[1:]
        else:
            return self.send(404, {'error': 'not found'})
        if not f.exists():
            return self.send(404, {'error': 'not found'})
        self.send(200, f.read_bytes(), TYPES.get(f.suffix, 'application/octet-stream'))

    def do_POST(self):
        p = self.path.split('?')[0]
        try:
            if p == '/api/preview':
                n = int(self.headers.get('Content-Length', 0))
                if n <= 0 or n > MAX_BYTES:
                    raise ValueError('Datei fehlt oder ist zu groß.')
                s = convert(self.rfile.read(n))
                return self.send(200, {'ok': True, 'summary': s})
            if p == '/api/apply':
                apply_pending()
                return self.send(200, {'ok': True, 'current': current_info()})
            self.send(404, {'error': 'not found'})
        except ValueError as e:
            self.send(400, {'ok': False, 'error': str(e)})
        except Exception as e:  # noqa
            self.send(500, {'ok': False, 'error': f'Interner Fehler: {e}'})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8080)
    ap.add_argument('--lan', action='store_true', help='auch aus dem Netzwerk erreichbar (Admin ohne Passwort)')
    a = ap.parse_args()
    DATA.mkdir(exist_ok=True)
    host = '0.0.0.0' if a.lan else '127.0.0.1'
    print(f'Kiosk:  http://localhost:{a.port}/\nAdmin:  http://localhost:{a.port}/admin' + ('   (im Netzwerk erreichbar)' if a.lan else ''))
    ThreadingHTTPServer((host, a.port), H).serve_forever()


if __name__ == '__main__':
    main()

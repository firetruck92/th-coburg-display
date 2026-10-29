#!/usr/bin/env python3
"""Kiosk-Server: liefert die Anzeige und eine Admin-Seite zum Hochladen der Excel-Zeitplanung.

    python3 server.py            # nur lokal erreichbar (http://localhost:8080)
    python3 server.py --lan      # auch aus dem WLAN erreichbar (Admin ohne Passwort!)
"""
import argparse, json, re, shutil, subprocess, sys, tempfile, threading, time, uuid
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


def backup_current():
    BACKUP.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime('%Y%m%d-%H%M%S')
    for name in ('schedule.json', 'schedule.js'):
        cur = ROOT / name
        if cur.exists():
            shutil.copy2(cur, BACKUP / f'{stamp}-{name}')


def prune_backups():
    old = sorted(BACKUP.glob('*-schedule.json'))
    for f in old[:-10]:  # nur die letzten 10 Sicherungen behalten
        f.unlink(missing_ok=True)
        (BACKUP / f.name.replace('.json', '.js')).unlink(missing_ok=True)


def apply_pending():
    if not (PENDING / 'schedule.json').exists():
        raise ValueError('Keine Vorschau vorhanden. Bitte Datei zuerst hochladen.')
    backup_current()
    # atomar ersetzen, damit der Kiosk nie eine halbe Datei liest
    for name in ('schedule.js', 'schedule.json'):
        tmp = ROOT / (name + '.tmp')
        shutil.copy2(PENDING / name, tmp)
        tmp.replace(ROOT / name)
    shutil.copy2(PENDING / 'upload.xlsx', DATA / 'zeitplanung.xlsx')
    shutil.rmtree(PENDING, ignore_errors=True)
    prune_backups()


def clear_all():
    """Stundenplan und Termine leeren. Vorher wird eine Sicherung angelegt."""
    backup_current()
    empty = {'meta': {'cleared': time.strftime('%Y-%m-%dT%H:%M:%S'), 'semesters': []},
             'lessons': [], 'events': [], 'notes': []}
    text = {'schedule.json': json.dumps(empty, ensure_ascii=False, indent=1),
            'schedule.js': 'window.SCHEDULE = ' + json.dumps(empty, ensure_ascii=False) + ';\n'}
    for name, body in text.items():
        tmp = ROOT / (name + '.tmp')
        tmp.write_text(body, encoding='utf-8')
        tmp.replace(ROOT / name)
    (DATA / 'zeitplanung.xlsx').unlink(missing_ok=True)
    shutil.rmtree(PENDING, ignore_errors=True)
    prune_backups()


def current_info():
    f = ROOT / 'schedule.json'
    if not f.exists():
        return {'exists': False}
    js = json.loads(f.read_text(encoding='utf-8'))
    s = summarize(js)
    s.update(exists=True, updated=time.strftime('%d.%m.%Y %H:%M', time.localtime(f.stat().st_mtime)))
    return s


COFFEE = DATA / 'coffee.json'
COFFEE_LOCK = threading.Lock()
COFFEE_MAX = 3         # Tassen pro Person ...
COFFEE_WINDOW = 3600   # ... in diesem Zeitfenster (Sekunden, gleitend)
COFFEE_NAME_MAX = 30


def coffee_load():
    try:
        return json.loads(COFFEE.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return []


def semester_start():
    """Beginn der Semesterwertung: erster Vorlesungstag im Stundenplan (sonst alles zählen)."""
    try:
        js = json.loads((ROOT / 'schedule.json').read_text(encoding='utf-8'))
        first = min(l['date'] for l in js['lessons'])
        return time.mktime(time.strptime(first, '%Y-%m-%d'))
    except (OSError, ValueError, KeyError):
        return 0


def coffee_rows(entries, now):
    lt = time.localtime(now)
    day = time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, 0, 0, 0, 0, 0, -1))
    week = day - lt.tm_wday * 86400
    sem = semester_start()
    rows = {}
    for e in entries:
        r = rows.setdefault(e['n'].lower(), {'n': e['n'], 'v': [0, 0, 0]})
        if e['t'] >= day:
            r['v'][0] += e['c']
        if e['t'] >= week:
            r['v'][1] += e['c']
        if e['t'] >= sem:
            r['v'][2] += e['c']
    return list(rows.values())


def coffee_add(name, cups):
    """Trägt Tassen ein. Gibt (rows, None) oder (None, Fehler-dict) bei überschrittenem Limit zurück."""
    name = ' '.join(str(name).split())[:COFFEE_NAME_MAX]
    if not name:
        raise ValueError('Name fehlt.')
    if not isinstance(cups, int) or not 1 <= cups <= COFFEE_MAX:
        raise ValueError(f'Anzahl Tassen muss zwischen 1 und {COFFEE_MAX} liegen.')
    with COFFEE_LOCK:
        now = time.time()
        entries = coffee_load()
        recent = sorted((e for e in entries if e['n'].lower() == name.lower() and now - e['t'] < COFFEE_WINDOW),
                        key=lambda e: e['t'])
        used = sum(e['c'] for e in recent)
        if used + cups > COFFEE_MAX:
            need, freed, retry = used + cups - COFFEE_MAX, 0, 0
            for e in recent:
                freed += e['c']
                if freed >= need:
                    retry = e['t'] + COFFEE_WINDOW - now
                    break
            return None, {'limit': COFFEE_MAX, 'remaining': COFFEE_MAX - used, 'retry_minutes': max(1, int(retry // 60) + 1)}
        # vorhandene Schreibweise des Namens beibehalten
        known = next((e['n'] for e in entries if e['n'].lower() == name.lower()), name)
        entries.append({'n': known, 'c': cups, 't': now})
        DATA.mkdir(exist_ok=True)
        tmp = COFFEE.with_suffix('.tmp')
        tmp.write_text(json.dumps(entries, ensure_ascii=False), encoding='utf-8')
        tmp.replace(COFFEE)
        return coffee_rows(entries, now), None


def coffee_remove(name=None):
    """Entfernt eine Person (name) oder alle Einträge (name=None). Vorher Sicherung in data/backup/."""
    with COFFEE_LOCK:
        entries = coffee_load()
        if not entries:
            return
        BACKUP.mkdir(parents=True, exist_ok=True)
        shutil.copy2(COFFEE, BACKUP / f'{time.strftime("%Y%m%d-%H%M%S")}-coffee.json')
        for f in sorted(BACKUP.glob('*-coffee.json'))[:-10]:
            f.unlink(missing_ok=True)
        keep = [] if name is None else [e for e in entries if e['n'].lower() != ' '.join(str(name).split()).lower()]
        tmp = COFFEE.with_suffix('.tmp')
        tmp.write_text(json.dumps(keep, ensure_ascii=False), encoding='utf-8')
        tmp.replace(COFFEE)


# Listen, die über die Admin-Seite gepflegt werden: Events und Profs Kontakt
STORES = {
    'events': {'file': DATA / 'events.json', 'req': ('d', 't'), 'fields': ('d', 'time', 't', 'o', 'g')},
    'profs': {'file': DATA / 'profs.json', 'req': ('n', 'f'), 'fields': ('n', 'f', 'r', 'h', 'm', 'p')},
}
STORE_LOCK = threading.Lock()
STORE_MAX_ITEMS = 500
STORE_MAX_LEN = 200
LABELS = {'d': 'Datum', 't': 'Titel', 'n': 'Name', 'f': 'Fakultät', 'time': 'Uhrzeit'}


def store_load(kind):
    try:
        return json.loads(STORES[kind]['file'].read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return []


def store_write(kind, items):
    DATA.mkdir(exist_ok=True)
    f = STORES[kind]['file']
    tmp = f.with_suffix('.tmp')
    tmp.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding='utf-8')
    tmp.replace(f)


def store_save(kind, body):
    """Legt einen Eintrag an oder ändert ihn (wenn body['id'] bekannt ist)."""
    cfg = STORES[kind]
    item = {k: ' '.join(str(body.get(k, '')).split())[:STORE_MAX_LEN] for k in cfg['fields']}
    for k in cfg['req']:
        if not item[k]:
            raise ValueError(f'Pflichtfeld fehlt: {LABELS.get(k, k)}.')
    if kind == 'events':
        try:
            time.strptime(item['d'], '%Y-%m-%d')
        except ValueError:
            raise ValueError('Ungültiges Datum.')
        if item['time'] and not re.fullmatch(r'\d{1,2}:\d{2}', item['time']):
            raise ValueError('Ungültige Uhrzeit (Format HH:MM).')
    with STORE_LOCK:
        items = store_load(kind)
        old = next((i for i in items if i['id'] == body.get('id')), None)
        if old:
            old.update(item)
        else:
            if len(items) >= STORE_MAX_ITEMS:
                raise ValueError('Zu viele Einträge.')
            items.append({'id': uuid.uuid4().hex[:8], **item})
        store_write(kind, items)
        return items


def store_delete(kind, item_id):
    with STORE_LOCK:
        items = [i for i in store_load(kind) if i['id'] != item_id]
        store_write(kind, items)
        return items


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
        if p == '/api/coffee':
            return self.send(200, {'rows': coffee_rows(coffee_load(), time.time()), 'max': COFFEE_MAX})
        if p in ('/api/events', '/api/profs'):
            return self.send(200, {'items': store_load(p[5:])})
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
            m = re.fullmatch(r'/api/(events|profs)/(save|delete)', p)
            if m:
                n = int(self.headers.get('Content-Length', 0))
                if n <= 0 or n > 4096:
                    raise ValueError('Ungültige Anfrage.')
                body = json.loads(self.rfile.read(n))
                kind = m.group(1)
                items = store_save(kind, body) if m.group(2) == 'save' else store_delete(kind, body.get('id'))
                return self.send(200, {'ok': True, 'items': items})
            if p in ('/api/coffee/clear', '/api/coffee/remove'):
                name = None
                if p.endswith('remove'):
                    n = int(self.headers.get('Content-Length', 0))
                    name = json.loads(self.rfile.read(n)).get('name', '') if 0 < n <= 2048 else ''
                    if not str(name).strip():
                        raise ValueError('Name fehlt.')
                coffee_remove(name)
                return self.send(200, {'ok': True, 'rows': coffee_rows(coffee_load(), time.time())})
            if p == '/api/coffee':
                n = int(self.headers.get('Content-Length', 0))
                if n <= 0 or n > 2048:
                    raise ValueError('Ungültige Anfrage.')
                body = json.loads(self.rfile.read(n))
                rows, err = coffee_add(body.get('name', ''), body.get('cups'))
                if err:
                    return self.send(429, {'ok': False, **err})
                return self.send(200, {'ok': True, 'rows': rows})
            if p == '/api/clear':
                clear_all()
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

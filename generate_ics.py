#!/usr/bin/env python3
"""Rebuilds calendar.ics from sessions.json.  Run:  python3 generate_ics.py
Subscribers' calendars update from calendar.ics, so re-run this and re-deploy
whenever sessions.json changes (a new month, a time change, a cancellation)."""
import json, datetime as dt, pathlib

here = pathlib.Path(__file__).parent
cfg = json.loads((here / "sessions.json").read_text())

def esc(s):
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

def utc(s):
    return dt.datetime.fromisoformat(s).astimezone(dt.timezone.utc)

def fold(line):
    out, b = [], line.encode()
    while len(b) > 74:
        cut = 74
        while (b[cut] & 0xC0) == 0x80:
            cut -= 1
        out.append(b[:cut].decode()); b = b[cut:]
        b = b" " + b
    out.append(b.decode())
    return "\r\n".join(out)

now = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
HEAD = ["BEGIN:VCALENDAR", "VERSION:2.0",
     "PRODID:-//Monthly Mortgage Roundtable//Calendar//EN", "CALSCALE:GREGORIAN",
     "METHOD:PUBLISH", f"X-WR-CALNAME:{esc(cfg['title'])}",
     "X-WR-TIMEZONE:America/Chicago", "REFRESH-INTERVAL;VALUE=DURATION:PT6H",
     "X-PUBLISHED-TTL:PT6H"]
def write(path, lines):
    path.write_bytes(("\r\n".join(fold(x) for x in lines) + "\r\n").encode())
feed = []
for s in cfg["sessions"]:
    L = []
    st = utc(s["start"]); en = st + dt.timedelta(minutes=s["minutes"])
    status = s.get("status", "scheduled")
    desc = f"{cfg['tagline']}. Register and get details: {cfg['pageUrl']}"
    if status == "rescheduled":
        desc += " NOTE: this session was rescheduled. Check the page for the latest date and time."
    if s.get("note"):
        desc += " " + s["note"]
    title = cfg["title"] + (" (CANCELED)" if status == "cancelled" else "")
    L += ["BEGIN:VEVENT", f"UID:{s['id']}@monthlymortgageroundtable.com",
          f"DTSTAMP:{now}", f"SEQUENCE:{s.get('sequence', 0)}",
          f"DTSTART:{st:%Y%m%dT%H%M%SZ}", f"DTEND:{en:%Y%m%dT%H%M%SZ}",
          f"SUMMARY:{esc(title)}", f"DESCRIPTION:{esc(desc)}",
          f"LOCATION:{esc('Zoom Webinar - register at ' + cfg['pageUrl'])}",
          f"URL:{cfg['pageUrl']}",
          "STATUS:CANCELLED" if status == "cancelled" else "STATUS:CONFIRMED",
          "TRANSP:OPAQUE", "BEGIN:VALARM", "TRIGGER:-PT15M", "ACTION:DISPLAY",
          "DESCRIPTION:Monthly Mortgage Roundtable starts in 15 minutes", "END:VALARM",
          "END:VEVENT"]
    feed += L
    write(here / f"session-{s['id']}.ics", HEAD + L + ["END:VCALENDAR"])
write(here / "calendar.ics", HEAD + feed + ["END:VCALENDAR"])
print("calendar.ics and", len(cfg["sessions"]), "session file(s) written")

# rebuild index.html with the schedule embedded (so the page works even if sessions.json can't load)
import re as _re
tpl = (here / "index.template.html").read_text()
tx = (here / "tx.txt").read_text().strip()
m = _re.search(r'd="([^"]+)"', tx); tx = m.group(1) if m else tx
(here / "index.html").write_text(tpl.replace("%%TX%%", tx).replace("%%CFG%%", json.dumps(cfg)))
print("index.html rebuilt")

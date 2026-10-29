#!/usr/bin/env python3
"""Rebuilds index.html and the calendar files from sessions.json.

    python3 generate_ics.py

Files written:
  calendar.ics / monthly.ics  - the repeating monthly series (first Wednesday), with any moved or
                                canceled months from "overrides". Subscribers follow calendar.ics.
  session-YYYY-MM.ics         - a single session, for the "Just this session" buttons
  index.html                  - the page, with the schedule built in
Run it again whenever sessions.json changes, then re-deploy.
"""
import json, re, datetime as dt, pathlib
from zoneinfo import ZoneInfo

here = pathlib.Path(__file__).parent
cfg = json.loads((here / "sessions.json").read_text())
CT = ZoneInfo("America/Chicago")
UTC = dt.timezone.utc
ser = cfg["series"]
hh, mm = map(int, ser["time"].split(":"))
anchor = dt.date.fromisoformat(ser["anchor"])
overrides = {o["month"]: o for o in cfg.get("overrides", [])}
LINK = cfg["pageUrl"]
DOMAIN = "monthlymortgageroundtable.com"
now = dt.datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def esc(s):
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def fold(line):
    out, b = [], line.encode()
    while len(b) > 74:
        cut = 74
        while (b[cut] & 0xC0) == 0x80:
            cut -= 1
        out.append(b[:cut].decode())
        b = b" " + b[cut:]
    out.append(b.decode())
    return "\r\n".join(out)


def write(path, lines):
    path.write_bytes(("\r\n".join(fold(x) for x in lines) + "\r\n").encode())


def first_wed(y, m):
    d = dt.date(y, m, 1)
    while d.weekday() != 2:
        d += dt.timedelta(days=1)
    return d


def local(d, h=hh, m=mm):
    return dt.datetime(d.year, d.month, d.day, h, m, tzinfo=CT)


def utc(s):
    return s.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def lt(s):
    return s.strftime("%Y%m%dT%H%M%S")


DESC = LINK + "\n\n" + cfg["tagline"] + ". Register and get details at the link above. If the date or time changes, the latest is always on that page."
ALARM = ["BEGIN:VALARM", "TRIGGER:-PT15M", "ACTION:DISPLAY",
         "DESCRIPTION:Monthly Mortgage Roundtable starts in 15 minutes", "END:VALARM"]
HEAD = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Monthly Mortgage Roundtable//Calendar//EN",
        "CALSCALE:GREGORIAN", "METHOD:PUBLISH", f"X-WR-CALNAME:{esc(cfg['title'])}",
        "X-WR-TIMEZONE:America/Chicago", "REFRESH-INTERVAL;VALUE=DURATION:PT6H", "X-PUBLISHED-TTL:PT6H"]
VTZ = ["BEGIN:VTIMEZONE", "TZID:America/Chicago",
       "BEGIN:DAYLIGHT", "TZOFFSETFROM:-0600", "TZOFFSETTO:-0500", "TZNAME:CDT",
       "DTSTART:19700308T020000", "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU", "END:DAYLIGHT",
       "BEGIN:STANDARD", "TZOFFSETFROM:-0500", "TZOFFSETTO:-0600", "TZNAME:CST",
       "DTSTART:19701101T020000", "RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU", "END:STANDARD",
       "END:VTIMEZONE"]


def base_props(summary):
    return [f"SUMMARY:{esc(summary)}", f"DESCRIPTION:{esc(DESC)}", f"LOCATION:{esc(LINK)}", f"URL:{LINK}"]


# ---- the repeating series -------------------------------------------------
first = local(anchor)
series = ["BEGIN:VEVENT", f"UID:series@{DOMAIN}", f"DTSTAMP:{now}", "SEQUENCE:" + str(len(overrides)),
          f"DTSTART;TZID=America/Chicago:{lt(first)}",
          f"DTEND;TZID=America/Chicago:{lt(first + dt.timedelta(minutes=ser['minutes']))}",
          f"RRULE:{ser['rule']}"]
exdates, moved = [], []
for month, o in sorted(overrides.items()):
    y, m = map(int, month.split("-"))
    orig = local(first_wed(y, m))
    if o.get("status") == "cancelled":
        exdates.append(orig)
    else:
        moved.append((orig, o))
if exdates:
    series.append("EXDATE;TZID=America/Chicago:" + ",".join(lt(x) for x in exdates))
series += base_props(cfg["title"]) + ["STATUS:CONFIRMED", "TRANSP:OPAQUE"] + ALARM + ["END:VEVENT"]
events = list(series)
for orig, o in moved:
    st = dt.datetime.fromisoformat(o["start"]).astimezone(CT)
    en = st + dt.timedelta(minutes=o.get("minutes", ser["minutes"]))
    desc_note = " NOTE: this session was rescheduled." + (" " + o["note"] if o.get("note") else "")
    events += ["BEGIN:VEVENT", f"UID:series@{DOMAIN}", f"DTSTAMP:{now}", "SEQUENCE:1",
               f"RECURRENCE-ID;TZID=America/Chicago:{lt(orig)}",
               f"DTSTART;TZID=America/Chicago:{lt(st)}", f"DTEND;TZID=America/Chicago:{lt(en)}",
               f"SUMMARY:{esc(cfg['title'])}", f"DESCRIPTION:{esc(DESC + desc_note)}",
               f"LOCATION:{esc(LINK)}", f"URL:{LINK}", "STATUS:CONFIRMED", "TRANSP:OPAQUE"] + ALARM + ["END:VEVENT"]
cal = HEAD + VTZ + events + ["END:VCALENDAR"]
write(here / "calendar.ics", cal)
write(here / "monthly.ics", cal)

# ---- single-session files for the next 14 months --------------------------
for p in here.glob("session-*.ics"):
    p.unlink()
y, m = max(dt.date.today(), anchor).year, max(dt.date.today(), anchor).month
count = 0
for k in range(-1, 14):
    yy, mm_ = divmod(y * 12 + (m - 1) + k, 12)
    mm_ += 1
    key = f"{yy}-{mm_:02d}"
    orig = local(first_wed(yy, mm_))
    if orig.date() < anchor:
        continue
    o = overrides.get(key)
    st, mins, status = orig, ser["minutes"], "CONFIRMED"
    title, extra = cfg["title"], ""
    if o:
        if o.get("start"):
            st = dt.datetime.fromisoformat(o["start"]).astimezone(CT)
        mins = o.get("minutes", mins)
        if o.get("status") == "cancelled":
            status, title = "CANCELLED", cfg["title"] + " (CANCELED)"
        else:
            extra = " NOTE: this session was rescheduled." + (" " + o["note"] if o.get("note") else "")
    en = st + dt.timedelta(minutes=mins)
    lines = ["BEGIN:VEVENT", f"UID:session-{key}@{DOMAIN}", f"DTSTAMP:{now}", f"SEQUENCE:{1 if o else 0}",
             f"DTSTART:{utc(st)}", f"DTEND:{utc(en)}", f"SUMMARY:{esc(title)}",
             f"DESCRIPTION:{esc(DESC + extra)}", f"LOCATION:{esc(LINK)}", f"URL:{LINK}",
             f"STATUS:{status}", "TRANSP:OPAQUE"] + ALARM + ["END:VEVENT"]
    write(here / f"session-{key}.ics", HEAD + lines + ["END:VCALENDAR"])
    count += 1
print(f"calendar.ics, monthly.ics and {count} single-session files written")

# ---- the page, with the schedule built in ----------------------------------
tpl = (here / "index.template.html").read_text()
tx = (here / "tx.txt").read_text().strip()
mt = re.search(r'd="([^"]+)"', tx)
tx = mt.group(1) if mt else tx
(here / "index.html").write_text(tpl.replace("%%TX%%", tx).replace("%%CFG%%", json.dumps(cfg)))
print("index.html rebuilt")

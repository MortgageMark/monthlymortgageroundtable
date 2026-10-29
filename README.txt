MONTHLY MORTGAGE ROUNDTABLE - website files

The page repeats automatically on the FIRST WEDNESDAY of each month at 10:30 AM Central (1 hour).
You only edit sessions.json when something changes.

CHANGE OR CANCEL ONE MONTH: add an entry to "overrides" in sessions.json, for example:
  "overrides": [
    {"month":"2026-12","start":"2026-12-09T10:30:00-06:00","minutes":60,"status":"rescheduled","note":""}
  ]
  - "month" is the month the session normally falls in (YYYY-MM)
  - "start" is the new date and time. -06:00 = winter Central time, -05:00 = summer (Mar-Nov)
  - to cancel instead: {"month":"2026-12","status":"cancelled"}
THEN: run  python3 generate_ics.py  (or send sessions.json to Claude and ask for updated files)
THEN: upload index.html, sessions.json, calendar.ics, monthly.ics and the session-*.ics files to GitHub (or drag the folder onto Netlify).

CHANGE THE REGISTRATION LINK: edit "registerUrl" in sessions.json, then run generate_ics.py and re-upload.
Do not edit the .ics files or index.html by hand; they are generated.

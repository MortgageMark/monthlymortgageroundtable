MONTHLY MORTGAGE ROUNDTABLE - website files

TO PUBLISH: on Netlify, drag this whole folder (unzipped) onto "Deploy manually".
BEFORE YOU PUBLISH: open sessions.json and replace the registerUrl with your Zoom registration link.

EACH MONTH / WHEN A TIME CHANGES:
1. Edit sessions.json (add the new session, or change "start").
   - start format: 2026-12-02T11:00:00-06:00  (-06:00 = winter Central time, -05:00 = summer)
   - to reschedule: set "status" to "rescheduled", put the old time in "previousStart", and add 1 to "sequence"
   - to cancel: set "status" to "cancelled"
   - give every session a unique "id", like 2026-12
2. Run: python3 generate_ics.py   (or send sessions.json to Claude and ask for the updated calendar files)
3. Re-deploy the folder.
Do not use the files named session-*.ics or calendar.ics as a place to edit; they are generated.

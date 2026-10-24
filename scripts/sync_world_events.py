from __future__ import annotations
import csv, io, json, re
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

SOURCE_URL = "https://raw.githubusercontent.com/snauhaus/historic_events/master/historic_events.tsv"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "world_historical_events.json"

MONTHS={m:i for i,m in enumerate(["January","February","March","April","May","June","July","August","September","October","November","December"],1)}
DATE_RE=re.compile(r"^(January|February|March|April|May|June|July|August|September|October|November|December) (\d{1,2})$")

def event_type(kind:int)->str:
    return {1:"world_event",2:"birth",3:"death"}.get(kind,"world_event")

def parse(limit=1000):
    req=Request(SOURCE_URL,headers={"User-Agent":"Jyotish-Lab-world-corpus/0.8.7"})
    with urlopen(req,timeout=30) as r:
        raw=r.read().decode("utf-8","replace")
    rows=[]
    for line in raw.splitlines():
        parts=line.split("\t",3)
        if len(parts)!=4: continue
        year_s,kind_s,md,desc=parts
        m=DATE_RE.match(md.strip())
        if not m: continue
        try: year=int(year_s); kind=int(kind_s); month=MONTHS[m.group(1)]; day=int(m.group(2))
        except ValueError: continue
        # Skip dates outside the datetime range supported by the astronomy layer.
        if year < 1 or year > 9999: continue
        dt=f"{year:04d}-{month:02d}-{day:02d}"
        rows.append({
            "country":"World","event_name":re.sub(r"\[/?i\]","",desc).strip(),
            "local_date":dt,"local_time":"12:00:00","place":"Global","latitude":0.0,"longitude":0.0,
            "timezone":"UTC","event_type":event_type(kind),
            "source_note":"Imported from snauhaus/historic_events; date-only source record, noon UTC reference used for astronomical pattern matching. CC BY-SA 3.0."
        })
        if len(rows)>=limit: break
    # Deduplicate by date/name.
    seen=set(); out=[]
    for row in rows:
        key=(row["local_date"],row["event_name"])
        if key not in seen:
            seen.add(key); out.append(row)
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
    return len(out)

if __name__ == "__main__":
    n=parse(1000)
    print(f"Wrote {n} world historical events to {OUT}")
    if n < 1000:
        raise SystemExit("Source yielded fewer than 1000 exact-date records")

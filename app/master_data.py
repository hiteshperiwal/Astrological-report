"""Curated public-figure reference data loaded from the bundled JSON corpus.

Birth times are never invented. Profiles without a reliably verified public birth
time use a clearly labelled 12:00 local reference chart.
"""
from __future__ import annotations
import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "reference_profiles.json"

FALLBACK_PEOPLE = [
    {"name":"Narendra Modi","category":"politician","dob":"1950-09-17","tob":None,"place":"Vadnagar, Gujarat, India","latitude":23.813,"longitude":72.638,"timezone":"Asia/Kolkata","time_status":"unknown","source":"PM India biography"},
    {"name":"Mahatma Gandhi","category":"historical_political","dob":"1869-10-02","tob":None,"place":"Porbandar, Gujarat, India","latitude":21.6417,"longitude":69.6293,"timezone":"Asia/Kolkata","time_status":"unknown","source":"Government of India / Rajghat chronology"},
]

def _load_people():
    try:
        rows=json.loads(DATA_PATH.read_text(encoding="utf-8"))
        if isinstance(rows,list) and rows:
            return rows
    except Exception:
        pass
    return FALLBACK_PEOPLE

PEOPLE = _load_people()

ALIASES={
    "modi":"Narendra Modi","narendra modi":"Narendra Modi","gandhi":"Mahatma Gandhi","mahatma gandhi":"Mahatma Gandhi",
    "rahul gandhi":"Rahul Gandhi","mamata":"Mamata Banerjee","mamata banerjee":"Mamata Banerjee","ambani":"Mukesh Ambani",
    "mukesh ambani":"Mukesh Ambani","elon musk":"Elon Musk","musk":"Elon Musk","bill gates":"Bill Gates","jeff bezos":"Jeff Bezos",
    "ratan tata":"Ratan Tata","dhirubhai ambani":"Dhirubhai Ambani",
}

def canonical_person(name:str)->str:
    k=" ".join(name.strip().lower().split())
    return ALIASES.get(k,name.strip())

def search_people(query:str="",category:str|None=None):
    q=query.strip().lower()
    rows=[p for p in PEOPLE if (not q or q in p.get("name","").lower()) and (not category or p.get("category")==category)]
    return rows

def get_person(name:str):
    c=canonical_person(name)
    for p in PEOPLE:
        if p.get("name")==c:return p
    raise KeyError(f"No reference profile for {name}")

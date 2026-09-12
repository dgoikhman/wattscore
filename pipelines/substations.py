"""Watt Score — substation layer from OpenStreetMap (Overpass API).
Public ODbL data (attribution on-site). Output: data/substations.csv.
Run: python pipelines/substations.py | offline: WS_LOCAL=data/test_fixtures"""
import csv, json, os, sys, time
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATES = os.environ.get("WS_STATES", "US-TX,US-OH,US-MI").split(",")
OVERPASS = "https://overpass-api.de/api/interpreter"
OUT = os.path.join(ROOT, "data", "substations.csv")

def fetch(state):
    local = os.environ.get("WS_LOCAL")
    if local:
        p = os.path.join(local, f"osm_{state[-2:].lower()}.json")
        return json.load(open(p)) if os.path.exists(p) else {"elements": []}
    q = ('[out:json][timeout:180];area["ISO3166-2"="%s"][admin_level=4]->.a;'
         '(node["power"="substation"](area.a);way["power"="substation"](area.a););'
         'out center tags;' % state)
    r = requests.post(OVERPASS, data={"data": q}, timeout=300,
                      headers={"User-Agent": "WattScore/0.1 (public data research)"})
    r.raise_for_status()
    return r.json()

def main():
    rows = []
    for st in STATES:
        try:
            data = fetch(st)
        except Exception as e:
            print(f"[substations] {st} FAILED: {e}")
            continue
        n = 0
        for e in data.get("elements", []):
            lat = e.get("lat") or (e.get("center") or {}).get("lat")
            lon = e.get("lon") or (e.get("center") or {}).get("lon")
            if not lat:
                continue
            t = e.get("tags", {})
            rows.append({"state": st[-2:], "lat": round(lat, 5), "lon": round(lon, 5),
                         "voltage": t.get("voltage", ""), "name": t.get("name", "")})
            n += 1
        print(f"[substations] {st}: {n}")
        time.sleep(2)
    if len(rows) < 50 and not os.environ.get("WS_LOCAL"):
        sys.exit("[error] implausibly few substations — query likely broken")
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["state", "lat", "lon", "voltage", "name"])
        w.writeheader(); w.writerows(rows)
    print(f"[done] {len(rows)} substations -> {OUT}")

if __name__ == "__main__":
    main()

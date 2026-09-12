"""Watt Score — closure signals from state WARN notices (public records).
WARN filings are public notices that include employer name, site city,
affected headcount, dates, and usually a company contact. Tolerant table
parsing (state formats drift; failures log loudly for the repair agent).
Watt Score v0.1 = facility size 40 + industrial classification 40 +
freshness 20. Grid proximity joins in v0.2 with parcel geocoding — scored
honestly as absent until then, never faked.
Output: data/leads.csv (public-safe) + data/pro/leads_contacts.csv
(contact names from the filings — customer delivery only, gitignored)."""
import csv, io, os, re, sys, datetime
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HDRS = {"User-Agent": "Mozilla/5.0 (WattScore research; public records)"}
SOURCES = {
    "TX": ["https://www.twc.texas.gov/data-reports/warn-act-listings",
           "https://www.twc.texas.gov/news/warn-act-listings"],
    "OH": ["https://jfs.ohio.gov/job-services-and-unemployment/job-services/warn/current-warn-notices",
           "https://jfs.ohio.gov/warn/current.stm"],
    "MI": ["https://www.michigan.gov/leo/bureaus-agencies/wd/warn-notices",
           "https://milmi.org/warn"],
}
IND_HOT = re.compile(r"manufactur|steel|alumin|paper|mill|plastic|chemical|distribut|"
                     r"warehouse|logistic|assembl|foundry|machin|print|textile|food|"
                     r"process|plant|refin|smelt|fabricat|industri|packag|automotive|tool", re.I)

def read_tables(url):
    import pandas as pd
    r = requests.get(url, headers=HDRS, timeout=90)
    r.raise_for_status()
    if "spreadsheet" in r.headers.get("content-type", "") or url.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(r.content), sheet_name=0), url
    tables = pd.read_html(io.StringIO(r.text))
    return max(tables, key=len), url

def col(df, *keys):
    for c in df.columns:
        if any(k in str(c).lower() for k in keys):
            return c
    return None

def watt_score(employees, industrial):
    size = min(1.0, (employees or 0) / 400) * 40
    ind = 40 if industrial else 12
    return round(size + ind + 20)   # +20 freshness: current-notice files only

def main():
    local = os.environ.get("WS_LOCAL")
    leads, pro = [], []
    for st, urls in SOURCES.items():
        df, src = None, ""
        if local:
            p = os.path.join(local, f"warn_{st.lower()}.csv")
            if os.path.exists(p):
                import pandas as pd
                df, src = pd.read_csv(p), f"fixture:{st}"
        else:
            for u in urls:
                try:
                    df, src = read_tables(u)
                    print(f"[warn:{st}] parsed {len(df)} rows from {u}")
                    break
                except Exception as e:
                    print(f"[warn:{st}] {u} -> {type(e).__name__}: {str(e)[:90]}")
        if df is None or not len(df):
            print(f"[warn:{st}] NO PARSE — repair-agent attention needed")
            continue
        c_co = col(df, "company", "employer", "business")
        c_city = col(df, "city", "location", "address")
        c_n = col(df, "affected", "employees", "workers", "number", "total", "laid")
        c_contact = col(df, "contact", "official", "representative")
        if not c_co:
            print(f"[warn:{st}] no company column in parsed table — repair needed")
            continue
        for _, r in df.iterrows():
            co = str(r.get(c_co, "")).strip()
            if not co or co.lower() in ("nan", "company", "none"):
                continue
            city = str(r.get(c_city, "")).replace("nan", "").strip() if c_city else ""
            try:
                emp = int(re.sub(r"\D", "", str(r.get(c_n, "")))[:6] or 0) if c_n else 0
            except Exception:
                emp = 0
            ind = bool(IND_HOT.search(co)) or (emp >= 200)
            row = {"state": st, "company": co[:80], "city": city.title()[:40],
                   "employees": emp, "industrial": "Y" if ind else "N",
                   "watt": watt_score(emp, ind),
                   "as_of": datetime.date.today().isoformat(), "source": src}
            leads.append(row)
            contact = str(r.get(c_contact, "")).replace("nan", "").strip() if c_contact else ""
            pro.append({**row, "contact": contact[:80]})
    if not leads:
        sys.exit("[error] zero leads parsed across all states")
    leads.sort(key=lambda x: -x["watt"]); pro.sort(key=lambda x: -x["watt"])
    with open(os.path.join(ROOT, "data", "leads.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(leads[0].keys())); w.writeheader(); w.writerows(leads)
    os.makedirs(os.path.join(ROOT, "data", "pro"), exist_ok=True)
    with open(os.path.join(ROOT, "data", "pro", "leads_contacts.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(pro[0].keys())); w.writeheader(); w.writerows(pro)
    hot = sum(1 for l in leads if l["watt"] >= 70)
    print(f"[done] {len(leads)} scored closure leads ({hot} rated 70+) -> data/leads.csv; contacts in data/pro/ (gitignored)")

if __name__ == "__main__":
    main()

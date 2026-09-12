"""Watt Score — teaser site + private customer feed."""
import csv, json, os, sys, datetime
from jinja2 import Environment, DictLoader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out")
BASE_URL = (sys.argv[sys.argv.index("--base-url") + 1].rstrip("/")
            if "--base-url" in sys.argv else "https://dgoikhman.github.io/wattscore")
TODAY = datetime.date.today().strftime("%B %d, %Y")

BASE = """<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title }}</title><meta name="description" content="{{ description }}">
<link rel="canonical" href="{{ canonical }}">{% if noindex %}<meta name="robots" content="noindex, nofollow">{% endif %}
<style>
:root{--ink:#101418;--paper:#F4F2ED;--volt:#E6C229;--muted:#5C636B;--line:#D7D3C8;--grid:#25313B}
*{box-sizing:border-box;margin:0}body{background:var(--paper);color:var(--ink);font-family:"Avenir Next","Segoe UI",system-ui,sans-serif;line-height:1.55;font-variant-numeric:tabular-nums}
.wrap{max-width:780px;margin:0 auto;padding:20px 16px 60px}
header a{color:var(--ink);text-decoration:none;font-weight:800;letter-spacing:.04em;font-size:15px}
header span{color:#B8940D}
h1{font-size:clamp(24px,5.5vw,34px);line-height:1.12;margin:14px 0 10px}
h2{font-size:19px;margin:26px 0 8px}p{margin:10px 0;max-width:64ch}
.hero{background:linear-gradient(160deg,#101418,#25313B);color:#EDEAE0;margin:12px -16px 18px;padding:28px 18px 24px}
.hero h1{color:#fff}.hero .k{color:var(--volt)}.hero p{color:#C9CDC4}
.stat{display:inline-block;border:1px solid rgba(237,234,224,.3);border-radius:999px;padding:5px 12px;font-size:12.5px;margin:8px 8px 0 0;font-weight:600}
.stat b{color:var(--volt)}
table{border-collapse:collapse;width:100%;margin:12px 0;font-size:14px}
th,td{text-align:left;padding:8px 9px;border-bottom:1px solid var(--line)}
th{color:var(--muted);font-size:12.5px}td.n,th.n{text-align:right}
.chip{display:inline-block;min-width:2.2em;text-align:center;border-radius:4px;padding:1px 7px;font-weight:800;background:var(--volt);color:#101418}
.lock{color:var(--muted);letter-spacing:.14em}
.card{background:#fff;border:1px solid var(--line);border-radius:8px;padding:13px;margin:10px 0}
.meta{color:var(--muted);font-size:13px;border-top:1px solid var(--line);margin-top:26px;padding-top:12px}
button,.cta{font:inherit;font-weight:800;font-size:15px;padding:12px 18px;border-radius:7px;border:none;background:var(--volt);color:#101418;min-height:46px;text-decoration:none;display:inline-block}
</style></head><body><div class="wrap">
<header><a href="{{ base }}/">WATT<span>⚡</span>SCORE</a></header>
{{ body }}
<div class="meta"><p>Sources: state WARN notices (public records), OpenStreetMap power infrastructure (© OpenStreetMap contributors, ODbL). Watt Score v0.1 weighs facility scale, industrial classification, and signal freshness; grid-proximity scoring lands in v0.2 with parcel geocoding. Screening-grade intelligence — not a representation of interconnection availability. {{ today }}.</p></div>
</div></body></html>"""

INDEX = """
<div class="hero"><h1>Powered shells, <span class="k">found first</span></h1>
<p>When an industrial facility announces closure, its power infrastructure goes on sale — usually years before anyone lists it that way. We read the public closure filings, score every site's data-center potential, and hand you the lead before the market reprices it.</p>
<div><span class="stat"><b>{{ n }}</b> live closure leads</span><span class="stat"><b>{{ hot }}</b> rated 70+</span><span class="stat"><b>{{ subs }}</b> substations mapped</span><span class="stat">TX · OH · MI</span></div></div>
<h2>This week's board <span class="lock">— identities locked</span></h2>
{% if not teaser %}<p class="card">The first live sweep is running — the board populates within the hour.</p>{% endif %}
{% if teaser %}<table><tr><th>Watt</th><th>Signal</th><th class="n">Scale</th><th>State</th></tr>
{% for l in teaser %}<tr><td><span class="chip">{{ l.watt }}</span></td><td>{{ "Industrial closure" if l.industrial == "Y" else "Facility closure" }} · {{ l.city or "city withheld" }}</td><td class="n">{{ l.employees }} jobs</td><td>{{ l.state }}</td></tr>
{% endfor %}</table>{% endif %}
<div class="card"><b>The full board unlocks company names, addresses-of-record, filing details, and the outbound contact sheet</b> — refreshed weekly, delivered as a feed plus a CSV your outreach team can load directly. Founding seats: <b>$2,490/yr, 20 seats</b>. <p style="margin-top:8px"><a class="cta" href="mailto:dan@brrrrmarkets.com?subject=Watt%20Score%20founding%20seat">Request a founding seat</a></p></div>
<h2>Why closures</h2>
<p>Interconnection queues run 4-7 years. A shuttered plant already has industrial electrical service, water, fiber that followed the industry, and a motivated seller. Everyone bids the farmland next to the substation; the smarter trade is the building that already drew the load. WARN filings announce exactly these sites, publicly, with a contact attached — weeks before brokers circle.</p>"""

MEMBERS = """
<div class="hero"><h1>The board <span class="k">— full access</span></h1>
<p>Every scored closure lead with identities and the outbound sheet. Private link — please don't share. Refreshed weekly; CSV below for your outreach team.</p>
<div><span class="stat"><b>{{ n }}</b> leads</span><span class="stat">as of <b>{{ today }}</b></span></div></div>
<table><tr><th>Watt</th><th>Company</th><th>City</th><th class="n">Jobs</th><th>St</th><th>Contact</th></tr>
{% for l in rows %}<tr><td><span class="chip">{{ l.watt }}</span></td><td>{{ l.company }}</td><td>{{ l.city }}</td><td class="n">{{ l.employees }}</td><td>{{ l.state }}</td><td>{{ l.contact }}</td></tr>
{% endfor %}</table>
<p><a class="cta" href="{{ base }}/m/{{ tok }}/watt-leads.csv" download>Download the outbound CSV</a></p>
<p style="color:#5C636B;font-size:13.5px">Contacts come from the public filings themselves. Outreach etiquette: these are companies navigating closures — lead with the asset conversation, be human, honor any do-not-contact request permanently.</p>"""

env = Environment(loader=DictLoader({"base": BASE, "index": INDEX, "members": MEMBERS}))

def page(path, title, desc, body, noindex=False):
    html = env.get_template("base").render(title=title, description=desc, body=body,
        canonical=f"{BASE_URL}{path}", base=BASE_URL, today=TODAY, noindex=noindex)
    d = os.path.join(OUT, path.strip("/"))
    os.makedirs(d or OUT, exist_ok=True)
    open(os.path.join(d or OUT, "index.html"), "w").write(html)

def main():
    lp = os.path.join(ROOT, "data", "leads.csv")
    leads = [l for l in (csv.DictReader(open(lp)) if os.path.exists(lp) else [])
             if "fixture" not in l.get("source", "")]
    subs = sum(1 for _ in open(os.path.join(ROOT, "data", "substations.csv"))) - 1 \
        if os.path.exists(os.path.join(ROOT, "data", "substations.csv")) else 0
    hot = sum(1 for l in leads if int(l["watt"]) >= 70)
    page("/", "Watt Score: Powered Shells, Found First",
         "Industrial closures scored for data-center potential — the lead before the listing. TX, OH, MI live.",
         env.get_template("index").render(n=len(leads), hot=hot, subs=f"{subs:,}",
             teaser=leads[:10], base=BASE_URL))
    tok = os.environ.get("WS_MEMBERS_TOKEN", "")
    pp = os.path.join(ROOT, "data", "pro", "leads_contacts.csv")
    if tok and os.path.exists(pp):
        pro = list(csv.DictReader(open(pp)))
        page(f"/m/{tok}/", "Watt Score — Member Board", "Members only.",
             env.get_template("members").render(rows=pro, n=len(pro), today=TODAY,
                 base=BASE_URL, tok=tok), noindex=True)
        import shutil
        shutil.copy(pp, os.path.join(OUT, "m", tok, "watt-leads.csv"))
        print(f"[build] member board + CSV at /m/{tok[:4]}…/")
    open(os.path.join(OUT, "robots.txt"), "w").write(
        f"User-agent: *\nDisallow: /m/\nAllow: /\n")
    print(f"[build] wattscore site -> {OUT}")

if __name__ == "__main__":
    main()

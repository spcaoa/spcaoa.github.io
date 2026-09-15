#!/usr/bin/env python3
"""Build the residents' pages into docs/ from the MC site's data plus local JSON.
Usage: python3 tools/build.py   (passcode read from tools/passcode.txt; empty file = no gate)"""
import csv, json, os, sys, hashlib, datetime, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MC=os.path.join(os.path.dirname(ROOT),"spc-finance-site","site","data")
OUT=os.path.join(ROOT,"docs"); DATA=os.path.join(ROOT,"data")
UPDATED="15 September 2026"
def rd(p): return list(csv.DictReader(open(p,newline="",encoding="utf-8")))
def _assetver():
    h=hashlib.sha256()
    for f in ("site.css","ui.js","gate.js"):
        try: h.update(open(os.path.join(ROOT,"docs","assets",f),"rb").read())
        except FileNotFoundError: pass
    try: h.update(open(os.path.join(ROOT,"tools","passcode.txt"),"rb").read())
    except FileNotFoundError: pass
    return h.hexdigest()[:8]
VER=_assetver()
def L(n): return f"₹{n/1e5:.1f} L" if abs(n)<1e7 else f"₹{n/1e7:.2f} Cr"
def LL(n): return f"₹{n/1e5:.2f} L"
def INR(n): return "₹"+f"{round(n):,}".replace(",","_").replace("_",",")  # simple grouping
def inr(n):
    s=str(int(round(abs(n)))); 
    if len(s)>3: s=s[:-3][::-1]; s=",".join(s[i:i+2] for i in range(0,len(s),2))[::-1]+","+str(int(round(abs(n))))[-3:]
    return ("−" if n<0 else "")+"₹"+s
# ---------- data
ex=rd(os.path.join(MC,"expenses.csv")); inc=rd(os.path.join(MC,"income.csv")); tr=rd(os.path.join(MC,"treasury.csv")); sv=rd(os.path.join(MC,"survey.csv"))
for r in ex: r["amount"]=float(r["amount"] or 0)
for r in inc: r["amount"]=float(r["amount"] or 0)
spend=[r for r in ex if r["kind"]!="memo"]; months=sorted({r["month"] for r in spend}); nM=len(months)
ML=lambda m: datetime.date(int(m[:4]),int(m[5:7]),1).strftime("%b %y")
CATS=["Facility & housekeeping","Security","Utilities","Plant & equipment","Admin & governance","Taxes & statutory","One-time"]
CATCOL=['css("--c1")','css("--c3")','css("--c2")','css("--c4")','css("--c5")','css("--c6")','css("--c7")']  # raw JS exprs, resolved from CSS vars
bymc={m:{c:0 for c in CATS} for m in months}; byhead=collections.defaultdict(float)
for r in spend:
    c="One-time" if r["kind"]=="onetime" else r["category"]; bymc[r["month"]][c]+=r["amount"]
    if r["kind"]=="routine": byhead[r["head"]]+=r["amount"]
tot=sum(v for m in months for v in bymc[m].values()); routine=sum(r["amount"] for r in spend if r["kind"]=="routine"); onetime=tot-routine
cattot={c:sum(bymc[m][c] for m in months) for c in CATS}
maint=sum(r["amount"] for r in inc if r["line"]=="Maintenance billed")/nM
inc_lines=collections.defaultdict(float)
for r in inc: inc_lines[r["line"]]+=r["amount"]
hdfc_int=inc_lines.get("Interest - HDFC FDs (monthly payout)",0)/nM; sobha_int=inc_lines.get("Interest - corpus with Sobha",0)/nM
other=sum(v for k,v in inc_lines.items() if k not in("Maintenance billed","Maintenance received (incl. penal interest)") and "Interest" not in k)/nM
icici_acc=inc_lines.get("Interest - ICICI FDs (accrues to maturity)",0)/nM
fl=lambda r:float(r["bank_hdfc_close"])+float(r["bank_icici_close"])+float(r["cash_close"])
floats=[(ML(r["month"]),fl(r)) for r in tr]
fds=json.load(open(os.path.join(DATA,"fds.json"))); runway=json.load(open(os.path.join(DATA,"runway.json"))); rates=json.load(open(os.path.join(DATA,"rates.json")))
lifts=rd(os.path.join(DATA,"lifts.csv")); comps=rd(os.path.join(DATA,"complaints.csv"))
hdfc=[b for b in fds["banks"] if b["bank"].startswith("HDFC")][0]; icici=[b for b in fds["banks"] if b["bank"].startswith("ICICI")][0]; sobha=[b for b in fds["banks"] if "Sobha" in b["bank"]][0]
reserves=hdfc["principal"]+icici["ledger"]+sobha["principal"]
# survey aggregates
SV={"Very good":5,"Good":4,"Acceptable":3,"Poor":2,"Very poor":1}; OV={"Very satisfied":5,"Satisfied":4,"Neutral":3,"Dissatisfied":2,"Very dissatisfied":1}
SERV=[("s_housekeeping","Housekeeping and cleanliness"),("s_landscaping","Landscaping and gardening"),("s_waste","Waste collection"),("s_electrical","Electrical and lighting"),("s_plumbing","Plumbing and water"),("s_security","Security and access"),("s_common","Common-area upkeep and repairs"),("s_clubhouse","Clubhouse and amenities"),("s_helpdesk","Helpdesk / complaint handling"),("s_pest","Pest control"),("s_lifts","Lifts")]
def stat(rows,k,m=SV):
    v=[m[r[k]] for r in rows if r[k] in m]; poor=sum(1 for r in rows if r[k] in("Poor","Very poor")); return (sum(v)/len(v) if v else 0, len(v), poor)
n=len(sv); sat=sum(1 for r in sv if r["overall"] in("Satisfied","Very satisfied")); rep=[r for r in sv if r["reported"]=="Yes"]
serv=sorted([(l,)+stat(sv,k)+(k,) for k,l in SERV], key=lambda x:-x[1])
dist={k:{s:sum(1 for r in sv if r[k]==s) for s in ["Very good","Good","Acceptable","Poor","Very poor"]} for k,_ in SERV}
prio=collections.Counter(p for r in sv for p in r["priorities"].split("|") if p)
ISS=[("i_ease","Ease of reporting"),("i_courtesy","Courtesy of staff"),("i_quality","Quality of the fix"),("i_ack","Speed of acknowledgement"),("i_time","Time taken to resolve"),("i_comms","Communication and updates"),("i_ownership","Ownership until closure")]
iss=[(l,)+stat(rep,k) for k,l in ISS]
wings=sorted({r["wing"] for r in sv}); wingrows=[(w,sum(1 for r in sv if r["wing"]==w),sum(1 for r in sv if r["wing"]==w and r["overall"] in("Satisfied","Very satisfied")),stat([r for r in sv if r["wing"]==w],"s_lifts")[0]) for w in wings]
# ---------- html helpers
NAV=[("index.html","Where we stand"),("money.html","Money"),("shortfall.html","Shortfall"),("simulator.html","Options"),("reserves.html","Reserves"),("contracts.html","Contracts"),("actions.html","Actions"),("feedback.html","Survey"),("services.html","Lifts & complaints"),("documents.html","Documents")]
def page(fn,title,body,scripts=""):
    cur=' aria-current="page"'
    nav="".join(f'<a href="{f}"{cur if f==fn else ""}>{t}</a>' for f,t in NAV)
    html=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>{title} · Sobha Palm Court</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400..800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css?v={VER}"><script src="assets/gate.js?v={VER}"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script></head><body>
<div class="topbar"><div class="in"><a class="brand" href="index.html">Sobha Palm Court<small>Apartment Owners' Association</small></a><button class="menubtn" id="menubtn" aria-label="Menu" aria-expanded="false" aria-controls="tabs"><svg class="b" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 6h18M3 12h18M3 18h18"/></svg><svg class="x" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg></button><nav class="tabs" id="tabs" aria-label="Pages">{nav}</nav></div></div>
<div class="wrap">{body}
<div class="updated">Updated {UPDATED}. Accounts to end {ML(months[-1])}; deposits as at {fds["as_at"]}; survey August 2026. Published by the Managing Committee. Questions: spcaoa@gmail.com</div>
</div><footer>1 lakh = ₹1,00,000. 1 crore = 100 lakh. Figures come from the accountant's monthly statements and the banks' summaries. They are not audited. Updated monthly.</footer>
<script src="assets/ui.js?v={VER}"></script>
<script>{scripts}</script></body></html>'''
    open(os.path.join(OUT,fn),"w",encoding="utf-8").write(html)
def tile(cls,k,v,d): return f'<div class="tile {cls}"><div class="k">{k}</div><div class="v">{v}</div><div class="d">{d}</div></div>'
CH='const css=v=>getComputedStyle(document.documentElement).getPropertyValue(v).trim();Chart.defaults.color=css("--muted");Chart.defaults.borderColor=css("--line-soft");Chart.defaults.font.weight="500";Chart.defaults.font.family="Inter,-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif";Chart.defaults.font.size=12;const fmtL=v=>"₹"+(v/1e5).toFixed(1)+" L";'
# ---------- pages
per_month=tot/nM; gap=per_month-maint; inc_other=hdfc_int+sobha_int+other+icici_acc
idx=f'''<section><div class="eyebrow">September 2026</div>
<h1>Where we stand</h1>
<p class="lead">Running Palm Court costs about {L(per_month)} a month. Maintenance brings in {L(maint)}. Interest covers some of the rest. The reserves cover the remainder. These pages show the numbers, what the Managing Committee is doing, and what happens next.</p>
<div class="hero">
<div class="big"><div class="k">Shortfall this year</div><div class="v">₹70–90 L</div><div class="d">We spend about {L(per_month)} a month and collect {L(maint)} in maintenance. Interest and other income add {L(inc_other)}. The rest comes from the reserves, before any savings from the tenders.</div></div>
<div class="rest">
{tile("","Spend per month",L(per_month),f"{ML(months[0])}–{ML(months[-1])} average, everything included")}
{tile("","Maintenance per month",L(maint),"₹57.6 L billed each quarter")}
{tile("accent","Reserves",L(reserves),"fixed deposits plus the balance with Sobha")}
{tile("crit" if floats[-1][1] < per_month*0.3 else "warn","Cash in the bank, end "+ML(months[-1]),L(floats[-1][1]),f"about {round(floats[-1][1]/per_month*4.3)} week{'s' if round(floats[-1][1]/per_month*4.3)!=1 else ''} of spending")}
</div></div>
<div class="glossary">1 lakh = ₹1,00,000. 1 crore = 100 lakh. Reserves (the corpus) are the money owners paid at handover, kept in fixed deposits for big repairs.</div>
</section>
<section><h2>In six sentences</h2>
<ol class="steps">
<li>Last year the association spent ₹48 lakh more than it collected. The difference came from the reserves. The General Body was not asked.</li>
<li>This year is running the same way. {ML(months[0])} to {ML(months[-1])}: {L(tot)} spent, against {L(maint*nM)} of maintenance for those months.</li>
<li>The reserves are about {L(reserves)}. That money is for big repairs in the years ahead. Its interest is already being spent on running costs.</li>
<li>A resident Sub-Committee reviewed last year's accounts. Their questions have gone to the previous Managing Committee and to the auditor. The answers will be published here.</li>
<li>A Special General Body Meeting on <strong>Sunday, 18 October</strong> will decide the budget and the maintenance rate. The notice goes out this week. The 1 October bill stays at the current rate; only the General Body can change it.</li>
<li>Until then the gap is met from the reserves. The amount drawn is published here every month.</li>
</ol></section>
<section><h2>What happens next</h2>
<div class="timeline">
<div class="when">18 Sep</div><div>Meeting notice to every owner, with the Sub-Committee's report and other supporting documents, the resolutions, and how to vote.</div>
<div class="when">21 Sep</div><div>Written responses due from the previous Managing Committee, requested for each point the Sub-Committee raised. Published as received.</div>
<div class="when">1 Oct</div><div>Q3 maintenance bill, at the current rate. Please pay by the due date.</div>
<div class="when">Before 18 Oct</div><div>Full meeting pack: the responses, the audited accounts, the budget, tabled alongside the Sub-Committee's report.</div>
<div class="when">Sun, 18 Oct</div><div>Special General Body Meeting. One flat, one vote. Proxies and e-mail votes allowed.</div>
<div class="when">Nov</div><div>If a new rate is approved from 1 October, the difference for October–December is billed in November.</div>
</div></section>
<section><h2>Read on</h2><div class="readon">
<a href="money.html"><span class="t">Where the money goes</span><span class="d">Every expense, month by month</span></a>
<a href="simulator.html"><span class="t">Try the options</span><span class="d">Five ways to fund the year; see which ones close the gap</span></a>
<a href="reserves.html"><span class="t">Our reserves</span><span class="d">₹11.76 crore at handover, {L(reserves)} today — where it is and what it earns</span></a>
<a href="feedback.html"><span class="t">What you told us</span><span class="d">The August survey and what is being done about it</span></a>
</div></section>'''
page("index.html","Where we stand",idx)
# money
rows=sorted(byhead.items(),key=lambda x:-x[1])[:12]
headrows="".join(f'<tr><td>{h}</td><td class="num">{inr(v/nM)}</td><td class="num">{v/routine*100:.0f}%</td></tr>' for h,v in rows)
ot=sorted([r for r in spend if r["kind"]=="onetime"],key=lambda r:-r["amount"])[:6]
otrows="".join(f'<tr><td>{ML(r["month"])}</td><td>{r["head"]}</td><td class="num">{inr(r["amount"])}</td></tr>' for r in ot)
money=f'''<section><div class="eyebrow">{ML(months[0])} to {ML(months[-1])} · receipts and payments basis</div><h1>Where the money goes</h1>
<p class="lead">Everything paid out from {ML(months[0])} to {ML(months[-1])}, in the month it was paid. Nothing is smoothed. The half-yearly lift contract shows in June because that is when it was paid.</p>
<div class="tiles">{tile("","Paid out, "+ML(months[0])+chr(8211)+ML(months[-1]),L(tot),f"{L(routine)} running costs + {L(onetime)} one-time items")}{tile("","Per month",L(per_month),"one-time items included")}{tile("crit","Maintenance covers",f"{maint/(routine/nM)*100:.0f}%","of running costs")}</div></section>
<section><div class="charts"><div class="chartbox"><h3>Month by month, by category</h3><div class="ch" style="height:280px"><canvas id="c1"></canvas></div></div><div class="chartbox"><h3>{nM} months, by category</h3><div class="ch donut" style="height:240px"><canvas id="c2"></canvas></div></div></div>
<p class="small">The dashed line is monthly maintenance income. The gap above it is the shortfall.</p></section>
<section><h2>The biggest heads</h2>
<div class="tablewrap"><table><thead><tr><th>Head</th><th class="num">Per month</th><th class="num">Share of running costs</th></tr></thead><tbody>{headrows}</tbody></table></div>
<p>Three items are two-thirds of everything: facility management by Sobha (₹98 L a year), security by VEX (₹85 L including GST) and electricity (₹60 L). Both service contracts are going to tender. The target is ₹25–30 L a year in savings.</p></section>
<section><h2>One-time items</h2><p>Repairs and purchases outside the monthly run. {L(onetime)} in four months. The largest:</p>
<div class="tablewrap"><table><thead><tr><th>Month</th><th>Item</th><th class="num">Amount</th></tr></thead><tbody>{otrows}</tbody></table></div>
<p class="small">The association's purchasing and accounting controls are being reviewed. A revised policy will be put to the General Body for approval.</p></section>'''
mjs=CH+f'''new Chart(document.getElementById("c1"),{{data:{{labels:{json.dumps([ML(m) for m in months])},datasets:[{",".join(f'{{type:"bar",label:{json.dumps(c)},data:{json.dumps([round(bymc[m][c]) for m in months])},backgroundColor:{CATCOL[i]},stack:"s",borderWidth:0}}' for i,c in enumerate(CATS))},{{type:"line",label:"Maintenance billed",data:{json.dumps([round(maint)]*nM)},borderColor:css("--crit"),borderDash:[6,4],borderWidth:2,pointRadius:0}}]}},options:{{responsive:true,maintainAspectRatio:false,interaction:{{mode:"index",intersect:false}},scales:{{x:{{stacked:true,grid:{{display:false}}}},y:{{stacked:true,ticks:{{callback:fmtL}},beginAtZero:true}}}},plugins:{{legend:{{position:"bottom",labels:{{boxWidth:10,font:{{size:11}}}}}}}}}}}});
new Chart(document.getElementById("c2"),{{type:"doughnut",data:{{labels:{json.dumps(CATS)},datasets:[{{data:{json.dumps([round(cattot[c]) for c in CATS])},backgroundColor:[{",".join(CATCOL)}],borderWidth:2,borderColor:css("--surface")}}]}},options:{{responsive:true,maintainAspectRatio:false,cutout:"58%",plugins:{{legend:{{position:"bottom",labels:{{boxWidth:10,font:{{size:11}}}}}}}}}}}});'''
page("money.html","Where the money goes",money,mjs)
# shortfall
rw=runway["rows"]
def cell(v): return f'<td class="num{" neg" if v<0 else ""}">{v:+.1f}</td>'.replace("+","") if v>=0 else f'<td class="num neg">−{abs(v):.1f}</td>'
rrows="".join(f'<tr><td>{r["m"]}</td><td class="num">{r["in"]:.1f}</td><td class="num">{r["out"]:.1f}</td>{cell(r["a"])}{cell(r["c"])}</tr>' for r in rw)
inc_pct=rates["increase"]
def rate_row(t):
    q=t["quarter"]; m=q/3; new=m*(1+inc_pct); gst_whole=new*0.18 if new>7500 else 0; gst_excess=(new-7500)*0.18 if new>7500 else 0
    return f'<tr><td>{t["type"]}</td><td class="num">{inr(m)}</td><td class="num">{inr(new)}</td><td class="num">{inr(new+gst_whole)}</td><td class="num">{inr(new+gst_excess)}</td></tr>'
raterows="".join(rate_row(t) for t in rates["types"])
sf=f'''<section><div class="eyebrow">The gap, the runway, and the proposal</div><h1>The shortfall and the plan</h1>
<p class="lead">Three groups estimated this year's shortfall and got three numbers. They differ on what to count, not on the facts.</p>
<div class="tablewrap"><table><thead><tr><th>Estimate</th><th class="num">Shortfall, FY 2026–27</th><th>What it assumes</th></tr></thead><tbody>
<tr><td>Treasurer's projection</td><td class="num">₹91 L</td><td>Spending of ₹33 L a month; only HDFC interest counted; nothing saved.</td></tr>
<tr><td>Managing Committee's working model</td><td class="num">₹70–80 L</td><td>Actual spending of about ₹31 L a month; all interest counted, including ICICI interest that arrives at maturity; tax on interest provided; no savings yet.</td></tr>
<tr><td>Finance Sub-Committee's report</td><td class="num">₹23 L</td><td>Running costs only (no one-time items), ₹18 L a year of savings assumed before they are made, and tax at a third of last year's level.</td></tr>
</tbody></table></div>
<div class="callout"><strong>The MC plans on ₹70–90 L.</strong> Savings from the tenders reduce it from next year. The target is ₹25–30 L a year.</div></section>
<section><h2>Cash, month by month</h2>
<p>The account had {L(floats[-1][1])} at the end of {ML(months[-1])} — about a week of spending. Spending is ₹26 L a month, plus tax in September, December and March, plus the ₹8 L lift contract in December. The next bill is 1 October at the current rate. The meeting cannot be held before 18 October. The table below starts from the real {ML(months[-1])} closing balance: even with a 20% increase from 1 October, the account still needs the reserves in several months, because there is no cushion left to absorb the wait.</p>
<div class="tablewrap"><table><thead><tr><th>Month-end</th><th class="num">In</th><th class="num">Out</th><th class="num">Cash if nothing changes</th><th class="num">Cash with +20% from 1 Oct</th></tr></thead><tbody>{rrows}</tbody></table></div>
<p class="small">Assumes no ICICI deposits mature and no savings from tenders yet. A maturing ICICI deposit (one is expected within weeks) would ease this. Tax is at the current ₹2.5 L a quarter; the Options page defaults to the higher, correct provision, so it shows a somewhat larger draw. Negative means the reserves are used.</p>
<div class="callout crit"><strong>Until the General Body decides, the gap is met from the reserves.</strong> There is no other source this year. What is drawn will be shown on the <a href="reserves.html">reserves page</a> month by month, and the meeting will be asked to decide how it is repaid.</div></section>
<section><h2>What an increase would mean for your flat</h2>
<p>Illustrative only. The MC's proposal will be in the meeting notice. Once a flat's monthly charge crosses ₹7,500, 18% GST applies. It can apply to the whole amount (the tax department's position) or only to the amount above ₹7,500 (a High Court reading). The difference is over ₹1,300 a month for the larger flats. Written advice is being taken.</p>
<div class="tablewrap"><table><thead><tr><th>Flat type</th><th class="num">Today, per month</th><th class="num">At +{int(inc_pct*100)}%</th><th class="num">With GST on the whole amount</th><th class="num">With GST only above ₹7,500</th></tr></thead><tbody>{raterows}</tbody></table></div>
<p class="small">Flats still below ₹7,500 pay no GST under either reading. If the association can reclaim the GST on its own contracts (about ₹35 L a year), the increase needed is smaller.</p></section>
<section><h2>Why not just cut costs?</h2>
<p>Both are needed. The two big contracts have never been tendered. They are being tendered now. But tenders take months, and the savings start next year. Residents rated housekeeping and landscaping the best services on the estate. Cutting those to avoid an increase would trade a visible service for an invisible saving. The lift contract, rated worst, is being rebid on uptime.</p></section>'''
page("shortfall.html","The shortfall and the plan",sf)
# reserves
bankrows="".join(f'<tr><td><strong>{b["bank"]}</strong></td><td class="num">{b["count"] or "—"}</td><td class="num">{L(b["principal"])}</td><td class="num">{(str(b["rate"])+"%") if b["rate"] else "≈7–7.5% (to confirm)"}</td><td>{b["payout"]}</td><td>{b["maturity"]}</td></tr>' for b in fds["banks"])
res=f'''<section><div class="eyebrow">Fixed deposits and the corpus · as at {fds["as_at"]}</div><h1>Our reserves</h1>
<p class="lead">At handover in June 2022 the owners' corpus was ₹11.76 crore. Today it is about {L(reserves)}: {L(hdfc["principal"])} at HDFC, {L(icici["ledger"])} at ICICI, and {L(sobha["principal"])} still with Sobha.</p>
<div class="tiles">{tile("","Reserves today",L(reserves),"HDFC + ICICI + held by Sobha")}{tile("","Interest they earn, per year","≈ ₹67 L","before tax at about 31%")}{tile("warn","Used for running costs, FY 25–26","₹50 L","net, without General Body approval")}{tile("","At handover, June 2022","₹11.76 Cr","held by Sobha until returned in 2023–24")}</div></section>
<section><div class="charts even"><div class="chartbox"><h3>Where the reserves sit</h3><div class="ch donut" style="height:240px"><canvas id="c3"></canvas></div></div><div class="chartbox"><h3>Cash in the operating account, month-end</h3><div class="ch" style="height:240px"><canvas id="c4"></canvas></div></div></div>
<p class="small">The quarterly bill fills the account. By month three it is empty. The June figure is being reconciled.</p></section>
<section><h2>The deposits</h2>
<div class="tablewrap"><table><thead><tr><th>Where</th><th class="num">Deposits</th><th class="num">Principal</th><th class="num">Rate</th><th>How interest is paid</th><th>Maturity</th></tr></thead><tbody>{bankrows}</tbody></table></div>
<p class="small">Sources: the banks' own deposit summaries dated {fds["as_at"]} and Sobha's corpus statement. Account numbers are not published.</p>
<div class="callout warn"><strong>Two figures are being reconciled.</strong> The accountant's statements show ₹3.81 crore in HDFC deposits; the bank's own summary on 7 September shows ₹3.20 crore. And Sobha's ledger shows about ₹75 lakh of the corpus held, against ₹90 lakh in the books, because Sobha sets its unpaid bills off against the balance. The figures on this page are the banks' and Sobha's. Both differences will be explained in the meeting pack.</div></section>
<section><h2>How ₹11.76 crore became {L(reserves)}</h2>
<div class="timeline">
<div class="when">Jun 2022</div><div>₹11.76 Cr collected by Sobha at handover. For sixteen months Sobha ran the estate from it: ₹1.88 Cr charged, ₹1.17 Cr of interest credited.</div>
<div class="when">Nov 2023 – Jun 2024</div><div>Sobha returned ₹9.30 Cr in nine instalments. It went into fixed deposits at HDFC and ICICI. Sobha kept ₹91 L as security for its facility service.</div>
<div class="when">2024–25 and 2025–26</div><div>Interest was spent on running costs. In 2025–26, ₹50 L of principal was also used, without General Body approval.</div>
<div class="when">Today</div><div>{L(reserves)}, of which {L(hdfc["principal"]+icici["ledger"])} is in bank deposits. A full bridge from the audited accounts will be in the meeting pack.</div>
</div></section>
<section><h2>Going to the meeting</h2>
<ol class="steps"><li><strong>Interest is income. Principal is not.</strong> Principal is not withdrawn without a General Body resolution. Every withdrawal is reported here the month it happens.</li>
<li><strong>Three signatures or five MC signatures</strong> for every deposit movement.</li>
<li><strong>A monthly deposit statement</strong> on these pages, from the banks, not from the books.</li>
<li><strong>A sinking fund</strong> from next year, so the ₹50 L used is rebuilt and the big repairs of the next ten years have a plan.</li></ol></section>'''
rjs=CH+f'''new Chart(document.getElementById("c3"),{{type:"doughnut",data:{{labels:["HDFC deposits","ICICI deposits (with interest)","Held by Sobha"],datasets:[{{data:[{hdfc["principal"]},{icici["ledger"]},{sobha["principal"]}],backgroundColor:[css("--c1"),css("--c4"),css("--c2")],borderWidth:2,borderColor:css("--surface")}}]}},options:{{responsive:true,maintainAspectRatio:false,cutout:"58%",plugins:{{legend:{{position:"bottom",labels:{{boxWidth:10,font:{{size:11}}}}}},tooltip:{{callbacks:{{label:c=>" "+c.label+": "+fmtL(c.parsed)}}}}}}}}}});
new Chart(document.getElementById("c4"),{{type:"line",data:{{labels:{json.dumps([m for m,_ in floats])},datasets:[{{label:"Bank + cash",data:{json.dumps([round(v) for _,v in floats])},borderColor:css("--c1"),backgroundColor:css("--c1")+"26",fill:true,tension:.25,pointRadius:3,pointBackgroundColor:css("--c1")}},{{label:"One month of spending",data:{json.dumps([round(per_month)]*len(floats))},borderColor:css("--crit"),borderDash:[6,4],borderWidth:1.5,pointRadius:0}}]}},options:{{responsive:true,maintainAspectRatio:false,scales:{{y:{{ticks:{{callback:fmtL}}}},x:{{grid:{{display:false}}}}}},plugins:{{legend:{{position:"bottom",labels:{{boxWidth:10,font:{{size:11}}}}}}}}}}}});'''
page("reserves.html","Our reserves",res,rjs)
# feedback
def bar(d):
    t=sum(d.values()) or 1; cols={"Very good":"var(--s-vg)","Good":"var(--s-g)","Acceptable":"var(--s-a)","Poor":"var(--s-p)","Very poor":"var(--s-vp)"}
    return '<div class="bar">'+"".join(f'<span style="width:{d[s]/t*100}%;background:{cols[s]}" title="{s}: {d[s]}"></span>' for s in cols)+'</div>'
servrows="".join(f'<tr><td>{l}</td><td>{bar(dist[k])}</td><td class="num">{m:.2f}</td><td class="num{" neg" if p/nn>=0.2 else ""}">{p/nn*100:.0f}%</td></tr>' for l,m,nn,p,k in serv)
prows="".join(f'<tr><td>{p}</td><td class="num">{c}</td><td class="num">{c/n*100:.0f}%</td></tr>' for p,c in prio.most_common(8))
irows="".join(f'<tr><td>{l}</td><td class="num">{m:.2f}</td><td class="num{" neg" if p/nn>=0.25 else ""}">{p/nn*100:.0f}%</td></tr>' for l,m,nn,p in iss)
wrows="".join(f'<tr><td>{w}</td><td class="num">{c}</td><td class="num">{s/c*100:.0f}%</td><td class="num{" neg" if lm<3 else ""}">{lm:.2f}</td></tr>' for w,c,s,lm in wingrows)
fb=f'''<section><div class="eyebrow">Resident services survey · 23 August to 2 September 2026</div><h1>What you told us</h1>
<p class="lead">{n} households answered. {sat/n*100:.0f}% are satisfied overall. Lifts and pest control are the problems. Complaints are easy to raise and slow to close.</p>
<div class="tiles">{tile("","Responses",str(n),"of 294 flats, all four wings")}{tile("good","Satisfied overall",f"{sat/n*100:.0f}%","mean {:.2f} of 5".format(sum(OV[r["overall"]] for r in sv)/n))}{tile("crit sm","Weakest service",serv[-1][0],f"{serv[-1][3]/serv[-1][2]*100:.0f}% rate it poor or worse")}{tile("good sm","Strongest service",serv[0][0],f"mean {serv[0][1]:.2f} of 5")}</div></section>
<section><h2>Service ratings</h2>
<div class="tablewrap"><table><thead><tr><th>Service</th><th>Ratings</th><th class="num">Mean / 5</th><th class="num">Poor or worse</th></tr></thead><tbody>{servrows}</tbody></table></div>
<div class="legend"><span><i style="background:var(--s-vg)"></i>Very good</span><span><i style="background:var(--s-g)"></i>Good</span><span><i style="background:var(--s-a)"></i>Acceptable</span><span><i style="background:var(--s-p)"></i>Poor</span><span><i style="background:var(--s-vp)"></i>Very poor</span></div></section>
<section><div class="charts"><div><h2>What you want fixed first</h2><div class="tablewrap"><table><thead><tr><th>Priority</th><th class="num">Chose it</th><th class="num">Share</th></tr></thead><tbody>{prows}</tbody></table></div><p class="small">Each household could pick up to three.</p></div>
<div><h2>Complaint handling</h2><p class="small">Rated by the {len(rep)} households that reported an issue in the last six months.</p><div class="tablewrap"><table><thead><tr><th>Step</th><th class="num">Mean / 5</th><th class="num">Poor or worse</th></tr></thead><tbody>{irows}</tbody></table></div></div></div></section>
<section><h2>By wing</h2><div class="tablewrap"><table><thead><tr><th>Wing</th><th class="num">Responses</th><th class="num">Satisfied</th><th class="num">Lifts, mean / 5</th></tr></thead><tbody>{wrows}</tbody></table></div><p class="small">Wing 1 had the fewest responses and the lowest lift score. The MC is visiting.</p></section>
<section><h2>What is being done</h2>
<ol class="steps">
<li><strong>Lifts.</strong> A monthly log of breakdowns and time-to-restore per lift, published on the <a href="services.html">lifts page</a> from October; a root-cause report on the Wing 1 and Wing 4 machines; the lift contract rebid on uptime, with penalties.</li>
<li><strong>Pest control and mosquitoes.</strong> The vendor's schedule audited against what was actually done; source reduction around the STP, basements and drains; a published fogging calendar; drain-line treatment for cockroaches.</li>
<li><strong>Complaints.</strong> A response standard in MyGate: acknowledged within four working hours, an update every 48 hours, closed only when you confirm. The numbers will be published monthly on the <a href="services.html">complaints page</a>.</li>
<li><strong>Security.</strong> The retender specification is written from your comments: guards who speak Kannada, a limit on turnover, a post at each block entrance, logged basement rounds, and a way for guards to recognise residents.</li>
<li><strong>Play area.</strong> The hardened sand and exposed pipes reported by two households are being inspected and fixed first, as a safety matter.</li>
<li><strong>Costs.</strong> Several of you raised overstaffing, Sobha's cost, the ₹7,500 GST line and user charges for the gym and tennis court. All four are addressed on <a href="shortfall.html">the shortfall page</a> and will be in the meeting pack.</li>
</ol>
<p class="small">The survey was anonymous. Individual comments are not published. Each one has been read and assigned to an MC member.</p></section>'''
page("feedback.html","What you told us",fb)
# services
def lifts_html():
    if not lifts: return '<div class="empty"><strong>No data published yet.</strong> The first monthly lift report will be published here by 10 October 2026, covering September. It will show, for each wing: the number of breakdowns, the hours each lift was out of service, the uptime percentage, and the time taken to restore service, from the lift contractor\'s call log checked against the security register.</div>'
    return '<div class="tablewrap"><table><thead><tr><th>Month</th><th>Wing</th><th class="num">Lifts</th><th class="num">Breakdowns</th><th class="num">Hours down</th><th class="num">Uptime</th><th>Note</th></tr></thead><tbody>'+"".join(f'<tr><td>{r["month"]}</td><td>{r["wing"]}</td><td class="num">{r["lifts"]}</td><td class="num">{r["breakdowns"]}</td><td class="num">{r["hours_down"]}</td><td class="num">{r["uptime_pct"]}%</td><td class="small">{r["note"]}</td></tr>' for r in lifts)+'</tbody></table></div>'
def comps_html():
    if not comps: return '<div class="empty"><strong>No data published yet.</strong> From October, a monthly table from MyGate: complaints opened and closed by category, how many were still open at month-end, and the average days to close. The standard the MC has set is: acknowledged within four working hours, an update every 48 hours, closed only when the resident confirms.</div>'
    return '<div class="tablewrap"><table><thead><tr><th>Month</th><th>Category</th><th class="num">Opened</th><th class="num">Closed</th><th class="num">Open at month-end</th><th class="num">Avg days to close</th><th>Note</th></tr></thead><tbody>'+"".join(f'<tr><td>{r["month"]}</td><td>{r["category"]}</td><td class="num">{r["opened"]}</td><td class="num">{r["closed"]}</td><td class="num">{r["open_at_month_end"]}</td><td class="num">{r["avg_days_to_close"]}</td><td class="small">{r["note"]}</td></tr>' for r in comps)+'</tbody></table></div>'
svc=f'''<section><div class="eyebrow">Service performance · published monthly from October 2026</div><h1>Lifts and complaints</h1>
<p class="lead">Lifts and complaints were the top two issues in the survey. Both will be measured and published here every month from October.</p></section>
<section><h2>Lift uptime</h2><p>Lifts were the lowest-rated service (3.30 of 5) and the top priority for 54% of households. The lift contract costs ₹16 L a year. Batteries cost ₹6.75 L last year.</p>{lifts_html()}</section>
<section><h2>Complaint resolution</h2><p>Half the households had raised a complaint in the last six months. Reporting was easy (3.90 of 5). Getting it closed was not: ownership scored 3.05, time to resolve 3.13.</p>{comps_html()}</section>
<section><h2>Where the numbers come from</h2><ol class="steps"><li>Lift figures: the contractor's call log, checked against the gate register.</li><li>Complaint figures: MyGate's ticket export, unedited.</li><li>Published by the 10th of the following month. Raw files on request.</li></ol></section>'''
page("services.html","Lifts and complaints",svc)
# documents & faq
FAQ=[("Why is the association short of money?","Costs have risen faster than the maintenance rate, which has not changed since handover, and last year's Managing Committee covered the difference from the reserves. Security alone costs ₹15 L a year more after the change of agency in November 2025. The full picture is on the money page."),
("Isn't ₹9 crore in reserves enough to carry on?","It would carry on for a few years and then be gone, and it is the fund for lifts, painting and waterproofing in the years ahead. Its interest, about ₹67 L a year before tax, is already being spent on running costs. Spending the principal too is what last year's Managing Committee did, and what the General Body objected to."),
("Why can't the MC just raise the rate now?","The bye-laws give the General Body, not the MC, the power to approve the budget and set the monthly charge. The earliest a Special General Body Meeting can be held is 18 October. The 1 October bill is therefore at the current rate."),
("What will the increase be?","The MC's proposal will be in the meeting notice, with the budget behind it. The working range is 18–22% on the base charge before GST. The shortfall page shows what 20% would mean for each flat type, and the two ways GST could apply."),
("Why does GST suddenly matter?","Maintenance above ₹7,500 a month per flat attracts 18% GST. The larger flats (A and A1 types) are at ₹7,432–7,499 today, so any increase crosses the line. Whether GST then applies to the whole amount or only to the excess changes the bill by over ₹1,300 a month, and whether the association can reclaim the GST on its own contracts changes the increase needed. The MC is taking written advice before the notice."),
("What happened to last year's money?","The Finance Sub-Committee's report, on the documents page, sets out the specific decisions it questioned: the pool repair, lift batteries, the security agency switch, paver work, a payment without an invoice, and withdrawals from the reserves. The previous Managing Committee has been asked to respond in writing to each; the auditor has been asked to explain. Both responses will be published, and the General Body will be asked to approve an independent review."),
("Is anyone being accused of anything?","No. The Sub-Committee's report raises questions; the answers are being sought; a professional review will establish facts. Nobody will be named or blamed on these pages ahead of that."),
("Why not cut costs instead of raising the rate?","Both are happening. The facility and security contracts, ₹1.8 Cr a year between them, are being tendered for the first time. But tenders take months, and residents rated housekeeping and landscaping the best-run services on the estate. The MC will not cut those to avoid an increase; it will cut what is not working, starting with the lift contract."),
("What is the MC doing about lifts and pest control?","See the feedback page. In short: a public lift log from October, a root-cause report on the worst machines, the lift contract rebid on uptime; and for pests, an audit of what the vendor actually does, source reduction, and a published schedule."),
("How do I know these numbers are right?","They are taken from the accountant's monthly statements and the banks' own deposit summaries, and the sources are named on each page. They are not audited figures; the audited accounts are annual. Anything that is an estimate says so. If you find an error, write to spcaoa@gmail.com and it will be corrected and noted."),
("How often are these pages updated?","Monthly, after the accountant's statement for the month is received, and immediately after any General Body decision. The date at the foot of each page says what the figures cover.")]
faq="".join(f'<details><summary>{q}</summary><p>{a}</p></details>' for q,a in FAQ)
docs=f'''<section><div class="eyebrow">Source documents and questions</div><h1>Documents and FAQ</h1>
<div class="cards">
<div class="card"><h3>Finance Sub-Committee report</h3><p class="small">31 August 2026. The resident volunteers' review of FY 2025–26, with annexures on expenses, income and their 10% simulation.</p><a class="btn ghost" href="docs/SPC-Finance-SubCommittee-Report-2026-08-31.pdf">Open PDF</a></div>
<div class="card"><h3>General Body Meeting presentation</h3><p class="small">26 July 2026. The MC's presentation: audited FY 2025–26 summary, the corpus drawdown, cost proposals and the two funding options the meeting declined.</p><a class="btn ghost" href="docs/SPCAOA-GBM-Deck-2026-07-26.pdf">Open PDF</a></div>
<div class="card"><h3>Independent Auditor's Report, FY 2025–26</h3><p class="small">20 July 2026. Two pages; unqualified opinion. The full audited statements with notes will be added with the meeting pack.</p><a class="btn ghost" href="docs/Independent-Auditors-Report-FY25-26.pdf">Open PDF</a></div>
</div></section>
<section><h2>The numbers behind these pages</h2><p>The data files these pages are built from, and the ledgers received from Sobha and the Treasurer. Files with individual flats' dues or staff names are not published. Their totals are.</p>
<div class="cards">
<div class="card"><h3>Expenses, {ML(months[0])}–{ML(months[-1])}</h3><p class="small">Every head, every month, from the accountant's statements. CSV.</p><a class="btn ghost" href="data/expenses.csv">Download</a></div>
<div class="card"><h3>Income, treasury and budget</h3><p class="small">Income lines, month-end bank and deposit positions, and the working budget. CSV.</p><a class="small" href="data/income.csv">income.csv</a> · <a class="small" href="data/treasury.csv">treasury.csv</a> · <a class="small" href="data/budget.csv">budget.csv</a></div>
<div class="card"><h3>Vendor bills and deposits</h3><p class="small">The two largest contracts invoice by invoice, and the fixed deposits by bank. CSV.</p><a class="small" href="data/vendor_bills.csv">vendor_bills.csv</a> · <a class="small" href="data/fds.csv">fds.csv</a></div>
<div class="card"><h3>Sobha's corpus ledger</h3><p class="small">Sobha's own statement of the owners' corpus, June 2022 to August 2026. Excel, as received.</p><a class="small" href="docs/Sobha-corpus-fund-statement-2022-06-to-2026-08.xlsx">Download</a></div>
<div class="card"><h3>Treasurer's deposit ledger</h3><p class="small">Month-by-month fixed-deposit balances by bank, November 2023 to June 2026. Excel, as received.</p><a class="small" href="docs/FD-ledger-2023-2026-treasurer.xlsx">Download</a></div>
<div class="card"><h3>The books themselves</h3><p class="small">The association's accounts are kept in TallyPrime. A backup dated 7 September 2026 is held by the MC; audited statements are published annually, and ledger extracts can be requested by any owner.</p></div>
</div></section>
<section><h2>Questions residents are asking</h2><div class="faq">{faq}</div></section>'''
page("documents.html","Documents and FAQ",docs)
from extra import build_extra
build_extra(page, CH, runway)
# gate
pw=open(os.path.join(ROOT,"tools","passcode.txt")).read().strip().lower() if os.path.exists(os.path.join(ROOT,"tools","passcode.txt")) else ""
h=hashlib.sha256(pw.encode()).hexdigest() if pw else ""
g=open(os.path.join(ROOT,"docs","assets","gate.js")).read()
import re; g=re.sub(r'var PASS_HASH = "[^"]*";', f'var PASS_HASH = "{h}";', g); open(os.path.join(ROOT,"docs","assets","gate.js"),"w").write(g)
print("built 10 pages; gate", "ON" if h else "OFF"); print(f"spend/mo {per_month:,.0f} maint/mo {maint:,.0f} other/mo {inc_other:,.0f} reserves {reserves:,.0f} survey n={n} sat={sat}")

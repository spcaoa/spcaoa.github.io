#!/usr/bin/env python3
"""Build the residents' pages into docs/ from the MC site's data plus local JSON.
Usage: python3 tools/build.py   (passcode read from tools/passcode.txt; empty file = no gate)"""
import csv, json, os, sys, hashlib, datetime, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MC=os.path.join(os.path.dirname(ROOT),"spc-finance-site","site","data")
OUT=os.path.join(ROOT,"docs"); DATA=os.path.join(ROOT,"data")
UPDATED="10 September 2026"
def rd(p): return list(csv.DictReader(open(p,newline="",encoding="utf-8")))
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
CATCOL=["#0f5b57","#8a3f2c","#c9a227","#3c6ea0","#7b6b8f","#5c7e5c","#9c9a91"]
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
NAV=[("index.html","Where we stand"),("money.html","Where the money goes"),("shortfall.html","The shortfall"),("simulator.html","Try the options"),("reserves.html","Our reserves"),("contracts.html","Contracts"),("actions.html","What the committee is doing"),("feedback.html","What you told us"),("services.html","Lifts and complaints"),("documents.html","Documents and FAQ")]
def page(fn,title,body,scripts=""):
    cur=' aria-current="page"'
    nav="".join(f'<a href="{f}"{cur if f==fn else ""}>{t}</a>' for f,t in NAV)
    html=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>{title} · Sobha Palm Court</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="assets/site.css"><script src="assets/gate.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script></head><body>
<div class="topbar"><div class="in"><a class="brand" href="index.html">Sobha Palm Court<small>Owners' association · finances, plainly</small></a><nav class="tabs" aria-label="Pages">{nav}</nav></div></div>
<div class="wrap">{body}
<div class="updated">Updated {UPDATED} · accounts through {ML(months[-1])} 2026 (accountant's monthly statements) · deposits as at {fds["as_at"]} (bank summaries) · survey August 2026. Published by the Managing Committee for owners and residents. Questions: spcaoa@gmail.com</div>
</div><footer>Amounts are in Indian rupees. 1 lakh (L) = ₹1,00,000. 1 crore (Cr) = ₹100 lakh. Figures are receipts and payments as recorded by the association's accountant, not audited, and will be updated monthly.</footer>
<script>{scripts}</script></body></html>'''
    open(os.path.join(OUT,fn),"w",encoding="utf-8").write(html)
def tile(cls,k,v,d): return f'<div class="tile {cls}"><div class="k">{k}</div><div class="v">{v}</div><div class="d">{d}</div></div>'
CH='Chart.defaults.color=getComputedStyle(document.documentElement).getPropertyValue("--muted").trim();Chart.defaults.borderColor=getComputedStyle(document.documentElement).getPropertyValue("--line-soft").trim();Chart.defaults.font.family="IBM Plex Sans, system-ui, sans-serif";const fmtL=v=>"₹"+(v/1e5).toFixed(1)+" L";'
# ---------- pages
per_month=tot/nM; gap=per_month-maint; inc_other=hdfc_int+sobha_int+other+icici_acc
idx=f'''<section><div class="eyebrow">Sobha Palm Court Apartment Owners' Association · September 2026</div>
<h1>Where we stand</h1>
<p class="lead">Running Palm Court costs about {L(per_month)} a month. Maintenance charges bring in about {L(maint)} a month. Interest on the association's reserves covers part of the difference; the rest has been coming out of the reserves themselves. These pages say exactly how much, why, and what the Managing Committee proposes to do about it, so that nothing at the General Body Meeting is a surprise.</p>
<div class="tiles">
{tile("crit","We spend, per month",L(per_month),f"average April–July 2026, everything included")}
{tile("","Maintenance brings in, per month",L(maint),"₹57.6 L billed each quarter, ÷ 3")}
{tile("","Interest and other income, per month",L(inc_other),"fixed-deposit interest, Sobha interest, rentals, fees")}
{tile("crit","Shortfall this year","₹70–90 L","before any savings from the tenders now in progress")}
{tile("","Reserves today",L(reserves),"fixed deposits at two banks plus a balance held by Sobha")}
{tile("warn","Cash in the bank, end July",L(floats[-1][1]),"about five weeks of spending; the quarterly bill refills it")}
</div>
<div class="glossary">1 lakh (L) = ₹1,00,000 · 1 crore (Cr) = ₹100 lakh · "Reserves" or "corpus" = the money owners paid at handover, kept in fixed deposits for the building's big repairs.</div>
</section>
<section><h2>The situation in six sentences</h2>
<ol class="steps">
<li>Last year (April 2025 to March 2026) the association spent ₹48 lakh more than it collected, after tax. The difference came out of the reserves, without the General Body being asked.</li>
<li>This year is running the same way: in April to July we spent {L(tot)} against {L(maint*nM)} of maintenance billed.</li>
<li>The reserves are still substantial, about {L(reserves)}, but they are the building's savings for lifts, painting and waterproofing in the years ahead, and the interest they earn is already being spent on running costs.</li>
<li>A resident Sub-Committee reviewed last year's accounts in August and found specific decisions that need answering. The previous committee has been asked for written responses, and the auditor for explanations. Those will be shared with everyone.</li>
<li>The Managing Committee has called a Special General Body Meeting for <strong>18–19 October</strong> to approve this year's budget and the maintenance rate that goes with it. The 1 October bill will be at the current rate because only the General Body can change it.</li>
<li>Until the General Body decides, the shortfall is being met from the reserves, as it was last year. The difference is that it is being reported: the amount drawn appears on these pages each month.</li>
</ol></section>
<section><h2>What happens next</h2>
<div class="timeline">
<div class="when">By 12 Sep</div><div>Meeting notice to every owner, with the resolutions, the voting process, and the full pack to follow.</div>
<div class="when">By 29 Sep</div><div>Written responses from the previous committee and the auditor due; shared with owners as received.</div>
<div class="when">1 Oct</div><div>Q3 maintenance bill at the current rate. Please pay by the due date: October is the month the account refills.</div>
<div class="when">By 4 Oct</div><div>Full meeting pack: Sub-Committee report, responses, audited accounts, the budget and the committee's proposals.</div>
<div class="when">18–19 Oct</div><div>Special General Body Meeting. One flat, one vote; proxies and e-mail votes allowed as the bye-laws provide.</div>
<div class="when">Nov</div><div>If the General Body approves a new rate from 1 October, the difference for October–December is billed in November; otherwise the new rate starts with the January bill.</div>
</div></section>
<section><h2>Read on</h2><div class="cards">
<div class="card"><h3>Where the money goes</h3><p class="small">Every head of expense, month by month, and what maintenance actually covers.</p><a class="btn ghost" href="money.html">Open</a></div>
<div class="card"><h3>The shortfall and the plan</h3><p class="small">How big the gap is, three ways of counting it, the cash runway to March, and what an increase would mean for your flat.</p><a class="btn ghost" href="shortfall.html">Open</a></div>
<div class="card"><h3>Our reserves</h3><p class="small">₹11.76 crore at handover to {L(reserves)} today: where it sits, what it earns, and the rule the committee proposes for it.</p><a class="btn ghost" href="reserves.html">Open</a></div>
<div class="card"><h3>What you told us</h3><p class="small">The August survey, 76 responses, and what is being done about lifts, pest control and complaint handling.</p><a class="btn ghost" href="feedback.html">Open</a></div>
</div></section>'''
page("index.html","Where we stand",idx)
# money
rows=sorted(byhead.items(),key=lambda x:-x[1])[:12]
headrows="".join(f'<tr><td>{h}</td><td class="num">{inr(v/nM)}</td><td class="num">{v/routine*100:.0f}%</td></tr>' for h,v in rows)
ot=sorted([r for r in spend if r["kind"]=="onetime"],key=lambda r:-r["amount"])[:6]
otrows="".join(f'<tr><td>{ML(r["month"])}</td><td>{r["head"]}</td><td class="num">{inr(r["amount"])}</td></tr>' for r in ot)
money=f'''<section><div class="eyebrow">April to July 2026 · receipts and payments basis</div><h1>Where the money goes</h1>
<p class="lead">Everything the association paid out in the first four months of the year, as recorded by the accountant, in the month it was paid. Nothing is smoothed: the half-yearly lift contract shows in June, when it was paid.</p>
<div class="tiles">{tile("","Paid out, April–July",L(tot),f"{L(routine)} running costs + {L(onetime)} one-time items")}{tile("","Per month",L(per_month),"one-time items included")}{tile("crit","Maintenance covers",f"{maint/(routine/nM)*100:.0f}%","of running costs; interest and reserves cover the rest")}</div></section>
<section><div class="charts"><div class="chartbox"><h3>Month by month, by category</h3><canvas id="c1" height="140"></canvas></div><div class="chartbox"><h3>Four months, by category</h3><canvas id="c2" height="220"></canvas></div></div>
<p class="small">The dashed line is what maintenance brings in each month. The gap between the bars and the line is the shortfall.</p></section>
<section><h2>The biggest heads</h2>
<div class="tablewrap"><table><thead><tr><th>Head</th><th class="num">Per month</th><th class="num">Share of running costs</th></tr></thead><tbody>{headrows}</tbody></table></div>
<p>Three contracts make up two-thirds of everything: facility management by Sobha (housekeeping, gardeners, technicians, ₹98 L a year), security by VEX (₹85 L a year including GST) and electricity (₹60 L a year). Both service contracts are being put out to tender; the committee's target is ₹25–30 L a year of savings without touching the services residents rated highest.</p></section>
<section><h2>One-time items</h2><p>Repairs and purchases outside the monthly run: {L(onetime)} in four months. The largest:</p>
<div class="tablewrap"><table><thead><tr><th>Month</th><th>Item</th><th class="num">Amount</th></tr></thead><tbody>{otrows}</tbody></table></div>
<p class="small">From September every purchase above ₹25,000 needs three quotes on file before it is paid, and the list is published monthly.</p></section>'''
mjs=CH+f'''new Chart(document.getElementById("c1"),{{data:{{labels:{json.dumps([ML(m) for m in months])},datasets:[{",".join(f'{{type:"bar",label:{json.dumps(c)},data:{json.dumps([round(bymc[m][c]) for m in months])},backgroundColor:"{CATCOL[i]}",stack:"s",borderWidth:0}}' for i,c in enumerate(CATS))},{{type:"line",label:"Maintenance billed",data:{json.dumps([round(maint)]*nM)},borderColor:"#a4432e",borderDash:[6,4],borderWidth:2,pointRadius:0}}]}},options:{{responsive:true,interaction:{{mode:"index",intersect:false}},scales:{{x:{{stacked:true,grid:{{display:false}}}},y:{{stacked:true,ticks:{{callback:fmtL}},beginAtZero:true}}}},plugins:{{legend:{{position:"bottom",labels:{{boxWidth:10,font:{{size:11}}}}}}}}}}}});
new Chart(document.getElementById("c2"),{{type:"doughnut",data:{{labels:{json.dumps(CATS)},datasets:[{{data:{json.dumps([round(cattot[c]) for c in CATS])},backgroundColor:{json.dumps(CATCOL)},borderWidth:2}}]}},options:{{cutout:"58%",plugins:{{legend:{{position:"bottom",labels:{{boxWidth:10,font:{{size:11}}}}}}}}}}}});'''
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
<p class="lead">Three groups have estimated this year's shortfall and got three numbers. They differ on what counts as spending and what counts as income, not on the facts. Here are all three, and the range the committee is planning on.</p>
<div class="tablewrap"><table><thead><tr><th>Estimate</th><th class="num">Shortfall, FY 2026–27</th><th>What it assumes</th></tr></thead><tbody>
<tr><td>Treasurer's projection</td><td class="num">₹91 L</td><td>Spending of ₹33 L a month; only HDFC interest counted; nothing saved.</td></tr>
<tr><td>Managing Committee's working model</td><td class="num">₹70–80 L</td><td>Actual spending of ₹30 L a month; all interest counted, including ICICI interest that arrives at maturity; tax on interest provided; no savings yet.</td></tr>
<tr><td>Finance Sub-Committee's report</td><td class="num">₹23 L</td><td>Running costs only (no one-time items), ₹18 L a year of savings assumed before they are made, and tax at a third of last year's level.</td></tr>
</tbody></table></div>
<div class="callout"><strong>The committee plans on ₹70–90 L.</strong> Every rupee saved by the tenders now under way reduces it; the target there is ₹25–30 L a year, from next year onward.</div></section>
<section><h2>Why the meeting cannot be the cash plan</h2>
<p>The account had {L(floats[-1][1])} on 31 July. Spending runs at ₹26 L a month plus the lumps: advance tax in September, December and March, and the ₹8 L lift contract in December. The next bill is 1 October, at the current rate, because only the General Body can change it, and the General Body cannot meet before 18 October. The table shows the cash in the account at each month-end, in lakh, if nothing changes, and if a 20% increase is approved from 1 October with the difference billed in November.</p>
<div class="tablewrap"><table><thead><tr><th>Month-end</th><th class="num">In</th><th class="num">Out</th><th class="num">Cash if nothing changes</th><th class="num">Cash with +20% from 1 Oct</th></tr></thead><tbody>{rrows}</tbody></table></div>
<p class="small">Assumes no ICICI deposits mature in the period and no savings from the tenders. Negative means the account would be overdrawn without a bridge.</p>
<div class="callout crit"><strong>Until the General Body decides, the gap is met from the reserves.</strong> There is no other source this year. What is drawn will be shown on the <a href="reserves.html">reserves page</a> month by month, and the meeting will be asked to decide how it is repaid.</div></section>
<section><h2>What an increase would mean for your flat</h2>
<p>{rates["note"]} The table shows today's monthly charge by flat type, the charge at a {int(inc_pct*100)}% increase, and the two ways GST can apply once a flat's monthly charge crosses ₹7,500: on the whole amount (the tax department's stated position) or only on the amount above ₹7,500 (a High Court reading). The committee is taking written advice before the notice; the difference is over ₹1,300 a month for the larger flats, so it matters.</p>
<div class="tablewrap"><table><thead><tr><th>Flat type</th><th class="num">Today, per month</th><th class="num">At +{int(inc_pct*100)}%</th><th class="num">With GST on the whole amount</th><th class="num">With GST only above ₹7,500</th></tr></thead><tbody>{raterows}</tbody></table></div>
<p class="small">Flats below ₹7,500 a month after the increase pay no GST under either reading. Whether the association can reclaim the GST it pays on its own contracts (about ₹35 L a year) depends on this design; if it can, the base increase needed is smaller.</p></section>
<section><h2>Why not just cut costs?</h2>
<p>Both. The two big service contracts have never been tendered; they are being tendered now, with residents' survey ratings as the benchmark bidders must meet. But tenders take three to four months, the savings start next year, and residents rated housekeeping and landscaping the best-run services on the estate. Cutting those to avoid an increase would trade a visible service for an invisible saving. The lift contract, rated worst, is being rebid on uptime rather than price.</p></section>'''
page("shortfall.html","The shortfall and the plan",sf)
# reserves
bankrows="".join(f'<tr><td><strong>{b["bank"]}</strong></td><td class="num">{b["count"] or "—"}</td><td class="num">{L(b["principal"])}</td><td class="num">{(str(b["rate"])+"%") if b["rate"] else "≈7–7.5% (to confirm)"}</td><td>{b["payout"]}</td><td>{b["maturity"]}</td></tr>' for b in fds["banks"])
res=f'''<section><div class="eyebrow">Fixed deposits and the corpus · as at {fds["as_at"]}</div><h1>Our reserves</h1>
<p class="lead">At handover in June 2022 the owners' corpus was ₹11.76 crore, held by Sobha. Today the association holds about {L(reserves)}: {L(hdfc["principal"])} in HDFC Bank, {L(icici["ledger"])} in ICICI Bank (including interest added so far), and about {L(sobha["principal"])} still with Sobha. What happened in between, and what the reserves earn, is below.</p>
<div class="tiles">{tile("","Reserves today",L(reserves),"HDFC + ICICI + held by Sobha")}{tile("","Interest they earn, per year","≈ ₹67 L","before tax at about 31%")}{tile("warn","Used for running costs, FY 25–26","₹50 L","net, without General Body approval")}{tile("","At handover, June 2022","₹11.76 Cr","held by Sobha until returned in 2023–24")}</div></section>
<section><div class="charts"><div class="chartbox"><h3>Where the reserves sit</h3><canvas id="c3" height="200"></canvas></div><div class="chartbox"><h3>Cash in the operating account, month-end</h3><canvas id="c4" height="200"></canvas></div></div>
<p class="small">The operating account is refilled by the quarterly bill and drained by month three. The June figure is as the accountant's statement shows it; it is being reconciled.</p></section>
<section><h2>The deposits</h2>
<div class="tablewrap"><table><thead><tr><th>Where</th><th class="num">Deposits</th><th class="num">Principal</th><th class="num">Rate</th><th>How interest is paid</th><th>Maturity</th></tr></thead><tbody>{bankrows}</tbody></table></div>
<p class="small">Sources: the banks' own deposit summaries dated {fds["as_at"]} and Sobha's corpus statement. Account numbers are not published.</p>
<div class="callout warn"><strong>Two figures still being reconciled.</strong> The association's books show ₹3.81 crore in HDFC deposits at the end of July; the bank's summary on 7 September shows ₹3.20 crore. And Sobha's ledger shows about ₹75 lakh held, while the books show ₹90 lakh, because Sobha has been adjusting unpaid facility bills against the balance. Both will be explained in the meeting pack.</div></section>
<section><h2>How ₹11.76 crore became {L(reserves)}</h2>
<div class="timeline">
<div class="when">Jun 2022</div><div>Owners' corpus of ₹11.76 Cr collected by Sobha at handover. For sixteen months Sobha ran the estate out of it: ₹1.88 Cr of maintenance was charged to the corpus while interest of ₹1.17 Cr was credited.</div>
<div class="when">Nov 2023 – Jun 2024</div><div>Sobha returned ₹9.30 Cr to the association in nine instalments. The association placed it in fixed deposits at HDFC and ICICI. Sobha kept ₹91 L, which it treats as security for its facility-management service.</div>
<div class="when">FY 2024–25 and 2025–26</div><div>Interest was spent on running costs, which is reasonable; ₹50 L of principal was also used in FY 25–26, which was not approved by the General Body. The Sub-Committee's report sets out the withdrawals.</div>
<div class="when">Today</div><div>{L(reserves)}, of which {L(hdfc["principal"]+icici["ledger"])} is in bank deposits. A bridge from the audited balance sheets, showing every rupee of the difference, will be in the meeting pack.</div>
</div></section>
<section><h2>The rule the committee proposes</h2>
<ol class="steps"><li><strong>Interest is income; principal is not.</strong> Interest is budgeted and spent on running costs. Principal is not withdrawn without a General Body resolution, and every withdrawal is reported here the month it happens.</li>
<li><strong>Two signatures for every deposit movement</strong>, one of them not an office-bearer, as the Sub-Committee recommended.</li>
<li><strong>A monthly statement of the deposits</strong> on these pages, from the banks' summaries, not from the books.</li>
<li><strong>A sinking fund</strong>, from next year, so that the ₹50 L used is rebuilt and the big repairs of the next ten years (lifts, painting, waterproofing) have a plan.</li></ol></section>'''
rjs=CH+f'''new Chart(document.getElementById("c3"),{{type:"doughnut",data:{{labels:["HDFC deposits","ICICI deposits (with interest)","Held by Sobha"],datasets:[{{data:[{hdfc["principal"]},{icici["ledger"]},{sobha["principal"]}],backgroundColor:["#0f5b57","#3c6ea0","#c9a227"],borderWidth:2}}]}},options:{{cutout:"58%",plugins:{{legend:{{position:"bottom",labels:{{boxWidth:10,font:{{size:11}}}}}},tooltip:{{callbacks:{{label:c=>" "+c.label+": "+fmtL(c.parsed)}}}}}}}}}});
new Chart(document.getElementById("c4"),{{type:"line",data:{{labels:{json.dumps([m for m,_ in floats])},datasets:[{{label:"Bank + cash",data:{json.dumps([round(v) for _,v in floats])},borderColor:"#0f5b57",backgroundColor:"rgba(15,91,87,.12)",fill:true,tension:.25,pointRadius:4}},{{label:"One month of spending",data:{json.dumps([round(per_month)]*len(floats))},borderColor:"#a4432e",borderDash:[6,4],borderWidth:1.5,pointRadius:0}}]}},options:{{scales:{{y:{{ticks:{{callback:fmtL}}}},x:{{grid:{{display:false}}}}}},plugins:{{legend:{{position:"bottom",labels:{{boxWidth:10,font:{{size:11}}}}}}}}}}}});'''
page("reserves.html","Our reserves",res,rjs)
# feedback
def bar(d):
    t=sum(d.values()) or 1; cols={"Very good":"#2f6b3a","Good":"#0f5b57","Acceptable":"#c9c6b8","Poor":"#c9a227","Very poor":"#a4432e"}
    return '<div class="bar">'+"".join(f'<span style="width:{d[s]/t*100}%;background:{cols[s]}" title="{s}: {d[s]}"></span>' for s in cols)+'</div>'
servrows="".join(f'<tr><td>{l}</td><td>{bar(dist[k])}</td><td class="num">{m:.2f}</td><td class="num{" neg" if p/nn>=0.2 else ""}">{p/nn*100:.0f}%</td></tr>' for l,m,nn,p,k in serv)
prows="".join(f'<tr><td>{p}</td><td class="num">{c}</td><td class="num">{c/n*100:.0f}%</td></tr>' for p,c in prio.most_common(8))
irows="".join(f'<tr><td>{l}</td><td class="num">{m:.2f}</td><td class="num{" neg" if p/nn>=0.25 else ""}">{p/nn*100:.0f}%</td></tr>' for l,m,nn,p in iss)
wrows="".join(f'<tr><td>{w}</td><td class="num">{c}</td><td class="num">{s/c*100:.0f}%</td><td class="num{" neg" if lm<3 else ""}">{lm:.2f}</td></tr>' for w,c,s,lm in wingrows)
fb=f'''<section><div class="eyebrow">Resident services survey · 23 August to 2 September 2026</div><h1>What you told us</h1>
<p class="lead">{n} households answered, about a quarter of the estate. {sat/n*100:.0f}% are satisfied or very satisfied overall. Two services fail: lifts and pest control. And complaints are easy to raise but slow to close. Here is the full picture, and what is being done.</p>
<div class="tiles">{tile("","Responses",str(n),"of 294 flats, all four wings")}{tile("good","Satisfied overall",f"{sat/n*100:.0f}%","mean {:.2f} of 5".format(sum(OV[r["overall"]] for r in sv)/n))}{tile("crit","Weakest service",serv[-1][0],f"{serv[-1][3]/serv[-1][2]*100:.0f}% rate it poor or worse")}{tile("good","Strongest service",serv[0][0],f"mean {serv[0][1]:.2f} of 5")}</div></section>
<section><h2>Service ratings</h2>
<div class="tablewrap"><table><thead><tr><th>Service</th><th>Ratings</th><th class="num">Mean / 5</th><th class="num">Poor or worse</th></tr></thead><tbody>{servrows}</tbody></table></div>
<div class="legend"><span><i style="background:#2f6b3a"></i>Very good</span><span><i style="background:#0f5b57"></i>Good</span><span><i style="background:#c9c6b8"></i>Acceptable</span><span><i style="background:#c9a227"></i>Poor</span><span><i style="background:#a4432e"></i>Very poor</span></div></section>
<section><div class="charts"><div><h2>What you want fixed first</h2><div class="tablewrap"><table><thead><tr><th>Priority</th><th class="num">Chose it</th><th class="num">Share</th></tr></thead><tbody>{prows}</tbody></table></div><p class="small">Each household could pick up to three.</p></div>
<div><h2>Complaint handling</h2><p class="small">Rated by the {len(rep)} households that reported an issue in the last six months.</p><div class="tablewrap"><table><thead><tr><th>Step</th><th class="num">Mean / 5</th><th class="num">Poor or worse</th></tr></thead><tbody>{irows}</tbody></table></div></div></div></section>
<section><h2>By wing</h2><div class="tablewrap"><table><thead><tr><th>Wing</th><th class="num">Responses</th><th class="num">Satisfied</th><th class="num">Lifts, mean / 5</th></tr></thead><tbody>{wrows}</tbody></table></div><p class="small">Wing 1 had the fewest responses and the lowest lift score; the committee is visiting rather than surveying.</p></section>
<section><h2>What is being done</h2>
<ol class="steps">
<li><strong>Lifts.</strong> A monthly log of breakdowns and time-to-restore per lift, published on the <a href="services.html">lifts page</a> from October; a root-cause report on the Wing 1 and Wing 4 machines; the lift contract rebid on uptime, with penalties.</li>
<li><strong>Pest control and mosquitoes.</strong> The vendor's schedule audited against what was actually done; source reduction around the STP, basements and drains; a published fogging calendar; drain-line treatment for cockroaches.</li>
<li><strong>Complaints.</strong> A response standard in MyGate: acknowledged within four working hours, an update every 48 hours, closed only when you confirm. The numbers will be published monthly on the <a href="services.html">complaints page</a>.</li>
<li><strong>Security.</strong> The retender specification is written from your comments: guards who speak Kannada, a limit on turnover, a post at each block entrance, logged basement rounds, and a way for guards to recognise residents.</li>
<li><strong>Play area.</strong> The hardened sand and exposed pipes reported by two households are being inspected and fixed first, as a safety matter.</li>
<li><strong>Costs.</strong> Several of you raised overstaffing, Sobha's cost, the ₹7,500 GST line and user charges for the gym and tennis court. All four are addressed on <a href="shortfall.html">the shortfall page</a> and will be in the meeting pack.</li>
</ol>
<p class="small">The survey was anonymous. Individual comments are not published; they have been read, grouped, and each one has an owner on the committee.</p></section>'''
page("feedback.html","What you told us",fb)
# services
def lifts_html():
    if not lifts: return '<div class="empty"><strong>No data published yet.</strong> The first monthly lift report will be published here by 10 October 2026, covering September. It will show, for each wing: the number of breakdowns, the hours each lift was out of service, the uptime percentage, and the time taken to restore service, from the lift contractor\'s call log checked against the security register.</div>'
    return '<div class="tablewrap"><table><thead><tr><th>Month</th><th>Wing</th><th class="num">Lifts</th><th class="num">Breakdowns</th><th class="num">Hours down</th><th class="num">Uptime</th><th>Note</th></tr></thead><tbody>'+"".join(f'<tr><td>{r["month"]}</td><td>{r["wing"]}</td><td class="num">{r["lifts"]}</td><td class="num">{r["breakdowns"]}</td><td class="num">{r["hours_down"]}</td><td class="num">{r["uptime_pct"]}%</td><td class="small">{r["note"]}</td></tr>' for r in lifts)+'</tbody></table></div>'
def comps_html():
    if not comps: return '<div class="empty"><strong>No data published yet.</strong> From October, a monthly table from MyGate: complaints opened and closed by category, how many were still open at month-end, and the average days to close. The standard the committee has set is: acknowledged within four working hours, an update every 48 hours, closed only when the resident confirms.</div>'
    return '<div class="tablewrap"><table><thead><tr><th>Month</th><th>Category</th><th class="num">Opened</th><th class="num">Closed</th><th class="num">Open at month-end</th><th class="num">Avg days to close</th><th>Note</th></tr></thead><tbody>'+"".join(f'<tr><td>{r["month"]}</td><td>{r["category"]}</td><td class="num">{r["opened"]}</td><td class="num">{r["closed"]}</td><td class="num">{r["open_at_month_end"]}</td><td class="num">{r["avg_days_to_close"]}</td><td class="small">{r["note"]}</td></tr>' for r in comps)+'</tbody></table></div>'
svc=f'''<section><div class="eyebrow">Service performance · published monthly from October 2026</div><h1>Lifts and complaints</h1>
<p class="lead">The two things residents asked for most in the survey were lifts that work and complaints that get closed. Both will be measured and published here every month, by the 10th, so that the trend is visible to everyone and not just to the committee.</p></section>
<section><h2>Lift uptime</h2><p>Lifts were the lowest-rated service in the survey (3.30 of 5) and the top priority for 54% of households. The association pays about ₹16 L a year for the lift maintenance contract and spent ₹6.75 L on batteries last year.</p>{lifts_html()}</section>
<section><h2>Complaint resolution</h2><p>Half of the households that answered the survey had raised a complaint in the last six months. They found it easy to report (3.90 of 5) and hard to get closed: ownership until closure scored 3.05, and time to resolve 3.13.</p>{comps_html()}</section>
<section><h2>How this will be kept honest</h2><ol class="steps"><li>Lift figures come from the contractor's call log, cross-checked against the security gate register of technician visits.</li><li>Complaint figures come straight from MyGate's ticket export; nothing is re-typed.</li><li>Both are published by the 10th of the following month, with the raw file available on request to any owner.</li></ol></section>'''
page("services.html","Lifts and complaints",svc)
# documents & faq
FAQ=[("Why is the association short of money?","Costs have risen faster than the maintenance rate, which has not changed since handover, and last year's committee covered the difference from the reserves. Security alone costs ₹15 L a year more after the change of agency in November 2025. The full picture is on the money page."),
("Isn't ₹9 crore in reserves enough to carry on?","It would carry on for a few years and then be gone, and it is the fund for lifts, painting and waterproofing in the years ahead. Its interest, about ₹67 L a year before tax, is already being spent on running costs. Spending the principal too is what last year's committee did, and what the General Body objected to."),
("Why can't the committee just raise the rate now?","The bye-laws give the General Body, not the committee, the power to approve the budget and set the monthly charge. The earliest a Special General Body Meeting can be held is 18 October. The 1 October bill is therefore at the current rate."),
("What will the increase be?","The committee's proposal will be in the meeting notice, with the budget behind it. The working range is 18–22% on the base charge before GST. The shortfall page shows what 20% would mean for each flat type, and the two ways GST could apply."),
("Why does GST suddenly matter?","Maintenance above ₹7,500 a month per flat attracts 18% GST. The larger flats (A and A1 types) are at ₹7,432–7,499 today, so any increase crosses the line. Whether GST then applies to the whole amount or only to the excess changes the bill by over ₹1,300 a month, and whether the association can reclaim the GST on its own contracts changes the increase needed. The committee is taking written advice before the notice."),
("What happened to last year's money?","The Finance Sub-Committee's report, on the documents page, sets out the specific decisions it questioned: the pool repair, lift batteries, the security agency switch, paver work, a payment without an invoice, and withdrawals from the reserves. The previous committee has been asked to respond in writing to each; the auditor has been asked to explain. Both responses will be published, and the General Body will be asked to approve an independent review."),
("Is anyone being accused of anything?","No. The Sub-Committee's report raises questions; the answers are being sought; a professional review will establish facts. Nobody will be named or blamed on these pages ahead of that."),
("Why not cut costs instead of raising the rate?","Both are happening. The facility and security contracts, ₹1.8 Cr a year between them, are being tendered for the first time. But tenders take months, and residents rated housekeeping and landscaping the best-run services on the estate. The committee will not cut those to avoid an increase; it will cut what is not working, starting with the lift contract."),
("What is the committee doing about lifts and pest control?","See the feedback page. In short: a public lift log from October, a root-cause report on the worst machines, the lift contract rebid on uptime; and for pests, an audit of what the vendor actually does, source reduction, and a published schedule."),
("How do I know these numbers are right?","They are taken from the accountant's monthly statements and the banks' own deposit summaries, and the sources are named on each page. They are not audited figures; the audited accounts are annual. Anything that is an estimate says so. If you find an error, write to spcaoa@gmail.com and it will be corrected and noted."),
("How often are these pages updated?","Monthly, after the accountant's statement for the month is received, and immediately after any General Body decision. The date at the foot of each page says what the figures cover.")]
faq="".join(f'<details><summary>{q}</summary><p>{a}</p></details>' for q,a in FAQ)
docs=f'''<section><div class="eyebrow">Source documents and questions</div><h1>Documents and FAQ</h1>
<div class="cards">
<div class="card"><h3>Finance Sub-Committee report</h3><p class="small">31 August 2026. The resident volunteers' review of FY 2025–26, with annexures on expenses, income and their 10% simulation.</p><a class="btn ghost" href="docs/SPC-Finance-SubCommittee-Report-2026-08-31.pdf">Open PDF</a></div>
<div class="card"><h3>General Body Meeting presentation</h3><p class="small">26 July 2026. The committee's presentation: audited FY 2025–26 summary, the corpus drawdown, cost proposals and the two funding options the meeting declined.</p><a class="btn ghost" href="docs/SPCAOA-GBM-Deck-2026-07-26.pdf">Open PDF</a></div>
<div class="card"><h3>Independent Auditor's Report, FY 2025–26</h3><p class="small">20 July 2026. Two pages; unqualified opinion. The full audited statements with notes will be added with the meeting pack.</p><a class="btn ghost" href="docs/Independent-Auditors-Report-FY25-26.pdf">Open PDF</a></div>
</div></section>
<section><h2>The numbers behind these pages</h2><p>Nothing here is a summary you have to take on trust. The data files the pages are built from are below, along with the ledgers received from Sobha and the Treasurer. Files that carry individual flats' dues, employee salaries by name or guards' names are not published; the totals from them are.</p>
<div class="cards">
<div class="card"><h3>Expenses, April–July 2026</h3><p class="small">Every head, every month, from the accountant's statements. CSV.</p><a class="btn ghost" href="data/expenses.csv">Download</a></div>
<div class="card"><h3>Income, treasury and budget</h3><p class="small">Income lines, month-end bank and deposit positions, and the working budget. CSV.</p><a class="small" href="data/income.csv">income.csv</a> · <a class="small" href="data/treasury.csv">treasury.csv</a> · <a class="small" href="data/budget.csv">budget.csv</a></div>
<div class="card"><h3>Vendor bills and deposits</h3><p class="small">The two largest contracts invoice by invoice, and the fixed deposits by bank. CSV.</p><a class="small" href="data/vendor_bills.csv">vendor_bills.csv</a> · <a class="small" href="data/fds.csv">fds.csv</a></div>
<div class="card"><h3>Sobha's corpus ledger</h3><p class="small">Sobha's own statement of the owners' corpus, June 2022 to August 2026. Excel, as received.</p><a class="small" href="docs/Sobha-corpus-fund-statement-2022-06-to-2026-08.xlsx">Download</a></div>
<div class="card"><h3>Treasurer's deposit ledger</h3><p class="small">Month-by-month fixed-deposit balances by bank, November 2023 to June 2026. Excel, as received.</p><a class="small" href="docs/FD-ledger-2023-2026-treasurer.xlsx">Download</a></div>
<div class="card"><h3>The books themselves</h3><p class="small">The association's accounts are kept in TallyPrime. A backup dated 7 September 2026 is held by the committee; audited statements are published annually, and ledger extracts can be requested by any owner.</p></div>
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

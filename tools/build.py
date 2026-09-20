#!/usr/bin/env python3
"""Build the residents' pages into docs/ from the MC site's data plus local JSON.
Usage: python3 tools/build.py   (passcode read from tools/passcode.txt; empty file = no gate)"""
import csv, json, os, sys, hashlib, datetime, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MC=os.path.join(os.path.dirname(ROOT),"spc-finance-site","site","data")
OUT=os.path.join(ROOT,"docs"); DATA=os.path.join(ROOT,"data")
UPDATED="17 September 2026"
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
bankbal=json.load(open(os.path.join(DATA,"bank_balances.json")))["rows"]
floats=[(ML(r["month"]),float(r["bank_cash"])) for r in bankbal]
book_last=fl(tr[-1])
fds=json.load(open(os.path.join(DATA,"fds.json"))); runway=json.load(open(os.path.join(DATA,"runway.json"))); rates=json.load(open(os.path.join(DATA,"rates.json")))
lifts=rd(os.path.join(DATA,"lifts.csv")); comps=rd(os.path.join(DATA,"complaints.csv")); lsvc=rd(os.path.join(DATA,"lifts_service.csv"))
hdfc=[b for b in fds["banks"] if b["bank"].startswith("HDFC")][0]; icici=[b for b in fds["banks"] if b["bank"].startswith("ICICI")][0]; sobha=[b for b in fds["banks"] if "Sobha" in b["bank"]][0]
reserves=hdfc["principal"]+icici["ledger"]+sobha["principal"]
int_yr=hdfc["principal"]*hdfc["rate"]/100+icici["principal"]*icici["rate"]/100+sobha["principal"]*sobha["rate"]/100
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
<meta name="theme-color" content="#0b4f37">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%230b4f37'/%3E%3Ctext x='32' y='43' font-family='Georgia,serif' font-size='30' font-weight='700' fill='%23f4f1e4' text-anchor='middle'%3ESP%3C/text%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400..800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css?v={VER}"><script src="assets/gate.js?v={VER}"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script></head><body>
<div class="topbar"><div class="in"><a class="brand" href="index.html">Sobha Palm Court<small>Apartment Owners' Association</small></a><button class="menubtn" id="menubtn" aria-label="Menu" aria-expanded="false" aria-controls="tabs"><svg class="b" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 6h18M3 12h18M3 18h18"/></svg><svg class="x" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg></button><nav class="tabs" id="tabs" aria-label="Pages">{nav}</nav></div></div>
<div class="wrap">{body}
</div><footer><div class="fin">
<p>Updated {UPDATED}. Accounts to end {ML(months[-1])}; deposits as at {fds["as_at"]}; survey August 2026. Published by the Managing Committee.</p>
<p>1 lakh = ₹1,00,000. 1 crore = 100 lakh. Figures come from the accountant's monthly statements and the banks' own statements. They are not audited and are updated monthly.</p>
<p>Questions: <a href="mailto:spcaoa@gmail.com">spcaoa@gmail.com</a></p>
</div></footer>
<script src="assets/ui.js?v={VER}"></script>
<script>{scripts}</script></body></html>'''
    open(os.path.join(OUT,fn),"w",encoding="utf-8").write(html)
def tile(cls,k,v,d): return f'<div class="tile {cls}"><div class="k">{k}</div><div class="v">{v}</div><div class="d">{d}</div></div>'
CH='const css=v=>getComputedStyle(document.documentElement).getPropertyValue(v).trim();Chart.defaults.color=css("--muted");Chart.defaults.borderColor=css("--line-soft");Chart.defaults.font.weight="500";Chart.defaults.font.family="Inter,-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif";Chart.defaults.font.size=12;const fmtL=v=>"₹"+(v/1e5).toFixed(1)+" L";'
# ---------- pages
per_month=tot/nM; gap=per_month-maint; inc_other=hdfc_int+sobha_int+other+icici_acc
idx=f'''<section><div class="eyebrow">September 2026</div>
<h1>Where we stand</h1>
<p class="lead">Running Palm Court costs about {L(per_month)} a month. Maintenance brings in {L(maint)}. The rest has been coming out of the reserves — the money owners paid at handover, meant for big repairs. That cannot go on. These pages show the numbers, what the Managing Committee is proposing, and what you will be asked to decide.</p>
<div class="hero">
<div class="big"><div class="k">Shortfall</div><div class="v">₹84 L a year</div><div class="d">We spend about {L(per_month)} a month and collect {L(maint)} in maintenance. Interest and other income add {L(inc_other)}. The rest comes from the reserves. ₹15 L a year of cost has already been cut, and we hope for ₹5 L more; the rest has to come from maintenance.</div></div>
<div class="rest">
{tile("","Spend per month",L(per_month),f"{ML(months[0])}–{ML(months[-1])} average, everything included")}
{tile("","Maintenance per month",L(maint),"₹57.6 L billed each quarter")}
{tile("accent","Reserves",L(reserves),"fixed deposits plus the balance with Sobha")}
{tile("crit" if floats[-1][1] < per_month*0.5 else "warn","Cash in the bank, end "+ML(months[-1]),L(floats[-1][1]),f"{L(book_last)} after cheques already written; about {round(floats[-1][1]/per_month*4.3)} weeks of spending")}
</div></div>
<div class="glossary">1 lakh = ₹1,00,000. 1 crore = 100 lakh. Reserves (the corpus) are the money owners paid at handover, kept in fixed deposits for big repairs.</div>
</section>
<section><h2>The short version</h2>
<ol class="steps">
<li>Between April and August we spent {L(tot)}. Maintenance for those five months was {L(maint*nM)}. The difference came from the reserves.</li>
<li>The reserves are about {L(reserves)}. Their interest already goes on running costs. Last year ₹50 L of the reserves themselves was used as well, and this year another ₹38 L so far.</li>
<li>The Managing Committee is proposing a <strong>23% increase</strong> in maintenance, with a second option that adds a one-time ₹1 lakh per flat to rebuild the reserves. The <a href="simulator.html">options page</a> shows what each would mean for your flat.</li>
<li>A <strong>Special General Body Meeting on Sunday, 25 October</strong> discusses it. Every owner then votes in an online poll that opens straight after the meeting and closes a week later.</li>
<li>The 1 October bill is at the current rate. Only the General Body can change it.</li>
<li>Last year's accounts were reviewed by the Finance Sub-Committee, a group of resident owners. Their report, and the previous Managing Committee's answers, go out with the meeting notice. <span class="small">The ₹48 lakh shortfall last year was reported at the July AGM.</span></li>
</ol></section>
<section><h2>What happens next</h2>
<div class="timeline">
<div class="when">20 Sep</div><div>These pages shared with every owner.</div>
<div class="when">Fri, 25 Sep</div><div>Meeting notice to every owner, with the budget, the options, the Finance Sub-Committee's report and how to vote.</div>
<div class="when">28 Sep</div><div>Previous Managing Committee's written answers due. Published as received.</div>
<div class="when">1 Oct</div><div>Quarterly maintenance bill, at the current rate.</div>
<div class="when">Sun, 25 Oct</div><div>Special General Body Meeting.</div>
<div class="when">25 Oct – 1 Nov</div><div>Online poll for every owner: the maintenance rate and the other decisions. One flat, one vote.</div>
<div class="when">Nov</div><div>If a new rate is approved from 1 October, the difference for October–December is billed in November.</div>
</div></section>
<section><h2>Read on</h2><div class="readon">
<a href="money.html"><span class="t">Where the money goes</span><span class="d">Every expense, month by month</span></a>
<a href="simulator.html"><span class="t">Try the options</span><span class="d">What 23%, or 23% plus ₹1 lakh, means for your flat</span></a>
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
<p class="lead">Everything paid out from {ML(months[0])} to {ML(months[-1])}, in the month it was paid. Nothing is smoothed. The half-yearly lift contract shows in June because that is when it was paid. One correction has been made to the accountant's figures: the June statement charged Sobha's ₹8.4 L monthly bill, and July charged it again; the ledger and the bank show one payment, on 23 July, so June has been reduced by ₹8.4 L pending a reissued statement.</p>
<div class="tiles">{tile("","Paid out, "+ML(months[0])+chr(8211)+ML(months[-1]),L(tot),f"{L(routine)} running costs + {L(onetime)} one-time items")}{tile("","Per month",L(per_month),"one-time items included")}{tile("crit","Maintenance covers",f"{maint/(routine/nM)*100:.0f}%","of running costs")}</div></section>
<section><div class="charts"><div class="chartbox"><h3>Month by month, by category</h3><div class="ch" style="height:280px"><canvas id="c1"></canvas></div></div><div class="chartbox"><h3>{nM} months, by category</h3><div class="ch donut" style="height:240px"><canvas id="c2"></canvas></div></div></div>
<p class="small">The dashed line is monthly maintenance income. The gap above it is the shortfall.</p></section>
<section><h2>The biggest heads</h2>
<div class="tablewrap"><table><thead><tr><th>Head</th><th class="num">Per month</th><th class="num">Share of running costs</th></tr></thead><tbody>{headrows}</tbody></table></div>
<p>The three largest of these are about two-thirds of the total, but the rest is not small: taxes, water, lifts, the sewage plant, waste, pest control, repairs and insurance make up the remainder. The big three are facility management by Sobha (₹{byhead["Sobha Ltd - FMS"]/nM*12/1e5:.0f} L a year), security by VEX (₹85 L including GST) and electricity (₹60 L). Both service contracts are going to tender. The target is ₹15–20 L a year in savings, on top of the ₹15 L already taken out of the security bill.</p></section>
<section><h2>One-time items</h2><p>Repairs and purchases outside the monthly run. {L(onetime)} in {nM} months. The largest:</p>
<div class="tablewrap"><table><thead><tr><th>Month</th><th>Item</th><th class="num">Amount</th></tr></thead><tbody>{otrows}</tbody></table></div>
<p class="small">New rules for how the association buys things and pays for them will be put to owners for approval at the meeting.</p></section>'''
mjs=CH+f'''new Chart(document.getElementById("c1"),{{data:{{labels:{json.dumps([ML(m) for m in months])},datasets:[{",".join(f'{{type:"bar",label:{json.dumps(c)},data:{json.dumps([round(bymc[m][c]) for m in months])},backgroundColor:{CATCOL[i]},stack:"s",borderWidth:0}}' for i,c in enumerate(CATS))},{{type:"line",label:"Maintenance billed",data:{json.dumps([round(maint)]*nM)},borderColor:css("--crit"),borderDash:[6,4],borderWidth:2,pointRadius:0}}]}},options:{{responsive:true,maintainAspectRatio:false,interaction:{{mode:"index",intersect:false}},scales:{{x:{{stacked:true,grid:{{display:false}}}},y:{{stacked:true,ticks:{{callback:fmtL}},beginAtZero:true}}}},plugins:{{legend:{{position:"bottom",labels:{{boxWidth:10,font:{{size:11}}}}}}}}}}}});
new Chart(document.getElementById("c2"),{{type:"doughnut",data:{{labels:{json.dumps(CATS)},datasets:[{{data:{json.dumps([round(cattot[c]) for c in CATS])},backgroundColor:[{",".join(CATCOL)}],borderWidth:2,borderColor:css("--surface")}}]}},options:{{responsive:true,maintainAspectRatio:false,cutout:"58%",plugins:{{legend:{{position:"bottom",labels:{{boxWidth:10,font:{{size:11}}}}}}}}}}}});'''
page("money.html","Where the money goes",money,mjs)
# shortfall
rw=runway["rows"]
def cell(v): return f'<td class="num{" neg" if v<0 else ""}">{v:+.1f}</td>'.replace("+","") if v>=0 else f'<td class="num neg">−{abs(v):.1f}</td>'
rrows="".join(f'<tr><td>{r["m"]}</td><td class="num">{r["in"]:.1f}</td><td class="num">{r["out"]:.1f}</td>{cell(r["a"])}{cell(r["c"])}</tr>' for r in rw)
inc_pct=rates["increase"]
def gst_flats(p):
    return sum(t["count"] for t in rates["types"] if t["quarter"]/3*(1+p)>7500)
def a_type(p):
    t=rates["types"][0]; return t["quarter"]/3*(1+p)
def rate_row(t):
    q=t["quarter"]; m=q/3
    def at(p):
        nw=m*(1+p); g=nw*0.18 if nw>7500 else 0
        return f'<td class="num">{inr(nw)}</td><td class="num">{inr(nw+g)}</td>'
    return f'<tr><td>{t["type"]}</td><td class="num">{inr(m)}</td>'+at(inc_pct)+at(0.39)+'</tr>'
raterows="".join(rate_row(t) for t in rates["types"])
sf=f'''<section><div class="eyebrow">The gap, and two ways to close it</div><h1>The shortfall and the plan</h1>
<p class="lead">We spend more than we collect. This page shows how much, what is being done about costs, and the three options the Managing Committee is putting to owners.</p></section>
<section class="split"><div class="body"><h2>How big is the gap?</h2>
<p>At this year's rate of spending, the association is about ₹84 L a year short. ₹15 L a year has already been cut by reducing the number of security posts, and the Managing Committee hopes for about ₹5 L more from housekeeping and technical staffing. If both come through, ₹64 L is left to come from maintenance.</p>
<div class="tablewrap"><table><thead><tr><th>A full year, at this year's rate</th><th class="num">₹ a year</th></tr></thead><tbody>
<tr><td>What we spend (running costs ₹3.20 Cr, plus about ₹40 L of one-off repairs and renewals)</td><td class="num">3.60 Cr</td></tr>
<tr><td>What comes in (maintenance ₹2.31 Cr, interest ₹66 L, other income ₹10 L, less ₹25 L tax on the interest)</td><td class="num">2.76 Cr</td></tr>
<tr><td><strong>Gap</strong></td><td class="num"><strong>84 L</strong></td></tr>
<tr><td>Already cut: fewer security posts</td><td class="num">15 L</td></tr>
<tr><td>Hoped for: housekeeping and technical staffing</td><td class="num">5 L</td></tr>
<tr><td><strong>Left to find from maintenance</strong></td><td class="num"><strong>64 L</strong></td></tr>
<tr><td>A 20% increase brings in</td><td class="num">45 L — still ₹19 L short</td></tr>
<tr><td><strong>A 23% increase brings in</strong></td><td class="num"><strong>52 L — still ₹12 L short</strong></td></tr>
<tr><td>To balance from maintenance alone would take</td><td class="num">about 28%</td></tr>
</tbody></table></div>
<p class="small">Earlier estimates of the gap ranged from ₹23 L to ₹91 L because they counted different things. This page uses what was actually spent from April to August. The ₹40 L of one-offs includes an ₹8 L five-year licence, so next year's one-offs may be lower, which would cover most of the ₹12 L.</p></div>
<aside class="side"><h3>The year in five numbers</h3><dl>
<dt>What we spend</dt><dd>₹3.60 Cr</dd>
<dt>What comes in</dt><dd>₹2.76 Cr</dd>
<dt>Gap</dt><dd class="up">₹84 L</dd>
<dt>Already cut</dt><dd>₹15 L</dd>
<dt>Hoped for</dt><dd>₹5 L</dd>
<dt>To find from maintenance</dt><dd class="key">₹64 L</dd>
</dl><p class="note">A full year at this year's rate of spending. Every figure comes from what was actually paid between April and August.</p></aside></section>
<section class="split"><div class="body"><h2>Each option, in plain words</h2>
<p><strong>Carry on as we are.</strong> The reserves keep paying the difference — about ₹64 L a year after the savings. The interest they earn is already spent; this eats the principal. At that rate, the money set aside for the big jobs — lift replacement and overhaul, painting, waterproofing, the sewage plant, and the things we cannot yet foresee — is gone in about fifteen years, and the estate has nothing when those bills come.</p>
<p><strong>The Finance Sub-Committee's 10.1%.</strong> The Finance Sub-Committee, the resident owners who reviewed last year's accounts, proposed 10.1%. It does not work, for two separate reasons, and it is worth being precise about both. First, their 10.1% was on the bill <em>including</em> GST. For the 148 flats that cross ₹7,500, that GST is inside the new amount, so the association's own share goes <em>down</em>: an A-type flat would pay ₹8,183, of which ₹1,248 is GST, leaving ₹6,934 for the association against ₹7,432 today. Across the estate the association ends up about ₹2 L a year better off — not ₹23 L. (If GST applied only above ₹7,500, it would be about ₹22 L.) Second, their gap of ₹23 L was small because it left out one-off repairs, counted ₹18 L of savings before any had been made, and put tax at a third of what is actually paid. Even 10.1% on the base charge would raise ₹23 L of the ₹64 L needed.</p>
<p><strong>Option A: a 23% increase.</strong> Raises ₹52 L. The monthly account is still about ₹12 L a year short on paper; if one-off repairs ease next year, that closes. Nothing is set aside for the future. The A- and B-type flats cross ₹7,500 and pay GST; the C, D and D1 flats do not.</p>
<p><strong>Option B: 23%, plus a one-time ₹1 lakh from each flat into the reserves.</strong> The ₹1 lakh is not spent. It goes into fixed deposits, and the interest — about ₹12 L a year after tax — closes the gap. The ₹2.9 Cr also puts back what was taken out of the reserves over the last two years. Collected over about six months from November. Whether GST applies to it is being checked.</p>
<p><strong>Option C: a 39% increase, nothing one-time.</strong> Raises ₹86 L. This is the only way to both balance the account and rebuild the reserves out of maintenance alone, and it is close to what the July meeting was asked for and turned down. The cost is the GST line: at 39% the C and D1 flats cross ₹7,500 too, so 286 of the 294 flats pay 18% GST — for a C-type that is about ₹1,515 a month going to the government on top of the increase. Option B reaches the same place for 23% and a one-time payment.</p>
<p>Either way, this financial year still needs about ₹75 L from the reserves, because a new rate would only apply from October. The increase fixes next year, not this one.</p></div>
<div class="sidecol"><aside class="side"><h3>An A-type flat pays</h3><dl>
<dt>Today</dt><dd>{inr(a_type(0))}</dd>
<dt>Option A or B</dt><dd class="key">{inr(a_type(inc_pct))}</dd>
<dt>Option C</dt><dd class="up">{inr(a_type(0.39))}</dd>
</dl><p class="note">A month, before GST. Option B adds ₹1 lakh once. The other flat types are in the table below.</p></aside>
<aside class="side"><h3>Left short each year</h3><dl>
<dt>Carry on as we are</dt><dd class="up">₹64 L</dd>
<dt>Sub-Committee 10.1%</dt><dd class="up">₹62 L</dd>
<dt>Option A</dt><dd>₹12 L</dd>
<dt>Option B</dt><dd class="key">none</dd>
<dt>Option C</dt><dd class="key">none</dd>
</dl></aside></div></section>
<section class="split"><div class="body"><h2>Why 23%?</h2>
<p>Two reasons. It is the most that can be asked before the C-type flats cross ₹7,500 a month, which is where 18% GST starts. The A- and B-type flats cross that line at any increase at all — that is the tax law's threshold, not the association's choice — but going past 23% would put three-quarters of the estate into GST for no gain to the association, because the GST goes to the government. And 23% is close enough that the ₹1 lakh option, or a good year on repairs, balances it.</p>
<p><strong>Why not 15% plus ₹1 lakh?</strong> Because of tax. At 15% the account is ₹30 L a year short, and the ₹1 lakh from each flat earns only ₹12 L a year after the association's 39% tax on interest. The other ₹18 L would have to be taken out of the reserves every year. For 15% to work without touching the reserves, the one-time amount would need to be about ₹2.4 lakh per flat.</p></div>
<aside class="side"><h3>Flats paying GST</h3><dl>
<dt>Today</dt><dd>{gst_flats(0)}</dd>
<dt>At 23%</dt><dd class="key">{gst_flats(0.23)}</dd>
<dt>At 24%</dt><dd class="up">{gst_flats(0.24)}</dd>
<dt>At 39%</dt><dd class="up">{gst_flats(0.39)}</dd>
</dl><p class="note">Out of 294 flats. GST starts once a flat's charge passes ₹7,500 a month. The jump between 23% and 24% is the C-type flats crossing the line.</p></aside></section>
<section><h2>Cash, month by month</h2>
<p>The bank held {L(floats[-1][1])} at the end of {ML(months[-1])}, {L(book_last)} after the cheques already written — under two weeks of spending. The next bill is 1 October, at the current rate. The table shows where the account goes if nothing changes, and with a 23% increase from 1 October. Below zero means the reserves are being used.</p>
<div class="tablewrap"><table><thead><tr><th>Month-end</th><th class="num">In</th><th class="num">Out</th><th class="num">If nothing changes</th><th class="num">With +23% from 1 Oct</th></tr></thead><tbody>{rrows}</tbody></table></div>
<p class="small">Spending ₹26 L a month, plus advance tax in September, December and March and the ₹8 L lift contract in December. No deposits maturing, no savings yet. Figures in lakhs.</p></section>
<section><h2>What it means for your flat</h2>
<p>Once a flat's monthly charge crosses ₹7,500, 18% GST applies. The tax department says it applies to the whole amount; a High Court has said only to the part above ₹7,500. The difference is about ₹1,300 a month for the larger flats. Which reading applies to us is not settled, so both are shown.</p>
<div class="tablewrap"><table><thead><tr><th>Flat type</th><th class="num">Today</th><th class="num">A and B: +{int(inc_pct*100)}%</th><th class="num">with GST</th><th class="num">C: +39%</th><th class="num">with GST</th></tr></thead><tbody>{raterows}</tbody></table></div>
<p class="small">GST is shown on the tax department's reading, which applies 18% to the whole amount once a flat crosses ₹7,500. On the High Court reading it applies only to the part above ₹7,500, which is about ₹1,300 a month less for the larger flats; both readings are shown because the position is not settled. At 23% the C, D and D1 flats stay under the line and pay none. At 39% the C flats cross it, and pay about ₹1,364 a month of GST on top of the increase. Option B adds ₹1 lakh once, for every flat.</p></section>
<section><h2>Why not just cut costs?</h2>
<p>Both are happening. The facility and security contracts have never been put out to tender; they are being tendered now, and ₹15 L a year has already been saved on guards. But the two together are ₹1.8 Cr a year, and residents rated housekeeping and gardening the best things about living here. Cutting those to avoid an increase would trade a visible service for an invisible saving.</p></section>'''
page("shortfall.html","The shortfall and the plan",sf)
# reserves
def rate_cell(b):
    if not b["rate"]: return "to confirm"
    return str(b["rate"])+"%"+(' <span class="small">implied</span>' if b.get("rate_note") else "")
bankrows="".join(f'<tr><td><strong>{b["bank"]}</strong></td><td class="num">{b["count"] or "—"}</td><td class="num">{L(b["principal"])}</td><td class="num">{rate_cell(b)}</td><td>{b["payout"]}</td><td>{b["maturity"]}</td></tr>' for b in fds["banks"])
res=f'''<section><div class="eyebrow">Fixed deposits and the corpus · as at {fds["as_at"]}</div><h1>Our reserves</h1>
<p class="lead">At handover in June 2022 the owners' corpus was ₹11.76 crore. Today it is about {L(reserves)}: {L(hdfc["principal"])} at HDFC, {L(icici["principal"])} at ICICI ({L(icici["ledger"])} with the interest added so far), and {L(sobha["principal"])} still with Sobha.</p>
<div class="tiles">{tile("","Reserves today",L(reserves),"HDFC + ICICI + held by Sobha")}{tile("","Interest they earn, per year","≈ "+L(int_yr),"HDFC 7.16%, ICICI 6.5%, Sobha 8%; taxed at 39% — an association pays the top rate plus surcharge and cess")}{tile("warn","Used for running costs, FY 25–26","₹50 L","net, without General Body approval")}{tile("","At handover, June 2022","₹11.76 Cr","held by Sobha until returned in 2023–24")}</div></section>
<section><div class="charts even"><div class="chartbox"><h3>Where the reserves sit</h3><div class="ch donut" style="height:240px"><canvas id="c3"></canvas></div></div><div class="chartbox"><h3>Cash in the operating account, month-end</h3><div class="ch" style="height:240px"><canvas id="c4"></canvas></div></div></div>
<p class="small">The quarterly bill fills the account. By month three it is nearly empty. Month-end balances are from the bank statements.</p></section>
<section><h2>The deposits</h2>
<div class="tablewrap"><table><thead><tr><th>Where</th><th class="num">Deposits</th><th class="num">Principal</th><th class="num">Rate</th><th>How interest is paid</th><th>Maturity</th></tr></thead><tbody>{bankrows}</tbody></table></div>
<p class="small">Sources: HDFC's account statements to 14 September 2026, ICICI's deposit summary of 7 September 2026, and Sobha's corpus statement. Account numbers are not published.</p>
</section>
<section class="split warnsec"><div class="body"><h2>Reconciling the deposits</h2>
<p class="lead-warn">The deposit figures on this page come from the banks' own statements, checked line by line against the association's accounts in September. <strong>ICICI is settled</strong> at ₹5.27 crore, confirmed against the bank's own statement. <strong>HDFC is nearly settled.</strong> The accounts and the interest actually received both give ₹3.81 crore at the end of August; one deposit of ₹24 lakh was closed on 3 September, leaving about ₹3.57 crore. The bank's summary screen lists sixteen deposits, and the full list is being obtained to confirm the last ₹37 lakh. <strong>Sobha still holds part of the corpus.</strong> Sobha's ledger shows ₹75 lakh, the association's books ₹90 lakh, because Sobha sets its unpaid bills off against it. Getting that money back is on the actions page. When any of these changes, this note will say so.</p></div>
<aside class="side"><h3>Where the figures stand</h3><dl>
<dt>ICICI, confirmed</dt><dd class="key">₹5.27 Cr</dd>
<dt>HDFC in the books, 31 Aug</dt><dd>₹3.81 Cr</dd>
<dt>Closed 3 September</dt><dd class="up">−₹24.2 L</dd>
<dt>HDFC today</dt><dd>₹3.57 Cr</dd>
<dt>Still to tie out</dt><dd class="up">≈ ₹37 L</dd>
</dl><p class="note">The bank's summary screen lists sixteen deposits; the full list has been asked for to close the last ₹37 L.</p></aside>
</section>
<section><h2>How ₹11.76 crore became {L(reserves)}</h2>
<div class="timeline">
<div class="when">Jun 2022</div><div>₹11.76 Cr collected by Sobha at handover. For sixteen months Sobha ran the estate from it: ₹1.88 Cr charged, ₹1.17 Cr of interest credited.</div>
<div class="when">Nov 2023 – Jun 2024</div><div>Sobha returned ₹9.30 Cr in nine instalments. It went into fixed deposits at HDFC and ICICI. Sobha kept ₹91 L as security for its facility service.</div>
<div class="when">2024–25 and 2025–26</div><div>Interest was spent on running costs. In 2025–26, ₹50 L of principal was also used, without General Body approval.</div>
<div class="when">2026–27 so far</div><div>Two HDFC deposits closed, ₹48.6 L in all (12 June and 3 September); ₹11 L placed in April. Net ₹37.6 L of principal used. ICICI's maturities were all re-deposited.</div>
<div class="when">Today</div><div>{L(reserves)}, of which {L(hdfc["principal"]+icici["ledger"])} is in bank deposits. How it got from ₹11.76 Cr to here, step by step from the audited accounts, goes out with the meeting notice.</div>
</div></section>
<section class="split"><div class="body"><h2>What owners will be asked to approve</h2>
<p>Several resolutions will be put to the vote so that what happened over the last two years cannot happen again. On the reserves, these four matter most; the full list will be in the meeting notice:</p>
<ol class="steps"><li><strong>The reserves stay put.</strong> Interest can be used for running costs. The deposits themselves are not broken without owners' approval, and if one ever is, it is reported here the month it happens.</li>
<li><strong>No one person can move deposit money.</strong> Any deposit movement needs three authorised signatories, or five members of the Managing Committee.</li>
<li><strong>A monthly deposit statement, from the banks.</strong> Published on these pages every month, taken from the banks' own statements rather than the association's books.</li>
<li><strong>A sinking fund from next year.</strong> A fixed amount set aside each year, so the ₹50 L used last year is rebuilt and the big jobs of the next ten years — lift replacement and overhaul, painting, waterproofing, the sewage plant and the rest — have money waiting for them.</li></ol></div>
<aside class="side"><h3>What has gone from the reserves</h3><dl>
<dt>At handover, June 2022</dt><dd>₹11.76 Cr</dd>
<dt>Returned by Sobha, 2023–24</dt><dd>₹9.30 Cr</dd>
<dt>Used in FY 2025–26</dt><dd class="up">₹50 L</dd>
<dt>Used so far in 2026–27</dt><dd class="up">₹38 L</dd>
<dt>Today</dt><dd class="key">{L(reserves)}</dd>
</dl><p class="note">Interest on the reserves is treated as income and already pays for running costs. The figures above are the principal itself.</p></aside></section>'''
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
<section><div class="charts even"><div><h2>What you want fixed first</h2><div class="tablewrap"><table><thead><tr><th>Priority</th><th class="num">Chose it</th><th class="num">Share</th></tr></thead><tbody>{prows}</tbody></table></div><p class="small">Each household could pick up to three.</p></div>
<div><h2>Complaint handling</h2><div class="tablewrap"><table><thead><tr><th>Step</th><th class="num">Mean / 5</th><th class="num">Poor or worse</th></tr></thead><tbody>{irows}</tbody></table></div><p class="small">Rated by the {len(rep)} households that reported an issue in the last six months.</p></div></div></section>
<section><h2>By wing</h2><div class="tablewrap"><table><thead><tr><th>Wing</th><th class="num">Responses</th><th class="num">Satisfied</th><th class="num">Lifts, mean / 5</th></tr></thead><tbody>{wrows}</tbody></table></div><p class="small">Wing 1 had the fewest responses and the lowest lift score. The MC is visiting.</p></section>
<section><h2>What is being done</h2>
<ol class="steps">
<li><strong>Lifts.</strong> A monthly log of breakdowns and time-to-restore per lift, published on the <a href="services.html">lifts page</a> from October; a root-cause report on the Wing 2 lifts, where most of the complaints are; and a renegotiation of the lift contract. The contract covers all eight lifts, runs five years, was signed by the previous committee and is now in its second or third year, so the MC can press for uptime targets and penalties but cannot promise to change it.</li>
<li><strong>Pest control and mosquitoes.</strong> The vendor's schedule audited against what was actually done; source reduction around the STP, basements and drains; a published fogging calendar; drain-line treatment for cockroaches.</li>
<li><strong>Complaints.</strong> A response standard in MyGate: acknowledged within four working hours, an update every 48 hours, closed only when you confirm. The numbers will be published monthly on the <a href="services.html">complaints page</a>.</li>
<li><strong>Security.</strong> The retender specification is written from your comments: guards who speak Kannada, a limit on turnover, a post at each block entrance, logged basement rounds, and a way for guards to recognise residents.</li>
<li><strong>Play area.</strong> The hardened sand and exposed pipes reported by two households are being inspected and fixed first, as a safety matter.</li>
<li><strong>Costs.</strong> Several of you raised overstaffing, Sobha's cost, the ₹7,500 GST line and user charges for the gym and tennis court. All four are addressed on <a href="shortfall.html">the shortfall page</a> and will go out with the meeting notice.</li>
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
lsvc_rows="".join(f'<tr><td>{r["wing"]} · {r["type"].lower()} <span class="small">({r["lift"]})</span></td><td>{datetime.date.fromisoformat(r["date"]).strftime("%-d %b %Y")}</td><td>{"<strong>"+r["kind"]+"</strong>" if r["kind"]=="Repair" else r["kind"]}</td><td class="small">{r["detail"]}</td></tr>' for r in lsvc)
svc=f'''<section><div class="eyebrow">Service performance · published monthly from October 2026</div><h1>Lifts and complaints</h1>
<p class="lead">Lifts and complaints were the top two issues in the survey. Both will be measured and published here every month from October.</p></section>
<section><h2>Lift uptime</h2><p>Lifts were the lowest-rated service (3.30 of 5) and the top priority for 54% of households. The lift contract costs ₹16 L a year. Batteries cost ₹6.75 L last year.</p>{lifts_html()}</section>
<section><h2>Service record, January to August 2026</h2>
<p>From the contractor's worksheets for the eight lifts. Each lift had three maintenance visits in eight months, roughly one a quarter, and three lifts had a repair call: the Wing 2 service lift (door sensor, March), the Wing 4 passenger lift (door clutch, June, a week to complete) and the Wing 4 service lift (16th-floor button, June). The worksheets do not record how long a lift was out of service, which is why the uptime log above starts from October.</p>
<div class="tablewrap"><table class="svc"><thead><tr><th>Lift</th><th>Date</th><th>Visit</th><th>What was done</th></tr></thead><tbody>{lsvc_rows}</tbody></table></div>
<p class="small">Each wing has a passenger lift and a service lift; the number in brackets is the manufacturer's serial. "Statutory 5-year inspection" is the contractor's five-yearly safety check. Source: Schindler's e-worksheets, as received — <a href="docs/Schindler-lift-worksheets-Jan-Aug-2026.zip">download all 30 (zip, 8 MB)</a>.</p></section>
<section><h2>Complaint resolution</h2><p>Half the households had raised a complaint in the last six months. Reporting was easy (3.90 of 5). Getting it closed was not: ownership scored 3.05, time to resolve 3.13.</p>{comps_html()}</section>
<section><h2>Where the numbers come from</h2><ol class="steps"><li>Lift figures: the contractor's call log, checked against the gate register.</li><li>Complaint figures: MyGate's ticket export, unedited.</li><li>Published by the 10th of the following month. Raw files on request.</li></ol></section>'''
page("services.html","Lifts and complaints",svc)
# documents & faq
FAQ=[("Why is the association short of money?","Costs have risen faster than the maintenance rate, which has not changed since handover, and last year's Managing Committee covered the difference from the reserves. Security alone costs ₹15 L a year more after the change of agency in November 2025. The full picture is on the money page."),
("Isn't ₹9.7 crore in reserves enough to carry on?","It would carry on for a few years and then be gone, and it is the fund for the big jobs ahead — lift replacement and overhaul, painting, waterproofing, the sewage plant and the rest. Its interest, about "+L(int_yr)+" a year before tax, is already being spent on running costs. Spending the principal too is what last year's Managing Committee did, and what the General Body objected to."),
("Why can't the MC just raise the rate now?","The bye-laws give the General Body, not the MC, the power to approve the budget and set the monthly charge. The previous Managing Committee has until 28 September to respond to the Finance Sub-Committee's findings, and owners are then entitled to 21 days' notice with the full pack attached. That makes 25 October the earliest the meeting can be held. The 1 October bill is therefore at the current rate."),
("What will the increase be?","The Managing Committee is proposing 23%, with a second option of 23% plus a one-time ₹1 lakh per flat into the reserves. Owners choose in the poll after the meeting. The shortfall page shows what 20% would mean for each flat type, and the two ways GST could apply."),
("Why does GST suddenly matter?","Maintenance above ₹7,500 a month per flat attracts 18% GST. The A- and B-type flats are between ₹6,900 and ₹7,500 today, so any increase puts them over the line; C-type flats would cross at 24%, which is why the proposal stops at 23%. Whether GST then applies to the whole amount or only the part above ₹7,500 changes the bill by about ₹1,300 a month for the larger flats. Written advice is being taken."),
("What happened to last year's money?","The Finance Sub-Committee's report, on the documents page, sets out the specific decisions it questioned: the pool repair, lift batteries, the security agency switch, paver work, a payment without an invoice, and withdrawals from the reserves. The previous Managing Committee has been asked to respond in writing to each; the auditor has been asked to explain. Both responses will be published, and the General Body will be asked to approve an independent review."),
("Is anyone being accused of anything?","No. The Finance Sub-Committee's report raises questions; the answers are being sought; a professional review will establish facts. Nobody will be named or blamed on these pages ahead of that."),
("Why not cut costs instead of raising the rate?","Both are happening. The facility and security contracts, ₹1.8 Cr a year between them, are being tendered for the first time. But tenders take months, and residents rated housekeeping and landscaping the best-run services on the estate. The MC will not cut those to avoid an increase; it will cut what is not working, starting with the lift contract."),
("What is the MC doing about lifts and pest control?","See the feedback page. In short: a public lift log from October, a root-cause report on the Wing 2 lifts, and an attempt to renegotiate the five-year contract that covers all eight lifts, for uptime targets and penalties (it cannot simply be rebid mid-term); and for pests, an audit of what the vendor actually does, source reduction, and a published schedule."),
("How do I know these numbers are right?","They come from the accountant's monthly statements, checked line by line against both banks' statements in September 2026. Where the two disagreed, the bank figure is used and the page says so. They are not audited figures; the audited accounts are annual. Anything that is an estimate says so. If you find an error, write to spcaoa@gmail.com and it will be corrected and noted."),
("How often are these pages updated?","Monthly, after the accountant's statement for the month is received, and immediately after any General Body decision. The date at the foot of each page says what the figures cover.")]
faq="".join(f'<details><summary>{q}</summary><p>{a}</p></details>' for q,a in FAQ)
docs=f'''<section><div class="eyebrow">Source documents and questions</div><h1>Documents and FAQ</h1>
<div class="cards">
<div class="card"><h3>Finance Sub-Committee report</h3><p class="small">31 August 2026. The Finance Sub-Committee's review of FY 2025–26, with annexures on expenses, income and their 10% simulation.</p><div class="card-actions"><a class="btn ghost" href="docs/SPC-Finance-SubCommittee-Report-2026-08-31.pdf">Open PDF</a></div></div>
<div class="card"><h3>General Body Meeting presentation</h3><p class="small">26 July 2026. The MC's presentation: audited FY 2025–26 summary, the corpus drawdown, cost proposals and the two funding options the meeting declined.</p><div class="card-actions"><a class="btn ghost" href="docs/SPCAOA-GBM-Deck-2026-07-26.pdf">Open PDF</a></div></div>
<div class="card"><h3>Independent Auditor's Report, FY 2025–26</h3><p class="small">20 July 2026. Two pages; unqualified opinion. The full audited statements with notes will be added with the meeting notice.</p><div class="card-actions"><a class="btn ghost" href="docs/Independent-Auditors-Report-FY25-26.pdf">Open PDF</a></div></div>
</div></section>
<section><h2>The numbers behind these pages</h2><p>The data files these pages are built from, and the ledgers received from Sobha and the Treasurer. Files with individual flats' dues or staff names are not published. Their totals are.</p>
<div class="cards">
<div class="card"><h3>Expenses, {ML(months[0])}–{ML(months[-1])}</h3><p class="small">Every head, every month, from the accountant's statements. CSV.</p><div class="card-actions"><a class="btn ghost" href="data/expenses.csv">expenses.csv</a></div></div>
<div class="card"><h3>Income, treasury and budget</h3><p class="small">Income lines, month-end bank and deposit positions, and the working budget. CSV.</p><div class="card-actions"><a class="btn ghost" href="data/income.csv">income.csv</a><a class="btn ghost" href="data/treasury.csv">treasury.csv</a><a class="btn ghost" href="data/budget.csv">budget.csv</a></div></div>
<div class="card"><h3>Vendor bills and deposits</h3><p class="small">The two largest contracts invoice by invoice, and the fixed deposits by bank. CSV.</p><div class="card-actions"><a class="btn ghost" href="data/vendor_bills.csv">vendor_bills.csv</a><a class="btn ghost" href="data/fds.csv">fds.csv</a></div></div>
<div class="card"><h3>Sobha's corpus ledger</h3><p class="small">Sobha's own statement of the owners' corpus, June 2022 to August 2026. Excel, as received.</p><div class="card-actions"><a class="btn ghost" href="docs/Sobha-corpus-fund-statement-2022-06-to-2026-08.xlsx">Excel file</a></div></div>
<div class="card"><h3>Lift service worksheets</h3><p class="small">Schindler's maintenance and repair worksheets for all eight lifts, January to August 2026. Thirty PDFs, as received; the summary is on the lifts page.</p><div class="card-actions"><a class="btn ghost" href="docs/Schindler-lift-worksheets-Jan-Aug-2026.zip">Zip, 8 MB</a></div></div>
<div class="card"><h3>Treasurer's deposit ledger</h3><p class="small">Month-by-month fixed-deposit balances by bank, November 2023 to August 2026, as received on 16 September 2026. Its July and August maturity entries do not appear in the bank statements; see the reserves page.</p><div class="card-actions"><a class="btn ghost" href="docs/FD-ledger-2023-2026-treasurer.xlsx">Excel file</a></div></div>
<div class="card"><h3>The books themselves</h3><p class="small">The association's accounts are kept in TallyPrime. A backup dated 7 September 2026 is held by the MC; audited statements are published annually, and ledger extracts can be requested by any owner.</p></div>
</div></section>
<section><h2>Questions owners are asking</h2><div class="faq">{faq}</div></section>'''
page("documents.html","Documents and FAQ",docs)
from extra import build_extra
build_extra(page, CH, runway)
# gate
pw=open(os.path.join(ROOT,"tools","passcode.txt")).read().strip().lower() if os.path.exists(os.path.join(ROOT,"tools","passcode.txt")) else ""
h=hashlib.sha256(pw.encode()).hexdigest() if pw else ""
g=open(os.path.join(ROOT,"docs","assets","gate.js")).read()
import re; g=re.sub(r'var PASS_HASH = "[^"]*";', f'var PASS_HASH = "{h}";', g); open(os.path.join(ROOT,"docs","assets","gate.js"),"w").write(g)
print("built 10 pages; gate", "ON" if h else "OFF"); print(f"spend/mo {per_month:,.0f} maint/mo {maint:,.0f} other/mo {inc_other:,.0f} reserves {reserves:,.0f} survey n={n} sat={sat}")

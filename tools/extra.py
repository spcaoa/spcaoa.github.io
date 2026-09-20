# Extra pages: simulator, contracts, actions. Called from build.py with the shared context.
import json
def build_extra(page, CH, runway):
    TYPES=[{"t":"A / E","n":58,"m":7432,"c2":32357},{"t":"A1 / E1","n":16,"m":7499,"c2":32649},{"t":"B / F","n":58,"m":6921,"c2":30133},{"t":"B1 / F1","n":16,"m":6988,"c2":30424},{"t":"C","n":72,"m":6058,"c2":26375},{"t":"D1","n":66,"m":5723,"c2":24917},{"t":"D","n":8,"m":5381,"c2":23428}]
    sim = """<section class="simhead"><div class="eyebrow">Compare the options</div><h1>What it means for your flat</h1>
<p class="lead">Pick an option and see what your bill becomes and whether the association balances. Move the slider or change an assumption and everything updates. If nothing changes, <b id="gapInline"></b> comes out of the reserves this year and next year is still short.</p></section>
<div class="simgrid">
<aside class="simpanel" id="simpanel" aria-label="Options and assumptions">
  <div class="live" id="live" aria-live="polite">
    <div class="live-h"><span>Option</span><span>FY 2027&#8211;28</span></div>
    <div id="optList"></div>
  </div>
  <div class="ctls">
    <div class="ctl"><div class="ctl-h">MC option A: base increase <b id="pctLabel">23</b>%</div>
      <input type="range" id="pct" min="0" max="45" step="1" value="23" aria-label="MC option base increase">
      <div class="ctl-note">Moving this selects option A. Above 23%, C-type flats cross the GST line.</div></div>
    <div class="ctl"><div class="ctl-h">GST above ₹7,500</div>
      <label><input type="radio" name="gst" value="whole" checked> On the whole amount</label>
      <label><input type="radio" name="gst" value="excess"> Only on the part above ₹7,500</label>
      <label><input type="checkbox" id="itc"> Association reclaims GST on its own bills (adviser's opinion awaited)</label></div>
    <div class="ctl"><div class="ctl-h">When the new rate starts</div>
      <label><input type="radio" name="eff" value="oct" checked> 1 Oct, difference billed in Nov</label>
      <label><input type="radio" name="eff" value="jan"> 1 Jan</label>
</div>
    <div class="ctl"><div class="ctl-h">Costs</div>
      <label><input type="checkbox" id="esc" checked> Maintenance rises 5% a year from Apr 2028</label>
      <label><input type="checkbox" id="cesc" checked> Costs rise about 5% a year too</label>
      <div class="ctl-sub">Savings on staff and contracts, from Jan 2027</div>
      <select id="sav"><option value="0">None</option><option value="15">₹15 L: only what is already cut</option><option value="20" selected>₹20 L: ₹15 L cut + ₹5 L hoped for</option><option value="25">₹25 L a year</option><option value="30">₹30 L a year</option></select>
      <details class="ctl-more"><summary>More assumptions</summary>
      <div class="ctl-sub">Spending base</div>
      <select id="base"><option value="mc" selected>₹26 L a month + lift contract and tax</option><option value="tr">₹33 L a month flat (Treasurer)</option></select>
      <div class="ctl-sub">Tax on interest</div>
      <select id="tax"><option value="4">₹4 L a quarter (as paid in September)</option><option value="6.3" selected>₹6.3 L a quarter (39% on all interest)</option></select>
      <label><input type="checkbox" id="rep2" checked> July's Option 2 repeated next year</label></details></div>
    <input type="hidden" id="preset" value="mc">
  </div>
</aside>
<div class="simresults">
<section class="cardsec"><div class="opts" id="optCards"></div>
<p class="small">"This year" runs from the real end-of-August cash position through March 2027. FY 2027&#8211;28 is April 2027 to March 2028, the first full year at a new rate on the same basis as the shortfall page: this year's run-rate including ₹40 L of one-time items, 98% collection, all interest counted, tax at 39%.</p></section>
<section><h2>Your bill</h2><div class="tablewrap"><table><thead><tr><th>Flat type</th><th class="num">Flats</th><th class="num">Today / month</th><th class="num">New base</th><th class="num">GST</th><th class="num">Total / month</th><th class="num">Extra per year</th></tr></thead><tbody id="flatRows"></tbody></table></div><p class="small" id="flatNote"></p></section>
<section><h2>Cash in the account</h2><div class="chartbox"><div class="ch" style="height:280px"><canvas id="cSim"></canvas></div></div><p class="small">Starts from ₹14.4 L in the bank at the end of August 2026 (₹5.9 L after the cheques already written, which the September outflow includes). Below zero, the reserves are used.</p></section>
<section><h2>Side by side</h2><div class="tablewrap"><table><thead><tr><th>Option</th><th class="num">A-type flat / month</th><th class="num">Extra per year</th><th class="num">Raised this year</th><th class="num">From reserves this year</th><th class="num">FY 2027&#8211;28</th><th class="num">Reserves used, 2028&#8211;38</th><th>Verdict</th></tr></thead><tbody id="cmpRows"></tbody></table></div></section>
<section><h2>How this is worked out</h2><ol class="steps"><li>Spending is this year's actual rate: ₹26 L a month, the ₹8 L lift contract in June and December, tax each quarter, and about ₹40 L a year of one-off repairs. Savings come off from January 2027.</li><li>Income is maintenance (98% of what is billed, which is what has been collected this year), interest on the deposits, and rentals and fees. Tax on interest is 39%, the rate that applies to the association.</li><li>GST collected goes to the government, not to the association. If the association can claim back the GST on its own bills, that helps; the CA's opinion is awaited, so it is off unless you switch it on.</li><li>Option C is 39% with nothing one-time: it balances the account and rebuilds the reserves from maintenance alone. It is close to what the July meeting was asked for and turned down. Option B reaches the same place for 23% plus a one-time payment.</li><li>Option B: the ₹1 lakh per flat goes into deposits and is not spent. Only its interest, about ₹12 L a year after tax, is counted, from mid-2027.</li><li><strong>The last column.</strong> What each option would take from the reserves between April 2028 and 2038, if maintenance rises 5% a year as proposed and costs rise about 5% too. An option that starts near balance stays near it; one that starts well short falls further behind each year, because 5% of a bigger cost is more than 5% of a smaller maintenance bill.</li><li>The Finance Sub-Committee's 10.1% is applied to the bill including GST, as in their report. The two options the July meeting turned down (a 39% increase; an annual contribution) are not shown.</li></ol></section>
</div>
</div>
<button class="livebar" id="livebar" type="button" hidden aria-label="Back to options"></button>"""
    simjs = CH + "const TYPES=" + json.dumps(TYPES) + ";" + r"""
const START=14.4, MONTHS=[];(()=>{let y=2026,m=9;for(let i=0;i<19;i++){MONTHS.push({y,m,label:new Date(y,m-1,1).toLocaleString("en-IN",{month:"short"})+" "+String(y).slice(2)});m++;if(m>12){m=1;y++;}}})();
const P={asis:{pct:0,inside:false,contrib:false},sc:{pct:10.1,inside:true,contrib:false},mc:{pct:null,inside:false,contrib:false},mcb:{pct:23,inside:false,contrib:false,corpus:true},opt1:{pct:39,inside:false,contrib:false},opt2:{pct:0,inside:false,contrib:true}};
const CORPUS_PER_FLAT=1, CORPUS_RATE=0.07, TAXR=0.39;
function flatCalc(t,pct,inside,gst){ let base,total;
  if(inside){ total=t.m*(1+pct/100); base= total>7500 ? (gst==="whole"? total/1.18 : total-((total-7500)*0.18/1.18)) : total; }
  else { base=t.m*(1+pct/100); const g= base>7500 ? (gst==="whole"? base*0.18 : (base-7500)*0.18) : 0; total=base+g; }
  return {base,gstAmt:total-base,total}; }
function run(o){
  const rows=TYPES.map(t=>({t,...flatCalc(t,o.pct,o.inside,o.gst)}));
  const monthlyBaseNew=rows.reduce((a,r)=>a+r.base*r.t.n,0), monthlyBaseOld=TYPES.reduce((a,t)=>a+t.m*t.n,0);
  const taxableShare=rows.reduce((a,r)=>a+(r.gstAmt>0?(o.gst==="whole"?r.base:Math.max(0,r.base-7500))*r.t.n:0),0)/monthlyBaseNew;
  const itcYear=(o.itc && rows.some(r=>r.gstAmt>0)) ? 35*taxableShare : 0;
  const contribNet=o.contrib? TYPES.reduce((a,t)=>a+t.c2/1.18*t.n,0)/1e5 : 0;
  const corpusRaised=o.corpus? 0.98*CORPUS_PER_FLAT*TYPES.reduce((a,t)=>a+t.n,0) : 0;   // ₹ L, collected Nov 2026–Apr 2027, placed in deposits, not spent
  const corpusIntNet=corpusRaised*CORPUS_RATE*(1-TAXR);   // ₹ L a year, after tax, available from May 2027
  let bal=START, series=[], minB=1e9, minM="", b27=0,b28=0;
  MONTHS.forEach((mo)=>{
    const newRateOn = o.eff==="oct" ? (mo.y>2026 || mo.m>=10) : (mo.y>=2027);
    let inn=1.8+0.8+2.1+0.5;
    if([10,1,4,7].includes(mo.m)){ const q=(newRateOn?monthlyBaseNew:monthlyBaseOld)*3/1e5; inn+=0.92*q; if(newRateOn) inn+=itcYear/4; }
    if(o.eff==="oct" && mo.y===2026 && mo.m===11) inn+=0.92*(monthlyBaseNew-monthlyBaseOld)*3/1e5;
    if(o.contrib && mo.m===11 && (mo.y===2026 || (mo.y===2027 && o.rep2))) inn+=0.92*contribNet;
    if(o.corpus && (mo.y>2027 || (mo.y===2027 && mo.m>=5))) inn+=corpusIntNet/12;
    let out= o.base==="tr" ? 33 : 26;
    if(o.base==="mc"){ if([9,12,3,6].includes(mo.m)) out+=o.taxQ; if([12,6].includes(mo.m)) out+=8; }
    if(mo.y>=2027) out-=o.sav/12;
    bal=bal+inn-out; series.push(bal); if(bal<minB){minB=bal;minM=mo.label;}
    if(mo.y===2027&&mo.m===3) b27=bal; if(mo.y===2028&&mo.m===3) b28=bal; });
  const collections=monthlyBaseNew*12*0.98/1e5 + (o.contrib&&o.rep2?0.98*contribNet:0);
  const fixedInc=25.6+34.3+6+9.6+itcYear-(o.taxQ*4)+(o.corpus?corpusIntNet:0);
  const income=collections+fixedInc;
  const spend=(o.base==="tr"?33*12+40:320+40)-o.sav;   // ₹3.20 Cr running (this year's rate, lift included) + ₹40 L one-time
  let coll=collections, cost=spend, drawn=0;
  for(let y=0;y<10;y++){ drawn+=Math.max(0,cost-(coll+fixedInc)); if(o.esc) coll*=1.05; if(o.cesc) cost*=1.05; }
  return {rows,monthlyBaseNew,itcYear,contribNet,corpusRaised,corpusIntNet,collections,fixedInc,spend,drawn10:drawn,series,minB,minM,b27,b28,surplus:income-spend,taxableShare}; }
function read(){ const preset=document.getElementById("preset").value; const p=P[preset]; const pct=p.pct==null?+document.getElementById("pct").value:p.pct;
  return {preset,pct,inside:p.inside,contrib:p.contrib,corpus:!!p.corpus,gst:document.querySelector('input[name=gst]:checked').value,itc:document.getElementById("itc").checked,eff:document.querySelector('input[name=eff]:checked').value,sav:+document.getElementById("sav").value,esc:document.getElementById("esc").checked,cesc:document.getElementById("cesc").checked,base:document.getElementById("base").value,taxQ:+document.getElementById("tax").value,rep2:document.getElementById("rep2").checked}; }
const inr=n=>"₹"+Math.round(n).toLocaleString("en-IN"); const L=n=>(n<0?"−":"")+"₹"+Math.abs(n).toFixed(1)+" L";
let chart;
const KEYS=["asis","sc","mc","mcb","opt1"];
const NM={asis:"Carry on as we are: +0%",sc:"Finance Sub-Committee: +10.1%",mc:"MC option A:",mcb:"MC option B: +23% and ₹1 L to the corpus",opt1:"MC option C: +39%, nothing one-time",opt2:"GBM Option 2: annual contribution"};
function optOf(o,k){ const p=P[k]; return {...o,preset:k,pct:p.pct==null?+document.getElementById("pct").value:p.pct,inside:p.inside,contrib:p.contrib,corpus:!!p.corpus}; }
function nameOf(k,oo){ return k==="mc"?NM[k]+" +"+oo.pct+"%":NM[k]; }
const SHORT={asis:"Carry on",sc:"Sub-Committee 10.1%",mc:"MC option A",mcb:"MC option B: 23% + ₹1 L corpus",opt1:"MC option C: 39%",opt2:"Option 2 contribution"};
function shortOf(k,oo){ return k==="mc"?SHORT[k]+" +"+oo.pct+"%":SHORT[k]; }
function verdict(rr){ if(rr.surplus<0) return {c:"no",t:"Not enough. Still short next year."}; if(rr.surplus<15) return {c:"mid",t:"Just balances next year. No buffer."}; return {c:"ok",t:"Balances next year, with a buffer."}; }
const signL=n=>(n>0?"+":"")+L(n);
let prevText={};
function flashChanged(root){
  root.querySelectorAll("[data-f]").forEach(el=>{ const k=el.dataset.f, t=el.textContent;
    if(prevText[k]!==undefined && prevText[k]!==t){ el.classList.remove("flash"); void el.offsetWidth; el.classList.add("flash"); }
    prevText[k]=t; });
}
function render(){
  const o=read(); document.getElementById("pctLabel").textContent=document.getElementById("pct").value;
  const LCOL={asis:css("--c7"),sc:css("--c3"),mc:css("--accent"),mcb:css("--c6"),opt1:css("--c2"),opt2:css("--c5")};
  // run each option once
  const R={}; KEYS.forEach(k=>{ const oo=optOf(o,k), rr=run(oo); R[k]={oo,rr,a:rr.rows[0],v:verdict(rr),name:nameOf(k,oo)}; });
  const asis=R.asis.rr, gapNow=Math.max(0,-asis.b27);
  KEYS.forEach(k=>{ const x=R[k]; x.raised=Math.max(0,x.rr.b27-asis.b27); x.fromRes=Math.max(0,-x.rr.b27); x.extra=(x.a.total-x.a.t.m)*12+(x.oo.contrib?x.a.t.c2:0); });
  const S=R[o.preset];
  const tile=(c,k,v,d)=>'<div class="tile '+c+'"><div class="k">'+k+'</div><div class="v">'+v+'</div><div class="d">'+d+'</div></div>';
  document.getElementById("gapInline").textContent=L(gapNow);

  // --- the live panel: every option, the selected one expanded
  const list=document.getElementById("optList");
  list.innerHTML=KEYS.map(k=>{ const x=R[k], sel=k===o.preset;
    const maxAbs=Math.max(20,...KEYS.map(q=>Math.abs(R[q].rr.surplus))), w=Math.min(50,Math.abs(x.rr.surplus)/maxAbs*50);
    const row='<button type="button" class="orow'+(sel?' sel':'')+'" data-k="'+k+'" aria-pressed="'+sel+'"><span class="nm"><i class="dot" style="background:'+LCOL[k]+'"></i>'+shortOf(k,x.oo)+'</span><span class="track" aria-hidden="true"><i class="'+(x.rr.surplus<0?"neg":"pos")+'" style="width:'+w+'%"></i></span><span class="ny '+(x.rr.surplus<0?"neg":"pos")+'" data-f="ny-'+k+'">'+signL(x.rr.surplus)+'</span></button>';
    if(!sel) return row;
    return row+'<div class="odetail"><div class="big" data-f="bill">'+inr(x.a.total)+'<span> /month, A-type flat</span></div>'
      +'<div class="kv"><span>Extra per year</span><b data-f="extra">'+(x.extra>0?inr(x.extra):"none")+'</b></div>'
      +'<div class="kv"><span>From reserves this year</span><b class="'+(x.fromRes>0?"neg":"pos")+'" data-f="res">'+L(x.fromRes)+'</b></div>'
      +'<div class="verdict '+x.v.c+'" data-f="verdict">'+x.v.t+'</div></div>'; }).join("");
  list.querySelectorAll(".orow").forEach(b=>b.onclick=()=>select(b.dataset.k));
  flashChanged(list);

  // --- cards
  document.getElementById("optCards").innerHTML=KEYS.map(k=>{ const x=R[k], cov=gapNow?Math.min(1,x.raised/gapNow):0;
    return '<div class="opt'+(k===o.preset?' sel':'')+'" data-k="'+k+'" role="button" tabindex="0"><h3>'+x.name+'</h3><div class="bill">'+inr(x.a.total)+'<span class="small"> /month, A-type</span></div><div class="sub">'+(x.extra>0?inr(x.extra)+" more per year":"no change")+(x.oo.contrib?" (annual contribution)":"")+'</div><div class="row"><span>Raises this year</span><b>'+L(x.raised)+'</b></div><div class="gapbar"><span style="width:'+(cov*100)+'%"></span></div><div class="row" style="border:0;padding-top:0"><span>From reserves</span><b class="'+(x.fromRes>0?"neg":"pos")+'">'+L(x.fromRes)+'</b></div><div class="row"><span>FY 2027&#8211;28</span><b class="'+(x.rr.surplus<0?"neg":"pos")+'">'+L(x.rr.surplus)+'</b></div><div class="verdict '+x.v.c+'">'+x.v.t+'</div></div>'; }).join("");
  document.querySelectorAll(".opt").forEach(el=>{ el.onclick=()=>select(el.dataset.k); el.onkeydown=e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();select(el.dataset.k);}}; });

  // --- bill table
  document.getElementById("flatRows").innerHTML=S.rr.rows.map(x=>'<tr><td>'+x.t.t+'</td><td class="num">'+x.t.n+'</td><td class="num">'+inr(x.t.m)+'</td><td class="num">'+inr(x.base)+'</td><td class="num">'+(x.gstAmt?inr(x.gstAmt):"—")+'</td><td class="num"><strong>'+inr(x.total)+'</strong></td><td class="num">'+inr((x.total-x.t.m)*12+(o.contrib?x.t.c2:0))+'</td></tr>').join("");
  document.getElementById("flatNote").textContent=o.contrib?"Option 2: the monthly bill does not change. The extra per year is the annual contribution, including 18% GST.":(o.inside?"Sub-Committee method: the increase is on the whole bill and GST is taken out of it, so the association nets less than the bill.":"GST applies once the base crosses ₹7,500 a month.");

  // --- chart: build once, then update in place (smooth while dragging)
  const ds=KEYS.map(k=>{ const x=R[k], sel=k===o.preset, col=LCOL[k];
    return {label:x.name,data:x.rr.series.map(v=>+v.toFixed(1)),borderColor:col,backgroundColor:sel?col+"1f":"transparent",borderWidth:sel?2.5:1.5,borderDash:sel?[]:[5,4],tension:.3,pointRadius:sel?x.rr.series.map(v=>v<0?2:0):0,pointBackgroundColor:css("--crit"),fill:sel}; });
  if(!chart){ chart=new Chart(document.getElementById("cSim"),{type:"line",data:{labels:MONTHS.map(m=>m.label),datasets:ds},options:{responsive:true,maintainAspectRatio:false,animation:false,interaction:{mode:"index",intersect:false},scales:{y:{ticks:{callback:v=>v+" L"},grid:{color:css("--line-soft")}},x:{grid:{display:false}}},plugins:{legend:{position:"bottom",labels:{usePointStyle:true,pointStyle:"line",boxWidth:26,font:{size:11.5}}}}}}); }
  else { chart.data.datasets.forEach((d,i)=>Object.assign(d,ds[i])); chart.update("none"); }

  // --- side by side
  document.getElementById("cmpRows").innerHTML=KEYS.map(k=>{ const x=R[k];
    return '<tr'+(k===o.preset?' style="background:var(--accent-soft)"':'')+'><td><strong>'+x.name+'</strong></td><td class="num">'+inr(x.a.total)+'</td><td class="num">'+inr(x.extra)+'</td><td class="num">'+L(x.raised)+'</td><td class="num'+(x.fromRes>0?" neg":" pos")+'">'+L(x.fromRes)+'</td><td class="num'+(x.rr.surplus<0?" neg":" pos")+'">'+L(x.rr.surplus)+'</td><td class="num'+(x.rr.drawn10>50?" neg":"")+'">'+(x.rr.drawn10<1?"none":L(x.rr.drawn10))+'</td><td><span class="pill '+(x.v.c==="no"?"crit":x.v.c==="mid"?"warn":"ok")+'">'+x.v.t+'</span></td></tr>'; }).join("");

  // --- phone result bar
  const bar=document.getElementById("livebar");
  bar.className="livebar v-"+S.v.c;
  bar.innerHTML='<span class="lb-name">'+S.name+'</span><span class="lb-fig"><b data-f="lb-bill">'+inr(S.a.total)+'</b><small>/month</small></span><span class="lb-fig"><b class="'+(S.rr.surplus<0?"neg":"pos")+'" data-f="lb-ny">'+signL(S.rr.surplus)+'</b><small>next year</small></span>';
  flashChanged(bar);
  if(window.spcTables) window.spcTables();
}
function select(k){ document.getElementById("preset").value=k; schedule(); }
let raf=0; function schedule(){ if(raf) return; raf=requestAnimationFrame(()=>{ raf=0; render(); }); }
document.getElementById("pct").addEventListener("input",()=>{ document.getElementById("preset").value="mc"; schedule(); });
document.querySelectorAll(".ctls input:not(#pct),.ctls select").forEach(el=>el.addEventListener("input",schedule));
// phone: show the result bar once the panel's result has scrolled out of view
(function(){ const bar=document.getElementById("livebar"), live=document.getElementById("live"), mq=window.matchMedia("(max-width:1080px)");
  let liveVisible=true;
  function sync(){ const show=mq.matches && !liveVisible; bar.hidden=!show; document.body.classList.toggle("has-livebar",show); }
  if("IntersectionObserver" in window){ new IntersectionObserver(es=>{ liveVisible=es[0].isIntersecting; sync(); },{rootMargin:"-58px 0px 0px 0px"}).observe(live); }
  mq.addEventListener?mq.addEventListener("change",sync):mq.addListener(sync);
  bar.addEventListener("click",()=>{ document.getElementById("simpanel").scrollIntoView({behavior:"smooth",block:"start"}); });
})();
render();"""
    page("simulator.html","Try the options",sim,simjs)

    con = """<section><div class="eyebrow">What the association has signed, and what it has not</div><h1>Contracts and commitments</h1>
<p class="lead">Two contracts are two-thirds of all spending. Neither was tendered. One was never signed. The other was never signed by the association. Here is each commitment as it stands.</p>
<div class="tablewrap"><table><thead><tr><th>Service</th><th>Provider</th><th class="num">Cost per year</th><th>Contract position</th><th>What the MC is doing</th></tr></thead><tbody>
<tr><td>Facility management: housekeeping, gardeners, technicians, estate manager</td><td>Sobha Ltd (facility division)</td><td class="num">₹98 L incl. GST</td><td>No signed contract. A draft MOU from January 2026 exists, unsigned, with no price in it. Sobha bills salaries at cost plus 13% PF, plus a 15% fee, plus 18% GST: about ₹28,500 per staff member per month for 27–31 staff.</td><td>An interim agreement for October–March, with agreed rates and staff numbers, is being completed on this draft; then a tender with residents' ratings as the benchmark. Sobha bids like anyone else.</td></tr>
<tr><td>Security: 22 posts (2 supervisors, 18 guards, lifeguard, lady guard)</td><td>VEX India Securitas</td><td class="num">₹72 L + GST (≈₹85 L)</td><td>Agreement dated 16 Oct 2025, term to Nov 2027, signed by the agency only; the association's signature block is blank. Bills by the day worked. Deployment fell to 81% of contract in July and 76% in August.</td><td>Written position on the reduced deployment; the agreement's own attendance penalties applied; retender with a specification written from the survey (language, turnover, block posts, basement rounds).</td></tr>
<tr><td>Lifts and UPS maintenance</td><td>Lift contractor</td><td class="num">₹16 L</td><td>Half-yearly contract, ₹8 L paid in June and December. Lifts were the lowest-rated service in the survey. ₹6.75 L was spent on batteries last year while some were under warranty.</td><td>Monthly uptime log from October; root-cause report on the Wing 2 lifts; renegotiation sought on the existing five-year contract, which covers all eight lifts, for uptime targets and penalties — no promise it can be changed mid-term.</td></tr>
<tr><td>Sewage and water treatment operation</td><td>STP/WTP contractor</td><td class="num">₹9 L</td><td>Cost has doubled in two years (₹4.7 L to ₹9.2 L). Residents report odour near Wing 1 and in basements.</td><td>Odour audit; retender with odour standards and a chemical schedule.</td></tr>
<tr><td>Electricity</td><td>BESCOM</td><td class="num">₹60 L</td><td>Utility; no contract to negotiate. Corridor and staircase timers reported faulty.</td><td>Timer re-commissioning; energy audit; solar feasibility to come back to the General Body.</td></tr>
<tr><td>Water</td><td>BWSSB</td><td class="num">₹22 L</td><td>New Cauvery connection; a permanent line item from this year.</td><td>Meter and leak audit; maximise treated water for gardens and flushing.</td></tr>
<tr><td>Waste collection, pest control, consumables</td><td>Various</td><td class="num">≈₹11 L</td><td>Monthly arrangements without rate contracts. Pest control was the second-lowest-rated service.</td><td>Annual rate contracts with three quotes; pest vendor's schedule audited; drain-line treatment added.</td></tr>
</tbody></table></div></section>
<section class="split"><div class="body"><h2>Two things owners should know about the Sobha arrangement</h2>
<div class="callout"><strong>The deposit.</strong> When Sobha returned the corpus in 2023–24 it kept ₹91 L. Sobha treats this as its security for the facility service, and since June 2026 it has been adjusting its unpaid monthly bills against it and re-crediting them when the association pays. Its ledger shows about ₹75 L; the association's books show ₹90 L. The bye-laws do not permit association funds to sit with a developer; how and when the balance comes back is part of the interim agreement now being negotiated.</div>
<div class="callout"><strong>Purchases.</strong> Under the working arrangement, Sobha's estate manager buys consumables and spares on the association's account. That is where last year's monthly bulb purchases and above-market prices, noted by the Sub-Committee, came from. The purchasing and accounting policy is being reviewed, and a revised policy will be put to the Special General Body Meeting for approval.</div></div>
<aside class="side"><h3>The corpus Sobha holds</h3><dl>
<dt>Kept back in 2023&#8211;24</dt><dd>₹91 L</dd>
<dt>Association&#8217;s books</dt><dd>₹90 L</dd>
<dt>Sobha&#8217;s own ledger</dt><dd class="up">₹75 L</dd>
<dt>Interest paid to us</dt><dd>≈ ₹50,000 a month</dd>
</dl><p class="note">The ₹15 L difference is unpaid monthly bills Sobha has set off against the balance. Recovering it is on the actions page.</p></aside></section>
<section class="split"><div class="body"><h2>A tax point that affects the numbers</h2><p>The association is registered for GST. Security services bought from a proprietorship by a registered body are taxed under "reverse charge": the association must pay the 18% itself, and the agency should not charge it. The agency has been charging it, about ₹1 L a month, and the association has been paying it. The association's CA is computing what the association owes directly since November 2025 and what it can recover or set off. The net cost is small; the interest and the paperwork are not. It is mentioned here because it will appear in the accounts and owners should not be surprised by it.</p></div>
<aside class="side"><h3>The security GST</h3><dl>
<dt>Charged by the agency</dt><dd class="up">≈ ₹1 L a month</dd>
<dt>Owed by us directly</dt><dd>the same 18%</dd>
<dt>Since</dt><dd>Nov 2025</dd>
</dl><p class="note">Under reverse charge the association pays the tax to the government itself and the agency should not add it to the bill. The CA is working out what can be recovered or set off.</p></aside></section>
<section class="split"><div class="body"><h2>What will change</h2><ol class="steps"><li><strong>Big contracts go to owners.</strong> Any contract worth more than ₹25 L a year is approved by the General Body, however small the monthly bill looks.</li><li><strong>Three quotes, and the vendor checked.</strong> For anything over ₹25,000, three quotes; the vendor's identity and bank account verified before the first payment; no payments to personal accounts.</li><li><strong>Nothing renews by default.</strong> A list of every contract with its end date, and tendering starts 90 days before, so no contract rolls over unnoticed again.</li></ol></div>
<aside class="side"><h3>The two big contracts</h3><dl>
<dt>Facility management</dt><dd>₹98 L a year</dd>
<dt>Security</dt><dd>₹85 L a year</dd>
<dt>Together</dt><dd class="key">₹1.8 Cr</dd>
<dt>Saved so far</dt><dd class="key">₹15 L a year</dd>
</dl><p class="note">Neither has ever been put out to tender. Both are being tendered now, with the service standards owners rated in the survey.</p></aside></section>"""
    page("contracts.html","Contracts and commitments",con)

    ACT=[("Money and the meeting",[("Special General Body Meeting on Sunday 25 October; notice to every owner by Friday 25 September; online poll for all owners 25 October to 1 November","MC","Sep–Nov"),("Budget for 2026–27 from the accountant's statements and the bank figures, sent with the notice","Treasurer","by 25 Sep"),("Until owners decide, the shortfall is met from the reserves; the amount used is reported on the reserves page each month","Treasurer","monthly"),("Full list of HDFC deposits from the bank, and ICICI maturity dates","Treasurer","Sep"),("How the ₹11.76 Cr at handover became today's reserves, from the audited accounts; sent with the notice","Treasurer, auditor","by 25 Sep")]),
    ("Accountability",[("Finance Sub-Committee's report sent to the previous Managing Committee for written answers on each point; answers published as received","President","by 28 Sep"),("Written questions to the auditor on the withdrawals from the reserves, the payment without an invoice, payments to personal accounts and the security GST","MC","in progress"),("Owners asked to approve an independent review of the flagged transactions, with a defined scope and budget","MC","at the meeting"),("Nobody named or blamed ahead of findings; process and dates communicated instead","MC","always")]),
    ("Contracts",[("Interim agreement with Sobha for October–March, with agreed rates and staff numbers","Secretary","Sep"),("Facility-management tender with service standards from the survey","Secretary, engineering sub-committee","before the meeting"),("Security: written position on deployment, penalties applied, retender specification","Secretary","Sep–Oct"),("Root-cause report on the Wing 2 lifts; monthly lift log published from October; renegotiation of the existing five-year lift contract attempted","Engineering sub-committee","Oct"),("STP: odour audit, retender with standards","Engineering sub-committee","Oct")]),
    ("Services residents asked about",[("Complaint standard in MyGate: acknowledged in 4 working hours, updated every 48 hours, closed on your confirmation; monthly numbers published","Secretary","Oct"),("Pest control: vendor's schedule audited, mosquito source reduction, published fogging calendar, drain-line treatment","Secretary","Sep–Oct"),("Play area: hardened sand and exposed pipes inspected and fixed","Engineering sub-committee","Sep"),("Corridor and staircase light timers re-commissioned","Secretary","Sep"),("Tennis coaching slots; clubhouse booking through MyGate; gym and AC servicing","Secretary","Oct"),("Arrears: notices to the 30 flats with dues; owners more than 60 days in arrears at year-end cannot vote in or stand for the next election (bye-law 7)","Treasurer","Sep")]),
    ("Rules for the future",[("Rules for spending, put to owners: contracts over ₹25 L a year need owners' approval; three quotes above ₹25,000; vendors checked before payment; monthly reporting; accounts published by 31 May","Treasurer","at the meeting"),("Rules for the reserves, put to owners: deposits are not broken without owners' approval; three signatories or five MC members to move deposit money; a monthly deposit statement from the banks","Treasurer","at the meeting"),("Monthly transparency pack on MyGate and on these pages by the 10th","Secretary","from Oct"),("Sinking fund from next year for the big jobs: lift replacement and overhaul, painting, waterproofing, plant renewals","MC","next AGM")])]
    arows="".join('<section><h2>'+g+'</h2><div class="tablewrap"><table><thead><tr><th>Action</th><th>Who</th><th>When</th></tr></thead><tbody>'+"".join('<tr><td>'+a+'</td><td>'+w+'</td><td>'+d+'</td></tr>' for a,w,d in items)+'</tbody></table></div></section>' for g,items in ACT)
    act='<section><div class="eyebrow">The MC\'s commitments, in public</div><h1>What the MC is doing</h1><p class="lead">Everything the Managing Committee has committed to, with a name and a date. Updated each month. Anything that slips stays on the list with the reason.</p></section>'+arows+'<section><p class="small">"Engineering sub-committee" is the volunteer engineering sub-committee of owners. Personal names are not used on these pages.</p></section>'
    page("actions.html","What the MC is doing",act)

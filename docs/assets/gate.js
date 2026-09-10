// Residents' curtain. Not a lock: anyone with the passcode (or who reads this file's hash) can enter.
// To switch off, set PASS_HASH to "". To change, run in a browser console:
//   crypto.subtle.digest("SHA-256", new TextEncoder().encode("newpass")).then(b=>console.log([...new Uint8Array(b)].map(x=>x.toString(16).padStart(2,"0")).join("")))
(function(){
  var PASS_HASH = "c50ebd1de3dd67998491171b4eb1974fe5ae017cfc58aabc04b65ece4c55b7e6";
  if(!PASS_HASH) return;
  try { if (sessionStorage.getItem("spc-gate")===PASS_HASH || localStorage.getItem("spc-gate")===PASS_HASH) return; } catch(e){}
  document.documentElement.classList.add("gated");
  function sha(s){ return crypto.subtle.digest("SHA-256", new TextEncoder().encode(s)).then(function(b){ return Array.from(new Uint8Array(b)).map(function(x){return x.toString(16).padStart(2,"0");}).join(""); }); }
  window.addEventListener("DOMContentLoaded", function(){
    var g=document.createElement("div"); g.id="gate";
    g.innerHTML='<form id="gateForm"><div class="gcard"><div class="gbrand">Sobha Palm Court</div><h1>Residents’ finance pages</h1><p>Enter the passcode shared with owners and residents on MyGate.</p><input type="password" id="gatePass" autocomplete="off" autofocus placeholder="Passcode"><button type="submit">Enter</button><p class="gerr" id="gateErr" hidden>That passcode is not right.</p><p class="gsmall">Questions: write to spcaoa@gmail.com</p></div></form>';
    document.body.appendChild(g);
    document.getElementById("gateForm").addEventListener("submit", function(e){ e.preventDefault(); sha(document.getElementById("gatePass").value.trim().toLowerCase()).then(function(h){ if(h===PASS_HASH){ try{ localStorage.setItem("spc-gate",h); }catch(_){} g.remove(); document.documentElement.classList.remove("gated"); } else { document.getElementById("gateErr").hidden=false; } }); });
  });
})();

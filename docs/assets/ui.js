// Mobile navigation and table stacking. No dependencies.
(function(){
  function nav(){
    var b=document.getElementById("menubtn"), t=document.getElementById("tabs");
    if(!b||!t) return;
    function close(){ t.classList.remove("open"); b.setAttribute("aria-expanded","false"); }
    b.addEventListener("click",function(e){
      e.stopPropagation();
      var open=t.classList.toggle("open");
      b.setAttribute("aria-expanded",open?"true":"false");
    });
    document.addEventListener("keydown",function(e){ if(e.key==="Escape") close(); });
    document.addEventListener("click",function(e){ if(!t.contains(e.target)&&e.target!==b) close(); });
  }
  // Label each cell with its column heading, then stack any table too wide for the screen.
  function tables(){
    var narrow = window.matchMedia("(max-width:720px)").matches;
    document.querySelectorAll("table").forEach(function(tb){
      var hs=Array.prototype.map.call(tb.querySelectorAll("thead th"),function(th){return th.textContent.trim();});
      if(!hs.length) return;
      tb.querySelectorAll("tbody tr").forEach(function(tr){
        Array.prototype.forEach.call(tr.children,function(td,i){ if(hs[i]) td.setAttribute("data-label",hs[i]); });
      });
      tb.classList.remove("stack");
      var wrap=tb.parentElement;
      // phones: any table with more than four columns; any screen: a table wider than its box
      if((narrow && hs.length>4) || tb.scrollWidth > wrap.clientWidth + 2) tb.classList.add("stack");
    });
  }
  var t;
  window.addEventListener("resize",function(){ clearTimeout(t); t=setTimeout(tables,150); });
  window.spcTables=tables;
  if(document.readyState==="loading") document.addEventListener("DOMContentLoaded",function(){nav();tables();});
  else { nav(); tables(); }
})();

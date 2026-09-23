
let currentReport = null;
const $ = id => document.getElementById(id);

function toast(msg){
  const t=$("toast"); t.textContent=msg; t.classList.add("show");
  setTimeout(()=>t.classList.remove("show"),2600);
}
function fmt(n){return Number(n||0).toFixed(2)}
function nav(section){
  document.querySelectorAll(".nav-item").forEach(b=>b.classList.toggle("active",b.dataset.section===section));
  document.querySelectorAll(".section").forEach(s=>s.classList.toggle("active",s.id===section));
  $("page-title").textContent = ({dashboard:"Control Center",operations:"Route Operations",agents:"Agent Fleet",packages:"Package Flow",reports:"Reports"})[section];
}
document.querySelectorAll(".nav-item").forEach(b=>b.addEventListener("click",()=>nav(b.dataset.section)));

async function loadCases(){
  const res=await fetch("/api/cases"); const data=await res.json();
  const sel=$("caseSelect"); sel.innerHTML="";
  data.cases.forEach(c=>{const o=document.createElement("option");o.value=c;o.textContent=c;sel.appendChild(o)});
  await loadCaseInfo();
}
async function loadCaseInfo(){
  const name=$("caseSelect").value;
  const res=await fetch("/api/case/"+encodeURIComponent(name)); const d=await res.json();
  if(d.error){toast(d.error);return}
  $("statPackages").textContent=d.packages.length;
  $("statAgents").textContent=d.agents.length;
  $("statDelivered").textContent="—"; $("deliveryRate").textContent="Waiting to run"; $("statDistance").textContent="—";
  $("eventFeed").innerHTML='<div class="empty">Ready. Press Run Simulation.</div>';
  $("agentMini").innerHTML='<div class="empty">No results yet.</div>';
  $("routeBoard").innerHTML='<div class="empty">Run the simulation to populate route events.</div>';
  $("agentsTable").innerHTML=""; $("packagesTable").innerHTML="";
}
$("caseSelect").addEventListener("change",loadCaseInfo);

async function upload(){
  const f=$("fileInput").files[0]; if(!f)return;
  const fd=new FormData();fd.append("file",f);
  const res=await fetch("/api/upload",{method:"POST",body:fd}); const d=await res.json();
  if(!res.ok){toast(d.error||"Upload failed");return}
  await loadCases(); $("caseSelect").value=d.name; await loadCaseInfo();
  toast(`Loaded ${d.name} • ${d.counts.packages} packages`);
}
$("fileInput").addEventListener("change",upload);

async function runSimulation(){
  const btn=$("runBtn");btn.disabled=true;btn.textContent="⟳ Simulating...";
  const res=await fetch("/api/simulate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({case:$("caseSelect").value})});
  const d=await res.json();
  btn.disabled=false;btn.textContent="▶ Run Simulation";
  if(!res.ok){toast(d.error||"Simulation failed");return}
  currentReport=d; render(d); nav("dashboard"); toast("Simulation completed successfully");
}
$("runBtn").addEventListener("click",runSimulation);

function render(d){
  $("statPackages").textContent=d.summary.packages;
  $("statDelivered").textContent=`${d.summary.delivered}/${d.summary.packages}`;
  $("deliveryRate").textContent=`${d.summary.packages?Math.round(d.summary.delivered/d.summary.packages*100):0}% delivery completion`;
  $("statAgents").textContent=d.summary.agents;
  $("statDistance").textContent=fmt(d.summary.total_distance);
  $("eventFeed").innerHTML=d.events.length?d.events.map(e=>`
    <div class="event">
      <div class="event-top"><b>Package ${e.package_id} <span style="color:#58e6ad">• DELIVERED</span></b><span>#${String(e.sequence).padStart(2,"0")}</span></div>
      <div class="event-meta">Agent ${e.agent_id} → ${e.warehouse_id} → Destination (${e.destination.join(", ")})</div>
      <div class="event-distance">Warehouse leg ${fmt(e.to_warehouse_distance)} &nbsp;|&nbsp; Delivery leg ${fmt(e.delivery_distance)} &nbsp;|&nbsp; Total ${fmt(e.package_distance)}</div>
    </div>`).join(""):'<div class="empty">No events.</div>';
  const max=Math.max(...d.agents.map(a=>a.packages_delivered),1);
  $("agentMini").innerHTML=d.agents.map(a=>`
    <div class="agent-row"><div class="agent-line"><b>${a.id}</b><span>${a.packages_delivered} packages</span></div>
    <div class="meter"><i style="width:${a.packages_delivered/max*100}%"></i></div>
    <div class="event-meta">${fmt(a.total_distance)} distance • ${fmt(a.efficiency)} per package${a.id===d.best_agent?" • Best efficiency":""}</div></div>`).join("");
  $("agentsTable").innerHTML=d.agents.map(a=>`<tr><td><b>${a.id}</b></td><td>${a.packages_delivered}</td><td>${fmt(a.total_distance)}</td><td>${fmt(a.efficiency)}</td><td>(${a.final_location.join(", ")})</td></tr>`).join("");
  $("packagesTable").innerHTML=d.events.map(e=>`<tr><td><b>${e.package_id}</b></td><td>${e.agent_id}</td><td>${e.warehouse_id}</td><td>(${e.destination.join(", ")})</td><td><span class="tag">DELIVERED</span></td></tr>`).join("");
  $("routeBoard").innerHTML=d.events.map(e=>`<div class="route-card"><div class="route-path"><div class="node">AGENT ${e.agent_id}<br><small>(${e.start.join(", ")})</small></div><span class="arrow">→</span><div class="node">WAREHOUSE ${e.warehouse_id}<br><small>(${e.warehouse.join(", ")})</small></div><span class="arrow">→</span><div class="node">DESTINATION<br><small>(${e.destination.join(", ")})</small></div></div><div class="route-stats">Package ${e.package_id} • ${fmt(e.package_distance)} total distance • cumulative agent distance ${fmt(e.cumulative_distance)}</div></div>`).join("");
}

loadCases();

// ===== SHARED DATA & HELPERS =====
const BASE_COLORS=['#00d4ff','#ff6b35','#7dff8a','#be78ff','#ffc800','#ff5078','#50a0ff','#00dc82','#ffdd57','#ff85c0','#a0d8ef','#c8ff99'];
const EXTRA_COLORS=['#ff9f40','#c9cbcf','#ff6384','#36a2eb','#9966ff','#4bc0c0'];
const LAND_COLORS={urban:'#ff6b35',agriculture:'#7dff8a',forest:'#00dc82',wetland:'#50a0ff',other:'#6b85a8'};

let DATA=[], USER_DISTRICTS=[], ORIGINAL_DATA={};
let selectedYear=null, sortCol='risk_score';
let selectedDistrict=null, compareA=null, compareB=null;
let activeDistricts=new Set();
const chartInstances={};

function riskColor(s){return s>=75?'#ff3d00':s>=55?'#ffab00':'#00c853';}
function riskLabel(s){return s>=75?'HIGH':s>=55?'MEDIUM':'LOW';}
function getAllData(){return[...DATA,...USER_DISTRICTS];}
function getActiveData(){
  const all=getAllData();
  if(compareA&&compareB) return all.filter(d=>d.id===compareA||d.id===compareB);
  return selectedDistrict?all.filter(d=>d.id===selectedDistrict):all;
}

function chartDefaults(dur=1000){
  return{
    responsive:true,maintainAspectRatio:true,
    animation:{duration:dur,easing:'easeOutQuart'},
    plugins:{
      legend:{labels:{color:'#5a7a9e',font:{family:'DM Mono',size:10}}},
      tooltip:{backgroundColor:'#0c1526',borderColor:'#1a2d47',borderWidth:1,titleColor:'#e4edfb',bodyColor:'#5a7a9e',titleFont:{family:'DM Mono'},bodyFont:{family:'DM Mono'}}
    },
    scales:{
      x:{ticks:{color:'#5a7a9e',font:{family:'DM Mono',size:9}},grid:{color:'#1a2d47'}},
      y:{ticks:{color:'#5a7a9e',font:{family:'DM Mono',size:9}},grid:{color:'#1a2d47'}}
    }
  };
}

function makeChart(id,config){
  if(chartInstances[id]) chartInstances[id].destroy();
  const ctx=document.getElementById(id)?.getContext('2d');
  if(!ctx) return null;
  chartInstances[id]=new Chart(ctx,config);
  return chartInstances[id];
}

function exportChartPNG(id,name){
  const chart=chartInstances[id]; if(!chart) return;
  const url=chart.toBase64Image();
  const a=document.createElement('a'); a.href=url; a.download=(name||id)+'.png';
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
}

function downloadCSV(){
  const rows=[['District','Coastline (km)','Pop (K)','Erosion (m/yr)','Risk Score','Risk Level']];
  getAllData().forEach(d=>rows.push([d.name,d.coastline_km,d.population_exposed,d.erosion_rate,d.risk_score,riskLabel(d.risk_score)]));
  const blob=new Blob([rows.map(r=>r.join(',')).join('\n')],{type:'text/csv'});
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a'); a.href=url; a.download='coastal_risk_data.csv';
  document.body.appendChild(a); a.click(); document.body.removeChild(a); URL.revokeObjectURL(url);
}

async function loadData(callback){
  const res=await fetch('data/coastal_data.json');
  const json=await res.json();
  DATA=json.districts;
  DATA.forEach((d,i)=>{d._color=BASE_COLORS[i];d._isUser=false;});
  DATA.forEach(d=>{ORIGINAL_DATA[d.id]=JSON.parse(JSON.stringify(d));});
  activeDistricts=new Set(DATA.map(d=>d.id));
  if(callback) callback();
}

// ===== SHARED YEAR PANEL =====
let ypCharts={};
function setupYearPanel(){
  const panel=document.getElementById('yearPanel'); if(!panel) return;
  document.getElementById('ypClose')?.addEventListener('click',()=>panel.classList.remove('open'));
}
function openYearPanel(year){
  const panel=document.getElementById('yearPanel'); if(!panel) return;
  document.getElementById('ypYear').textContent=year;
  panel.classList.add('open');
  updateYearPanel(year);
}
function updateYearPanel(year){
  const d=getActiveData(), y=String(year);
  const totalFloods=d.reduce((s,x)=>s+(x.yearly_floods?.[y]||0),0);
  const maxD=d.reduce((a,b)=>(b.yearly_floods?.[y]||0)>(a.yearly_floods?.[y]||0)?b:a,d[0]);
  const avgRain=Math.round(d.reduce((s,x)=>s+(x.rainfall_mm?.[y]||0),0)/d.length);
  const hi=d.filter(x=>x.risk_score>=75).length;
  const statsEl=document.getElementById('ypStats'); if(!statsEl) return;
  statsEl.innerHTML=`
    <div class="yp-stat"><span class="yp-stat-val" style="color:#7dff8a">${totalFloods}</span><span class="yp-stat-lbl">TOTAL FLOODS</span></div>
    <div class="yp-stat"><span class="yp-stat-val" style="color:#00d4ff">${avgRain}</span><span class="yp-stat-lbl">AVG RAIN mm</span></div>
    <div class="yp-stat"><span class="yp-stat-val" style="color:#ff3d00">${hi}</span><span class="yp-stat-lbl">HIGH RISK</span></div>
    <div class="yp-stat"><span class="yp-stat-val" style="color:#ffc800;font-size:0.75rem">${maxD?.name?.substring(0,7)||'—'}</span><span class="yp-stat-lbl">WORST DIST.</span></div>`;
  if(ypCharts.bar) ypCharts.bar.destroy();
  const bc=document.getElementById('ypBar')?.getContext('2d');
  if(bc) ypCharts.bar=new Chart(bc,{type:'bar',data:{labels:d.map(x=>x.name.substring(0,5)),datasets:[{data:d.map(x=>x.yearly_floods?.[y]||0),backgroundColor:d.map(x=>riskColor(x.risk_score)+'cc'),borderRadius:3}]},options:{responsive:true,maintainAspectRatio:false,animation:{duration:300},plugins:{legend:{display:false},tooltip:{backgroundColor:'#0c1526',titleFont:{family:'DM Mono'},bodyFont:{family:'DM Mono'}}},scales:{x:{ticks:{color:'#5a7a9e',font:{family:'DM Mono',size:8}},grid:{display:false}},y:{ticks:{color:'#5a7a9e',font:{family:'DM Mono',size:8}},grid:{color:'#1a2d47'}}}}});
}

// ===== SHARED DISTRICT SEARCH =====
function setupDistrictSearch(onSelect){
  const input=document.getElementById('districtSearch');
  const drop=document.getElementById('searchDrop');
  if(!input||!drop) return;
  function render(f=''){
    const filtered=getAllData().filter(d=>d.name.toLowerCase().includes(f.toLowerCase()));
    drop.innerHTML=filtered.map(d=>`<div class="drop-item" data-id="${d.id}"><div class="drop-dot" style="background:${d._color}"></div>${d.name}<span style="margin-left:auto;font-size:0.55rem;color:${riskColor(d.risk_score)}">${riskLabel(d.risk_score)}</span></div>`).join('');
    drop.querySelectorAll('.drop-item').forEach(el=>el.addEventListener('click',()=>{
      drop.classList.remove('open'); input.value='';
      if(onSelect) onSelect(el.dataset.id);
    }));
  }
  input.addEventListener('focus',()=>{render(input.value);drop.classList.add('open');});
  input.addEventListener('input',()=>{render(input.value);drop.classList.add('open');});
  document.addEventListener('click',e=>{if(!e.target.closest('.search-wrap'))drop.classList.remove('open');});
}

// ===== SHARED COMPARE =====
function setupCompare(onApply){
  const selA=document.getElementById('compareA'), selB=document.getElementById('compareB');
  const clearBtn=document.getElementById('btnClearCompare');
  if(!selA||!selB) return;
  DATA.forEach(d=>{
    [selA,selB].forEach(s=>{const o=document.createElement('option');o.value=d.id;o.textContent=d.name;s.appendChild(o);});
  });
  function apply(){
    const a=selA.value,b=selB.value;
    if(a&&b&&a!==b){compareA=a;compareB=b;selectedDistrict=null;if(clearBtn)clearBtn.style.display='inline-block';if(onApply)onApply();}
  }
  selA.addEventListener('change',apply); selB.addEventListener('change',apply);
  clearBtn?.addEventListener('click',()=>{compareA=null;compareB=null;selA.value='';selB.value='';if(clearBtn)clearBtn.style.display='none';if(onApply)onApply();});
}

// ===== SHARED YEAR SLIDER =====
function setupYearSlider(onChange){
  const slider=document.getElementById('yearSlider');
  const display=document.getElementById('yearVal');
  const btnAll=document.getElementById('btnAllYears');
  let scrolled=false;
  if(!slider) return;
  slider.addEventListener('input',()=>{
    selectedYear=parseInt(slider.value);
    if(display) display.textContent=selectedYear;
    if(btnAll) btnAll.classList.remove('active');
    openYearPanel(selectedYear);
    if(!scrolled){document.querySelector('.page-content')?.scrollIntoView({behavior:'smooth',block:'start'});scrolled=true;}
    if(onChange) onChange();
  });
  btnAll?.addEventListener('click',()=>{
    selectedYear=null; if(display)display.textContent='All';
    btnAll.classList.add('active'); slider.value=2023; scrolled=false;
    document.getElementById('yearPanel')?.classList.remove('open');
    if(onChange) onChange();
  });
}

// ===== TOOLTIP MODAL =====
function showInfo(title,body){
  document.getElementById('infoTitle').textContent=title;
  document.getElementById('infoBody').textContent=body;
  document.getElementById('infoModal').classList.add('open');
}
function closeInfo(){document.getElementById('infoModal').classList.remove('open');}
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeInfo();});

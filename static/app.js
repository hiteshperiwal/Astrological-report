let latest=null, mundaneLatest=null;
let selectedPlaceResolved=false;
let libraryDataPromise=null, librarySearchTimer=null, librarySearchAbort=null;
const $=id=>document.getElementById(id);
function esc(s){return String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));}
function titleCase(s){return String(s??'').replace(/[_-]+/g,' ').replace(/\b\w/g,m=>m.toUpperCase());}
function syncBirthDateTime(){const d=$('birthDatePicker')?.value||'';const t=$('birthTimePicker')?.value||'';if(!d||!t)return false;$('dob').value=d;$('tob').value=t;$('birthDateTime').value=`${d} ${t}`;$('birthPickerPreview').textContent=`${d} · ${t}`;return true;}
function initBirthPicker(){const open=$('openBirthPicker'),field=$('birthDateTime'),panel=$('birthPicker');if(!open||!panel)return;const close=()=>panel.classList.add('hidden');const show=()=>{panel.classList.remove('hidden');if(!$('birthDatePicker').value&&$('dob').value)$('birthDatePicker').value=$('dob').value;if(!$('birthTimePicker').value&&$('tob').value)$('birthTimePicker').value=$('tob').value;};open.addEventListener('click',()=>panel.classList.contains('hidden')?show():close());field?.addEventListener('click',show);field?.addEventListener('focus',show);$('closeBirthPicker').addEventListener('click',close);$('applyBirthPicker').addEventListener('click',()=>{if(!syncBirthDateTime()){setStatus('Select both birth date and time.','error');return;}close();setStatus('Birth date and time selected.','success')});['birthDatePicker','birthTimePicker'].forEach(id=>$(id).addEventListener('input',syncBirthDateTime));document.addEventListener('click',e=>{if(!e.target.closest('.datetime-field'))close()});}
initBirthPicker();
function deg(v){return `${Number(v).toFixed(2)}°`;}
function row(cells){return `<tr>${cells.map(x=>`<td>${x}</td>`).join('')}</tr>`}
function th(cells){return `<tr>${cells.map(x=>`<th>${x}</th>`).join('')}</tr>`}

// Workspace navigation: Personal and Mundane are deliberately independent.
document.querySelectorAll('.workspace').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('.workspace').forEach(x=>x.classList.remove('active'));document.querySelectorAll('.workspace-pane').forEach(x=>x.classList.remove('active'));b.classList.add('active');$('workspace-'+b.dataset.workspace).classList.add('active');}));
document.querySelectorAll('.subtab').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('.subtab').forEach(x=>x.classList.remove('active'));document.querySelectorAll('.subpane').forEach(x=>x.classList.remove('active'));b.classList.add('active');$(b.dataset.tab).classList.add('active');renderActivePersonalTab(b.dataset.tab);}));

const waitFrame=()=>new Promise(resolve=>requestAnimationFrame(()=>resolve()));
function debugLog(message, kind='info'){
  const box=$('debugLog'); if(!box) return;
  const el=document.createElement('div'); el.className=kind; el.textContent=`${new Date().toLocaleTimeString()}  ${message}`; box.appendChild(el); box.scrollTop=box.scrollHeight;
}
function setStatus(message, kind='info'){
  const el=$('status'); if(!el) return; el.textContent=message; el.className=`status ${kind}`;
}
async function readJsonResponse(r){
  const text=await r.text();
  let d={}; try{d=JSON.parse(text)}catch{d={detail:text||`HTTP ${r.status}`}};
  if(!r.ok) throw new Error(d.detail||`Request failed (${r.status})`); return d;
}
$('birthForm').addEventListener('submit',async e=>{
  e.preventDefault();
  if(!$('place').value.trim() || !selectedPlaceResolved){setStatus('Select a birth place from the suggestions first.','error');$('place').focus();return;}
  const fs=$('personalForecastStart').value, fe=$('personalForecastEnd').value; if(Boolean(fs)!==Boolean(fe)||(fs&&fe&&fe<fs)){setStatus('Choose both forecast dates, with the end date on or after the start date.','error');return;} const started=performance.now(); const btn=e.submitter||document.querySelector('#birthForm button[type="submit"]');
  if(btn) btn.disabled=true; debugLog('Starting personal Kundali request'); setStatus('Connecting to calculation engine…','processing');
  const payload={name:$('name').value.trim(),dob:$('dob').value,tob:$('tob').value,place:$('place').value.trim(),latitude:Number($('lat').value),longitude:Number($('lon').value),timezone:$('tz').value,forecast_amount:Number($('forecastAmount').value),forecast_unit:$('forecastUnit').value,forecast_granularity:$('forecastGranularity').value||null,forecast_start_date:$('personalForecastStart').value||null,forecast_end_date:$('personalForecastEnd').value||null,school:$('school').value};
  try{
    await waitFrame(); debugLog('Sending birth data to /api/personal/analyze'); setStatus('Calculating astronomical positions, houses and Vargas…','processing');
    const r=await fetch('/api/personal/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),cache:'no-store'});
    debugLog(`Backend responded with HTTP ${r.status}`); setStatus('Calculation returned. Preparing the report…','processing');
    const d=await readJsonResponse(r); latest={payload,...d}; debugLog('Calculation data received; rendering compact overview');
    await waitFrame(); renderPersonal(latest); setStatus(`Kundali ready · ${((performance.now()-started)/1000).toFixed(1)}s`,'success'); debugLog('Overview rendered successfully','ok');
  }catch(err){console.error(err);debugLog(`ERROR: ${err.message||err}`,'bad');setStatus(err.message||String(err),'error');showUiError('personalResults',err,'Personal report failed');$('personalResults').classList.remove('hidden');}
  finally{if(btn)btn.disabled=false;}
});
function renderPersonal(x){
  const c=x.chart||{}, n=x.narrative||{}; $('personalResults').classList.remove('hidden');
  $('personalKpis').innerHTML=[['Lagna',c.lagna_sign],['Moon Nakshatra',`${c.nakshatra_analysis?.moon?.name||'—'} · P${c.nakshatra_analysis?.moon?.pada||'—'}`],['Dasha Lord',c.dashas?.starting_lord||'—'],['Vargas',Object.keys(c.divisional_charts||{}).length],['Forecast',`${c.forecast?.amount||'—'} ${c.forecast?.unit||''}`]].map(k=>`<div class="kpi"><b>${esc(k[1])}</b><span>${esc(k[0])}</span></div>`).join('');
  const lifeCards=Object.entries(c.recommendations||{}).filter(([k,v])=>!['start_new','career_switch','family_time','learning_push','relationship_focus'].includes(k) && (v.windows||[]).length).map(([k,v])=>`<div class="action-card"><b>${esc(titleCase(v.label||k))}</b><div class="mini-list">${(v.windows||[]).slice(0,3).map(w=>`<span>${esc(w.date)} · ${w.score}/100</span>`).join('')}</div></div>`).join('');
  $('personal-overview').innerHTML=`<div class="section"><div class="section-heading"><div><span class="eyebrow">KUNDALI OVERVIEW</span><h3>${esc(c.meta?.name||'Native')}</h3><p class="muted">${esc(c.meta?.birth_local||'')} · ${esc(c.meta?.place||'')} · ${esc(c.meta?.timezone||'')}</p></div><div class="method-chip">${esc(c.meta?.ayanamsha||'Lahiri')}</div></div><div class="insight-grid"><div class="insight"><b>Moon Lens</b><p>${esc(c.nakshatra_analysis?.reading?.[0]||'Moon nakshatra analysis available in the Nakshatra tab.')}</p></div><div class="insight"><b>Ascendant Lens</b><p>${esc(c.nakshatra_analysis?.reading?.[1]||'Ascendant analysis available in the detailed report.')}</p></div><div class="insight"><b>Timing Lens</b><p>${esc(c.nakshatra_analysis?.reading?.[2]||'Timing layers are available in Forecast & Timing.')}</p></div></div></div><div class="section"><h3>Life-Area Planning Map</h3><p class="muted">The scores are deterministic activation indices produced by the timing rules. Higher values mean stronger rule activation for that life area.</p><div class="action-grid">${lifeCards}</div></div><div class="section"><h3>Forecast Horizon</h3><p class="muted">${esc(c.forecast?.start||'')} → ${esc(c.forecast?.end||'')} · ${esc(c.forecast?.amount||'')} ${esc(c.forecast?.unit||'')} · ${esc(c.forecast?.granularity||'')}</p><p class="note">The detailed report is split into tabs so the browser does not have to render every large research table at once.</p></div>`;
  // Overview is already rendered above; heavy tabs are rendered on demand.
  renderedTabs.clear(); renderedTabs.add('personal-overview');
}
const renderedTabs=new Set(['personal-overview']);
function renderActivePersonalTab(id,force=false){
  if(!latest?.chart) return; if(renderedTabs.has(id)&&!force) return; const c=latest.chart;
  try{
    debugLog(`Rendering ${id.replace('personal-','')}`); setStatus(`Rendering ${id.replace('personal-','')}…`,'processing');
    const map={
      'personal-overview':()=>{}, 'personal-charts':()=>renderCharts(c), 'personal-grahas':()=>renderGrahas(c), 'personal-nakshatra':()=>renderNakshatra(c), 'personal-dashas':()=>renderDashas(latest), 'personal-yogas':()=>renderYogas(latest), 'personal-strength':()=>renderStrength(c), 'personal-timing':()=>renderTiming(c), 'personal-predictions':()=>renderPredictions(latest), 'personal-panchanga':()=>renderPanchanga(c), 'personal-advanced':()=>renderAdvanced(c), 'personal-numerology':()=>renderNumerology(c), 'personal-interpretation':()=>renderInterpretations(latest), 'personal-ai':()=>renderAI(latest), 'personal-chat':()=>renderChat(latest)
    }; if(map[id]) map[id](); renderedTabs.add(id); setStatus('Ready','success');
  }catch(err){console.error(err);debugLog(`Render error in ${id}: ${err.message||err}`,'bad');showUiError(id,err,'This section could not be rendered');setStatus(`Error rendering ${id.replace('personal-','')}`,'error');}
}

const chartPos={1:[200,45],2:[95,75],3:[45,150],4:[95,225],5:[200,255],6:[305,225],7:[355,150],8:[305,75],9:[200,135],10:[125,150],11:[200,200],12:[275,150]};
const signs=['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'];
function chartSvg(v,title){
  const lagna=Number(v.lagna_sign_index??0);
  const hs=Object.fromEntries([...Array(12)].map((_,i)=>[i+1,{sign:(lagna+i)%12,planets:[]} ]));
  for(const [p,d] of Object.entries(v.planets||{})){const h=Number(d.house); if(hs[h]) hs[h].planets.push(p)}
  const pos={1:[200,72],2:[92,42],3:[43,132],4:[94,200],5:[43,286],6:[92,352],7:[200,328],8:[308,352],9:[357,286],10:[306,200],11:[357,132],12:[308,42]};
  let s=`<svg class="kundali north-kundali" viewBox="0 0 400 400" role="img" aria-label="${esc(title)}"><rect x="4" y="4" width="392" height="392" rx="10" fill="#fffaf0" stroke="#8b6b3e" stroke-width="2"/><path d="M4 4 L396 396 M396 4 L4 396 M200 4 L396 200 L200 396 L4 200 Z" fill="none" stroke="#8b6b3e" stroke-width="1.8"/>`;
  for(const [h,b] of Object.entries(hs)){const [x,y]=pos[h]; const ps=b.planets||[]; s+=`<g><text x="${x}" y="${y-20}" text-anchor="middle" font-size="8" fill="#9b7a45">H${h}</text><text x="${x}" y="${y-7}" text-anchor="middle" font-size="10" font-weight="700" fill="#372718">${esc(signs[b.sign])}</text>`; ps.forEach((p,i)=>{const pd=v.planets?.[p]||{};s+=`<text x="${x}" y="${y+10+i*12}" text-anchor="middle" font-size="9" font-weight="800" fill="#7b2348">${esc(p+(pd.retrograde?' (R)':''))}</text>`}); s+='</g>'}
  s+=`<text x="200" y="20" text-anchor="middle" font-size="10" font-weight="800" fill="#5b3a21">${esc(title)}</text></svg>`; return s;
}

function renderCharts(c){const principal=['D1','D9','D10','D7','D12','D16','D20','D24','D27','D30','D40','D45','D60','D2','D3','D4'];const cards=principal.map(k=>{const v=c.divisional_charts[k];return `<div class="chart-card"><div class="chart-title"><b>${k} · ${esc(v.name)}</b><span>${esc(v.lagna_sign||'')}</span></div><p class="varga-method">${esc(v.method||'Parashari divisional mapping')}</p>${chartSvg(v,k+' / '+v.name)}</div>`}).join('');const moonChart={lagna_sign_index:c.planets.Moon.sign_index,planets:Object.fromEntries(Object.entries(c.planets).map(([p,d])=>[p,{...d,house:((d.sign_index-c.planets.Moon.sign_index)%12)+1}]))};const sunChart={lagna_sign_index:c.planets.Sun.sign_index,planets:Object.fromEntries(Object.entries(c.planets).map(([p,d])=>[p,{...d,house:((d.sign_index-c.planets.Sun.sign_index)%12)+1}]))};$('personal-charts').innerHTML=`<div class="section"><div class="section-heading"><div><span class="eyebrow">KUNDALI FAMILY</span><h3>Rashi, Navamsa, Bhava and reference charts</h3></div></div><div class="chart-grid feature-charts"><div class="chart-card hero-chart"><b>D1 · Rashi / Lagna</b>${chartSvg(c,'D1 / Rashi')}</div><div class="chart-card hero-chart"><b>D9 · Navamsa</b><p class="varga-method">${esc(c.divisional_charts.D9?.method||'Fixed signs count from the 9th; dual signs from the 5th.')}</p>${chartSvg(c.divisional_charts.D9,'D9 / Navamsa')}</div><div class="chart-card hero-chart"><b>Chandra Lagna</b>${chartSvg(moonChart,'Moon chart')}</div><div class="chart-card hero-chart"><b>Surya Lagna</b>${chartSvg(sunChart,'Sun chart')}</div></div></div><div class="section"><h3>All 16 principal Vargas</h3><div class="chart-grid">${cards}</div></div>`}
function renderGrahas(c){const rows=Object.entries(c.planets).map(([p,d])=>row([esc(p+(d.retrograde?' (R)':'')),esc(d.sign),d.house,deg(d.degree_in_sign),esc(d.nakshatra.name),`P${d.nakshatra.pada}`,esc(d.dignity),d.combust?'Yes':'No'])).join('');const aspects=c.aspects.slice(0,60).map(a=>row([esc(a.a),esc(a.b),a.aspect,`${a.orb}°`,a.exactness])).join('');$('personal-grahas').innerHTML=`<div class="section"><h3>Graha matrix</h3><div class="table-wrap"><table>${th(['Graha','Sign','House','Degree','Nakshatra','Pada','Dignity','Combust'])}${rows}</table></div></div><div class="section"><h3>Planetary aspects</h3><div class="table-wrap"><table>${th(['A','B','Aspect','Orb','Exactness'])}${aspects}</table></div></div>`}
function renderNakshatra(c){const m=c.nakshatra_analysis.moon,a=c.nakshatra_analysis.lagna;const all=Object.entries(c.nakshatra_analysis.planetary).map(([p,n])=>row([esc(p+(c.planets?.[p]?.retrograde?' (R)':'')),esc(n.name),n.pada,esc(n.deity),esc(n.shakti),esc(n.gana),esc(n.yoni),esc(n.nadi)])).join('');$('personal-nakshatra').innerHTML=`<div class="section"><div class="nak-hero"><div><span class="eyebrow">MOON NAKSHATRA</span><h3>${esc(m.name)} · Pada ${m.pada}</h3><p>${esc(m.shakti)} · ${esc(m.symbol)} · Lord ${esc(m.vimshottari_lord)}</p></div><div class="nak-meta"><span>${esc(m.deity)}</span><span>${esc(m.gana)}</span><span>${esc(m.yoni)}</span><span>${esc(m.nadi)}</span></div></div></div><div class="section"><h3>Nakshatra interpretation</h3>${c.nakshatra_analysis.reading.map(x=>`<p class="muted">${esc(x)}</p>`).join('')}</div><div class="section"><h3>Planetary Nakshatra matrix</h3><div class="table-wrap"><table>${th(['Planet','Nakshatra','Pada','Deity','Shakti','Gana','Yoni','Nadi'])}${all}</table></div></div><div class="section"><h3>Ascendant Nakshatra</h3><p><b>${esc(a.name)} · Pada ${a.pada}</b> — ${esc(a.symbol)} · ${esc(a.quality)} · ${esc(a.shakti)}</p></div>`}
function renderDashas(source){
  const c=source?.chart||source||{};
  const narrative=source?.narrative||c.narrative||{};
  const ctx=narrative?.interpretations?.dasha_context||{};
  // Defensive fallback: the chart itself always carries the Vimshottari hierarchy.
  // The narrative is an interpretation layer, not the source of truth for Dasha data.
  if(!ctx.selected_mahadashas?.length && c.dashas?.periods?.length){
    const timeline=c.dashas?.mahadasha_timeline||[];
    const now=Date.now();
    const current=timeline.find(x=>{const st=Date.parse(x.start),en=Date.parse(x.end);return Number.isFinite(st)&&Number.isFinite(en)&&st<=now&&now<en;});
    const idx=current?timeline.indexOf(current):Math.max(0,timeline.length-1);
    const order=['Ketu','Venus','Sun','Moon','Mars','Rahu','Jupiter','Saturn','Mercury'];
    const durations=[7,20,6,10,7,18,16,19,17];
    const makeChildren=(start,end,lord,depth)=>{
      if(depth>5)return [];
      const st=Date.parse(start),en=Date.parse(end),total=en-st;
      if(!Number.isFinite(st)||!Number.isFinite(en)||total<=0)return [];
      const parentIndex=Math.max(0,order.indexOf(lord));
      let cur=st; const out=[];
      for(let k=0;k<9;k++){
        const i=(parentIndex+k)%9, child=order[i];
        const childEnd=k===8?en:cur+total*(durations[i]/120);
        const node={level:depth,level_name:{2:'Antardasha',3:'Pratyantar Dasha',4:'Sookshma Dasha',5:'Prana Dasha'}[depth]||'Dasha',lord:child,start:new Date(cur).toISOString(),end:new Date(childEnd).toISOString()};
        if(depth<5)node.children=makeChildren(node.start,node.end,child,depth+1);
        out.push(node); cur=childEnd;
      }
      return out;
    };
    const serialize=x=>({level:1,level_name:'Mahadasha',lord:x.lord,start:x.start,end:x.end,children:makeChildren(x.start,x.end,x.lord,2)});
    const selected=timeline.slice(Math.max(0,idx-2),idx+4).map(serialize);
    ctx.selected_mahadashas=selected;
    ctx.previous_mahadashas=selected.slice(0,Math.min(2,selected.length));
    ctx.current_mahadasha=selected[2]||selected[0]||null;
    ctx.next_mahadashas=selected.slice(3);
  }
  const selected=ctx.selected_mahadashas||[];
  const levelName={1:'Mahadasha',2:'Antardasha',3:'Pratyantar Dasha',4:'Sookshma Dasha',5:'Prana Dasha'};
  const nodeHtml=(node,depth=1)=>`<details class="dasha-node" ${depth===1?'open':''}><summary><span class="dasha-level">${esc(levelName[depth]||node.level_name||`Level ${depth}`)}</span><b>${esc(node.lord)}</b><span>${esc(String(node.start||'').slice(0,10))} → ${esc(String(node.end||'').slice(0,10))}</span></summary>${depth<5&&(node.children||[]).length?`<div class="dasha-children">${node.children.map(x=>nodeHtml(x,depth+1)).join('')}</div>`:''}</details>`;
  const labels=selected.map((x,i)=>{const phase=i<ctx.previous_mahadashas?.length?'Previous':(ctx.current_mahadasha?.start===x.start?'Current':'Next');return `<span>${phase}: ${esc(x.lord)} · ${esc(String(x.start||'').slice(0,10))} → ${esc(String(x.end||'').slice(0,10))}</span>`}).join('');
  $('personal-dashas').innerHTML=`<div class="section"><div class="section-heading"><div><span class="eyebrow">VIMSHOTTARI TIMING</span><h3>Mahadasha → Antardasha → Pratyantar → Sookshma → Prana</h3><p class="muted">Current Mahadasha plus the previous two and next three are shown. Expand any Mahadasha to inspect all available sub-periods.</p></div></div><div class="dasha-summary">${labels}</div><div class="dasha-tree">${selected.map(x=>nodeHtml(x,1)).join('')}</div></div>`;
}
function renderYogas(source){
  const c=source?.chart||source||{};
  const narrative=source?.narrative||c.narrative||{};
  const ys=narrative?.interpretations?.yoga_interpretations||[];
  const ds=narrative?.interpretations?.dosha_interpretations||[];
  // If an older/cached narrative is missing, use the chart-level detected Yoga/Dosha
  // objects rather than incorrectly reporting that no screen fired.
  const yogaRows=ys.length?ys:(c.yogas||[]).map(y=>({name:y.name,strength:y.strength,basis:y.basis,meaning:y.meaning||y.interpretation||y.basis,life_impact:y.life_impact||'',interpretation:y.interpretation||y.basis,fruitification:y.fruitification||{}}));
  const doshaRows=ds.length?ds:(c.doshas||[]).map(d=>({name:d.name,severity:d.severity,life_impact:d.life_impact||d.interpretation||d.basis,interpretation:d.interpretation||d.basis,basis:d.basis}));
  const yhtml=yogaRows.length?yogaRows.map(y=>{const impact=y.life_impact||y.interpretation||y.basis||''; const meaning=y.meaning||'Plain-language reading is not available for this yoga.'; const domains=(y.life_impact_by_domain||[]).map(z=>`<span>${esc(titleCase(z.domain))}: ${esc(z.text)}</span>`).join(''); return `<div class="card-line yoga-card"><div class="interpret-head"><b>${esc(y.name)}</b><span>${esc(y.strength||'')}</span></div><p><b>Meaning in plain language:</b> ${esc(meaning)}</p><p><b>Life Impact:</b> ${esc(impact)}</p>${domains?`<div class="mini-list yoga-domains">${domains}</div>`:''}<p><b>When Activated:</b> ${esc(y.interpretation||'')}</p>${(y.fruitification?.possible_dates||[]).slice(0,5).map(w=>`<small>Fruitification: <b>${esc(w.date)}</b> · ${esc(w.active_dasha||w.dasha_lord||'—')} · ${esc((w.transit_triggers||[]).map(a=>a.transit+'→'+a.natal).join(', ')||'transit contact')}</small>`).join('')}</div>`}).join(''):'<p class="muted">No applicable yoga screen fired for this chart.</p>';
  const dhtml=doshaRows.length?doshaRows.map(d=>`<div class="card-line"><div class="interpret-head"><b>${esc(d.name)}</b><span>${esc(d.severity||'')}</span></div><p><b>Life Impact:</b> ${esc(d.life_impact||d.interpretation||d.basis||'')}</p><p><b>When Activated:</b> ${esc(d.interpretation||d.basis||'')}</p></div>`).join(''):'<p class="muted">No applicable dosha screen fired for this chart.</p>';
  $('personal-yogas').innerHTML=`<div class="section"><h3>Applicable Yogas</h3><p class="muted">The Meaning field explains the yoga as a life pattern, not merely as a list of planetary placements.</p>${yhtml}</div><div class="section"><h3>Applicable Doshas / Afflictions</h3>${dhtml}</div>`;
}
function renderStrength(c){const ps=Object.entries(c.planet_strengths.planets).map(([p,d])=>row([esc(p+(d.components.retrograde?' (R)':'')),d.score,esc(d.components.dignity),d.components.house,d.components.combust?'Yes':'No'])).join('');const bs=c.bhava_strengths.map(h=>row([h.house,esc(h.sign),esc(h.lord),h.strength,esc((h.occupants||[]).join(', '))])).join('');$('personal-strength').innerHTML=`<div class="section"><h3>Planet strength screen</h3><p class="muted">Normalized 0–100 readability layer; not classical Shadbala units.</p><div class="table-wrap"><table>${th(['Planet','Score','Dignity','House','Combust'])}${ps}</table></div></div><div class="section"><h3>Bhava strength screen</h3><div class="table-wrap"><table>${th(['House','Sign','Lord','Strength','Occupants'])}${bs}</table></div></div>`}
function lineChart(rows,keys){
  if(!rows?.length)return '<div class="empty">No forecast rows.</div>';
  const W=1000,H=320,P=44; const xs=i=>P+i*(W-2*P)/Math.max(1,rows.length-1); const ys=v=>H-P-v*(H-2*P)/100;
  const palette=['#69d9ea','#b8a1ff','#f08fa9','#8fe1b1','#f1c46d','#8cb7ff','#d77cf2','#77e0c1','#ff9d76'];
  let s=`<svg class="modern-chart" viewBox="0 0 ${W} ${H}"><rect width="${W}" height="${H}" rx="16" fill="#0b1118"/>`;
  [0,25,50,75,100].forEach(v=>s+=`<line x1="${P}" y1="${ys(v)}" x2="${W-P}" y2="${ys(v)}" stroke="#22303e"/><text x="8" y="${ys(v)+4}" fill="#8090a0" font-size="10">${v}</text>`);
  keys.forEach((k,idx)=>{const path=rows.map((r,i)=>(i?'L':'M')+xs(i).toFixed(1)+','+ys(Number(r[k]||0)).toFixed(1)).join(' ');s+=`<path d="${path}" fill="none" stroke="${palette[idx%palette.length]}" stroke-width="2.2"/>`});
  const step=Math.max(1,Math.floor(rows.length/8)); for(let i=0;i<rows.length;i+=step)s+=`<text x="${xs(i)}" y="${H-12}" text-anchor="middle" fill="#8090a0" font-size="9">${esc(rows[i].date.slice(0,10))}</text>`;
  return s+'</svg>';
}
function chartLegend(keys){const palette=['#69d9ea','#b8a1ff','#f08fa9','#8fe1b1','#f1c46d','#8cb7ff','#d77cf2','#77e0c1','#ff9d76']; return `<div class="chart-legend">${keys.map((k,i)=>`<span><i style="background:${palette[i%palette.length]}"></i>${esc(titleCase(k))}</span>`).join('')}</div>`;}

function renderTiming(c){
  const f=c.narrative?.forecast_interpretations||{};
  const rows=c.performance?.monthly||[];
  const domains=c.performance?.domains||[];
  const peaks=domains.map(d=>`<div class="peak-panel"><b>${esc(titleCase(d))}</b>${(c.performance.peaks[d]||[]).slice(0,5).map(x=>`<div class="peak-row"><b>${esc(x.date)}</b><span>${x.score}/100</span><small>${esc(x.dasha)}</small></div>`).join('')}</div>`).join('');
  const renderRows=(arr)=>`<div class="forecast-interpret-list">${(arr||[]).slice(0,320).map(x=>`<details class="forecast-row"><summary><b>${esc(x.date||x.year)}</b><span>${esc((x.focus||[]).join(' · '))}</span><em>${esc(x.dasha||'')}</em></summary><p><b>Interpretation:</b> ${esc(x.interpretation||'')}</p>${x.interpretation_depth?`<div class="interpretation-depth"><p><b>Summary:</b> ${esc(x.interpretation_depth.summary||'')}</p><p><b>Mechanism:</b> ${esc(x.interpretation_depth.mechanism||'')}</p><p><b>Cross-confirmation:</b> ${esc(x.interpretation_depth.cross_confirmation||'')}</p></div>`:''}${(x.deep_rules||[]).length?`<p><b>Additional corpus matches:</b> ${esc(x.deep_rules.join(' · '))}</p>`:''}</details>`).join('')}</div>`;
  $('personal-timing').innerHTML=`<div class="section"><div class="section-heading"><div><span class="eyebrow">DYNAMIC FORECAST</span><h3>${esc(c.forecast.amount)} ${esc(c.forecast.unit)} · ${esc(c.forecast.granularity)}</h3><p class="muted">${esc(c.forecast.start)} → ${esc(c.forecast.end)}</p></div></div><div class="chart-card dark-chart">${lineChart(rows,domains)}${chartLegend(domains)}<p class="chart-note"><b>How to read the colours:</b> each colour is one life-area activation series. Higher values mean the configured Jyotish timing rules are more strongly activated for that domain on that date. The colour identifies the life area; the score is a deterministic rule output.</p></div></div><div class="section"><h3>Peak activation windows</h3><div class="peak-grid">${peaks}</div></div><div class="section"><h3>Week-by-week interpretation</h3>${renderRows(f.weekly)}</div><div class="section"><h3>Month-by-month interpretation</h3>${renderRows(f.monthly)}</div><div class="section"><h3>Year-by-year interpretation</h3>${renderRows(f.yearly)}</div>`;
}
function renderPredictions(x){
  const c=x.chart||{}, p=x.narrative?.predictions||{};
  const rows=(p.predictions||[]);
  const methods=(p.methods||[]).map(m=>`<span class="method-chip">${esc(m)}</span>`).join('');
  const summary=(p.domain_summary||[]).map(z=>`<article class="prediction-card"><div class="interpret-head"><b>${esc(z.domain.replaceAll('_',' '))}</b><span>${esc(z.date)} · ${esc(String(z.score))}</span></div><p>${esc(z.interpretation)}</p></article>`).join('');
  const cards=rows.map(z=>{const dp=(z.domain_predictions||[]).slice(0,20).map(d=>`<div class="prediction-domain"><div class="interpret-head"><b>${esc(titleCase(d.domain))}</b><span>${esc(String(d.score))}/100 · ${esc(d.strength)}</span></div><p>${esc(d.prediction)}</p></div>`).join(''); const dv=(z.divisional_evidence||[]).map(v=>`<div class="prediction-varga"><b>${esc(v.varga)} · ${esc(v.purpose)}</b><p>${esc(v.text)}</p></div>`).join(''); return `<details class="forecast-row prediction-row"><summary><b>${esc(z.date)}</b><span>${esc((z.focus||[]).join(' · ')||'Integrated activation')}</span><em>${esc(z.dasha||'—')}</em></summary><div class="prediction-detail"><p class="direct-reading"><b>Direct result:</b> ${esc(z.interpretation||'')}</p><div class="prediction-domain-grid">${dp}</div>${dv?`<div class="prediction-varga-grid">${dv}</div>`:''}<div class="mini-list"><span>Prediction mode: ${esc(z.prediction_mode||'deterministic-rule')}</span><span>Evidence depth: ${esc(z.evidence_depth||'—')}</span><span>Jupiter H${esc(z.transit_houses?.Jupiter??'—')} · ${(z.transit_nakshatra?.Jupiter?.name||'—')} P${esc(z.transit_nakshatra?.Jupiter?.pada??'—')}</span><span>Saturn H${esc(z.transit_houses?.Saturn??'—')} · ${(z.transit_nakshatra?.Saturn?.name||'—')} P${esc(z.transit_nakshatra?.Saturn?.pada??'—')}</span><span>Rahu H${esc(z.transit_houses?.Rahu??'—')} · Ketu H${esc(z.transit_houses?.Ketu??'—')}</span>${(z.evidence||[]).slice(0,12).map(e=>`<span>${esc(e.type||'Evidence')}: ${esc(e.planet||e.system||e.name||e.value||'')}</span>`).join('')}</div></div></details>`}).join('');
  $('personal-predictions').innerHTML=`<div class="section prediction-hero"><span class="eyebrow">ADVANCED PREDICTIVE ASTROLOGY</span><h3>${esc(p.horizon?.amount||'')} ${esc(p.horizon?.unit||'')} · ${esc(p.granularity||'monthly')}</h3><p class="reading-paragraph">This section synthesizes the selected forecast horizon using the active Vimshottari hierarchy, slow-planet transits, transit Nakshatra/Pada, Ashtakavarga, alternative Dasha layers, Sudarshana and exact astronomical events available in the calculated horizon.</p><div class="method-chips">${methods}</div></div><div class="section"><h3>Strongest calculated life-area periods</h3><div class="interpret-grid">${summary||'<p class="muted">No domain summary is available for this horizon.</p>'}</div></div><div class="section"><h3>${esc((p.granularity||'forecast').replace(/(^|\s)\S/g,m=>m.toUpperCase()))}-by-${esc((p.granularity||'forecast'))} predictions</h3><p class="muted">${esc(p.count||0)} calculated periods are available. Expand a period to see the Dasha, transit, Nakshatra/Pada and advanced timing evidence behind the interpretation.</p><div class="forecast-interpret-list">${cards||'<p class="muted">No calculated prediction rows are available.</p>'}</div></div>`;
}
function renderPanchanga(c){const p=c.panchanga;$('personal-panchanga').innerHTML=`<div class="metric-grid">${[['Weekday',p.weekday],['Tithi',`${p.tithi} · ${p.paksha}`],['Nakshatra',`${p.nakshatra} · P${p.nakshatra_pada}`],['Yoga',p.yoga_number],['Karana',p.karana],['Elongation',deg(p.elongation)]].map(x=>`<div class="metric"><span>${esc(x[0])}</span><b>${esc(x[1])}</b></div>`).join('')}</div><p class="muted">Panchanga values are calculated for the recorded birth moment using the same sidereal astronomical layer.</p>`}
function renderAdvanced(c){
 const kar=(c.chara_karakas?.karakas||[]).map(x=>row([esc(x.role),esc(x.planet),x.degree_in_sign])).join('');
 const ar=Object.entries(c.arudha_padas||{}).map(([k,x])=>row([k,x.house,esc(x.sign),esc(x.lord)])).join('');
 const bav=Object.entries(c.ashtakavarga_classical?.bav||{}).map(([p,v])=>row([esc(p),...v])).join('');
 const tri=Object.entries(c.ashtakavarga_classical?.trikona_shodhana||{}).map(([p,v])=>row([esc(p),...v])).join('');
 const eka=Object.entries(c.ashtakavarga_classical?.ekadhipatya_shodhana||{}).map(([p,v])=>row([esc(p),...v])).join('');
 const sh=Object.entries(c.shadbala?.planets||{}).map(([p,d])=>row([esc(p),d.sthana,d.dig,d.kala,d.cheshta,d.naisargika,d.drik,d.rupas,d.strength_pct+'%',esc(d.classification)])).join('');
 const ev=(c.exact_astronomical_events?.events||[]).slice(0,120).map(x=>row([esc(x.type),esc(x.planet||''),esc(x.station||''),esc(x.from_sign||''),esc(x.to_sign||''),esc(x.datetime)])).join('');
 const ec=(c.eclipses?.events||[]).slice(0,40).map(x=>row([esc(x.type),esc(x.maximum),x.flags])).join('');
 const ds=(c.advanced_timing?.chara_dasha?.periods||[]).slice(0,24).map(x=>row([esc(x.sign),esc(x.start).slice(0,10),esc(x.end).slice(0,10)])).join('');
 const taj=(c.tajaka?.years||[]).slice(0,10).map(x=>row([x.year,esc(x.solar_return||''),esc(x.lagna_sign||''),esc(x.muntha_sign||''),esc(x.year_lord||'')])).join('');
 $('personal-advanced').innerHTML=`
 <div class="section"><h3>Selected school: ${esc(c.methodology?.school_label||'Multi-school synthesis')}</h3><p class="muted">${esc(c.methodology?.school_profile?.notes||c.advanced_timing?.school_profile?.notes||'Independent school layers are shown side by side.')}</p></div>
 <div class="section"><h3>Shadbala screening estimate</h3><p class="muted">Six-component approximate screen in virupas/rupas; not a complete canonical Shadbala calculation. Rahu/Ketu excluded. See the method and component limitations before interpreting totals.</p><div class="table-wrap"><table>${th(['Planet','Sthana','Dig','Kala','Cheshta','Naisargika','Drik','Rupas','% min','Class'])}${sh}</table></div></div>
 <div class="section"><h3>Ashtakavarga · BAV / SAV / Shodhya Pinda</h3><p class="muted">BAV and SAV use the standard contributor tables; graha-wise Trikona and Ekadhipatya reductions and Pinda values use documented BPHS/PVR-style assumptions. School conventions can differ.</p><div class="table-wrap"><table>${th(['Planet',...signs])}${bav}<tr><th>SAV</th>${(c.ashtakavarga_classical?.sav||[]).map(x=>`<th>${x}</th>`).join('')}</tr></table></div><h4>Trikona Shodhana</h4><div class="table-wrap"><table>${th(['Planet',...signs])}${tri}</table></div><h4>Ekadhipatya Shodhana</h4><div class="table-wrap"><table>${th(['Planet',...signs])}${eka}</table></div><p class="muted">Total SAV bindus: ${esc(c.ashtakavarga_classical?.validation?.actual_sav_total??'—')} (expected standard total 337 when standard contributor tables are selected).</p></div>
 <div class="section"><h3>Jaimini Chara Karakas</h3><div class="table-wrap"><table>${th(['Role','Planet','Degree'])}${kar}</table></div></div>
 <div class="section"><h3>Arudha Padas</h3><div class="table-wrap"><table>${th(['Pada','House','Sign','Lord'])}${ar}</table></div></div>
 <div class="section"><h3>Jaimini / alternative Dasha layers</h3><div class="table-wrap"><table>${th(['Chara sign','Start','End'])}${ds}</table></div><p class="muted">Additional systems available: Ashtottari, Yogini, Narayana, Kalachakra and Sudarshana Chakra. Conditional/lineage-specific rules are explicitly labelled.</p></div>
 <div class="section"><h3>Tajaka / Varshaphala annual returns</h3><div class="table-wrap"><table>${th(['Year','Solar return','Return Lagna','Muntha','Year lord'])}${taj}</table></div></div>
 <div class="section"><h3>Exact astronomical timing events</h3><div class="table-wrap"><table>${th(['Type','Planet','Station','From','To','Datetime'])}${ev}</table></div><h4>Eclipses</h4><div class="table-wrap"><table>${th(['Type','Maximum','Flags'])}${ec}</table></div></div>
 <div class="section"><h3>Validation audit</h3><p class="muted">${c.validation_audit?.passed||0}/${c.validation_audit?.total||0} internal consistency checks passed. This validates calculations and data structure, not empirical forecast accuracy.</p></div>`;
}
function renderNumerology(c){
  const n=c.numerology||{}, core=n.core||{}, na=n.name_analysis||{}, meanings=n.number_meanings||{};
  const cards=[['Life Path',core.life_path,core.life_path_theme],['Birthday',core.birthday,'day expression'],['Destiny / Expression',core.destiny_expression,'name-driven direction'],['Soul Urge',core.soul_urge,'inner motivation'],['Personality',core.personality,'outer presentation'],['Maturity',core.maturity,'later-life synthesis'],['Chaldean Name',core.chaldean_name,'cross-check']];
  const meaningRows=Object.entries(meanings).map(([k,v])=>row([k,esc(v.strength||''),esc(v.shadow||''),esc(v.career||'')])).join('');
  const freq=Object.entries(na.letter_frequency||{}).map(([k,v])=>row([k,v])).join('');
  const yearly=(n.personal_years||[]).map(y=>row([y.year,y.number,esc(y.theme),esc(y.prediction||''),(y.months||[]).filter(m=>m.number===y.number).map(m=>m.month).join(', ')||'—'])).join('');
  $('personal-numerology').innerHTML=`<div class="section"><h3>Detailed Numerology Profile</h3><p class="reading-paragraph">The numerology layer now combines core birth-date numbers, name numbers, master-number preservation, name-letter structure, karmic lessons, repeated-number emphasis, pinnacles, challenges, long cycles and personal year/month/day timing.</p><div class="metric-grid">${cards.map(x=>`<div class="metric"><span>${esc(x[0])}</span><b>${esc(x[1])}</b><small>${esc(x[2])}</small></div>`).join('')}</div></div>
  <div class="section"><h3>Name Structure</h3><div class="cols"><div><p><b>Hidden passion:</b> ${esc((na.hidden_passion||[]).join(', ')||'none')}</p><p><b>Karmic lessons:</b> ${esc((na.karmic_lessons||[]).join(', ')||'none')}</p><p><b>First vowel:</b> ${esc(na.first_vowel?.letter||'—')} · ${esc(na.first_vowel?.number||'—')}</p><p><b>First consonant:</b> ${esc(na.first_consonant?.letter||'—')} · ${esc(na.first_consonant?.number||'—')}</p><p><b>Repeated-number emphasis:</b> ${esc((na.repeated_numbers||[]).join(', ')||'none')}</p><p><b>Name length:</b> ${esc(na.name_length||0)}</p></div><div><h4>Letter frequency by number</h4><div class="table-wrap"><table>${th(['Number','Count'])}${freq}</table></div></div></div></div>
  <div class="section"><h3>Numerology in plain language</h3><div class="interpret-grid">${Object.entries(n.interpretive_profiles||{}).map(([k,v])=>`<article class="interpret-card"><div class="interpret-head"><b>${esc(k)}</b><span>Life pattern</span></div><p>${esc(v.plain||'')}</p><p><b>Relationships:</b> ${esc(v.relationships||'')}</p><p><b>Money:</b> ${esc(v.money||'')}</p><p><b>Career:</b> ${esc(v.career||'')}</p></article>`).join('')}</div></div>
  <div class="section"><h3>Personal-year predictions</h3><div class="interpret-grid">${(n.personal_years||[]).map(y=>`<article class="interpret-card"><div class="interpret-head"><b>${esc(y.year)} · Number ${esc(y.number)}</b><span>${esc(y.theme)}</span></div><p>${esc(y.interpretation||'')}</p><p><b>Prediction:</b> ${esc(y.prediction||'')}</p></article>`).join('')}</div></div>
  <div class="section"><h3>Number Strengths, Shadows & Career Expressions</h3><div class="table-wrap"><table>${th(['Number','Strength','Shadow','Career expression'])}${meaningRows}</table></div></div>
  <div class="section"><h3>Pinnacles & Challenges</h3><div class="cols"><div class="table-wrap"><table>${th(['Pinnacle','Number'])}${Object.entries(n.pinnacles||{}).map(([k,v])=>row([esc(titleCase(k)),v])).join('')}</table></div><div class="table-wrap"><table>${th(['Challenge','Number'])}${Object.entries(n.challenges||{}).map(([k,v])=>row([esc(titleCase(k)),v])).join('')}</table></div></div></div>
  <div class="section"><h3>Long Cycles</h3><div class="interpret-grid">${Object.entries(n.long_cycles||{}).map(([k,v])=>`<article class="interpret-card"><div class="interpret-head"><b>${esc(titleCase(k))}</b><span>${esc(v.number)}</span></div><p>${esc(v.theme)}</p></article>`).join('')}</div></div>
  <div class="section"><h3>Personal-Year Forecast</h3><div class="table-wrap"><table>${th(['Year','Number','Theme','Prediction','Strong months'])}${yearly}</table></div></div>
  <div class="section"><h3>Method</h3>${(n.method_notes||[]).map(x=>`<p class="note">${esc(x)}</p>`).join('')}</div>`;
}
function renderInterpretations(x){
  const n=x.narrative||{}, i=n.interpretations||{};
  const placement=(i.planetary||[]).map(z=>`<article class="interpret-card"><div class="interpret-head"><b>${esc(z.planet)}</b><span>${esc(z.sign)} · House ${z.house}</span></div><b>Interpretation</b><p>${esc(z.text)}</p></article>`).join('');
  const nak=(i.nakshatra||[]).map(z=>`<article class="interpret-card"><div class="interpret-head"><b>${esc(z.planet)}</b><span>${esc(z.name)} · Pada ${z.pada}</span></div><b>Interpretation</b><p>${esc(z.text)}</p></article>`).join('');
  const houses=(i.house_themes||[]).map(z=>`<article class="interpret-card"><div class="interpret-head"><b>House ${z.house}</b><span>${esc(z.sign)} · Lord ${esc(z.lord)}</span></div><b>Interpretation</b><p>${esc(z.text)}</p></article>`).join('');
  const dignity=(i.dignity||[]).map(z=>`<article class="interpret-card"><div class="interpret-head"><b>${esc(z.planet)}</b><span>${esc(z.dignity)}</span></div><b>Interpretation</b><p>${esc(z.text)}</p></article>`).join('');
  const divs=(i.divisional||[]).map(z=>`<article class="interpret-card"><div class="interpret-head"><b>${esc(z.division)} · ${esc(z.name)}</b><span>Lagna ${esc(z.lagna)}</span></div><b>Interpretation</b><p>${esc(z.text)}</p></article>`).join('');
  const integrated=(i.integrated_factor_interpretations||[]).map(z=>`<article class="interpret-card"><div class="interpret-head"><b>${esc(z.planet)}</b><span>${esc(z.natal?.sign||'')} · H${esc(z.natal?.house||'')} · ${esc(z.natal?.nakshatra||'')} Pada ${esc(z.natal?.pada||'')}</span></div><p>${esc(z.interpretation)}</p></article>`).join('');
  const yogaFruit=(i.yoga_fruitification_interpretations||[]).map(z=>`<article class="interpret-card"><div class="interpret-head"><b>${esc(z.yoga)}</b><span>${esc(z.date)}</span></div><p>${esc(z.interpretation)}</p></article>`).join('');
  const career=(n.career_options||[]).map(z=>`<article class="interpret-card"><div class="interpret-head"><b>${esc(z.option)}</b><span>Fit ${z.score}/100</span></div><b>Interpretation</b><p>${esc(z.reason)}</p></article>`).join('');
  const timingBlock=(title,obj)=>`<div class="section"><h3>${title}</h3><p class="reading-paragraph">${esc(obj?.interpretation||'')}</p><div class="timing-list">${(obj?.windows||[]).slice(0,12).map(w=>`<div class="event"><b>${esc(w.date)}</b><span>${esc(w.dasha||'—')}</span><strong>${w.score}/100</strong></div>`).join('')}</div></div>`;
  $('personal-interpretation').innerHTML=`<div class="section interpretation-hero"><span class="eyebrow">JYOTISH INTERPRETATION ENGINE</span><h3>What the chart means</h3><p>Every interpretation below is tied to a computed chart factor and is written as an explicit reading rather than a raw data dump.</p><div class="interpret-count"><b>${i.reference_corpus?.entries||0}</b><span>runtime interpretation rules</span></div></div><div class="section"><h3>Executive interpretation</h3>${(i.executive||[]).map(t=>`<p class="reading-paragraph">${esc(t)}</p>`).join('')}</div><div class="section"><h3>Current transits</h3>${(i.transit_interpretations?.current||[]).map(z=>`<article class="interpret-card"><div class="interpret-head"><b>${esc(z.planet)}</b><span>${esc(z.sign)} · House ${z.house}</span></div><p>${esc(z.interpretation)}</p></article>`).join('')}<h4>Coming transit milestones</h4>${(i.transit_interpretations?.future_milestones||[]).slice(0,20).map(z=>`<article class="interpret-card"><div class="interpret-head"><b>${esc(z.planet)}</b><span>${esc(z.date)} · H${z.to_house}</span></div><p>${esc(z.interpretation)}</p></article>`).join('')}</div><div class="section"><h3>Past, current and future Mahadashas</h3><div class="table-wrap"><table>${th(['Phase','Lord','Start','End'])}${(i.dasha_context?.previous_mahadashas||[]).map(z=>row(['Past',esc(z.lord),esc(z.start).slice(0,10),esc(z.end).slice(0,10)])).join('')}${i.dasha_context?.current_mahadasha?row(['Current',esc(i.dasha_context.current_mahadasha.lord),esc(i.dasha_context.current_mahadasha.start).slice(0,10),esc(i.dasha_context.current_mahadasha.end).slice(0,10)]):''}${(i.dasha_context?.next_mahadashas||[]).map(z=>row(['Future',esc(z.lord),esc(z.start).slice(0,10),esc(z.end).slice(0,10)])).join('')}</table></div></div><div class="section"><h3>Divisional chart interpretations</h3><div class="interpret-grid">${divs}</div></div><div class="section"><h3>Spouse / Long-Term Partner Profile</h3><p class="reading-paragraph">${esc(i.spouse_profile?.reading||'')}</p></div><div class="section"><h3>Detailed Career Fields</h3><div class="interpret-grid">${(i.career_fields||[]).map(z=>`<article class="interpret-card"><div class="interpret-head"><b>${esc(z.field)}</b><span>${esc(z.score)}</span></div><p>Supporting factors: ${esc((z.factors||[]).join(', '))}</p></article>`).join('')}</div></div><div class="section"><h3>Integrated placement + Nakshatra/Pada + Dasha + Transit interpretations</h3><div class="interpret-grid">${integrated}</div></div><div class="section"><h3>Yoga fruitification candidates</h3><p class="muted">Only dates produced by the calculated dasha/transit evidence are shown.</p><div class="interpret-grid">${yogaFruit||'<p class="muted">No qualifying dates were found in the calculated horizon.</p>'}</div></div><div class="section"><h3>Career options indicated by the chart</h3><div class="interpret-grid">${career}</div></div>${timingBlock('Marriage timing interpretation',n.marriage_timing)}${timingBlock('Job-change timing interpretation',n.job_change_timing)}${timingBlock('Business timing interpretation',n.business_timing)}<div class="section"><h3>Personalised gemstone recommendations</h3><p class="muted">Recommendations are ranked from this chart's functional lordship, dignity, strength, D9 placement and active timing.</p><div class="interpret-grid">${(i.gemstone_recommendations||[]).map(z=>`<article class="interpret-card"><div class="interpret-head"><b>${esc(z.gemstone)}</b><span>${esc(z.planet)} · ${esc(z.priority||'')}</span></div><p>${esc(z.reason)}</p><small><b>Chart role:</b> ${esc(z.chart_role||'')}<br><b>Supporting factors:</b> ${esc((z.supporting_factors||[]).join('; '))}${(z.cautions||[]).length?`<br><b>Conditional factors:</b> ${esc(z.cautions.join('; '))}`:''}</small></article>`).join('')}</div></div><div class="section"><h3>Dasha significance</h3><div class="interpret-grid">${(i.dasha_interpretations||[]).map(z=>`<article class="interpret-card"><div class="interpret-head"><b>${esc(z.level_name)} · ${esc(z.lord)}</b><span>${esc(String(z.start||'').slice(0,10))}</span></div><p>${esc(z.text)}</p></article>`).join('')}</div></div><div class="section"><h3>Dosha significance</h3><div class="interpret-grid">${(i.dosha_interpretations||[]).map(z=>`<article class="interpret-card"><div class="interpret-head"><b>${esc(z.name)}</b><span>${esc(z.severity||'')}</span></div><p>${esc(z.interpretation||'')}</p></article>`).join('')}</div></div><div class="section"><h3>Planet-by-planet interpretations</h3><div class="interpret-grid">${placement}</div></div><div class="section"><h3>Nakshatra + Pada interpretations</h3><div class="interpret-grid">${nak}</div></div><div class="section"><h3>House interpretations</h3><div class="interpret-grid">${houses}</div></div><div class="section"><h3>Dignity interpretations</h3><div class="interpret-grid">${dignity}</div></div>`;
}
function renderAI(x){
  const c=x?.chart||{};
  const aiAuto=x.narrative?.ai_interpretation||x.chart?.ai_interpretation||{}; $('personal-ai').innerHTML=`<div class="section ai-hero"><span class="eyebrow">AI INTERPRETATION</span><h3>Automatic AI reading</h3><p class="reading-paragraph">AI interpretation runs automatically when credentials are configured in the backend.</p><div class="ai-status ${aiAuto.status==='generated'?'ok':'note'}"><b>${esc(aiAuto.status||'unavailable')}</b><span>${esc(aiAuto.message||'AI interpretation is ready below.')}</span></div>${aiAuto.status==='generated'?`<div class="section ai-generated"><h4>AI-generated interpretation</h4><div class="ai-reading">${esc(aiAuto.text||'')}</div></div>`:''}<div class="ai-actions"><button class="primary" type="button" id="aiBuildBtn">Prepare AI JSON</button><button class="ghost" type="button" id="aiCopyPrompt">Copy prompt</button><button class="ghost" type="button" id="aiCopyJson">Copy JSON</button><button class="ghost" type="button" id="aiDownloadJson">Download JSON</button></div><div id="aiOutput" class="ai-output"><p class="muted">Choose an action above. The JSON is generated from this exact chart.</p></div></div>`;
  let aiPack=null;
  const build=async()=>{ const out=$('aiOutput'); out.innerHTML='<p class="muted">Building AI interpretation package…</p>'; try{ const payload={...x.payload,forecast_granularity:x.payload?.forecast_granularity||null}; const r=await fetch('/api/personal/ai-payload',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),cache:'no-store'}); aiPack=await readJsonResponse(r); out.innerHTML=`<div class="ai-preview"><b>AI package ready</b><span>${Object.keys(aiPack.astrological_data||{}).length} data groups · ${JSON.stringify(aiPack).length.toLocaleString()} characters</span><p>${esc(aiPack.prompt||'')}</p></div>`; debugLog('AI interpretation package ready','ok'); }catch(e){out.innerHTML=`<p class="note">${esc(e.message)}</p>`;debugLog('AI package failed: '+e.message,'bad');}};
  const copyText=async(text)=>{
    try{
      if(navigator.clipboard?.writeText){await navigator.clipboard.writeText(text);}
      else {
        const field=document.createElement('textarea');field.value=text;field.setAttribute('readonly','');field.style.position='fixed';field.style.opacity='0';document.body.appendChild(field);field.select();
        const copied=document.execCommand('copy');field.remove();if(!copied)throw new Error('Clipboard access is unavailable in this browser context.');
      }
      $('aiOutput').insertAdjacentHTML('beforeend','<p class="muted">Copied to clipboard.</p>');
    }catch(error){$('aiOutput').insertAdjacentHTML('beforeend',`<p class="note">${esc(error.message||'Clipboard access is unavailable. You can select the text in the preview and copy it manually.')}</p>`);}
  };
  $('aiBuildBtn').onclick=build;
  $('aiCopyPrompt').onclick=async()=>{if(!aiPack) await build(); if(aiPack) await copyText(aiPack.prompt||'');};
  $('aiCopyJson').onclick=async()=>{if(!aiPack) await build(); if(aiPack) await copyText(JSON.stringify(aiPack,null,2));};
  $('aiDownloadJson').onclick=async()=>{if(!aiPack) await build(); if(!aiPack)return; const blob=new Blob([JSON.stringify(aiPack,null,2)],{type:'application/json'}); const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='jyotish-lab-ai-interpretation.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
}

function renderChat(x){
  $('personal-chat').innerHTML=`<div class="section chat-section"><span class="eyebrow">JYOTISH CONVERSATIONAL GUIDE</span><h3>Ask questions about this chart</h3><p class="reading-paragraph">Ask about career, marriage, dashas, yogas, doshas, gemstones, transits, Vargas or a specific period. The answer is grounded in the generated interpretation data.</p><div id="chatMessages" class="chat-messages"><div class="chat-bubble assistant">Your Kundali is loaded. Ask me what a Dasha, Yoga, transit, Nakshatra or timing window means for this chart.</div></div><div class="chat-compose"><textarea id="chatQuestion" rows="3" placeholder="e.g. What can the current Mahadasha change in my career?"></textarea><button id="chatSend" class="primary" type="button">Ask Jyotish</button></div><div id="chatStatus" class="muted"></div></div>`;
  const send=async()=>{const q=$('chatQuestion').value.trim();if(!q)return;const box=$('chatMessages');box.insertAdjacentHTML('beforeend',`<div class="chat-bubble user">${esc(q)}</div>`);const history=[...box.querySelectorAll('.chat-bubble')].slice(-8).map(el=>({role:el.classList.contains('user')?'user':'assistant',content:el.textContent||''}));$('chatQuestion').value='';$('chatStatus').textContent='Reading the chart interpretation…';$('chatSend').disabled=true;try{const r=await fetch('/api/personal/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q,birth:x.payload,history})});const d=await readJsonResponse(r);const text=d.text||d.message||'No answer returned.';box.insertAdjacentHTML('beforeend',`<div class="chat-bubble assistant">${esc(text)}</div>`);$('chatStatus').textContent='Deterministic chart answer used.';debugLog('Chat answer ready: '+d.status,'ok');}catch(e){$('chatStatus').textContent=e.message;debugLog('Chat failed: '+e.message,'bad')}finally{$('chatSend').disabled=false}};
  $('chatSend').onclick=send;$('chatQuestion').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}});
}

async function mundaneBacktest(){
  const panel=$('mundaneBacktest'),button=document.querySelector('[data-action="mundane-backtest"]');
  if(!panel)return;
  if(button?.disabled)return;
  if(button)button.disabled=true;
  panel.classList.remove('hidden'); panel.innerHTML='<div class="section"><h3>Running retrospective signal coverage…</h3><p class="muted">Testing the bundled historical event corpus. This is not a proof of predictive accuracy.</p></div>';
  try{
    const response=await fetch('/api/mundane/backtest?limit=100&window_days=15');
    const data=await readJsonResponse(response);
    const rows=(data.rows||[]).slice(0,120).map(x=>row([esc(x.country),esc(x.event),esc(x.date),esc(x.event_type),esc(x.peak_signal),x.covered?'Yes':'No',esc((x.best_triggers||[]).join('; '))])).join('');
    panel.innerHTML=`<div class="section"><h3>Retrospective mundane signal coverage</h3><div class="metric-grid"><div class="metric"><span>Events tested</span><b>${esc(data.events_tested)}</b></div><div class="metric"><span>Covered</span><b>${esc(data.covered_events)}</b></div><div class="metric"><span>Coverage</span><b>${esc(data.coverage_pct)}%</b></div><div class="metric"><span>Window</span><b>±${esc(data.window_days_each_side)} days</b></div></div><p class="note">${esc(data.interpretation)}</p><div class="table-wrap"><table>${th(['Country','Event','Date','Type','Peak signal','Covered','Triggers'])}${rows}</table></div></div>`;
  }catch(error){panel.innerHTML=`<p class="note">${esc(error.message||'Historical backtest failed.')}</p>`;}
  finally{if(button)button.disabled=false;}
}

// Personal tabs are rendered lazily to keep the browser responsive.
let placeSearchTimer=null;
// Native date/time picker helpers: manual typing remains available, while a
// calendar/clock popup is opened when the adjacent picker button is clicked.
function openNativePicker(id){ const el=$(id); if(!el) return; try{ if(typeof el.showPicker==='function'){ el.showPicker(); return; } }catch(e){} el.focus(); }
document.querySelectorAll('[data-picker-for]').forEach(btn=>btn.addEventListener('click',()=>openNativePicker(btn.dataset.pickerFor)));

let placeResultsCache=[];
async function searchPlacesLive(){
  const q=$('place').value.trim();
  const box=$('placeSuggestions');
  if(!q){ box.classList.add('hidden'); box.innerHTML=''; return; }
  box.classList.remove('hidden'); box.innerHTML='<div class="place-searching">Searching locations…</div>';
  try {
    const r=await fetch('/api/place?q='+encodeURIComponent(q));
    const d=await r.json();
    placeResultsCache=d.results||[];
    if(!placeResultsCache.length){ box.innerHTML='<div class="place-searching">No location found. You can use Advanced location details.</div>'; return; }
    box.innerHTML=placeResultsCache.map((x,i)=>`<button type="button" class="place-option" data-place-index="${i}"><span>⌖</span><div><b>${esc(x.display_name||'Location')}</b><small>${esc(x.timezone||'Timezone unavailable')}</small></div></button>`).join('');
    box.querySelectorAll('.place-option').forEach(btn=>btn.addEventListener('click',()=>applyPlaceResult(placeResultsCache[Number(btn.dataset.placeIndex)])));
  } catch(err){ box.innerHTML='<div class="place-searching">Location search failed. Check the backend terminal.</div>'; console.error('Place search failed',err); }
}
function applyPlaceResult(x){
  if(!x) return;
  selectedPlaceResolved=true;
  $('place').value=(x.display_name||'').replace(', preset','');
  $('lat').value=x.latitude; $('lon').value=x.longitude;
  if(x.timezone){ $('tz').value=x.timezone; }
  $('placeSuggestions').classList.add('hidden'); $('placeSuggestions').innerHTML='';
  $('resolvedPlace').classList.remove('hidden');
  $('resolvedPlaceName').textContent=$('place').value;
  $('resolvedPlaceMeta').textContent=`${Number(x.latitude).toFixed(4)}°, ${Number(x.longitude).toFixed(4)}° · ${x.timezone||'Timezone not resolved'}`;
  $('status').textContent=x.timezone_needs_confirmation ? 'Location selected. Please confirm timezone in Advanced location details.' : 'Location selected — coordinates and timezone filled automatically.';
}
$('place').addEventListener('input',()=>{ selectedPlaceResolved=false; $('resolvedPlace').classList.add('hidden'); clearTimeout(placeSearchTimer); placeSearchTimer=setTimeout(searchPlacesLive,320); });
$('place').addEventListener('focus',()=>{ if($('place').value.trim()) searchPlacesLive(); });
document.addEventListener('click',e=>{ if(!e.target.closest('.place-autocomplete')) $('placeSuggestions')?.classList.add('hidden'); });
$('clearPlace').addEventListener('click',()=>{ selectedPlaceResolved=false; $('place').value=''; $('resolvedPlace').classList.add('hidden'); $('place').focus(); });

function loadDemo(){
  selectedPlaceResolved=true; $('name').value='Demo Native'; $('birthDatePicker').value='1990-08-15'; $('birthTimePicker').value='10:30'; syncBirthDateTime(); $('place').value='Kolkata'; $('lat').value='22.5726'; $('lon').value='88.3639'; $('tz').value='Asia/Kolkata'; $('resolvedPlace').classList.remove('hidden'); $('resolvedPlaceName').textContent='Kolkata'; $('resolvedPlaceMeta').textContent='22.5726°, 88.3639° · Asia/Kolkata'; $('forecastAmount').value='5'; $('forecastUnit').value='years'; $('school').value='synthesis';
  $('status').textContent='Demo data loaded. Click Generate complete Kundali.';
}
async function downloadPdf(){
  if(!latest){ $('status').textContent='Generate a personal chart first.'; return; }
  const p=latest.payload;
  try { const r=await fetch('/api/personal/report.pdf',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(p)}); if(!r.ok){const d=await r.json().catch(()=>({}));throw new Error(d.detail||'PDF export failed');} const b=await r.blob(), a=document.createElement('a'); a.href=URL.createObjectURL(b); a.download='jyotish-lab-personal-report.pdf'; a.click(); setTimeout(()=>URL.revokeObjectURL(a.href),1000); $('status').textContent='Personal PDF exported.'; } catch(err){ $('status').textContent=err.message; }
}

function mundaneValue(v, fallback=''){
  if(v==null)return fallback;
  if(typeof v==='object') return v.event_name||v.name||v.title||v.text||v.description||JSON.stringify(v);
  return String(v);
}
function renderMundane(x){
  const a=x.analysis||{}, h=x.historical||{}, f=x.forecast||{};
  const near=Array.isArray(f.near_term)?f.near_term:(f.near_term?.monthly||[]);
  const long=Array.isArray(f.long_term)?f.long_term:(f.long_term?.monthly||[]);
  const peaks=f.peaks||[];
  $('mundaneResults').classList.remove('hidden');
  const pos=Object.entries(a.positions||{}).map(([p,d])=>row([esc(p+(d.retrograde?' (R)':'')),esc(d.sign||''),d.degree_in_sign!=null?deg(d.degree_in_sign):''])).join('');
  const hist=(h.results||[]).slice(0,40).map(r=>{
    const e=typeof r.event==='object'?(r.event||{}):{};
    return row([esc(r.country||e.country||''),esc(mundaneValue(r.event,e.event_name||'')),esc(r.date||e.local_date||''),esc(r.event_type||e.event_type||''),r.score??'',esc((r.matches||[]).join('; '))]);
  }).join('');
  const analogueRows=(arr)=>arr.slice(0,8).map(z=>`<div class="historical-analogue"><b>${esc(z.date||'')}</b><span>${esc(mundaneValue(z.country||''))} — ${esc(mundaneValue(z.event||''))}</span><small>${esc(z.type||'')} · similarity ${esc(String(z.similarity??''))}${z.matches?.length?' · '+esc(z.matches.join('; ')):''}</small></div>`).join('');
  const eventIndicationRows=(r)=> (r.event_indications||[]).slice(0,12).map(x=>`<div class="event-indication ${x.polarity==='positive'?'positive-event':''}"><div class="event-indication-head"><b>${esc(x.label||x.event_class||'Event indication')}</b><span>${x.polarity==='positive'?'Favourable · ':''}${esc(x.signal_level||'')} · ${esc(String(x.signal_score??''))}/100</span></div><p class="direct-reading">${esc(x.reading||x.astrological_indication||'')}</p><small>${esc((x.trigger?.planet||'')+' '+(x.trigger?.aspect??'')+'° · national house '+(x.trigger?.natal_house??''))}</small>${x.interpretation_depth?`<div class="interpretation-depth"><p><b>Summary:</b> ${esc(x.interpretation_depth.summary||'')}</p><p><b>Mechanism:</b> ${esc(x.interpretation_depth.mechanism||'')}</p><p><b>Cross-check:</b> ${esc(x.interpretation_depth.cross_check||'')}</p></div>`:''}</div>`).join('');
  const forecastRows=(arr,limit)=>{
    const rows=arr.slice().sort((a,b)=>String(a.date||'').localeCompare(String(b.date||'')));
    const signature=r=>JSON.stringify({outcomes:(r.event_indications||[]).map(x=>[x.event_class,x.label,x.signal_score,x.polarity,x.reading]).sort((a,b)=>String(a[0]).localeCompare(String(b[0]))),prediction:r.direct_prediction||'',interpretation:r.blunt_interpretation||''});
    const groups=[];
    for(const r of rows){const sig=signature(r),last=groups[groups.length-1];if(last&&last.sig===sig){last.rows.push(r);}else groups.push({sig,rows:[r]});}
    return groups.slice(0,limit).map(g=>{const r=g.rows[0],last=g.rows[g.rows.length-1],range=g.rows.length>1?`${r.date} – ${last.date}`:(r.date||'');return `<details class="forecast-row"><summary><b>${esc(range)}</b>${g.rows.length>1?`<span>${g.rows.length} consecutive periods · same outcomes</span>`:`<span>Activation ${esc(String(r.activation??''))}/100</span>`}<em>${esc((r.triggers||[]).join(' · '))}</em></summary><div class="prediction-detail">${eventIndicationRows(r)?`<h4>Specific astrological event indications</h4>${eventIndicationRows(r)}`:''}<p class="direct-reading"><b>Forecast synthesis:</b> ${esc(r.direct_prediction||'')}</p><p>${esc(r.blunt_interpretation||'')}</p>${g.rows.length>1?`<p class="muted">This exact outcome set repeats across ${g.rows.length} consecutive forecast dates; shown as one applicable date range.</p>`:''}<h4>Historical manifestations of similar signatures</h4>${analogueRows(r.global_historical_analogues||[])}</div></details>`}).join('');
  };
  const pr=peaks.slice(0,20).map(p=>{const top=(p.global_historical_analogues||[])[0]||{};return row([esc(p.date||''),p.activation??'',esc((p.triggers||[]).join('; ')),esc(`${top.date||''} · ${mundaneValue(top.country||'')} · ${mundaneValue(top.event||'')}`)])}).join('');
  const lagna=a.lagna||{};
  $('mundaneResults').innerHTML=`
  <div class="section mundane-summary"><div class="section-heading"><div><span class="eyebrow">COUNTRY CHART</span><h3>${esc(a.country||f.country||'')}</h3><p class="muted">${esc(a.chart_source?.primary_chart?.event_name||'Corpus chart')} · ${esc(a.event?.local_date||'')} · Lagna ${esc(lagna.sign||'—')}</p></div><div class="method-chip">DETERMINISTIC ASTROLOGICAL EVENT-CLASSIFICATION</div></div><p class="direct-reading"><b>Reading rule:</b> present and future rows are classified into specific astrological event types when a configured planetary + aspect + national-house combination is active. Historical event charts with similar signatures are shown as supporting evidence; an indication is an astrological forecast signal, not a verified fact about the future.</p><div class="metric-grid"><div class="metric"><span>Historical corpus compared</span><b>${esc(h.corpus_size??(h.results||[]).length)}</b></div><div class="metric"><span>Near-term matches</span><b>${near.length}</b></div><div class="metric"><span>Long-range matches</span><b>${long.length}</b></div><div class="metric"><span>Primary country Lagna</span><b>${esc(lagna.sign||'—')}</b></div><div class="metric"><span>Mundane interpretation rules</span><b>${esc(a.interpretation_corpus?.mundane_rule_count??'—')}</b></div><div class="metric"><span>Event classes</span><b>${esc(f.event_class_count??'—')}</b></div><div class="metric"><span>Event combinations</span><b>${esc(f.event_combination_rule_count??'—')}</b></div></div></div>
  <details class="mundane-collapsible"><summary>National planetary signature</summary><div class="section-inner"><div class="table-wrap"><table>${th(['Planet','Sign','Degree'])}${pos}</table></div><p class="note"><b>Country Lagna:</b> ${esc(lagna.sign||'—')} · ${esc(String(lagna.longitude??'—'))}° sidereal.</p></div></details>
  <details class="mundane-collapsible" open><summary>Historical analogues — top 40</summary><div class="section-inner"><p class="muted">Matched using planetary signs, major aspects, houses from the country/event Lagna and Lagna relationship.</p><div class="table-wrap compact-scroll"><table>${th(['Country','Event','Date','Type','Similarity','Matched factors'])}${hist}</table></div></div></details>
  <details class="mundane-collapsible" open><summary>Current / future signature matches — grouped date ranges</summary><div class="section-inner">${forecastRows(near,12)}</div></details>
  <details class="mundane-collapsible"><summary>Long-range signature matches — grouped date ranges</summary><div class="section-inner">${forecastRows(long,18)}</div></details>
  <details class="mundane-collapsible" open><summary>Historical forecast validation</summary><div class="section-inner"><p class="muted">Replays the same forecast engine at historical dates and compares only the following horizon with documented events. No later events are used to generate an earlier forecast.</p><div class="button-row"><button type="button" class="secondary" data-backtest-start="2020-01-01" data-backtest-end="2026-10-03">Israel · 2020–2026</button><button type="button" class="secondary" data-backtest-start="1970-01-01" data-backtest-end="1999-12-31">India · 1970–1999</button></div><div id="mundaneBacktestResult" class="backtest-result muted">Select a historical test range.</div></div></details>
  <details class="mundane-collapsible"><summary>Highest historical matches</summary><div class="section-inner"><div class="table-wrap compact-scroll"><table>${th(['Date','Signature','Closest historical event'])}${pr}</table></div></div></details>`;
  const synthesis=f.leader_country_synthesis;
  if(synthesis){
    const matches=synthesis.corroborations||[]; const lc=synthesis.leader_chart||{}; const lp=lc.planets||{}; const lrows=Object.entries(lp).map(([name,p])=>row([esc(name),esc(p.sign||'—'),p.degree_in_sign??'—',p.retrograde?'R':''])).join('');
    const yogas=lc.yogas||[], doshas=lc.doshas||[];
    $('mundaneResults').insertAdjacentHTML('beforeend', `<details class="mundane-collapsible" open><summary>Country + leader chart synthesis</summary><div class="section-inner"><p><b>${esc(synthesis.leader_name||'Selected leader')}</b> · ${esc(synthesis.data_quality_note||'')}</p><p class="muted">National chart remains the primary collective chart. Leader chart is a separate timing layer, not a proxy for the population or a guarantee of government strength.</p><div class="metric-grid"><div class="metric"><span>Country forecast period</span><b>${esc(synthesis.country_forecast_period?.start||'')} – ${esc(synthesis.country_forecast_period?.end||'')}</b></div><div class="metric"><span>Timing overlaps</span><b>${matches.length}</b></div><div class="metric"><span>Leader Lagna</span><b>${esc(lc.lagna_sign||lc.lagna||'Unavailable')}</b></div><div class="metric"><span>Leader Yogas / Doshas</span><b>${yogas.length} / ${doshas.length}</b></div></div><details class="mundane-collapsible"><summary>Leader planetary placements</summary><div class="table-wrap"><table>${th(['Planet','Sign','Degree in sign','Retrograde'])}${lrows}</table></div></details>${matches.length?`<h4>Overlapping timing signals</h4><div class="table-wrap"><table>${th(['Date','Country event class','Activation','Leader timing rows'])}${matches.slice(0,30).map(m=>row([esc(m.date),esc((m.country_event_types||[]).join(', ')),m.country_activation??'—',m.leader_timing_rows])).join('')}</table></div>`:'<p class="note">No close date overlap found between available country event indications and leader timing rows in this period.</p>'}<ul>${(synthesis.interpretation_limits||[]).map(x=>`<li>${esc(x)}</li>`).join('')}</ul></div></details>`);
  }
}
async function loadMundaneLeaders(){
  try{const d=await getLibraryData();const sel=$('mLeader');if(!sel)return;const custom=sel.querySelector('option[value="__custom__"]');(d.results||[]).filter(p=>p.category==='politician'||p.category==='historical_political').sort((a,b)=>a.name.localeCompare(b.name)).forEach(p=>{const o=document.createElement('option');o.value=p.name;o.textContent=`${p.name}${p.time_status==='unknown'?' · birth time unknown':''}`;sel.insertBefore(o,custom);});}catch(e){console.warn('Leader reference profiles unavailable',e);}
}
$('mLeader')?.addEventListener('change',()=>{$('mLeaderCustom').classList.toggle('hidden',$('mLeader').value!=='__custom__');});
$('mundaneForm').addEventListener('submit',async e=>{
  e.preventDefault(); const ps=$('mPeriodStart').value, pe=$('mPeriodEnd').value; if(Boolean(ps)!==Boolean(pe)||(ps&&pe&&pe<=ps)){ $('mundaneStatus').textContent='Choose both forecast dates, with the end date on or after the start date.'; return;}
  const submitButton=e.submitter||$('mundaneForm').querySelector('button[type="submit"]'); if(submitButton?.disabled)return; if(submitButton)submitButton.disabled=true;
  $('mundaneStatus').textContent='Analyzing country chart, historical analogues and future transits…'; debugLog('Starting mundane country request');
  const payload={country:$('mCountry').value.trim(),period_start_date:$('mPeriodStart').value||null,period_end_date:$('mPeriodEnd').value||null,historical_event_types:$('mTypes').value.split(',').map(x=>x.trim()).filter(Boolean),historical_limit:Number($('mLimit').value),near_term_amount:Number($('mNearAmount').value),near_term_unit:$('mNearUnit').value,long_term_amount:Number($('mLongAmount').value),long_term_unit:$('mLongUnit').value,leader_name:$('mLeader').value&&$('mLeader').value!=='__custom__'?$('mLeader').value:($('mLeader').value==='__custom__'?$('mLeaderName').value.trim():null),leader_custom:$('mLeader').value==='__custom__',leader_dob:$('mLeaderDob').value||null,leader_tob:$('mLeaderTob').value||null,leader_place:$('mLeaderPlace').value.trim()||null,leader_latitude:$('mLeaderLat').value===''?null:Number($('mLeaderLat').value),leader_longitude:$('mLeaderLon').value===''?null:Number($('mLeaderLon').value),leader_timezone:$('mLeaderTz').value.trim()||'Asia/Kolkata',leader_time_status:$('mLeaderTimeStatus').value};
  try { const r=await fetch('/api/mundane/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}); const d=await readJsonResponse(r); mundaneLatest={payload,...d}; renderMundane(mundaneLatest); $('mundaneStatus').textContent='Country analysis ready.'; } catch(err){ console.error(err); $('mundaneStatus').textContent=err.message; } finally {if(submitButton)submitButton.disabled=false;}
});
function mundaneExample(country){$('mCountry').value=country; $('mundaneForm').requestSubmit();}

async function downloadMundanePdf(){
  const status=$('mundaneStatus');
  if(!mundaneLatest?.payload){if(status)status.textContent='Analyze a country first, then export its PDF.';return;}
  const button=document.querySelector('[data-action="download-mundane-pdf"]');
  if(button)button.disabled=true;
  try{
    const response=await fetch('/api/mundane/report.pdf',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(mundaneLatest.payload),cache:'no-store'});
    if(!response.ok){const data=await response.json().catch(()=>({}));throw new Error(data.detail||`PDF export failed (${response.status})`);}
    const blob=await response.blob(),url=URL.createObjectURL(blob),anchor=document.createElement('a');
    anchor.href=url;anchor.download='jyotish-lab-mundane-report.pdf';anchor.click();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
    if(status)status.textContent='Mundane PDF exported.';
  }catch(error){if(status)status.textContent=error.message||'Mundane PDF export failed.';}
  finally{if(button)button.disabled=false;}
}

async function runMundaneBacktest(startDate,endDate,horizonDays=30,stepDays=30){
  const el=$('mundaneBacktestResult'); if(!el)return; el.textContent='Running historical walk-forward validation…';
  try{
    const country=(startDate.startsWith('2020')?'Israel':'India');
    const u=`/api/mundane/historical-backtest?country=${encodeURIComponent(country)}&start_date=${startDate}&end_date=${endDate}&horizon_days=${horizonDays}&step_days=${stepDays}`;
    const r=await fetch(u); const d=await r.json(); if(!r.ok) throw new Error(d.detail||'Backtest failed');
    const rows=(d.rows||[]).filter(x=>(x.actual_events||[]).length||((x.predicted_events||[]).length));
    const body=rows.slice(0,24).map(x=>`<div class="backtest-line"><b>${esc(x.anchor_date)}</b><span>Actual: ${esc((x.actual_events||[]).map(a=>a.event).join('; ')||'—')}</span><span>Hit: ${esc((x.hit_classes||[]).join(', ')||'—')}</span><span>Missed: ${esc((x.missed_classes||[]).join(', ')||'—')}</span></div>`).join('');
    el.innerHTML=`<div class="metric-grid"><div class="metric"><span>Anchors tested</span><b>${esc(d.anchors_tested??'')}</b></div><div class="metric"><span>Actual events</span><b>${esc(d.actual_events_in_corpus??'')}</b></div><div class="metric"><span>Class hits</span><b>${esc(d.class_hits??'')}</b></div><div class="metric"><span>Class hit rate</span><b>${esc(String(d.class_hit_rate_pct??''))}%</b></div></div><div class="backtest-list">${body||'<p>No rows matched.</p>'}</div>`;
  }catch(err){el.textContent=err.message||String(err);}
}

async function syncWorldEvents(){
  const el=$('worldCorpusStatus');
  const token=window.prompt('Administrative token for world-event sync (configured as WORLD_EVENTS_SYNC_TOKEN on the server):');
  if(token===null)return;
  if(!token.trim()){if(el)el.textContent='Sync cancelled: no administrative token supplied.';return;}
  if(el) el.textContent='Syncing source-backed world historical events…'; debugLog('Starting world historical corpus sync');
  try { const r=await fetch('/api/mundane/world-events/sync',{method:'POST',headers:{'X-Admin-Token':token.trim()}}); const d=await readJsonResponse(r); if(!r.ok) throw new Error(d.detail||'World event sync failed'); if(el) el.textContent=`World historical corpus: ${d.loaded||0} events loaded.`; debugLog(`World historical corpus ready: ${d.loaded||0} events`,'ok'); }
  catch(err){ if(el) el.textContent=`World historical corpus unavailable: ${err.message||err}`; debugLog(`World event sync failed: ${err.message||err}`,'bad'); }
}
async function loadWorldEventStatus(){ try { const r=await fetch('/api/mundane/world-events/status'); const d=await r.json(); const el=$('worldCorpusStatus'); if(el) el.textContent=d.ready?`World historical corpus: ${d.loaded} events loaded.`:`World historical corpus: ${d.loaded}/${d.target} loaded — sync requires a server admin token.`; } catch(err){} }
loadWorldEventStatus();


// One delegated handler replaces inline onclick attributes, enabling a strict script-src CSP.
document.addEventListener('click', e => {
  const countryButton=e.target.closest('[data-country-example]');
  if(countryButton){mundaneExample(countryButton.dataset.countryExample);return;}
  const backtestButton=e.target.closest('[data-backtest-start]');
  if(backtestButton){runMundaneBacktest(backtestButton.dataset.backtestStart,backtestButton.dataset.backtestEnd,30,30);return;}
  const action=e.target.closest('[data-action]');
  if(!action)return;
  switch(action.dataset.action){
    case 'load-demo': loadDemo(); break;
    case 'download-personal-pdf': downloadPdf(); break;
    case 'download-mundane-pdf': downloadMundanePdf(); break;
    case 'mundane-backtest': mundaneBacktest(); break;
    case 'sync-world-events': syncWorldEvents(); break;
  }
});

// Reference library bindings. Share the initial corpus request across both workspaces.
function getLibraryData(){
  if(!libraryDataPromise) libraryDataPromise=fetch('/api/library').then(readJsonResponse).catch(err=>{libraryDataPromise=null;throw err;});
  return libraryDataPromise;
}
loadMundaneLeaders();
async function loadLibrary(){
  try { const d=await getLibraryData(); const sel=$('libraryCategory'); if(sel){ const current=sel.value; sel.innerHTML='<option value="">All categories</option>'+(d.categories||[]).map(c=>`<option value="${esc(c)}">${esc(c.replaceAll('_',' '))}</option>`).join(''); sel.value=current; } renderLibrary(d.results||[]); } catch(err){ showUiError('libraryGrid',err,'Library load failed'); }
}
function renderLibrary(items){
  const grid=$('libraryGrid');
  grid.innerHTML='';
  items.forEach(profile=>{
    const card=document.createElement('button');
    card.className='profile-card'; card.type='button';
    card.innerHTML=`<b>${esc(profile.name)}</b><span>${esc(profile.category||'')}</span><small>${esc(profile.dob||'')} · ${esc(profile.place||'')}</small>`;
    card.addEventListener('click',()=>analyzeReference(profile.name));
    grid.appendChild(card);
  });
}
async function analyzeReference(name){
  $('libraryResult').classList.remove('hidden');
  $('libraryResult').innerHTML=`<div class="section loading-card"><span class="spinner"></span><p>Calculating ${esc(name)} reference chart…</p><small>Using the stored public reference profile; if birth time is unverified, the result is explicitly labelled as a reference.</small></div>`;
  debugLog(`Starting reference calculation: ${name}`);
  try {
    const r=await fetch('/api/library/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,forecast_amount:5,forecast_unit:'years',school:'synthesis'}),cache:'no-store'});
    const d=await readJsonResponse(r);
    const c=d.chart||{}; const n=d.narrative||{};
    latest={chart:c,narrative:n}; $('workspace-personal').classList.add('active'); document.querySelectorAll('.workspace-pane').forEach(x=>x.classList.remove('active')); $('workspace-personal').classList.add('active'); document.querySelectorAll('.workspace').forEach(x=>x.classList.toggle('active',x.dataset.workspace==='personal')); renderPersonal(latest); document.querySelectorAll('#personalTabs .subtab').forEach(x=>x.classList.remove('active')); document.querySelector('#personalTabs .subtab[data-tab="personal-overview"]')?.classList.add('active'); $('libraryResult').innerHTML=`<div class="section"><div class="section-heading"><div><span class="eyebrow">REFERENCE CHART LOADED</span><h3>${esc(d.profile?.name||name)}</h3><p class="muted">The full reference analysis has been opened in Personal Astrology using the same chart, interpretation, prediction and chatbot pipeline.</p></div></div></div>`;
    debugLog(`Reference chart ready: ${name}`,'ok');
  } catch(err){ debugLog(`Reference calculation failed: ${err.message||err}`,'bad'); showUiError('libraryResult',err,'Reference calculation failed'); }
}
function queueLibrarySearch(){
  clearTimeout(librarySearchTimer);
  librarySearchTimer=setTimeout(async()=>{
    librarySearchAbort?.abort(); librarySearchAbort=new AbortController();
    const q=$('librarySearch').value.trim(),cat=$('libraryCategory').value;
    const url='/api/library?q='+encodeURIComponent(q)+(cat?'&category='+encodeURIComponent(cat):'');
    try{const r=await fetch(url,{signal:librarySearchAbort.signal});const d=await readJsonResponse(r);renderLibrary(d.results||[]);}
    catch(err){if(err.name!=='AbortError')showUiError('libraryGrid',err,'Library search failed');}
  },180);
}
$('librarySearch')?.addEventListener('input',queueLibrarySearch);
$('libraryCategory')?.addEventListener('change',queueLibrarySearch);
loadLibrary();


window.addEventListener('error',e=>{debugLog(`Browser error: ${e.message||'unknown error'}${e.filename?` · ${e.filename}:${e.lineno||0}:${e.colno||0}`:''}`,'bad');});
window.addEventListener('unhandledrejection',e=>{debugLog(`Async error: ${e.reason?.message||e.reason||'unknown error'}`,'bad');});

// Personalized muhurta search: all calculations stay server-side and rule explanations are returned with each interval.
(function initMuhurta(){
  const form=$('muhurtaForm'); if(!form)return;
  const now=new Date(); const addDays=(d,n)=>{const x=new Date(d);x.setDate(x.getDate()+n);return x.toISOString().slice(0,10)};
  if(!$('muhurtaStart').value)$('muhurtaStart').value=addDays(now,1);
  if(!$('muhurtaEnd').value)$('muhurtaEnd').value=addDays(now,14);
  $('muhurtaPlace')?.addEventListener('change',()=>{const p=$('place')?.value?.trim();if(p&&$('muhurtaPlace').value.trim().toLowerCase()===p.toLowerCase()){ $('muhurtaLat').value=$('lat').value; $('muhurtaLon').value=$('lon').value; $('muhurtaTz').value=$('tz').value; }});
  form.addEventListener('submit',async e=>{
    e.preventDefault(); const start=$('muhurtaStart').value,end=$('muhurtaEnd').value;
    if(!start||!end||end<start){$('muhurtaStatus').textContent='Choose a valid start and end date.';return;}
    if((Date.parse(end)-Date.parse(start))/86400000>90){$('muhurtaStatus').textContent='Search at most 90 days per request.';return;}
    const personalize=$('muhurtaUseBirth').checked && $('dob')?.value && $('tob')?.value;
    const payload={activity:$('muhurtaActivity').value,start_date:start,end_date:end,latitude:Number($('muhurtaLat').value),longitude:Number($('muhurtaLon').value),timezone:$('muhurtaTz').value.trim(),natal_dob:personalize?$('dob').value:null,natal_tob:personalize?$('tob').value:null,natal_timezone:personalize?$('tz').value:null};
    const status=$('muhurtaStatus'),out=$('muhurtaResults');status.textContent='Calculating Panchanga and personalized timing screens…';out.innerHTML='<p class="muted">Searching local daylight windows. This may take a moment for a longer range.</p>';
    const btn=form.querySelector('button[type="submit"]');btn.disabled=true;
    try{const r=await fetch('/api/muhurta/search',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const d=await readJsonResponse(r);
      const windows=d.candidate_windows||[];status.textContent=`${windows.length} candidate windows shown · ${d.personalized?'personalized with natal Moon':'general Panchanga screen'} · ${d.method.ayanamsha}`;
      out.innerHTML=windows.length?windows.map((w,i)=>`<article class="muhurta-window"><div class="muhurta-window-head"><b>${esc(new Date(w.start).toLocaleString(undefined,{dateStyle:'medium',timeStyle:'short'}))} – ${esc(new Date(w.end).toLocaleTimeString(undefined,{timeStyle:'short'}))}</b><span class="muhurta-score">Rule score ${esc(w.score)}/100</span></div><p><b>${esc(w.panchanga.paksha)} ${esc(w.panchanga.tithi)}</b> · ${esc(w.panchanga.nakshatra)} · ${esc(w.panchanga.yoga)} · ${esc(w.panchanga.karana)}</p><div class="muhurta-notes"><b>Supporting:</b> ${esc((w.reasons||[]).join('; ')||'No positive factors recorded')}<br><b>Conflicts:</b> ${esc((w.penalties||[]).join('; ')||'No listed conflict in this screen')}<br><b>Local sunrise/set:</b> ${esc(w.sunrise?new Date(w.sunrise).toLocaleTimeString(undefined,{timeStyle:'short'}):'—')} / ${esc(w.sunset?new Date(w.sunset).toLocaleTimeString(undefined,{timeStyle:'short'}):'—')}</div></article>`).join(''):`<p>No candidate intervals met the screening threshold in this period. Expand the dates or consult the full local Panchanga rather than lowering a threshold blindly.</p>`;
      out.insertAdjacentHTML('beforeend',`<p class="muted">${esc(d.candidate_count_before_limit)} eligible intervals before display limit. ${esc((d.limitations||[]).join(' '))}</p>`);
    }catch(err){status.textContent=err.message||'Muhurta search failed.';out.innerHTML='';}finally{btn.disabled=false;}
  });
})();

/*
 * La Comunitat — ajudant per a portar partides d'«El Señor de los Anillos:
 * El Destino de la Comunidad».
 * Copyright (C) 2026 Col·laboradors de La Comunitat
 *
 * Aquest programa és programari lliure: el podeu redistribuir i/o modificar
 * segons els termes de la Llicència Pública General de GNU publicada per la
 * Free Software Foundation, ja siga la versió 3 de la Llicència o (a la vostra
 * elecció) qualsevol versió posterior.
 *
 * Aquest programa es distribueix amb l'esperança que siga útil, però SENSE CAP
 * GARANTIA; ni tan sols la garantia implícita de COMERCIABILITAT o ADEQUACIÓ A
 * UN PROPÒSIT PARTICULAR. Vegeu la Llicència Pública General de GNU per a més
 * detalls: <https://www.gnu.org/licenses/>.
 *
 * Projecte de fans no oficial, sense relació amb Z-Man Games, Asmodee ni
 * Middle-earth Enterprises.
 */
(() => {
"use strict";
/* ================= helpers ================= */
const $=(s,r=document)=>r.querySelector(s);
const $$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const clone=v=>v===undefined?undefined:JSON.parse(JSON.stringify(v));
const isObj=v=>v&&typeof v==='object'&&!Array.isArray(v);
function deepMerge(a,b){if(!isObj(a)||!isObj(b))return clone(b);const o={...a};for(const k in b)o[k]=(isObj(b[k])&&isObj(a[k]))?deepMerge(a[k],b[k]):clone(b[k]);return o}
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const newId=()=>Math.random().toString(36).slice(2,8)+Date.now().toString(36).slice(-4);
function ago(ts){const s=(Date.now()-ts)/1000;if(s<45)return'ara';if(s<3600)return`fa ${Math.round(s/60)} min`;if(s<86400)return`fa ${Math.round(s/3600)} h`;return new Date(ts).toLocaleDateString('ca')}
let toastT;function toast(m){const t=$('#toast');t.textContent=m;t.hidden=false;clearTimeout(toastT);toastT=setTimeout(()=>t.hidden=true,3500)}
function lsGet(k){try{return localStorage.getItem(k)}catch(e){return null}}
function lsSet(k,v){try{localStorage.setItem(k,v)}catch(e){}}
function armed(btn,fn,label='Prem de nou per a confirmar'){
  if(btn.dataset.armed){delete btn.dataset.armed;fn();return}
  btn.dataset.armed='1';const old=btn.textContent;btn.textContent=label;
  setTimeout(()=>{if(btn.isConnected&&btn.dataset.armed){delete btn.dataset.armed;btn.textContent=old}},4000);
}
const plural=(n,a,b)=>`${n} ${n===1?a:b}`;
const initials=n=>{const w=n.split(/\s+i\s+|\s+/).filter(Boolean);return (w[0][0]+(w[1]?w[1][0]:w[0][1]||'')).toUpperCase()};

const BATTLE_FACES=[['rout','Rebutjar','Retira 1 tropa de l\'Ombra.'],['tie','Taules','Retira 1 de l\'Ombra i 1 aliada.'],['over','Arrossegats','Retira 1 aliada (s\'ignora en un refugi).'],['naz','Natzgûl!','Si hi ha natzguls a la regió, retira 2 aliades.']];
const SEARCH_FACES=[['slip','Frodo s\'escapoleix','Sense efecte.'],['tired','Fatiga','Perd 1 d\'esperança.'],['seen','Al descobert','Perd 1 d\'esperança (s\'ignora en un refugi).'],['call','Convocatòria','Si hi ha natzguls, 1 torna a Mordor.']];

/* ================= store ================= */
const S={uid:null,token:null,camp:null,es:null};
const st={tab:lsGet('cm-tab2')||'partida',loaded:false,forceSetup:false};
let G=null,LOG=[],UNDO=[],CAMP=null;
const mem=new Map(),memL=new Set();
const parentOf=p=>p.split('/').slice(0,-1).join('/');
function memNotify(path){for(const l of [...memL]){if(l.doc?l.path===path:l.path===parentOf(path))l.fire()}}
function watchDoc(path,cb){const l={doc:true,path,fire:()=>{const d=mem.get(path);cb(d?clone(d):null)}};memL.add(l);setTimeout(l.fire,0)}
async function doWrite(path,mode,data){
  if(mode==='delete')mem.delete(path);else if(mode==='set')mem.set(path,clone(data));else mem.set(path,deepMerge(mem.get(path)||{},data));
  memNotify(path);
  if(!S.token)return;
  let r;
  try{r=await fetch('api/write',{method:'POST',headers:{'Content-Type':'application/json','X-Taula-Token':S.token},body:JSON.stringify({path,mode,data,camp:S.camp})})}catch(e){throw{code:'net'}}
  if(r.status===401){lsSet('cm-token','');location.reload();return}
  if(r.status===409){location.reload();return}
  if(!r.ok)throw{code:'http'};
}
const wq=new Map();
function write(path,data,mode='set'){
  let q=wq.get(path);if(!q){q={busy:false,next:null};wq.set(path,q)}
  q.next={mode,data:clone(data)};if(!q.busy)flush(path,q);
}
async function flush(path,q){
  q.busy=true;
  while(q.next){const{mode,data}=q.next;q.next=null;
    try{await doWrite(path,mode,data)}catch(e){await new Promise(r=>setTimeout(r,500));try{await doWrite(path,mode,data)}catch(e2){toast('No s\'ha pogut guardar. Comprova la connexió amb el servidor.')}}}
  q.busy=false;
}

/* ================= game ================= */
const threatNow=s=>s.threat[clamp(s.threatIdx,0,s.threat.length-1)];
const objectivesLeft=s=>s.objectives.filter(o=>!o.ring&&!o.done).length;
function hopeDelta(s,d,log,why){
  if(!d)return;const before=s.hope;s.hope=clamp(s.hope+d,0,s.hopeMax);const real=s.hope-before;
  if(real)log.push({t:`${real>0?'+':''}${real} d'esperança: ${why}. Ara ${s.hope}.`,c:real<0?'bad':'good'});
  else if(d>0)log.push({t:`L'esperança ja és al màxim (${why}).`});
  if(s.hope<=0&&!s.result){s.result='lose';log.push({t:'Frodo ha perdut tota l\'esperança. La partida s\'ha perdut.',c:'bad'})}
}
function commit(label,fn){
  if(!G)return null;
  const before=clone(G),log=[];const extra=fn(G,log);
  UNDO.push({label,state:before});if(UNDO.length>30)UNDO.shift();
  const ts=Date.now(),who=mem.get('users/'+S.uid)?.name||'';
  if(!log.length)log.push({t:label+'.'});
  LOG=[...log.map(e=>({...e,ts,who})).reverse(),...LOG].slice(0,250);
  write('game/state',G);write('game/undo',{stack:UNDO});write('game/log',{list:LOG});
  renderAll();return extra;
}
function undo(){
  if(!UNDO.length){toast('No hi ha res per desfer.');return}
  const u=UNDO.pop();G=u.state;
  LOG=[{t:`Desfet: ${u.label}.`,ts:Date.now()},...LOG].slice(0,250);
  write('game/state',G);write('game/undo',{stack:UNDO});write('game/log',{list:LOG});renderAll();
}
function newGame(cfg){
  const lv=LEVELS[cfg.level];
  const chars=[];cfg.players.forEach((p,i)=>p.chars.forEach(cid=>{const c=CHARACTERS.find(x=>x.id===cid);if(c)chars.push({...c,player:i})}));
  const events=EVENTS_BY_PLAYERS[cfg.players.length]||6,hand=HAND_BY_PLAYERS[cfg.players.length]||2;
  const objs=cfg.objectives.map(n=>({id:newId(),name:n,done:false}));objs.push({id:'ring',name:RING_OBJ,done:false,ring:true});
  return {v:2,level:cfg.level,hope:HOPE_START,hopeMax:HOPE_MAX,threat:THREAT.slice(),threatIdx:0,
    skies:{total:lv.skies,drawn:0},deck:48+events+lv.skies-hand*cfg.players.length,
    players:cfg.players.map(p=>({name:p.name})),chars,objectives:objs,setup:SETUP_STEPS.map(()=>false),
    round:1,turn:{p:0,step:0,a:[0,0],shadow:0},result:null,created:Date.now(),solo:cfg.players.length===1,
    calc:{naz:0,troops:0,ring:false,haven:false,mordor:false,bKind:'attack',bFr:1,bSh:1,bNaz:false,bHaven:false}};
}

/* ================= modal ================= */
function openModal(html,onMount){
  const root=$('#modal-root');
  root.innerHTML=`<div class="modal-back" id="mback"><div class="modal" role="dialog" aria-modal="true">${html}</div></div>`;
  const back=$('#mback');const close=()=>{root.innerHTML='';document.removeEventListener('keydown',onKey)};
  const onKey=e=>{if(e.key==='Escape')close()};document.addEventListener('keydown',onKey);
  back.addEventListener('click',e=>{if(e.target===back)close()});
  onMount&&onMount($('.modal',root),close);
  $('.modal button',root)?.focus();
}
function diceModal({title,intro,n,faces,valor,onApply,upTo}){
  const counts=Object.fromEntries(faces.map(f=>[f[0],0]));let val=0;
  const draw=m=>{
    const sum=Object.values(counts).reduce((a,b)=>a+b,0);
    $('#fc',m).innerHTML=faces.map(([k,nm,d])=>`<div class="face"><div><div class="fn">${nm}</div><div class="fd">${d}</div></div><div class="stepper"><button class="mini" data-dec="${k}" aria-label="Menys">−</button><b>${counts[k]}</b><button class="mini" data-inc="${k}" aria-label="Més">+</button></div></div>`).join('')+(valor?`<div class="face"><div><div class="fn">Valor gastat</div><div class="fd">Cada valor retira 1 tropa de l'Ombra.</div></div><div class="stepper"><button class="mini" data-vdec>−</button><b>${val}</b><button class="mini" data-vinc>+</button></div></div>`:'');
    $('#fsum',m).textContent=upTo?`${sum} ${sum===1?'dau anotat':'daus anotats'} (fins a ${n})`:`${sum} de ${n} ${n===1?'dau':'daus'} anotats`;
    $('#fok',m).disabled=upTo?(sum<1||sum>n):sum!==n;
  };
  openModal(`<h2>${esc(title)}</h2><p class="muted" style="margin:0">${intro}</p>
    <div class="row"><span class="big-n">${n}</span><span class="muted">${upTo?'daus com a màxim':n===1?'dau a tirar':'daus a tirar'}</span></div>
    <p class="small muted" style="margin:0">Tira els daus, fes les tornades a tirar amb Destí, i anota el resultat final de cada dau.</p>
    <div class="faces" id="fc"></div><p class="small" id="fsum" style="margin:0"></p>
    <div class="foot"><button class="btn" id="fcancel">Cancel·lar</button><button class="btn pri" id="fok">Aplicar</button></div>`,(m,close)=>{
    draw(m);
    m.addEventListener('click',e=>{
      const t=e.target.closest('button');if(!t)return;const sum=Object.values(counts).reduce((a,b)=>a+b,0);
      if(t.dataset.inc&&sum<n)counts[t.dataset.inc]++;if(t.dataset.dec&&counts[t.dataset.dec]>0)counts[t.dataset.dec]--;
      if('vinc' in t.dataset)val++;if('vdec' in t.dataset&&val>0)val--;
      if(t.id==='fcancel'){close();return}if(t.id==='fok'){close();onApply({...counts},val);return}
      draw(m);
    });
  });
}
function infoModal(title,html){openModal(`<h2>${esc(title)}</h2>${html}<div class="foot"><button class="btn pri" id="ok">D'acord</button></div>`,(m,close)=>{$('#ok',m).onclick=close})}

/* ================= calculators ================= */
const C=()=>G.calc;
function searchDice(){const c=C();return Math.min(7,c.naz+(c.ring?0:c.troops))}
function battleDice(){const c=C();return c.bKind==='attack'?clamp(c.bFr,1,3):Math.min(3,c.bSh)}
function doSearch({ring=false,doom=false,label}={}){
  const c=C();let n=c.naz+(ring?0:c.troops);if(doom)n+=G.hopeMax-G.hope;n=Math.min(7,n);
  const finish=res=>commit(label||'Tirada de cerca',(s,log)=>{
    if(res){
      log.push({t:`Tirada de cerca: ${res.slip} s'escapoleix, ${res.tired} fatiga, ${res.seen} al descobert, ${res.call} convocatòria.`});
      if(res.tired)hopeDelta(s,-res.tired,log,`fatiga (${res.tired})`);
      if(res.seen){if(s.calc.haven)log.push({t:'Al descobert ignorat: Frodo és en un refugi.'});else hopeDelta(s,-res.seen,log,`al descobert (${res.seen})`)}
      if(res.call&&!s.calc.mordor&&s.calc.naz){const k=Math.min(res.call,s.calc.naz);log.push({t:`Al tauler: torna ${plural(k,'natzgûl','natzguls')} de la regió de Frodo a Mordor.`});s.calc.naz-=k}
    }else log.push({t:'Tirada de cerca: no hi havia natzguls ni tropes de l\'Ombra, no cal tirar.'});
    if(doom&&s.hope>=1){s.result='win';s.objectives.forEach(o=>{if(o.ring)o.done=true});log.push({t:'L\'Anell Únic ha estat destruït! La Comunitat guanya la partida.',c:'good'})}
  });
  if(!n){finish(null);return}
  diceModal({title:doom?'Destruir l\'Anell Únic':ring?'Frodo es posa l\'Anell':'Tirada de cerca',
    intro:doom?`${c.naz} natzguls + ${c.troops} tropes de l'Ombra + ${G.hopeMax-G.hope} caselles per damunt de l'esperança. Màxim 7.`:`${c.naz} natzguls a la regió de Frodo${ring?' (l\'Anell ignora les tropes)':` + ${c.troops} tropes de l'Ombra al seu lloc`}. Màxim 7.`,
    n,faces:SEARCH_FACES,onApply:res=>finish(res)});
}
function doBattle(){
  const c=C(),n=battleDice();
  if(c.bKind==='attack'&&(!c.bFr||!c.bSh)){toast('Per a atacar cal que hi haja tropes aliades i de l\'Ombra al lloc.');return}
  if(!n){toast('No hi ha tropes de l\'Ombra: no hi ha batalla.');return}
  diceModal({title:'Tirada de batalla',
    intro:c.bKind==='attack'?`Atac d'un personatge: fins a ${n} ${n===1?'dau':'daus'} (1 per tropa aliada, mínim 1, màxim 3). Pots tirar-ne menys. Recorda desplaçar l'Ull a la regió.`:`La provoca l'Ombra: 1 dau per tropa de l'Ombra (màxim 3). L'Ull no es mou.`,
    n,upTo:c.bKind==='attack',faces:BATTLE_FACES,valor:true,
    onApply:(res,val)=>{
      let sh=c.bSh,fr=c.bFr;const rem=k=>{if(k==='s'&&sh>0)sh--;if(k==='f'&&fr>0)fr--};
      for(let i=0;i<res.rout;i++)rem('s');
      for(let i=0;i<res.tie;i++){rem('s');rem('f')}
      if(!c.bHaven)for(let i=0;i<res.over;i++)rem('f');
      if(c.bNaz)for(let i=0;i<res.naz*2;i++)rem('f');
      for(let i=0;i<val;i++)rem('s');
      const lostSh=c.bSh-sh,lostFr=c.bFr-fr,havenLost=c.bHaven&&sh>0&&fr===0;
      commit('Tirada de batalla',(s,log)=>{
        log.push({t:`Batalla${c.bKind==='attack'?' (atac)':''}: ${res.rout} rebutjar, ${res.tie} taules, ${res.over} arrossegats, ${res.naz} Natzgûl!${val?`, ${val} de valor`:''}. Al tauler: retira ${plural(lostSh,'tropa','tropes')} de l'Ombra i ${plural(lostFr,'aliada','aliades')}.`});
        s.calc.bSh=sh;s.calc.bFr=fr;
        if(havenLost){log.push({t:'L\'Ombra ha conquerit el refugi: posa-hi una fitxa de fortalesa de l\'Ombra.',c:'bad'});hopeDelta(s,-3,log,'refugi perdut')}
      });
      infoModal('Resultat de la batalla',`<p style="margin:0;font-size:19px">Retira <b>${plural(lostSh,'tropa','tropes')} de l'Ombra</b> i <b>${plural(lostFr,'tropa aliada','tropes aliades')}</b>.</p><p class="muted" style="margin:0">Hi queden ${sh} de l'Ombra i ${fr} aliades.${c.bHaven&&res.over?' Els «arrossegats» s\'han ignorat perquè és un refugi.':''}${!c.bNaz&&res.naz?' Els «Natzgûl!» no fan res: no hi ha natzguls a la regió.':''}</p>${havenLost?'<p style="margin:0;color:var(--blood)"><b>Refugi perdut:</b> posa-hi una fitxa de fortalesa de l\'Ombra. Ja he restat 3 d\'esperança.</p>':''}`);
    }});
}
function skiesFlow(){
  openModal(`<h2>El cel s'enfosqueix</h2>
    <ol class="steps">
      <li><div><b>L'Ombra creix.</b> Pujaré l'amenaça 1 casella.</div></li>
      <li><div><b>Et veig!</b> L'Ull de Sauron és ara a la regió de Frodo?
        <div class="radio-list" style="margin-top:8px"><label><input type="radio" name="eye" value="yes"><span>Sí: perdeu 2 d'esperança.</span></label><label><input type="radio" name="eye" value="no" checked><span>No: desplaça l'Ull a la regió de Frodo.</span></label></div></div></li>
      <li><div><b>A l'empara de la foscor.</b> Posa 3 tropes de l'Ombra al lloc de la carta. N'hi ha prou a la reserva?
        <div class="row" style="margin-top:8px"><span class="small">Tropes que falten</span><span class="stepper"><button class="mini" id="mdec">−</button><b id="miss">0</b><button class="mini" id="minc">+</button></span></div>
        <p class="small muted" style="margin:6px 0 0">Si hi ha tropes aliades en eixe lloc, fes després una tirada de batalla provocada per l'Ombra.</p></div></li>
      <li><div><b>El perill s'intensifica.</b> Barreja els descarts d'Ombra i posa'ls damunt del mazo d'Ombra.</div></li>
    </ol>
    <div class="foot"><button class="btn" id="sk-cancel">Cancel·lar</button><button class="btn pri" id="sk-ok">Fet</button></div>`,(m,close)=>{
    let miss=0;
    m.addEventListener('click',e=>{
      const b=e.target.closest('button');if(!b)return;
      if(b.id==='minc'&&miss<3)miss++;if(b.id==='mdec'&&miss>0)miss--;$('#miss',m).textContent=miss;
      if(b.id==='sk-cancel')close();
      if(b.id==='sk-ok'){
        const yes=$('input[name=eye]:checked',m).value==='yes';close();
        commit('El cel s\'enfosqueix',(s,log)=>{
          s.skies.drawn=Math.min(s.skies.total,s.skies.drawn+1);
          log.push({t:`El cel s'enfosqueix (${s.skies.drawn} de ${s.skies.total}).`,c:'bad'});
          if(s.threatIdx<s.threat.length-1){s.threatIdx++;log.push({t:`L'amenaça puja: ara es roben ${threatNow(s)} cartes d'Ombra per torn.`,c:'bad'})}
          if(yes)hopeDelta(s,-2,log,'Et veig! (l\'Ull era a la regió de Frodo)');else log.push({t:'Al tauler: desplaça l\'Ull a la regió de Frodo.'});
          if(miss)hopeDelta(s,-miss,log,'no quedaven tropes de l\'Ombra a la reserva');
        });
      }
    });
  });
}
function shadowCardFlow(){
  openModal(`<h2>Carta d'Ombra</h2>
    <p class="muted" style="margin:0">Mira la bandera que es veu al mazo d'Ombra.</p>
    <div class="faces">
      <div class="face" style="display:block"><div class="fn">Bandera roja: Avançar</div><div class="fd">Mou totes les tropes de l'Ombra de la línia indicada 1 espai en la direcció de la fletxa, començant per les més avançades. Les del final no es mouen. Després, batalla a cada lloc de la línia amb tropes de les dues bandes (de la més avançada cap enrere). Si l'Ombra ocupa un refugi sense aliades, el perds.</div></div>
      <div class="face" style="display:block"><div class="fn">Bandera negra: Reforçar</div><div class="fd">1 tropa de l'Ombra al lloc indicat (no si el vau capturar). Si hi ha aliades, batalla. Després, l'ordre especial: l'Ull a la regió de Frodo (o tirada de cerca si ja hi és) · acosta 2 natzguls a Frodo · desplega 3 natzguls de Mordor a la regió de l'Ull.</div></div>
    </div>
    <div class="radio-list">
      <label><input type="checkbox" id="sc-lost"><span>S'ha perdut un refugi (−3 d'esperança)</span></label>
      <label><span>Tropes de l'Ombra que no es podien posar per falta de reserva</span><span class="stepper" style="margin-left:auto"><button class="mini" id="sdec">−</button><b id="smiss">0</b><button class="mini" id="sinc">+</button></span></label>
    </div>
    <div class="foot"><button class="btn" id="sc-cancel">Cancel·lar</button><button class="btn pri" id="sc-ok">Carta resolta</button></div>`,(m,close)=>{
    let miss=0;
    m.addEventListener('click',e=>{
      const b=e.target.closest('button');if(!b)return;
      if(b.id==='sinc')miss++;if(b.id==='sdec'&&miss>0)miss--;$('#smiss',m).textContent=miss;
      if(b.id==='sc-cancel')close();
      if(b.id==='sc-ok'){const lost=$('#sc-lost',m).checked;close();
        commit('Carta d\'Ombra resolta',(s,log)=>{s.turn.shadow++;log.push({t:`Carta d'Ombra resolta (${s.turn.shadow} de ${threatNow(s)} aquest torn).`});if(lost)hopeDelta(s,-3,log,'refugi perdut');if(miss)hopeDelta(s,-miss,log,'no quedaven tropes de l\'Ombra a la reserva')})}
    });
  });
}

/* ================= render ================= */
function renderHeader(){
  const n=$('#camp-name');if(document.activeElement!==n)n.value=CAMP?.name||'';
  $$('.tab').forEach(t=>t.setAttribute('aria-selected',t.dataset.tab===st.tab));
  $('#who').innerHTML=S.token?`<span class="chip">${esc(mem.get('users/'+S.uid)?.name||'')}</span><button class="chip" id="logout">Eixir</button>`:'';
}
function renderTracks(){
  const el=$('#tracks');
  if(!G){el.innerHTML='<span class="muted small">Cap partida preparada encara.</span>';return}
  el.innerHTML=`
    <div class="trk"><span class="lbl">Esperança</span><button class="mini" data-hope="-1" aria-label="Perdre esperança">−</button><span class="val">${G.hope}<small>/${G.hopeMax}</small></span><button class="mini" data-hope="1" aria-label="Guanyar esperança">+</button>
      <span class="pips" aria-hidden="true">${Array.from({length:G.hopeMax},(_,i)=>`<i class="pip ${i<G.hope?'on':''} ${G.hope<=2?'low':''}"></i>`).join('')}</span></div>
    <div class="trk"><span class="lbl">Amenaça</span><button class="mini" data-thr="-1" aria-label="Baixar amenaça">−</button>
      <span class="pips">${G.threat.map((v,i)=>`<i class="pip thr ${i===G.threatIdx?'on':''}">${v}</i>`).join('')}</span><button class="mini" data-thr="1" aria-label="Pujar amenaça">+</button></div>
    <div class="trk"><span class="lbl">Cel enfosquit</span><span class="mono">${G.skies.drawn}/${G.skies.total}</span></div>
    <div class="trk"><span class="lbl">Mazo</span><button class="mini" data-deck="-1" aria-label="Una carta menys">−</button><span class="mono">${G.deck}</span><button class="mini" data-deck="1" aria-label="Una carta més">+</button></div>
    <div class="trk"><span class="lbl">Objectius</span><span class="mono">${G.objectives.filter(o=>o.done).length}/${G.objectives.length}</span></div>
    <div class="trk"><span class="lbl">Ronda</span><span class="mono">${G.round}</span></div>
    <button class="btn sm" id="undo" ${UNDO.length?'':'disabled'} title="${UNDO.length?esc('Desfer: '+UNDO[UNDO.length-1].label):''}">Desfer</button>`;
  const b=$('#banner');
  if(G.result){b.hidden=false;b.className='banner endstate '+G.result;b.textContent=G.result==='win'?'L\'Anell ha estat destruït. La Comunitat ha guanyat!':'Frodo ha perdut tota l\'esperança. L\'Ombra s\'estén per la Terra Mitjana.'}
  else if(b.classList.contains('endstate')){b.hidden=true;b.className='banner'}
}
const step=(id,label,val)=>`<span class="k">${label}</span><span class="stepper"><button class="mini" data-cdec="${id}" aria-label="Menys">−</button><b>${val}</b><button class="mini" data-cinc="${id}" aria-label="Més">+</button></span>`;
const chk=(id,label,on)=>`<label class="check"><input type="checkbox" data-cchk="${id}" ${on?'checked':''}> ${label}</label>`;
function renderPlay(){
  if(!G||st.forceSetup){renderSetup();return}
  const c=C(),sd=searchDice(),bd=battleDice(),left=objectivesLeft(G);
  const doomN=Math.min(7,c.naz+c.troops+(G.hopeMax-G.hope));
  $('#main').innerHTML=`<div class="play">
    <div class="mapcol" id="mapcol">${mapPanel()}</div>
    <div class="tools">
    <section class="panel tool"><h2>Tirada de cerca</h2>
      <p class="muted small" style="margin:0">Quan Frodo viatja sense gastar Sigil, o ho demana una carta.</p>
      <div class="kv2">${step('naz','Natzguls a la regió de Frodo',c.naz)}${step('troops','Tropes de l\'Ombra al lloc de Frodo',c.troops)}</div>
      <div class="col">${chk('haven','Frodo és en un refugi',c.haven)}${chk('mordor','Frodo és a Mordor',c.mordor)}</div>
      <div class="row tool-foot"><span class="big-n">${sd}</span><span class="muted">${sd===1?'dau':'daus'}${sd?'':' · no cal tirar'}</span><button class="btn pri" id="t-search" style="margin-left:auto">Anotar la tirada</button></div>
      <div class="row"><button class="btn sm" id="t-ring">Frodo es posa l'Anell</button><span class="small muted">−1 d'esperança, l'Ull a la seua regió i cerca sense comptar tropes.</span></div>
    </section>
    <section class="panel tool"><h2>Tirada de batalla</h2>
      <div class="row"><button class="btn sm" data-bk="attack" aria-pressed="${c.bKind==='attack'}">Atac d'un personatge</button><button class="btn sm" data-bk="shadow" aria-pressed="${c.bKind==='shadow'}">La provoca l'Ombra</button></div>
      <div class="kv2">${step('bFr','Tropes aliades al lloc',c.bFr)}${step('bSh','Tropes de l\'Ombra al lloc',c.bSh)}</div>
      <div class="col">${chk('bNaz','Hi ha natzguls a la regió',c.bNaz)}${chk('bHaven','El lloc és un refugi',c.bHaven)}</div>
      <div class="row tool-foot"><span class="big-n">${bd}</span><span class="muted">${c.bKind==='attack'?'daus com a màxim':bd===1?'dau':'daus'}</span><button class="btn pri" id="t-battle" style="margin-left:auto">Anotar la tirada</button></div>
      ${c.bKind==='attack'?'<p class="small muted" style="margin:0">Abans de tirar, desplaça l\'Ull de Sauron a la regió de l\'atac.</p>':''}
    </section>
    <section class="panel tool"><h2>Esperança</h2>
      <div class="hopebtns">
        <button class="btn" data-hev="-3:refugi perdut">Refugi perdut <b>−3</b></button>
        <button class="btn" data-hev="2:fortalesa capturada">Fortalesa capturada <b>+2</b></button>
        <button class="btn" data-hev="-1:falta una tropa de l'Ombra a la reserva">Falta una tropa de l'Ombra <b>−1</b></button>
        <button class="btn" data-hev="-1:falta una carta de joc al mazo">Falta una carta de joc <b>−1</b></button>
        <button class="btn" data-hev="-1:objectiu o habilitat">Altres <b>−1</b></button>
        <button class="btn" data-hev="1:objectiu o habilitat">Altres <b>+1</b></button>
      </div>
      <p class="small muted" style="margin:0">En capturar una fortalesa, recorda desplaçar l'Ull a la seua regió. Capturar Mòria, Isengard, Dol Guldur o Umbar fa que no hi isquen més tropes.</p>
    </section>
    <section class="panel tool"><h2>Destruir l'Anell Únic</h2>
      <p class="muted small" style="margin:0">Frodo, a la Muntanya del Destí, gasta 5 de Destí. Es fa una última cerca amb 1 dau extra per cada casella per damunt de l'esperança. Fa servir els natzguls i les tropes de la tirada de cerca.</p>
      <div class="row tool-foot"><span class="big-n">${doomN}</span><span class="muted">${doomN===1?'dau':'daus'} (màxim 7)</span><button class="btn pri" id="t-doom" style="margin-left:auto" ${left?'disabled':''}>Intentar-ho</button></div>
      ${left?`<p class="small" style="margin:0;color:var(--blood)">Encara queden ${plural(left,'objectiu','objectius')} per completar.</p>`:''}
    </section>
    <section class="panel tool"><h2>Objectius</h2>
      ${G.objectives.map(o=>`<div class="obj ${o.done?'done':''}"><input type="checkbox" data-objdone="${o.id}" ${o.done?'checked':''} ${o.ring?'disabled':''} aria-label="Completat"><span class="on">${esc(o.name)}</span>${o.ring?'<span class="badge" style="position:static">Últim</span>':''}</div>`).join('')}
    </section>
    <section class="panel tool"><h2>Referència ràpida</h2>
      <dl class="ref">
        <dt>Viatjar amb Frodo</dt><dd>Gasta 1 Sigil o fes una cerca al destí. Els camins especials costen els símbols que hi ha dibuixats.</dd>
        <dt>Comunitat</dt><dd>Al mateix lloc que un altre participant: dona-li o pren-li una carta de la teua regió.</dd>
        <dt>Preparar</dt><dd>En un refugi: descarta una carta de regió per a prendre la fitxa del seu símbol.</dd>
        <dt>Reclutar</dt><dd>En un lloc de color: 1 Amistat per 1 tropa d'eixe color.</dd>
        <dt>Capturar</dt><dd>Fortalesa sense Ombra i amb 1 aliada: 3 Valor, l'Ull a la regió, +2 d'esperança.</dd>
        <dt>Límit de mà</dt><dd>Set cartes. Els esdeveniments es poden jugar en qualsevol moment.</dd>
      </dl>
    </section>
  </div>  </div>`;
}
let MAP_OK=null;
function mapPanel(){
  if(MAP_OK===false)return `<div class="empty"><b>Sense mapa</b>Posa una imatge anomenada <code>mapa.jpg</code> al costat de <code>comunitat.py</code> i recarrega la pàgina.</div>`;
  return `<figure class="mapfig"><button class="mapbtn" id="map-open" aria-label="Ampliar el mapa"><img src="mapa" alt="Mapa de la Terra Mitjana" id="map-img"></button><figcaption class="small muted">Fes clic per a ampliar-lo.</figcaption></figure>`;
}
document.addEventListener('error',e=>{if(e.target&&e.target.id==='map-img'){MAP_OK=false;const c=$('#mapcol');if(c)c.innerHTML=mapPanel()}},true);
document.addEventListener('click',e=>{
  if(!e.target.closest('#map-open'))return;
  openModal(`<div class="mapzoom"><img src="mapa" alt="Mapa de la Terra Mitjana"></div><div class="foot"><button class="btn pri" id="mz-close">Tancar</button></div>`,(m,close)=>{m.classList.add('wide');$('#mz-close',m).onclick=close});
});
function renderSide(){
  const el=$('#side2');
  if(!G){el.innerHTML=`<h2>El torn</h2><p class="muted small">Prepara una partida per a començar.</p>`+logHtml();return}
  const T=G.turn,p=G.players[T.p]||{name:'?'},mine=G.chars.filter(c=>c.player===T.p),n=threatNow(G);
  el.innerHTML=`<div><span class="eyebrow">Ronda ${G.round} · torn de</span><div class="turn-who">${esc(p.name||'Participant '+(T.p+1))}</div><span class="muted small">${mine.map(c=>esc(c.name)).join(G.solo?', ':' i ')}</span></div>
    <ol class="steps">
      <li class="${T.step===0?'cur':'done'}"><div><b>Fes 4 + 1 accions</b><div class="muted small">${G.solo?'4 amb el personatge del testimoni i 1 amb Frodo i Sam.':'4 amb un personatge i 1 amb l\'altre.'}</div>
        <div class="apips">${[0,1,2,3].map(i=>`<button class="apip ${i<T.a[0]?'used':''}" data-ap="0:${i}" aria-label="Acció ${i+1}">${i+1}</button>`).join('')}<button class="apip sep ${T.a[1]?'used':''}" data-ap="1:0" aria-label="Acció extra">+1</button></div>
        ${T.step===0?'<div class="row" style="margin-top:8px"><button class="btn sm" id="acts-done">Fet</button></div>':''}</div></li>
      <li class="${T.step===1?'cur':T.step>1?'done':''}"><div><b>Roba 2 cartes de joc</b><div class="muted small">Queden ${G.deck} al mazo. Si en robes un cel enfosquit, resol-lo.</div>
        <div class="row" style="margin-top:8px"><button class="btn sm ${T.step===1?'pri':''}" id="draw2">He robat 2 cartes</button><button class="btn sm" id="skies">El cel s'enfosqueix!</button></div></div></li>
      <li class="${T.step===2?'cur':''}"><div><b>Roba ${n} ${n===1?'carta':'cartes'} d'Ombra</b><div class="muted small">Resoltes: ${T.shadow} de ${n}.</div>
        <div class="row" style="margin-top:8px"><button class="btn sm ${T.step===2&&T.shadow<n?'pri':''}" id="shadow-card">Resoldre una carta d'Ombra</button></div></div></li>
    </ol>
    <button class="btn pri" id="next-turn">Passar al següent torn</button>
    ${logHtml()}`;
}
function logHtml(){return `<h3>Registre</h3><ol class="log2">${LOG.slice(0,100).map(e=>`<li class="${e.c||''}"><time>${ago(e.ts)}${e.who?' · '+esc(e.who):''}</time>${esc(e.t)}</li>`).join('')||'<li class="muted">Encara no ha passat res.</li>'}</ol>`}

/* --- Comunitat tab --- */
function renderCommunity(){
  if(!G||st.forceSetup){renderSetup();return}
  const done=G.setup.filter(Boolean).length;
  $('#main').innerHTML=`<div class="grid2">
    <section class="panel tool"><h2>Preparació</h2><p class="muted small" style="margin:0">${done} de ${SETUP_STEPS.length} passos fets.</p>
      ${SETUP_STEPS.map(([t,d],i)=>`<div class="obj ${G.setup[i]?'done':''}"><input type="checkbox" data-setup="${i}" ${G.setup[i]?'checked':''} aria-label="${esc(t)}"><span><span class="on">${esc(t)}</span><br><span class="small muted">${esc(d)}</span></span></div>`).join('')}
    </section>
    <section class="panel tool"><h2>La Comunitat</h2>
      ${G.players.map((p,i)=>`<div><h3>${esc(p.name||'Participant '+(i+1))}${G.turn.p===i?' · torn':''}</h3>${G.chars.filter(c=>c.player===i).map(c=>`<div class="row" style="justify-content:space-between;margin-top:6px"><span class="cchip"><span class="av" style="background:${c.color}">${esc(initials(c.name))}</span>${esc(c.name)}</span><span class="small muted">Comença a ${esc(c.start)}</span></div>`).join('')}</div>`).join('')}
    </section>
    <section class="panel tool"><h2>Partida</h2>
      <p class="muted small" style="margin:0">Dificultat ${esc(LEVELS[G.level]?.name||'')} · ${plural(G.skies.total,'cel enfosquit','cels enfosquits')} al mazo · començada ${ago(G.created)}.</p>
      <button class="btn danger" id="re-setup">Preparar una partida nova</button>
      <p class="small muted" style="margin:0">Per a conservar aquesta partida i començar-ne una altra, fes servir la pestanya Partides.</p>
    </section></div>`;
}
function renderSetup(){
  const n=+(lsGet('cm-np')||2);
  $('#main').innerHTML=`<div class="camps" style="max-width:1000px">
    <div><h2 style="font-size:32px">Preparar la partida</h2><p class="muted" style="margin:6px 0 0;max-width:66ch">Tria la dificultat, els participants i els objectius. L'app calcula el mazo de joc i et guia en la preparació del tauler.</p></div>
    <form class="panel" id="setup-form" style="display:flex;flex-direction:column;gap:16px">
      <div class="row" style="align-items:flex-end;gap:16px">
        <label class="field"><span>Dificultat</span><select class="in" id="sf-level">${Object.entries(LEVELS).map(([k,v])=>`<option value="${k}" ${k==='intro'?'selected':''}>${v.name} · ${v.skies} cel enfosquit · ${v.obj} objectius</option>`).join('')}</select></label>
        <label class="field"><span>Participants</span><select class="in" id="sf-np">${[1,2,3,4,5].map(i=>`<option ${i===n?'selected':''}>${i}</option>`).join('')}</select></label>
      </div>
      <div id="sf-players" class="plist"></div>
      <div><h3>Objectius</h3><div class="row" style="margin:8px 0"><select class="in" id="sf-scen" style="width:auto"><option value="">Escenari suggerit…</option>${SCENARIOS.map((s,i)=>`<option value="${i}">${esc(s.name)} (${s.level.map(l=>LEVELS[l].name).join('/')})</option>`).join('')}</select></div>
        <div id="sf-objs" class="plist"></div><p class="small muted" style="margin:6px 0 0">${esc(RING_OBJ)} s'afegeix sempre, i només es pot completar l'últim.</p></div>
      <div class="row"><button class="btn pri" type="submit">Començar la partida</button>${G?'<button class="btn" type="button" id="sf-cancel">Tornar a la partida</button>':''}</div>
    </form></div>`;
  drawSetupPlayers();drawSetupObjs();
}
function drawSetupPlayers(){
  const n=+$('#sf-np').value,box=$('#sf-players');
  const opts=sel=>CHARACTERS.map(c=>`<option value="${c.id}" ${c.id===sel?'selected':''}>${esc(c.name)}</option>`).join('');
  if(n===1){
    const def=['frodosam','legolas','arwen','gandalf','gimli'];
    box.innerHTML=`<div class="prow" style="grid-template-columns:repeat(auto-fit,minmax(150px,1fr))"><label class="field"><span>Participant</span><input class="in" id="sp-name-0" value="${esc(mem.get('users/'+S.uid)?.name||'')}"></label>${def.map((d,i)=>`<label class="field"><span>Personatge ${i+1}</span><select class="in" id="sp-c-0-${i}" ${i===0?'disabled':''}>${opts(d)}</select></label>`).join('')}</div><p class="small muted" style="margin:0">En solitari portes Frodo i Sam i 4 personatges més.</p>`;return;
  }
  box.innerHTML=Array.from({length:n},(_,i)=>`<div class="prow"><label class="field"><span>Participant ${i+1}</span><input class="in" id="sp-name-${i}" value="${i===0?esc(mem.get('users/'+S.uid)?.name||''):''}" placeholder="Nom"></label><label class="field"><span>Personatge</span><select class="in" id="sp-c-${i}-0">${opts(SUGGESTED[i][0])}</select></label><label class="field"><span>Personatge</span><select class="in" id="sp-c-${i}-1">${opts(SUGGESTED[i][1])}</select></label></div>`).join('');
}
function drawSetupObjs(fill){
  const lv=LEVELS[$('#sf-level').value],k=lv.obj-1,cur=fill||$$('[data-obj]').map(s=>s.value);
  $('#sf-objs').innerHTML=Array.from({length:k},(_,i)=>`<select class="in" data-obj="${i}"><option value="">Tria un objectiu…</option>${OBJECTIVES.map(o=>`<option ${cur[i]===o?'selected':''}>${esc(o)}</option>`).join('')}</select>`).join('');
}

/* --- Partides tab --- */
async function campApi(body){
  const opt=body?{method:'POST',headers:{'Content-Type':'application/json','X-Taula-Token':S.token},body:JSON.stringify(body)}:{headers:{'X-Taula-Token':S.token},cache:'no-store'};
  const r=await fetch('api/campaigns',opt);const d=await r.json().catch(()=>({}));if(!r.ok)throw new Error(d.error||'No s\'ha pogut fer.');return d;
}
async function renderCamps(){
  $('#main').innerHTML=`<div class="camps"><div><h2 style="font-size:32px">Partides guardades</h2><p class="muted" style="margin:6px 0 0;max-width:62ch">Cada partida guarda les pistes, el torn, els objectius i el registre. Quan n'obris una, tots els que estan connectats hi passen.</p></div>
    <form class="panel camp-new" id="camp-new"><label class="field"><span>Partida nova</span><input class="in" id="cn-name" required maxlength="80" placeholder="Divendres amb la colla"></label><button class="btn pri" type="submit">Crear i obrir</button></form>
    <div id="camp-list" class="camp-list"><p class="muted">Carregant…</p></div></div>`;
  if(!S.token){$('#camp-list').innerHTML='<p class="muted">Obri l\'app des del servidor per a gestionar partides.</p>';return}
  try{drawCampList(await campApi())}catch(e){$('#camp-list').innerHTML=`<p class="small" style="color:var(--blood)">${esc(e.message)}</p>`}
}
function drawCampList(d){
  const box=$('#camp-list');if(!box)return;
  box.innerHTML=d.list.map(c=>`<article class="camp-card${c.active?' on':''}"><div class="cc-head"><h3 class="cc-name">${esc(c.name)}</h3>${c.active?'<span class="chip dm">Oberta</span>':''}</div>
    <p class="muted small" style="margin:0;font-style:italic">Darrer canvi ${ago(c.updated)}</p>
    <div class="row" style="margin-top:6px">${c.active?'':`<button class="btn pri sm" data-copen="${c.id}">Obrir</button>`}<button class="btn sm" data-cdup="${c.id}">Duplicar</button>${c.active?'':`<button class="btn sm danger" data-cdel="${c.id}">Esborrar</button>`}</div></article>`).join('');
}

function renderTab(){if(!st.loaded)return;if(st.tab==='partida')renderPlay();else if(st.tab==='comunitat')renderCommunity();else renderCamps()}
function renderAll(){renderHeader();renderTracks();renderSide();if(st.tab!=='partides')renderTab()}

/* ================= events ================= */
document.addEventListener('click',e=>{
  const t=e.target;
  // tracks
  if(t.closest('#tracks')&&G){
    const hp=t.closest('[data-hope]');if(hp){const d=+hp.dataset.hope;commit(`${d>0?'+':''}${d} d'esperança`,(s,log)=>hopeDelta(s,d,log,'canvi manual'));return}
    const th=t.closest('[data-thr]');if(th){const d=+th.dataset.thr;commit('Canviar l\'amenaça',(s,log)=>{s.threatIdx=clamp(s.threatIdx+d,0,s.threat.length-1);log.push({t:`Amenaça: ${threatNow(s)} cartes d'Ombra per torn.`})});return}
    const dk=t.closest('[data-deck]');if(dk){commit('Ajustar el mazo',(s,log)=>{s.deck=Math.max(0,s.deck+(+dk.dataset.deck));log.push({t:`Mazo de joc: ${s.deck} cartes.`})});return}
    if(t.id==='undo'){undo();return}
  }
  // sidebar
  if(t.closest('#side2')&&G){
    const ap=t.closest('[data-ap]');if(ap){const[w,i]=ap.dataset.ap.split(':').map(Number);commit('Comptador d\'accions',(s,log)=>{const cur=s.turn.a[w];s.turn.a[w]=(i<cur)?i:i+1;log.push({t:`Accions: ${s.turn.a[0]} de 4 i ${s.turn.a[1]} d'1.`})});return}
    if(t.id==='acts-done'){commit('Accions fetes',(s,log)=>{s.turn.step=1;log.push({t:'Accions fetes.'})});return}
    if(t.id==='draw2'){commit('Robar 2 cartes',(s,log)=>{const can=Math.min(2,s.deck);s.deck-=can;log.push({t:`Es roben ${can} cartes de joc. Queden ${s.deck}.`});if(can<2)hopeDelta(s,-(2-can),log,'el mazo de joc s\'ha acabat');s.turn.step=Math.max(s.turn.step,2)});return}
    if(t.id==='skies'){skiesFlow();return}
    if(t.id==='shadow-card'){shadowCardFlow();return}
    if(t.id==='next-turn'){
      const n=threatNow(G);
      if(G.turn.shadow<n&&!t.dataset.armed){armed(t,nextTurn,`Només n'has resolt ${G.turn.shadow} de ${n}. Prem de nou`);return}
      if(t.dataset.armed)delete t.dataset.armed;nextTurn();return;
    }
  }
  // play tab
  if(st.tab==='partida'&&G&&t.closest('#main')){
    const inc=t.closest('[data-cinc]'),dec=t.closest('[data-cdec]');
    if(inc||dec){const k=(inc||dec).dataset.cinc||(dec&&dec.dataset.cdec);G.calc[k]=Math.max(0,(G.calc[k]||0)+(inc?1:-1));write('game/state',G);renderPlay();return}
    const bk=t.closest('[data-bk]');if(bk){G.calc.bKind=bk.dataset.bk;write('game/state',G);renderPlay();return}
    if(t.id==='t-search'){doSearch();return}
    if(t.id==='t-ring'){commit('Frodo es posa l\'Anell',(s,log)=>{hopeDelta(s,-1,log,'Frodo es posa l\'Anell');log.push({t:'Al tauler: desplaça l\'Ull a la regió de Frodo.'})});doSearch({ring:true,label:'Cerca amb l\'Anell'});return}
    if(t.id==='t-battle'){doBattle();return}
    const hev=t.closest('[data-hev]');if(hev){const[d,...why]=hev.dataset.hev.split(':');commit(`Esperança: ${why.join(':')}`,(s,log)=>hopeDelta(s,+d,log,why.join(':')));return}
    if(t.id==='t-doom'){openModal(`<h2>Destruir l'Anell Únic</h2><p style="margin:0">Frodo és a la Muntanya del Destí i gasta <b>5 de Destí</b>. Si després de la tirada l'esperança és 1 o més, guanyeu.</p><div class="foot"><button class="btn" id="d-no">Encara no</button><button class="btn pri" id="d-yes">Tirar</button></div>`,(m,close)=>{$('#d-no',m).onclick=close;$('#d-yes',m).onclick=()=>{close();doSearch({doom:true,label:'Intent de destruir l\'Anell'})}});return}
  }
  // community tab
  if(st.tab==='comunitat'&&t.id==='re-setup'){armed(t,()=>{st.forceSetup=true;renderTab()},'Segur? Prem de nou');return}
  if(t.id==='sf-cancel'){st.forceSetup=false;renderTab();return}
});
document.addEventListener('change',e=>{
  const t=e.target;
  if(t.dataset.cchk&&G){G.calc[t.dataset.cchk]=t.checked;write('game/state',G);renderPlay();return}
  if(t.dataset.objdone&&G){const o=G.objectives.find(x=>x.id===t.dataset.objdone);commit(`${t.checked?'Completat':'Desmarcat'}: ${o.name}`,(s,log)=>{s.objectives.find(x=>x.id===o.id).done=t.checked;log.push({t:`${t.checked?'Objectiu completat':'Objectiu desmarcat'}: ${o.name}. Aplica el seu «En completar-lo».`,c:t.checked?'good':''})});return}
  if(t.dataset.setup!=null&&G){const i=+t.dataset.setup;G.setup[i]=t.checked;write('game/state',G);renderCommunity();return}
  if(!$('#setup-form'))return;
  if(t.id==='sf-np'){lsSet('cm-np',t.value);drawSetupPlayers()}
  if(t.id==='sf-level')drawSetupObjs();
  if(t.id==='sf-scen'&&t.value!==''){const sc=SCENARIOS[+t.value];$('#sf-level').value=sc.level[0];drawSetupObjs(sc.obj.map(i=>OBJECTIVES[i]))}
});
document.addEventListener('submit',async e=>{
  if(e.target.id==='setup-form'){
    e.preventDefault();
    const n=+$('#sf-np').value,players=[];
    if(n===1)players.push({name:$('#sp-name-0').value.trim()||'Participant',chars:[0,1,2,3,4].map(i=>$(`#sp-c-0-${i}`).value)});
    else for(let i=0;i<n;i++)players.push({name:$(`#sp-name-${i}`).value.trim()||`Participant ${i+1}`,chars:[$(`#sp-c-${i}-0`).value,$(`#sp-c-${i}-1`).value]});
    const all=players.flatMap(p=>p.chars);
    if(new Set(all).size!==all.length){toast('Cada personatge només el pot portar un participant.');return}
    if(!all.includes('frodosam')){toast('Algú ha de portar Frodo i Sam.');return}
    const objs=$$('[data-obj]').map(s=>s.value).filter(Boolean),level=$('#sf-level').value;
    if(new Set(objs).size!==objs.length){toast('Hi ha objectius repetits.');return}
    if(objs.length<LEVELS[level].obj-1){toast(`Tria ${LEVELS[level].obj-1} objectius.`);return}
    const before=G;G=newGame({level,players,objectives:objs});
    UNDO=before?[{label:'Preparar una partida nova',state:before}]:[];
    LOG=[{t:`Partida preparada: ${LEVELS[level].name}, ${plural(n,'participant','participants')}. Mazo de joc: ${G.deck} cartes. Mira la pestanya Comunitat per a preparar el tauler.`,ts:Date.now(),who:mem.get('users/'+S.uid)?.name||''}];
    write('game/state',G);write('game/undo',{stack:UNDO});write('game/log',{list:LOG});
    st.forceSetup=false;st.tab='comunitat';lsSet('cm-tab2','comunitat');renderAll();return;
  }
  if(e.target.id==='camp-new'){e.preventDefault();const n=$('#cn-name').value.trim();if(!n)return;try{await campApi({action:'create',name:n});lsSet('cm-tab2','partida')}catch(err){toast(err.message)}}
});
document.addEventListener('click',async e=>{
  if(st.tab!=='partides')return;
  const o=e.target.closest('[data-copen]'),du=e.target.closest('[data-cdup]'),de=e.target.closest('[data-cdel]');
  try{
    if(o){o.disabled=true;lsSet('cm-tab2','partida');await campApi({action:'switch',id:o.dataset.copen})}
    if(du){drawCampList(await campApi({action:'duplicate',id:du.dataset.cdup}));toast('Partida duplicada.')}
    if(de)armed(de,async()=>{try{drawCampList(await campApi({action:'delete',id:de.dataset.cdel}));toast('Partida esborrada. Està a la carpeta partides/esborrades si la necessites.')}catch(err){toast(err.message)}},'Prem de nou per a esborrar');
  }catch(err){toast(err.message);if(o)o.disabled=false}
});
function nextTurn(){commit('Torn següent',(s,log)=>{const np=(s.turn.p+1)%s.players.length;if(np===0)s.round++;s.turn={p:np,step:0,a:[0,0],shadow:0};log.push({t:`Torn de ${s.players[np].name||'participant '+(np+1)}.`})})}
$('.tabs').addEventListener('click',e=>{const t=e.target.closest('[data-tab]');if(!t)return;st.tab=t.dataset.tab;st.forceSetup=false;lsSet('cm-tab2',st.tab);renderHeader();renderTab()});
$('#camp-name').addEventListener('input',e=>{CAMP={...(CAMP||{}),name:e.target.value};clearTimeout(window.__cn);window.__cn=setTimeout(()=>write('campaign/main',CAMP),500)});
$('#who').addEventListener('click',e=>{if(e.target.id==='logout')armed(e.target,()=>{lsSet('cm-token','');location.reload()},'Segur? Prem de nou')});

/* ================= connection ================= */
let lanFirst=null,lanPoll=null,lanErrs=[],lanBannerT=null,lanLast=Date.now();
function showBanner(t){const b=$('#banner');if(b.classList.contains('endstate'))return;b.textContent=t;b.hidden=!t}
function lanOk(){clearTimeout(lanBannerT);lanBannerT=null;showBanner('')}
function lanTrouble(){if(!lanBannerT)lanBannerT=setTimeout(()=>showBanner('S\'ha perdut la connexió amb el servidor. Tornant a connectar…'),5000)}
function applySnapshot(d){
  S.uid=d.me.uid;
  if(S.camp&&d.campaign&&d.campaign!==S.camp){location.reload();return false}
  S.camp=d.campaign;
  if(lanFirst){mem.clear();for(const p in d.docs)mem.set(p,d.docs[p]);const f=lanFirst;lanFirst=null;f();return true}
  const changed=[];
  for(const p of [...mem.keys()])if(!(p in d.docs)){mem.delete(p);changed.push(p)}
  for(const p in d.docs)if(JSON.stringify(mem.get(p))!==JSON.stringify(d.docs[p])){mem.set(p,d.docs[p]);changed.push(p)}
  for(const p of changed)memNotify(p);return true;
}
function startPolling(){
  if(lanPoll)return;if(S.es){S.es.close();S.es=null}
  const tick=async()=>{try{const r=await fetch('api/snapshot',{headers:{'X-Taula-Token':S.token},cache:'no-store'});if(r.status===401){lsSet('cm-token','');location.reload();return}if(!r.ok)throw 0;if(applySnapshot(await r.json()))lanOk()}catch(_){lanTrouble()}lanPoll=setTimeout(tick,2000)};
  lanPoll=setTimeout(tick,0);
}
function lanConnect(){
  if(lanPoll)return;if(S.es)S.es.close();
  const es=new EventSource('api/events?t='+encodeURIComponent(S.token));S.es=es;
  es.addEventListener('snapshot',e=>{lanLast=Date.now();if(applySnapshot(JSON.parse(e.data)))lanOk()});
  es.addEventListener('ping',()=>{lanLast=Date.now()});
  es.addEventListener('campaign',()=>{showBanner('S\'ha obert una altra partida. Carregant…');setTimeout(()=>location.reload(),500)});
  es.addEventListener('doc',e=>{lanLast=Date.now();const d=JSON.parse(e.data);if(d.data==null)mem.delete(d.path);else mem.set(d.path,d.data);memNotify(d.path)});
  es.onerror=()=>{lanTrouble();const now=Date.now();lanErrs=lanErrs.filter(t=>now-t<60000);lanErrs.push(now);if(lanErrs.length>=3)startPolling();else if(es.readyState===2)setTimeout(lanConnect,3000)};
}
function joinScreen(){
  return new Promise(resolve=>{
    $('.tabs').hidden=true;
    $('#main').innerHTML=`<form id="join" class="panel" style="max-width:440px;display:flex;flex-direction:column;gap:14px"><h2>Uneix-te a la Comunitat</h2>
      <label class="field"><span>El teu nom</span><input class="in" id="j-name" required maxlength="40" autocomplete="nickname"></label>
      <p class="small" id="j-err" style="margin:0;color:var(--blood)"></p><button class="btn pri" type="submit">Entrar</button></form>`;
    $('#j-name').focus();
    $('#join').addEventListener('submit',async e=>{e.preventDefault();$('#j-err').textContent='';
      try{const r=await fetch('api/join',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:$('#j-name').value})});const d=await r.json();
        if(!r.ok){$('#j-err').textContent=d.error||'No s\'ha pogut entrar.';return}lsSet('cm-token',d.token);$('.tabs').hidden=false;resolve(d)}
      catch(_){$('#j-err').textContent='No es pot contactar amb el servidor.'}});
  });
}
function startSubs(){
  watchDoc('campaign/main',d=>{CAMP=d;renderHeader()});
  watchDoc('game/state',d=>{const ng=d&&d.v===2?d:null;
    const focused=document.activeElement&&document.activeElement.closest('#main')&&document.activeElement.matches('input,select');
    G=ng;if(st.loaded){renderHeader();renderTracks();renderSide();if(!focused&&!$('.modal')&&st.tab!=='partides')renderTab()}});
  watchDoc('game/log',d=>{LOG=d?.list||[];if(st.loaded)renderSide()});
  watchDoc('game/undo',d=>{UNDO=d?.stack||[];if(st.loaded)renderTracks()});
  setTimeout(()=>{st.loaded=true;renderAll();renderTab()},30);
  setInterval(()=>{if(document.visibilityState==='visible'&&st.loaded&&!$('.modal'))renderSide()},30000);
}
async function boot(){
  let ok=false;
  if(/^https?:$/.test(location.protocol)){try{const r=await fetch('api/hello',{cache:'no-store'});ok=r.ok}catch(_){}}
  if(!ok){
    S.uid='local';mem.set('users/local',{name:'Tu'});
    mem.set('game/state',newGame({level:'intro',players:[{name:'Tu',chars:['frodosam','legolas']},{name:'Company',chars:['gandalf','aragorn']}],objectives:OBJECTIVES.slice(0,3)}));
    showBanner('Mode de prova: obri la pàgina a través del servidor (python3 comunitat.py) perquè es guarde i es compartisca.');
    startSubs();return;
  }
  let tok=lsGet('cm-token'),me=null;
  if(tok){try{const r=await fetch('api/join',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:tok})});if(r.ok)me=await r.json()}catch(_){}}
  if(!me)me=await joinScreen();
  S.token=me.token;S.uid=me.uid;
  await new Promise(res=>{lanFirst=res;lanConnect();setTimeout(()=>{if(lanFirst)startPolling()},5000)});
  setInterval(()=>{if(!lanPoll&&Date.now()-lanLast>35000)startPolling()},5000);
  startSubs();
}
boot();
})();

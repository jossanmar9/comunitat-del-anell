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
function lsGet(k){try{return localStorage.getItem(k)}catch(e){return null}}
function lsSet(k,v){try{localStorage.setItem(k,v)}catch(e){}}

/* ================= idioma / idioma ================= */
// Les claus són el text en valencià; I18N.es té la traducció al castellà.
let LANG=lsGet('cm-lang')||(/^es/i.test(navigator.language||'')&&!/^ca|^va/i.test(navigator.language||'')?'es':'val');
function t(k,v){
  let s=(LANG==='es'&&I18N.es[k]!=null)?I18N.es[k]:k;
  if(v)s=s.replace(/\{(\w+)\}/g,(m,n)=>v[n]==null?m:T(v[n]));
  return s;
}
// T: tradueix un missatge guardat ({k,v}), una clau o un número.
function T(x){if(x==null)return'';if(typeof x==='number')return String(x);if(typeof x==='object'&&x.k!=null)return t(x.k,x.v);return t(String(x))}
const M=(k,v)=>v?{k,v}:{k};
const pl=(n,a,b)=>`${n} ${t(n===1?a:b)}`;
function ago(ts){const s=(Date.now()-ts)/1000;if(s<45)return t('ara');if(s<3600)return t('fa {n} min',{n:Math.round(s/60)});if(s<86400)return t('fa {n} h',{n:Math.round(s/3600)});return new Date(ts).toLocaleDateString(LANG==='es'?'es':'ca')}
let toastT;function toast(m){const el=$('#toast');el.textContent=m;el.hidden=false;clearTimeout(toastT);toastT=setTimeout(()=>el.hidden=true,3500)}
function armed(btn,fn,label){
  if(btn.dataset.armed){delete btn.dataset.armed;fn();return}
  btn.dataset.armed='1';const old=btn.textContent;btn.textContent=label||t('Prem de nou per a confirmar');
  setTimeout(()=>{if(btn.isConnected&&btn.dataset.armed){delete btn.dataset.armed;btn.textContent=old}},4000);
}
const initials=n=>{const w=n.split(/\s+(?:i|y)\s+|\s+/).filter(Boolean);return (w[0][0]+(w[1]?w[1][0]:w[0][1]||'')).toUpperCase()};
function applyStatic(){
  document.documentElement.lang=LANG==='es'?'es':'ca';
  document.title=t("Comunitat de l'Anell");
  $$('[data-i18n]').forEach(el=>{el.textContent=t(el.dataset.i18n)});
  $$('[data-i18n-ph]').forEach(el=>{el.placeholder=t(el.dataset.i18nPh);el.setAttribute('aria-label',t(el.dataset.i18nPh))});
  $$('[data-i18n-aria]').forEach(el=>{el.setAttribute('aria-label',t(el.dataset.i18nAria))});
}
function setLang(l){
  if(l===LANG)return;LANG=l;lsSet('cm-lang',l);MAP_OK=null;applyStatic();
  if(st.loaded){renderAll();if(st.tab==='partides')renderCamps()}else{renderHeader();const j=$('#join');if(j)joinRender()}
}
const langSwitch=()=>`<span class="langsw" role="group" aria-label="${esc(t('Idioma'))}"><button class="chip${LANG==='val'?' dm':''}" data-lang="val" aria-pressed="${LANG==='val'}">VAL</button><button class="chip${LANG==='es'?' dm':''}" data-lang="es" aria-pressed="${LANG==='es'}">CAS</button></span>`;
document.addEventListener('click',e=>{const b=e.target.closest('[data-lang]');if(b)setLang(b.dataset.lang)});

/* ================= tema (auto / clar / fosc) ================= */
let THEME=lsGet('cm-theme')||'auto';
function applyTheme(){if(THEME==='auto')document.documentElement.removeAttribute('data-theme');else document.documentElement.setAttribute('data-theme',THEME)}
applyTheme();
const THEME_NEXT={auto:'light',light:'dark',dark:'auto'};
const THEME_LBL={auto:'Tema: automàtic',light:'Tema: clar',dark:'Tema: fosc'};
const THEME_ICO={auto:'◐',light:'☀',dark:'☾'};
const themeBtn=()=>`<button class="chip ico" id="theme" title="${esc(t(THEME_LBL[THEME]))}" aria-label="${esc(t(THEME_LBL[THEME]))}">${THEME_ICO[THEME]}</button>`;
document.addEventListener('click',e=>{if(!e.target.closest('#theme'))return;THEME=THEME_NEXT[THEME];lsSet('cm-theme',THEME);applyTheme();renderHeader();toast(t(THEME_LBL[THEME]))});

/* ================= convidar amb QR ================= */
const QR_ICON='<svg viewBox="0 0 16 16" width="15" height="15" aria-hidden="true" fill="currentColor"><path d="M1 1h6v6H1zm1.5 1.5v3h3v-3zM9 1h6v6H9zm1.5 1.5v3h3v-3zM1 9h6v6H1zm1.5 1.5v3h3v-3zM9 9h2v2H9zm2 2h2v2h-2zm2-2h2v2h-2zm-4 4h2v2H9zm4 0h2v2h-2z"/></svg>';
async function inviteModal(){
  let d;try{const r=await fetch('api/invite',{cache:'no-store'});d=await r.json()}catch(_){toast(t('No es pot contactar amb el servidor.'));return}
  const list=d.list||[];let i=0;
  const draw=m=>{$('#qr-box',m).innerHTML=list[i].svg;$('#qr-url',m).textContent=list[i].url;$$('[data-qri]',m).forEach(b=>b.setAttribute('aria-pressed',+b.dataset.qri===i))};
  openModal(`<h2>${esc(t('Convida a la taula'))}</h2>
    <p class="muted" style="margin:0">${esc(t("Escaneja el codi amb la càmera del mòbil, o escriu l'adreça al navegador. Heu d'estar a la mateixa wifi."))}</p>
    <div class="qr-box" id="qr-box"></div><p class="qr-url" id="qr-url"></p>
    ${list.length>1?`<div class="row" style="justify-content:center"><span class="small muted">${esc(t("Si no funciona, prova una altra adreça:"))}</span>${list.map((x,j)=>`<button class="btn sm" data-qri="${j}">${j+1}</button>`).join('')}</div>`:''}
    <div class="foot"><button class="btn pri" id="qr-close">${esc(t('Tancar'))}</button></div>`,(m,close)=>{
    if(!list.length){$('#qr-box',m).textContent=t("No he trobat cap adreça de xarxa.");}else draw(m);
    m.addEventListener('click',e=>{const b=e.target.closest('[data-qri]');if(b){i=+b.dataset.qri;draw(m)}if(e.target.id==='qr-close')close()});
  });
}
document.addEventListener('click',e=>{if(e.target.closest('#invite'))inviteModal()});

const BATTLE_FACES=[['rout','Rebutjar',"Retira 1 tropa de l'Ombra."],['tie','Taules',"Retira 1 de l'Ombra i 1 aliada."],['over','Arrossegats',"Retira 1 aliada (s'ignora en un refugi)."],['naz','Natzgûl!','Si hi ha natzguls a la regió, retira 2 aliades.']];
const SEARCH_FACES=[['slip',"Frodo s'escapoleix",'Sense efecte.'],['tired','Fatiga',"Perd 1 d'esperança."],['seen','Al descobert',"Perd 1 d'esperança (s'ignora en un refugi)."],['call','Convocatòria','Si hi ha natzguls, 1 torna a Mordor.']];

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
    try{await doWrite(path,mode,data)}catch(e){await new Promise(r=>setTimeout(r,500));try{await doWrite(path,mode,data)}catch(e2){toast(t("No s'ha pogut guardar. Comprova la connexió amb el servidor."))}}}
  q.busy=false;
}

/* ================= game ================= */
const threatNow=s=>s.threat[clamp(s.threatIdx,0,s.threat.length-1)];
const objectivesLeft=s=>s.objectives.filter(o=>!o.ring&&!o.done).length;
function hopeDelta(s,d,log,why){
  if(!d)return;const before=s.hope;s.hope=clamp(s.hope+d,0,s.hopeMax);const real=s.hope-before;
  if(real)log.push({k:"{d} d'esperança: {why}. Ara {h}.",v:{d:(real>0?'+':'')+real,why,h:s.hope},c:real<0?'bad':'good'});
  else if(d>0)log.push({k:"L'esperança ja és al màxim ({why}).",v:{why}});
  if(s.hope<=0&&!s.result){s.result='lose';s.ended=Date.now();log.push({k:"Frodo ha perdut tota l'esperança. La partida s'ha perdut.",c:'bad'})}
}
function commit(label,fn){
  if(!G)return null;
  const before=clone(G),log=[];const extra=fn(G,log);
  UNDO.push({label,state:before});if(UNDO.length>30)UNDO.shift();
  const ts=Date.now(),who=mem.get('users/'+S.uid)?.name||'';
  if(!log.length)log.push({k:'{x}.',v:{x:label}});
  LOG=[...log.map(e=>({...e,ts,who})).reverse(),...LOG].slice(0,600);
  write('game/state',G);write('game/undo',{stack:UNDO});write('game/log',{list:LOG});
  renderAll();return extra;
}
function undo(){
  if(!UNDO.length){toast(t('No hi ha res per desfer.'));return}
  const u=UNDO.pop();G=u.state;
  LOG=[{k:'Desfet: {x}.',v:{x:u.label},ts:Date.now()},...LOG].slice(0,600);
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
// El nom d'un personatge sempre es pren de les dades actuals (així es tradueix).
const charName=c=>t((CHARACTERS.find(x=>x.id===c.id)||c).name);
const charStart=c=>t((CHARACTERS.find(x=>x.id===c.id)||c).start);
const playerName=(p,i)=>p&&p.name?p.name:t('Participant {n}',{n:i+1});

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
    $('#fc',m).innerHTML=faces.map(([k,nm,d])=>`<div class="face"><div><div class="fn">${esc(t(nm))}</div><div class="fd">${esc(t(d))}</div></div><div class="stepper"><button class="mini" data-dec="${k}" aria-label="${esc(t('Menys'))}">−</button><b>${counts[k]}</b><button class="mini" data-inc="${k}" aria-label="${esc(t('Més'))}">+</button></div></div>`).join('')+(valor?`<div class="face"><div><div class="fn">${esc(t('Valor gastat'))}</div><div class="fd">${esc(t("Cada valor retira 1 tropa de l'Ombra."))}</div></div><div class="stepper"><button class="mini" data-vdec>−</button><b>${val}</b><button class="mini" data-vinc>+</button></div></div>`:'');
    $('#fsum',m).textContent=upTo?t('{s} {daus} (fins a {n})',{s:sum,daus:sum===1?'dau anotat':'daus anotats',n}):t('{s} de {n} {daus} anotats',{s:sum,n,daus:n===1?'dau':'daus'});
    $('#fok',m).disabled=upTo?(sum<1||sum>n):sum!==n;
  };
  openModal(`<h2>${esc(title)}</h2><p class="muted" style="margin:0">${intro}</p>
    <div class="row"><span class="big-n">${n}</span><span class="muted">${esc(t(upTo?'daus com a màxim':n===1?'dau a tirar':'daus a tirar'))}</span></div>
    <p class="small muted" style="margin:0">${esc(t('Tira els daus, fes les tornades a tirar amb Destí, i anota el resultat final de cada dau.'))}</p>
    <div class="faces" id="fc"></div><p class="small" id="fsum" style="margin:0"></p>
    <div class="foot"><button class="btn" id="fcancel">${esc(t('Cancel·lar'))}</button><button class="btn pri" id="fok">${esc(t('Aplicar'))}</button></div>`,(m,close)=>{
    draw(m);
    m.addEventListener('click',e=>{
      const b=e.target.closest('button');if(!b)return;const sum=Object.values(counts).reduce((a,c)=>a+c,0);
      if(b.dataset.inc&&sum<n)counts[b.dataset.inc]++;if(b.dataset.dec&&counts[b.dataset.dec]>0)counts[b.dataset.dec]--;
      if('vinc' in b.dataset)val++;if('vdec' in b.dataset&&val>0)val--;
      if(b.id==='fcancel'){close();return}if(b.id==='fok'){close();onApply({...counts},val);return}
      draw(m);
    });
  });
}
function infoModal(title,html){openModal(`<h2>${esc(title)}</h2>${html}<div class="foot"><button class="btn pri" id="ok">${esc(t("D'acord"))}</button></div>`,(m,close)=>{$('#ok',m).onclick=close})}

/* ================= calculators ================= */
const C=()=>G.calc;
function searchDice(){const c=C();return Math.min(7,c.naz+(c.ring?0:c.troops))}
function battleDice(){const c=C();return c.bKind==='attack'?clamp(c.bFr,1,3):Math.min(3,c.bSh)}
function doSearch({ring=false,doom=false,label}={}){
  const c=C();let n=c.naz+(ring?0:c.troops);if(doom)n+=G.hopeMax-G.hope;n=Math.min(7,n);
  const finish=res=>commit(label||M('Tirada de cerca'),(s,log)=>{
    if(res){
      log.push({k:"Tirada de cerca: {a} s'escapoleix, {b} fatiga, {c} al descobert, {d} convocatòria.",v:{a:res.slip,b:res.tired,c:res.seen,d:res.call}});
      if(res.tired)hopeDelta(s,-res.tired,log,M('fatiga ({n})',{n:res.tired}));
      if(res.seen){if(s.calc.haven)log.push({k:'Al descobert ignorat: Frodo és en un refugi.'});else hopeDelta(s,-res.seen,log,M('al descobert ({n})',{n:res.seen}))}
      if(res.call&&!s.calc.mordor&&s.calc.naz){const k=Math.min(res.call,s.calc.naz);log.push({k:'Al tauler: torna {n} de la regió de Frodo a Mordor.',v:{n:M(k===1?'1 natzgûl':'{k} natzguls',{k})}});s.calc.naz-=k}
    }else log.push({k:"Tirada de cerca: no hi havia natzguls ni tropes de l'Ombra, no cal tirar."});
    if(doom&&s.hope>=1){s.result='win';s.ended=Date.now();s.objectives.forEach(o=>{if(o.ring)o.done=true});log.push({k:"L'Anell Únic ha estat destruït! La Comunitat guanya la partida.",c:'good'})}
  });
  if(!n){finish(null);return}
  diceModal({title:t(doom?"Destruir l'Anell Únic":ring?"Frodo es posa l'Anell":'Tirada de cerca'),
    intro:esc(doom?t("{a} natzguls + {b} tropes de l'Ombra + {c} caselles per damunt de l'esperança. Màxim 7.",{a:c.naz,b:c.troops,c:G.hopeMax-G.hope})
      :ring?t("{a} natzguls a la regió de Frodo (l'Anell ignora les tropes). Màxim 7.",{a:c.naz})
      :t("{a} natzguls a la regió de Frodo + {b} tropes de l'Ombra al seu lloc. Màxim 7.",{a:c.naz,b:c.troops})),
    n,faces:SEARCH_FACES,onApply:res=>finish(res)});
}
function doBattle(){
  const c=C(),n=battleDice();
  if(c.bKind==='attack'&&(!c.bFr||!c.bSh)){toast(t("Per a atacar cal que hi haja tropes aliades i de l'Ombra al lloc."));return}
  if(!n){toast(t("No hi ha tropes de l'Ombra: no hi ha batalla."));return}
  diceModal({title:t('Tirada de batalla'),
    intro:esc(c.bKind==='attack'?t("Atac d'un personatge: fins a {n} {daus} (1 per tropa aliada, mínim 1, màxim 3). Pots tirar-ne menys. Recorda desplaçar l'Ull a la regió.",{n,daus:n===1?'dau':'daus'}):t("La provoca l'Ombra: 1 dau per tropa de l'Ombra (màxim 3). L'Ull no es mou.")),
    n,upTo:c.bKind==='attack',faces:BATTLE_FACES,valor:true,
    onApply:(res,val)=>{
      let sh=c.bSh,fr=c.bFr;const rem=k=>{if(k==='s'&&sh>0)sh--;if(k==='f'&&fr>0)fr--};
      for(let i=0;i<res.rout;i++)rem('s');
      for(let i=0;i<res.tie;i++){rem('s');rem('f')}
      if(!c.bHaven)for(let i=0;i<res.over;i++)rem('f');
      if(c.bNaz)for(let i=0;i<res.naz*2;i++)rem('f');
      for(let i=0;i<val;i++)rem('s');
      const lostSh=c.bSh-sh,lostFr=c.bFr-fr,havenLost=c.bHaven&&sh>0&&fr===0;
      commit(M('Tirada de batalla'),(s,log)=>{
        log.push({k:"Batalla{atac}: {a} rebutjar, {b} taules, {c} arrossegats, {d} Natzgûl!{val}. Al tauler: retira {sh} de l'Ombra i {fr}.",
          v:{atac:c.bKind==='attack'?M(' (atac)'):'',a:res.rout,b:res.tie,c:res.over,d:res.naz,val:val?M(', {n} de valor',{n:val}):'',
             sh:M(lostSh===1?'1 tropa':'{n} tropes',{n:lostSh}),fr:M(lostFr===1?'1 aliada':'{n} aliades',{n:lostFr})}});
        s.calc.bSh=sh;s.calc.bFr=fr;
        if(havenLost){log.push({k:"L'Ombra ha conquerit el refugi: posa-hi una fitxa de fortalesa de l'Ombra.",c:'bad'});hopeDelta(s,-3,log,M('refugi perdut'))}
      });
      infoModal(t('Resultat de la batalla'),`<p style="margin:0;font-size:19px">${t("Retira <b>{a} de l'Ombra</b> i <b>{b}</b>.",{a:pl(lostSh,'tropa','tropes'),b:pl(lostFr,'tropa aliada','tropes aliades')})}</p><p class="muted" style="margin:0">${esc(t("Hi queden {a} de l'Ombra i {b} aliades.",{a:sh,b:fr}))}${c.bHaven&&res.over?' '+esc(t("Els «arrossegats» s'han ignorat perquè és un refugi.")):''}${!c.bNaz&&res.naz?' '+esc(t('Els «Natzgûl!» no fan res: no hi ha natzguls a la regió.')):''}</p>${havenLost?`<p style="margin:0;color:var(--blood)">${t("<b>Refugi perdut:</b> posa-hi una fitxa de fortalesa de l'Ombra. Ja he restat 3 d'esperança.")}</p>`:''}`);
    }});
}
function skiesFlow(){
  openModal(`<h2>${esc(t("El cel s'enfosqueix"))}</h2>
    <ol class="steps">
      <li><div><b>${esc(t("L'Ombra creix."))}</b> ${esc(t("Pujaré l'amenaça 1 casella."))}</div></li>
      <li><div><b>${esc(t('Et veig!'))}</b> ${esc(t("L'Ull de Sauron és ara a la regió de Frodo?"))}
        <div class="radio-list" style="margin-top:8px"><label><input type="radio" name="eye" value="yes"><span>${esc(t("Sí: perdeu 2 d'esperança."))}</span></label><label><input type="radio" name="eye" value="no" checked><span>${esc(t("No: desplaça l'Ull a la regió de Frodo."))}</span></label></div></div></li>
      <li><div><b>${esc(t("A l'empara de la foscor."))}</b> ${esc(t("Posa 3 tropes de l'Ombra al lloc de la carta. N'hi ha prou a la reserva?"))}
        <div class="row" style="margin-top:8px"><span class="small">${esc(t('Tropes que falten'))}</span><span class="stepper"><button class="mini" id="mdec">−</button><b id="miss">0</b><button class="mini" id="minc">+</button></span></div>
        <p class="small muted" style="margin:6px 0 0">${esc(t("Si hi ha tropes aliades en eixe lloc, fes després una tirada de batalla provocada per l'Ombra."))}</p></div></li>
      <li><div><b>${esc(t("El perill s'intensifica."))}</b> ${esc(t("Barreja els descarts d'Ombra i posa'ls damunt del mazo d'Ombra."))}</div></li>
    </ol>
    <div class="foot"><button class="btn" id="sk-cancel">${esc(t('Cancel·lar'))}</button><button class="btn pri" id="sk-ok">${esc(t('Fet'))}</button></div>`,(m,close)=>{
    let miss=0;
    m.addEventListener('click',e=>{
      const b=e.target.closest('button');if(!b)return;
      if(b.id==='minc'&&miss<3)miss++;if(b.id==='mdec'&&miss>0)miss--;$('#miss',m).textContent=miss;
      if(b.id==='sk-cancel')close();
      if(b.id==='sk-ok'){
        const yes=$('input[name=eye]:checked',m).value==='yes';close();
        commit(M("El cel s'enfosqueix"),(s,log)=>{
          s.skies.drawn=Math.min(s.skies.total,s.skies.drawn+1);
          log.push({k:"El cel s'enfosqueix ({a} de {b}).",v:{a:s.skies.drawn,b:s.skies.total},c:'bad'});
          if(s.threatIdx<s.threat.length-1){s.threatIdx++;log.push({k:"L'amenaça puja: ara es roben {n} cartes d'Ombra per torn.",v:{n:threatNow(s)},c:'bad'})}
          if(yes)hopeDelta(s,-2,log,M("Et veig! (l'Ull era a la regió de Frodo)"));else log.push({k:"Al tauler: desplaça l'Ull a la regió de Frodo."});
          if(miss)hopeDelta(s,-miss,log,M("no quedaven tropes de l'Ombra a la reserva"));
        });
      }
    });
  });
}
function shadowCardFlow(){
  openModal(`<h2>${esc(t("Carta d'Ombra"))}</h2>
    <p class="muted" style="margin:0">${esc(t("Mira la bandera que es veu al mazo d'Ombra."))}</p>
    <div class="faces">
      <div class="face" style="display:block"><div class="fn">${esc(t('Bandera roja: Avançar'))}</div><div class="fd">${esc(t("Mou totes les tropes de l'Ombra de la línia indicada 1 espai en la direcció de la fletxa, començant per les més avançades. Les del final no es mouen. Després, batalla a cada lloc de la línia amb tropes de les dues bandes (de la més avançada cap enrere). Si l'Ombra ocupa un refugi sense aliades, el perds."))}</div></div>
      <div class="face" style="display:block"><div class="fn">${esc(t('Bandera negra: Reforçar'))}</div><div class="fd">${esc(t("1 tropa de l'Ombra al lloc indicat (no si el vau capturar). Si hi ha aliades, batalla. Després, l'ordre especial: l'Ull a la regió de Frodo (o tirada de cerca si ja hi és) · acosta 2 natzguls a Frodo · desplega 3 natzguls de Mordor a la regió de l'Ull."))}</div></div>
    </div>
    <div class="radio-list">
      <label><input type="checkbox" id="sc-lost"><span>${esc(t("S'ha perdut un refugi (−3 d'esperança)"))}</span></label>
      <label><span>${esc(t("Tropes de l'Ombra que no es podien posar per falta de reserva"))}</span><span class="stepper" style="margin-left:auto"><button class="mini" id="sdec">−</button><b id="smiss">0</b><button class="mini" id="sinc">+</button></span></label>
    </div>
    <div class="foot"><button class="btn" id="sc-cancel">${esc(t('Cancel·lar'))}</button><button class="btn pri" id="sc-ok">${esc(t('Carta resolta'))}</button></div>`,(m,close)=>{
    let miss=0;
    m.addEventListener('click',e=>{
      const b=e.target.closest('button');if(!b)return;
      if(b.id==='sinc')miss++;if(b.id==='sdec'&&miss>0)miss--;$('#smiss',m).textContent=miss;
      if(b.id==='sc-cancel')close();
      if(b.id==='sc-ok'){const lost=$('#sc-lost',m).checked;close();
        commit(M("Carta d'Ombra resolta"),(s,log)=>{s.turn.shadow++;log.push({k:"Carta d'Ombra resolta ({a} de {b} aquest torn).",v:{a:s.turn.shadow,b:threatNow(s)}});if(lost)hopeDelta(s,-3,log,M('refugi perdut'));if(miss)hopeDelta(s,-miss,log,M("no quedaven tropes de l'Ombra a la reserva"))})}
    });
  });
}

/* ================= render ================= */
function renderHeader(){
  const n=$('#camp-name');if(document.activeElement!==n)n.value=CAMP?.name||'';
  $$('.tab').forEach(x=>x.setAttribute('aria-selected',x.dataset.tab===st.tab));
  $('#who').innerHTML=langSwitch()+themeBtn()+(S.token?`<button class="chip ico" id="invite" title="${esc(t('Convida a la taula'))}" aria-label="${esc(t('Convida a la taula'))}">${QR_ICON}</button>`:'')+(S.token?`<span class="chip">${esc(mem.get('users/'+S.uid)?.name||'')}</span><button class="chip" id="logout">${esc(t('Eixir'))}</button>`:'');
}
function renderTracks(){
  const el=$('#tracks');
  if(!G){el.innerHTML=`<span class="muted small">${esc(t('Cap partida preparada encara.'))}</span>`;return}
  el.innerHTML=`
    <div class="trk"><span class="lbl">${esc(t('Esperança'))}</span><button class="mini" data-hope="-1" aria-label="${esc(t('Perdre esperança'))}">−</button><span class="val">${G.hope}<small>/${G.hopeMax}</small></span><button class="mini" data-hope="1" aria-label="${esc(t('Guanyar esperança'))}">+</button>
      <span class="pips" aria-hidden="true">${Array.from({length:G.hopeMax},(_,i)=>`<i class="pip ${i<G.hope?'on':''} ${G.hope<=2?'low':''}"></i>`).join('')}</span></div>
    <div class="trk"><span class="lbl">${esc(t('Amenaça'))}</span><button class="mini" data-thr="-1" aria-label="${esc(t('Baixar amenaça'))}">−</button>
      <span class="pips">${G.threat.map((v,i)=>`<i class="pip thr ${i===G.threatIdx?'on':''}">${v}</i>`).join('')}</span><button class="mini" data-thr="1" aria-label="${esc(t('Pujar amenaça'))}">+</button></div>
    <div class="trk"><span class="lbl">${esc(t('Cel enfosquit'))}</span><span class="mono">${G.skies.drawn}/${G.skies.total}</span></div>
    <div class="trk"><span class="lbl">${esc(t('Mazo'))}</span><button class="mini" data-deck="-1" aria-label="${esc(t('Una carta menys'))}">−</button><span class="mono">${G.deck}</span><button class="mini" data-deck="1" aria-label="${esc(t('Una carta més'))}">+</button></div>
    <div class="trk"><span class="lbl">${esc(t('Objectius'))}</span><span class="mono">${G.objectives.filter(o=>o.done).length}/${G.objectives.length}</span></div>
    <div class="trk"><span class="lbl">${esc(t('Ronda'))}</span><span class="mono">${G.round}</span></div>
    <button class="btn sm" id="undo" ${UNDO.length?'':'disabled'} title="${UNDO.length?esc(t('Desfer: {x}',{x:UNDO[UNDO.length-1].label})):''}">${esc(t('Desfer'))}</button>`;
  const b=$('#banner');
  if(G.result){b.hidden=false;b.className='banner endstate '+G.result;b.innerHTML=`<span>${esc(G.result==='win'?t("L'Anell ha estat destruït. La Comunitat ha guanyat!"):t("Frodo ha perdut tota l'esperança. L'Ombra s'estén per la Terra Mitjana."))}</span> <button class="btn sm" id="sum-open">${esc(t('Veure el resum'))}</button>`}
  else if(b.classList.contains('endstate')){b.hidden=true;b.className='banner'}
}
const step=(id,label,val)=>`<span class="k">${esc(t(label))}</span><span class="stepper"><button class="mini" data-cdec="${id}" aria-label="${esc(t('Menys'))}">−</button><b>${val}</b><button class="mini" data-cinc="${id}" aria-label="${esc(t('Més'))}">+</button></span>`;
const chk=(id,label,on)=>`<label class="check"><input type="checkbox" data-cchk="${id}" ${on?'checked':''}> ${esc(t(label))}</label>`;
function renderPlay(){
  if(!G||st.forceSetup){renderSetup();return}
  const c=C(),sd=searchDice(),bd=battleDice(),left=objectivesLeft(G);
  const doomN=Math.min(7,c.naz+c.troops+(G.hopeMax-G.hope));
  const hev=(d,why,label)=>`<button class="btn" data-hev="${d}" data-why="${esc(why)}">${esc(t(label))} <b>${d>0?'+':'−'}${Math.abs(d)}</b></button>`;
  $('#main').innerHTML=`<div class="play">
    <div class="mapcol" id="mapcol">${mapPanel()}</div>
    <div class="tools">
    <section class="panel tool"><h2>${esc(t('Tirada de cerca'))}</h2>
      <p class="muted small" style="margin:0">${esc(t('Quan Frodo viatja sense gastar Sigil, o ho demana una carta.'))}</p>
      <div class="kv2">${step('naz','Natzguls a la regió de Frodo',c.naz)}${step('troops',"Tropes de l'Ombra al lloc de Frodo",c.troops)}</div>
      <div class="col">${chk('haven','Frodo és en un refugi',c.haven)}${chk('mordor','Frodo és a Mordor',c.mordor)}</div>
      <div class="row tool-foot"><span class="big-n">${sd}</span><span class="muted">${esc(t(sd===1?'dau':'daus'))}${sd?'':' · '+esc(t('no cal tirar'))}</span><button class="btn pri" id="t-search" style="margin-left:auto">${esc(t('Anotar la tirada'))}</button></div>
      <div class="row"><button class="btn sm" id="t-ring">${esc(t("Frodo es posa l'Anell"))}</button><span class="small muted">${esc(t("−1 d'esperança, l'Ull a la seua regió i cerca sense comptar tropes."))}</span></div>
    </section>
    <section class="panel tool"><h2>${esc(t('Tirada de batalla'))}</h2>
      <div class="row"><button class="btn sm" data-bk="attack" aria-pressed="${c.bKind==='attack'}">${esc(t("Atac d'un personatge"))}</button><button class="btn sm" data-bk="shadow" aria-pressed="${c.bKind==='shadow'}">${esc(t("La provoca l'Ombra"))}</button></div>
      <div class="kv2">${step('bFr','Tropes aliades al lloc',c.bFr)}${step('bSh',"Tropes de l'Ombra al lloc",c.bSh)}</div>
      <div class="col">${chk('bNaz','Hi ha natzguls a la regió',c.bNaz)}${chk('bHaven','El lloc és un refugi',c.bHaven)}</div>
      <div class="row tool-foot"><span class="big-n">${bd}</span><span class="muted">${esc(t(c.bKind==='attack'?'daus com a màxim':bd===1?'dau':'daus'))}</span><button class="btn pri" id="t-battle" style="margin-left:auto">${esc(t('Anotar la tirada'))}</button></div>
      ${c.bKind==='attack'?`<p class="small muted" style="margin:0">${esc(t("Abans de tirar, desplaça l'Ull de Sauron a la regió de l'atac."))}</p>`:''}
    </section>
    <section class="panel tool"><h2>${esc(t('Esperança'))}</h2>
      <div class="hopebtns">
        ${hev(-3,'refugi perdut','Refugi perdut')}
        ${hev(2,'fortalesa capturada','Fortalesa capturada')}
        ${hev(-1,"falta una tropa de l'Ombra a la reserva","Falta una tropa de l'Ombra")}
        ${hev(-1,'falta una carta de joc al mazo','Falta una carta de joc')}
        ${hev(-1,'objectiu o habilitat','Altres')}
        ${hev(1,'objectiu o habilitat','Altres')}
      </div>
      <p class="small muted" style="margin:0">${esc(t("En capturar una fortalesa, recorda desplaçar l'Ull a la seua regió. Capturar Mòria, Isengard, Dol Guldur o Umbar fa que no hi isquen més tropes."))}</p>
    </section>
    <section class="panel tool"><h2>${esc(t("Destruir l'Anell Únic"))}</h2>
      <p class="muted small" style="margin:0">${esc(t("Frodo, a la Muntanya del Destí, gasta 5 de Destí. Es fa una última cerca amb 1 dau extra per cada casella per damunt de l'esperança. Fa servir els natzguls i les tropes de la tirada de cerca."))}</p>
      <div class="row tool-foot"><span class="big-n">${doomN}</span><span class="muted">${esc(t(doomN===1?'dau':'daus'))} (${esc(t('màxim 7'))})</span><button class="btn pri" id="t-doom" style="margin-left:auto" ${left?'disabled':''}>${esc(t("Intentar-ho"))}</button></div>
      ${left?`<p class="small" style="margin:0;color:var(--blood)">${esc(t('Encara queden {n} per completar.',{n:pl(left,'objectiu','objectius')}))}</p>`:''}
    </section>
    <section class="panel tool"><h2>${esc(t('Objectius'))}</h2>
      ${G.objectives.map(o=>`<div class="obj ${o.done?'done':''}"><input type="checkbox" data-objdone="${o.id}" ${o.done?'checked':''} ${o.ring?'disabled':''} aria-label="${esc(t('Completat'))}"><span class="on">${esc(t(o.name))}</span>${o.ring?`<span class="badge" style="position:static">${esc(t('Últim'))}</span>`:''}</div>`).join('')}
    </section>
    <section class="panel tool"><h2>${esc(t('Referència ràpida'))}</h2>
      <dl class="ref">
        <dt>${esc(t('Viatjar amb Frodo'))}</dt><dd>${esc(t('Gasta 1 Sigil o fes una cerca al destí. Els camins especials costen els símbols que hi ha dibuixats.'))}</dd>
        <dt>${esc(t('Comunitat'))}</dt><dd>${esc(t('Al mateix lloc que un altre participant: dona-li o pren-li una carta de la teua regió.'))}</dd>
        <dt>${esc(t('Preparar'))}</dt><dd>${esc(t('En un refugi: descarta una carta de regió per a prendre la fitxa del seu símbol.'))}</dd>
        <dt>${esc(t('Reclutar'))}</dt><dd>${esc(t("En un lloc de color: 1 Amistat per 1 tropa d'eixe color."))}</dd>
        <dt>${esc(t('Capturar'))}</dt><dd>${esc(t("Fortalesa sense Ombra i amb 1 aliada: 3 Valor, l'Ull a la regió, +2 d'esperança."))}</dd>
        <dt>${esc(t('Límit de mà'))}</dt><dd>${esc(t('Set cartes. Els esdeveniments es poden jugar en qualsevol moment.'))}</dd>
      </dl>
    </section>
  </div>  </div>`;
}
let MAP_OK=null;
const mapSrc=()=>'mapa?lang='+LANG;
function mapPanel(){
  if(MAP_OK===false)return `<div class="empty"><b>${esc(t('Sense mapa'))}</b>${t('Posa una imatge anomenada <code>mapa.jpg</code> al costat de <code>comunitat.py</code> i recarrega la pàgina.')}</div>`;
  return `<figure class="mapfig"><button class="mapbtn" id="map-open" aria-label="${esc(t('Ampliar el mapa'))}"><img src="${mapSrc()}" alt="${esc(t('Mapa de la Terra Mitjana'))}" id="map-img"></button><figcaption class="small muted">${esc(t('Fes clic per a ampliar-lo.'))}</figcaption></figure>`;
}
document.addEventListener('error',e=>{if(e.target&&e.target.id==='map-img'){MAP_OK=false;const c=$('#mapcol');if(c)c.innerHTML=mapPanel()}},true);
document.addEventListener('click',e=>{
  if(!e.target.closest('#map-open'))return;
  openModal(`<div class="mapzoom"><img src="${mapSrc()}" alt="${esc(t('Mapa de la Terra Mitjana'))}"></div><div class="foot"><button class="btn pri" id="mz-close">${esc(t('Tancar'))}</button></div>`,(m,close)=>{m.classList.add('wide');$('#mz-close',m).onclick=close});
});
function renderSide(){
  const el=$('#side2');
  if(!G){el.innerHTML=`<h2>${esc(t('El torn'))}</h2><p class="muted small">${esc(t('Prepara una partida per a començar.'))}</p>`+logHtml();return}
  const TR=G.turn,p=G.players[TR.p],mine=G.chars.filter(c=>c.player===TR.p),n=threatNow(G);
  el.innerHTML=`<div><span class="eyebrow">${esc(t('Ronda {n} · torn de',{n:G.round}))}</span><div class="turn-who">${esc(playerName(p,TR.p))}</div><span class="muted small">${mine.map(c=>esc(charName(c))).join(' · ')}</span></div>
    <ol class="steps">
      <li class="${TR.step===0?'cur':'done'}"><div><b>${esc(t('Fes 4 + 1 accions'))}</b><div class="muted small">${esc(t(G.solo?'4 amb el personatge del testimoni i 1 amb Frodo i Sam.':"4 amb un personatge i 1 amb l'altre."))}</div>
        <div class="apips">${[0,1,2,3].map(i=>`<button class="apip ${i<TR.a[0]?'used':''}" data-ap="0:${i}" aria-label="${esc(t('Acció {n}',{n:i+1}))}">${i+1}</button>`).join('')}<button class="apip sep ${TR.a[1]?'used':''}" data-ap="1:0" aria-label="${esc(t('Acció extra'))}">+1</button></div>
        ${TR.step===0?`<div class="row" style="margin-top:8px"><button class="btn sm" id="acts-done">${esc(t('Fet'))}</button></div>`:''}</div></li>
      <li class="${TR.step===1?'cur':TR.step>1?'done':''}"><div><b>${esc(t('Roba 2 cartes de joc'))}</b><div class="muted small">${esc(t('Queden {n} al mazo. Si en robes un cel enfosquit, resol-lo.',{n:G.deck}))}</div>
        <div class="row" style="margin-top:8px"><button class="btn sm ${TR.step===1?'pri':''}" id="draw2">${esc(t('He robat 2 cartes'))}</button><button class="btn sm" id="skies">${esc(t("El cel s'enfosqueix!"))}</button></div></div></li>
      <li class="${TR.step===2?'cur':''}"><div><b>${esc(t("Roba {n} d'Ombra",{n:pl(n,'carta','cartes')}))}</b><div class="muted small">${esc(t('Resoltes: {a} de {b}.',{a:TR.shadow,b:n}))}</div>
        <div class="row" style="margin-top:8px"><button class="btn sm ${TR.step===2&&TR.shadow<n?'pri':''}" id="shadow-card">${esc(t("Resoldre una carta d'Ombra"))}</button></div></div></li>
    </ol>
    <button class="btn pri" id="next-turn">${esc(t('Passar al següent torn'))}</button>
    ${logHtml()}`;
}
const logText=e=>e.k!=null?t(e.k,e.v):(e.t||'');
function logHtml(){return `<h3>${esc(t('Registre'))}</h3><ol class="log2">${LOG.slice(0,100).map(e=>`<li class="${e.c||''}"><time>${ago(e.ts)}${e.who?' · '+esc(e.who):''}</time>${esc(logText(e))}</li>`).join('')||`<li class="muted">${esc(t('Encara no ha passat res.'))}</li>`}</ol>`}

/* --- resum de la partida --- */
const HOPE_KEY="{d} d'esperança: {why}. Ara {h}.";
function scenarioOf(objs){const set=objs.slice().sort().join('|');const sc=SCENARIOS.find(x=>x.obj.map(i=>OBJECTIVES[i]).sort().join('|')===set);return sc?sc.name:null}
function dur(ms){if(!(ms>0))return '—';const m=Math.round(ms/60000);if(m<60)return t('{n} min',{n:m});const h=Math.floor(m/60);return t('{h} h {m} min',{h,m:m%60})}
function gameStats(){
  const lost={},won={};let nLost=0,nWon=0,searches=0,battles=0,shadow=0;
  for(const e of LOG){
    if(e.k===HOPE_KEY&&e.v){const d=parseInt(e.v.d,10)||0,why=T(e.v.why)||'—';if(d<0){lost[why]=(lost[why]||0)-d;nLost-=d}else{won[why]=(won[why]||0)+d;nWon+=d}}
    else if(e.k&&e.k.startsWith('Tirada de cerca:'))searches++;
    else if(e.k&&e.k.startsWith('Batalla{atac}'))battles++;
    else if(e.k&&e.k.startsWith("Carta d'Ombra resolta ("))shadow++;
  }
  return {lost,won,nLost,nWon,searches,battles,shadow};
}
function summaryHtml(){
  const g=G,st2=gameStats(),objs=g.objectives.filter(o=>!o.ring),sc=scenarioOf(objs.map(o=>o.name));
  const rows=(o,sign)=>Object.entries(o).sort((a,b)=>b[1]-a[1]).map(([w,n])=>`<tr><td>${esc(w)}</td><td class="num">${sign}${n}</td></tr>`).join('');
  return `<div class="sum">
    <p class="sum-res ${g.result||''}">${esc(g.result==='win'?t('Victòria'):g.result==='lose'?t('Derrota'):t('En joc'))}</p>
    <p class="muted" style="margin:0">${esc(t(LEVELS[g.level]?.name||''))}${sc?' · '+esc(t(sc)):''} · ${g.players.map((p,i)=>esc(playerName(p,i))).join(', ')}</p>
    <div class="sum-grid">
      <div><b>${g.round}</b><span>${esc(t(g.round===1?'ronda':'rondes'))}</span></div>
      <div><b>${dur((g.ended||Date.now())-g.created)}</b><span>${esc(t('de joc'))}</span></div>
      <div><b>${g.hope}/${g.hopeMax}</b><span>${esc(t('esperança final'))}</span></div>
      <div><b>${g.objectives.filter(o=>o.done).length}/${g.objectives.length}</b><span>${esc(t('objectius'))}</span></div>
      <div><b>${st2.searches}</b><span>${esc(t('tirades de cerca'))}</span></div>
      <div><b>${st2.battles}</b><span>${esc(t('batalles'))}</span></div>
      <div><b>${g.skies.drawn}/${g.skies.total}</b><span>${esc(t('cels enfosquits'))}</span></div>
      <div><b>${st2.shadow}</b><span>${esc(t("cartes d'Ombra"))}</span></div>
    </div>
    ${st2.nLost?`<h3>${esc(t("On s'ha perdut l'esperança"))} <span class="muted">(−${st2.nLost})</span></h3><table class="sum-t">${rows(st2.lost,'−')}</table>`:''}
    ${st2.nWon?`<h3>${esc(t("On s'ha guanyat"))} <span class="muted">(+${st2.nWon})</span></h3><table class="sum-t">${rows(st2.won,'+')}</table>`:''}
    <h3>${esc(t('Objectius'))}</h3><ul class="sum-o">${g.objectives.map(o=>`<li class="${o.done?'done':''}">${o.done?'✓':'·'} ${esc(t(o.name))}</li>`).join('')}</ul>
  </div>`;
}
function summaryModal(){if(!G)return;openModal(`<h2>${esc(t('Resum de la partida'))}</h2>${summaryHtml()}<div class="foot"><button class="btn" id="sum-hist">${esc(t("Veure l'historial"))}</button><button class="btn pri" id="sum-close">${esc(t('Tancar'))}</button></div>`,(m,close)=>{$('#sum-close',m).onclick=close;$('#sum-hist',m).onclick=()=>{close();st.tab='partides';lsSet('cm-tab2','partides');renderHeader();renderTab()}})}
document.addEventListener('click',e=>{if(e.target.closest('#sum-open'))summaryModal()});
let lastResult=null;
function checkResult(){
  const key=G&&G.result?G.created+':'+G.result:null;
  if(key&&lastResult!==null&&key!==lastResult){const go=()=>{if($('.modal'))setTimeout(go,500);else summaryModal()};setTimeout(go,300)}
  lastResult=key||'';
}

/* --- Comunitat tab --- */
function renderCommunity(){
  if(!G||st.forceSetup){renderSetup();return}
  const done=G.setup.filter(Boolean).length;
  $('#main').innerHTML=`<div class="grid2">
    <section class="panel tool"><h2>${esc(t('Preparació'))}</h2><p class="muted small" style="margin:0">${esc(t('{a} de {b} passos fets.',{a:done,b:SETUP_STEPS.length}))}</p>
      ${SETUP_STEPS.map(([a,d],i)=>`<div class="obj ${G.setup[i]?'done':''}"><input type="checkbox" data-setup="${i}" ${G.setup[i]?'checked':''} aria-label="${esc(t(a))}"><span><span class="on">${esc(t(a))}</span><br><span class="small muted">${esc(t(d))}</span></span></div>`).join('')}
    </section>
    <section class="panel tool"><h2>${esc(t('La Comunitat'))}</h2>
      ${G.players.map((p,i)=>`<div><h3>${esc(playerName(p,i))}${G.turn.p===i?' · '+esc(t('torn')):''}</h3>${G.chars.filter(c=>c.player===i).map(c=>`<div class="row" style="justify-content:space-between;margin-top:6px"><span class="cchip"><span class="av" style="background:${c.color}">${esc(initials(charName(c)))}</span>${esc(charName(c))}</span><span class="small muted">${esc(t('Comença a {x}',{x:charStart(c)}))}</span></div>`).join('')}</div>`).join('')}
    </section>
    ${G.result?`<section class="panel tool"><h2>${esc(t('Resum de la partida'))}</h2>${summaryHtml()}</section>`:''}
    <section class="panel tool"><h2>${esc(t('Partida'))}</h2>
      <p class="muted small" style="margin:0">${esc(t('Dificultat {a} · {b} al mazo · començada {c}.',{a:t(LEVELS[G.level]?.name||''),b:pl(G.skies.total,'cel enfosquit','cels enfosquits'),c:ago(G.created)}))}</p>
      <button class="btn danger" id="re-setup">${esc(t('Preparar una partida nova'))}</button>
      <p class="small muted" style="margin:0">${esc(t('Per a conservar aquesta partida i començar-ne una altra, fes servir la pestanya Partides.'))}</p>
    </section></div>`;
}
function renderSetup(){
  const n=+(lsGet('cm-np')||2);
  $('#main').innerHTML=`<div class="camps" style="max-width:1000px">
    <div><h2 style="font-size:32px">${esc(t('Preparar la partida'))}</h2><p class="muted" style="margin:6px 0 0;max-width:66ch">${esc(t("Tria la dificultat, els participants i els objectius. L'app calcula el mazo de joc i et guia en la preparació del tauler."))}</p></div>
    <form class="panel" id="setup-form" style="display:flex;flex-direction:column;gap:16px">
      <div class="row" style="align-items:flex-end;gap:16px">
        <label class="field"><span>${esc(t('Dificultat'))}</span><select class="in" id="sf-level">${Object.entries(LEVELS).map(([k,v])=>`<option value="${k}" ${k==='intro'?'selected':''}>${esc(t('{a} · {b} cels enfosquits · {c} objectius',{a:t(v.name),b:v.skies,c:v.obj}))}</option>`).join('')}</select></label>
        <label class="field"><span>${esc(t('Participants'))}</span><select class="in" id="sf-np">${[1,2,3,4,5].map(i=>`<option ${i===n?'selected':''}>${i}</option>`).join('')}</select></label>
      </div>
      <div id="sf-players" class="plist"></div>
      <div><h3>${esc(t('Objectius'))}</h3><div class="row" style="margin:8px 0"><select class="in" id="sf-scen" style="width:auto"><option value="">${esc(t('Escenari suggerit…'))}</option>${SCENARIOS.map((s,i)=>`<option value="${i}">${esc(t(s.name))} (${s.level.map(l=>esc(t(LEVELS[l].name))).join('/')})</option>`).join('')}</select></div>
        <div id="sf-objs" class="plist"></div><p class="small muted" style="margin:6px 0 0">${esc(t("{x} s'afegeix sempre, i només es pot completar l'últim.",{x:RING_OBJ}))}</p></div>
      <div class="row"><button class="btn pri" type="submit">${esc(t('Començar la partida'))}</button>${G?`<button class="btn" type="button" id="sf-cancel">${esc(t('Tornar a la partida'))}</button>`:''}</div>
    </form></div>`;
  drawSetupPlayers();drawSetupObjs();
}
function drawSetupPlayers(){
  const n=+$('#sf-np').value,box=$('#sf-players');
  const opts=sel=>CHARACTERS.map(c=>`<option value="${c.id}" ${c.id===sel?'selected':''}>${esc(t(c.name))}</option>`).join('');
  if(n===1){
    const def=['frodosam','legolas','arwen','gandalf','gimli'];
    box.innerHTML=`<div class="prow" style="grid-template-columns:repeat(auto-fit,minmax(150px,1fr))"><label class="field"><span>${esc(t('Participant'))}</span><input class="in" id="sp-name-0" value="${esc(mem.get('users/'+S.uid)?.name||'')}"></label>${def.map((d,i)=>`<label class="field"><span>${esc(t('Personatge {n}',{n:i+1}))}</span><select class="in" id="sp-c-0-${i}" ${i===0?'disabled':''}>${opts(d)}</select></label>`).join('')}</div><p class="small muted" style="margin:0">${esc(t('En solitari portes Frodo i Sam i 4 personatges més.'))}</p>`;return;
  }
  box.innerHTML=Array.from({length:n},(_,i)=>`<div class="prow"><label class="field"><span>${esc(t('Participant {n}',{n:i+1}))}</span><input class="in" id="sp-name-${i}" value="${i===0?esc(mem.get('users/'+S.uid)?.name||''):''}" placeholder="${esc(t('Nom'))}"></label><label class="field"><span>${esc(t('Personatge'))}</span><select class="in" id="sp-c-${i}-0">${opts(SUGGESTED[i][0])}</select></label><label class="field"><span>${esc(t('Personatge'))}</span><select class="in" id="sp-c-${i}-1">${opts(SUGGESTED[i][1])}</select></label></div>`).join('');
}
function drawSetupObjs(fill){
  const lv=LEVELS[$('#sf-level').value],k=lv.obj-1,cur=fill||$$('[data-obj]').map(s=>s.value);
  $('#sf-objs').innerHTML=Array.from({length:k},(_,i)=>`<select class="in" data-obj="${i}"><option value="">${esc(t('Tria un objectiu…'))}</option>${OBJECTIVES.map(o=>`<option value="${esc(o)}" ${cur[i]===o?'selected':''}>${esc(t(o))}</option>`).join('')}</select>`).join('');
}

/* --- Partides tab --- */
async function campApi(body){
  const opt=body?{method:'POST',headers:{'Content-Type':'application/json','X-Taula-Token':S.token},body:JSON.stringify(body)}:{headers:{'X-Taula-Token':S.token},cache:'no-store'};
  const r=await fetch('api/campaigns',opt);const d=await r.json().catch(()=>({}));if(!r.ok)throw new Error(t(d.error||"No s'ha pogut fer."));return d;
}
async function renderCamps(){
  $('#main').innerHTML=`<div class="camps"><div><h2 style="font-size:32px">${esc(t('Partides guardades'))}</h2><p class="muted" style="margin:6px 0 0;max-width:62ch">${esc(t("Cada partida guarda les pistes, el torn, els objectius i el registre. Quan n'obris una, tots els que estan connectats hi passen."))}</p></div>
    <form class="panel camp-new" id="camp-new"><label class="field"><span>${esc(t('Partida nova'))}</span><input class="in" id="cn-name" required maxlength="80" placeholder="${esc(t('Divendres amb la colla'))}"></label><button class="btn pri" type="submit">${esc(t('Crear i obrir'))}</button></form>
    <div id="camp-list" class="camp-list"><p class="muted">${esc(t('Carregant…'))}</p></div>
    <div><h2 style="font-size:32px">${esc(t('Historial'))}</h2><p class="muted" style="margin:6px 0 0;max-width:62ch">${esc(t("Les partides acabades, guanyades o perdudes, de totes les partides guardades."))}</p></div>
    <div id="hist"><p class="muted">${esc(t('Carregant…'))}</p></div></div>`;
  if(!S.token){$('#camp-list').innerHTML=`<p class="muted">${esc(t("Obri l'app des del servidor per a gestionar partides."))}</p>`;return}
  try{drawCampList(await campApi())}catch(e){$('#camp-list').innerHTML=`<p class="small" style="color:var(--blood)">${esc(e.message)}</p>`}
  loadHistory();
}
function drawCampList(d){
  const box=$('#camp-list');if(!box)return;
  box.innerHTML=d.list.map(c=>`<article class="camp-card${c.active?' on':''}"><div class="cc-head"><h3 class="cc-name">${esc(c.name)}</h3>${c.active?`<span class="chip dm">${esc(t('Oberta'))}</span>`:''}</div>
    <p class="muted small" style="margin:0;font-style:italic">${esc(t('Darrer canvi {x}',{x:ago(c.updated)}))}</p>
    <div class="row" style="margin-top:6px">${c.active?'':`<button class="btn pri sm" data-copen="${c.id}">${esc(t('Obrir'))}</button>`}<button class="btn sm" data-cdup="${c.id}">${esc(t('Duplicar'))}</button>${c.active?'':`<button class="btn sm danger" data-cdel="${c.id}">${esc(t('Esborrar'))}</button>`}</div></article>`).join('');
}

async function histApi(body){
  const opt=body?{method:'POST',headers:{'Content-Type':'application/json','X-Taula-Token':S.token},body:JSON.stringify(body)}:{headers:{'X-Taula-Token':S.token},cache:'no-store'};
  const r=await fetch('api/history',opt);const d=await r.json().catch(()=>({}));if(!r.ok)throw new Error(t(d.error||"No s'ha pogut fer."));return d.list||[];
}
async function loadHistory(){try{drawHistory(await histApi())}catch(e){const h=$('#hist');if(h)h.innerHTML=`<p class="small" style="color:var(--blood)">${esc(e.message)}</p>`}}
function drawHistory(list){
  const box=$('#hist');if(!box)return;
  if(!list.length){box.innerHTML=`<p class="muted">${esc(t('Encara no heu acabat cap partida.'))}</p>`;return}
  const wins=list.filter(h=>h.result==='win').length;
  const by={};list.forEach(h=>{const k=h.level||'?';by[k]=by[k]||{w:0,n:0};by[k].n++;if(h.result==='win')by[k].w++});
  const lvRows=Object.keys(LEVELS).filter(k=>by[k]).map(k=>`<tr><td>${esc(t(LEVELS[k].name))}</td><td class="num">${by[k].n}</td><td class="num">${by[k].w}</td><td class="num">${Math.round(by[k].w*100/by[k].n)}%</td></tr>`).join('');
  box.innerHTML=`<div class="hist-top">
      <div class="sum-grid" style="max-width:520px"><div><b>${list.length}</b><span>${esc(t('partides'))}</span></div><div><b>${wins}</b><span>${esc(t('victòries'))}</span></div><div><b>${list.length-wins}</b><span>${esc(t('derrotes'))}</span></div><div><b>${Math.round(wins*100/list.length)}%</b><span>${esc(t('guanyades'))}</span></div></div>
      <table class="sum-t hist-lv"><tr><th>${esc(t('Dificultat'))}</th><th class="num">${esc(t('Jugades'))}</th><th class="num">${esc(t('Guanyades'))}</th><th class="num">%</th></tr>${lvRows}</table>
    </div>
    <div class="hist-list">${list.map(h=>{const sc=scenarioOf(h.objectives||[]);return `<article class="hist-card ${h.result}">
      <div class="cc-head"><span class="sum-res ${h.result}" style="font-size:20px">${esc(t(h.result==='win'?'Victòria':'Derrota'))}</span><span class="small muted">${esc(new Date(h.ended).toLocaleDateString(LANG==='es'?'es':'ca',{day:'numeric',month:'short',year:'numeric'}))}</span></div>
      <p style="margin:0"><b>${esc(h.camp||'')}</b> · ${esc(t(LEVELS[h.level]?.name||''))}${sc?' · '+esc(t(sc)):''}</p>
      <p class="small muted" style="margin:0">${esc(t('{r} · {d} · esperança {h} · objectius {o}',{r:pl(h.rounds||0,'ronda','rondes'),d:dur(h.ended-h.created),h:h.hope??'?',o:`${h.done}/${(h.objectives||[]).length+1}`}))}</p>
      <p class="small muted" style="margin:0">${h.players.map((p,i)=>esc(p||t('Participant {n}',{n:i+1}))).join(', ')} — ${h.chars.map(id=>esc(t((CHARACTERS.find(c=>c.id===id)||{name:id}).name))).join(', ')}</p>
      <div class="row"><button class="btn sm danger" data-hdel="${esc(h.id)}">${esc(t("Llevar de l'historial"))}</button></div></article>`}).join('')}</div>`;
}
document.addEventListener('click',e=>{const b=e.target.closest('[data-hdel]');if(!b)return;armed(b,async()=>{try{drawHistory(await histApi({action:'delete',id:b.dataset.hdel}))}catch(err){toast(err.message)}},t('Prem de nou per a llevar-la'))});

function renderTab(){if(!st.loaded)return;if(st.tab==='partida')renderPlay();else if(st.tab==='comunitat')renderCommunity();else renderCamps()}
function renderAll(){renderHeader();renderTracks();renderSide();if(st.tab!=='partides')renderTab()}

/* ================= events ================= */
document.addEventListener('click',e=>{
  const x=e.target;
  // tracks
  if(x.closest('#tracks')&&G){
    const hp=x.closest('[data-hope]');if(hp){const d=+hp.dataset.hope;commit(M("{d} d'esperança",{d:(d>0?'+':'')+d}),(s,log)=>hopeDelta(s,d,log,M('canvi manual')));return}
    const th=x.closest('[data-thr]');if(th){const d=+th.dataset.thr;commit(M("Canviar l'amenaça"),(s,log)=>{s.threatIdx=clamp(s.threatIdx+d,0,s.threat.length-1);log.push({k:"Amenaça: {n} cartes d'Ombra per torn.",v:{n:threatNow(s)}})});return}
    const dk=x.closest('[data-deck]');if(dk){commit(M('Ajustar el mazo'),(s,log)=>{s.deck=Math.max(0,s.deck+(+dk.dataset.deck));log.push({k:'Mazo de joc: {n} cartes.',v:{n:s.deck}})});return}
    if(x.id==='undo'){undo();return}
  }
  // sidebar
  if(x.closest('#side2')&&G){
    const ap=x.closest('[data-ap]');if(ap){const[w,i]=ap.dataset.ap.split(':').map(Number);commit(M("Comptador d'accions"),(s,log)=>{const cur=s.turn.a[w];s.turn.a[w]=(i<cur)?i:i+1;log.push({k:"Accions: {a} de 4 i {b} d'1.",v:{a:s.turn.a[0],b:s.turn.a[1]}})});return}
    if(x.id==='acts-done'){commit(M('Accions fetes'),(s,log)=>{s.turn.step=1;log.push({k:'Accions fetes.'})});return}
    if(x.id==='draw2'){commit(M('Robar 2 cartes'),(s,log)=>{const can=Math.min(2,s.deck);s.deck-=can;log.push({k:'Es roben {a} cartes de joc. Queden {b}.',v:{a:can,b:s.deck}});if(can<2)hopeDelta(s,-(2-can),log,M("el mazo de joc s'ha acabat"));s.turn.step=Math.max(s.turn.step,2)});return}
    if(x.id==='skies'){skiesFlow();return}
    if(x.id==='shadow-card'){shadowCardFlow();return}
    if(x.id==='next-turn'){
      const n=threatNow(G);
      if(G.turn.shadow<n&&!x.dataset.armed){armed(x,nextTurn,t("Només n'has resolt {a} de {b}. Prem de nou",{a:G.turn.shadow,b:n}));return}
      if(x.dataset.armed)delete x.dataset.armed;nextTurn();return;
    }
  }
  // play tab
  if(st.tab==='partida'&&G&&x.closest('#main')){
    const inc=x.closest('[data-cinc]'),dec=x.closest('[data-cdec]');
    if(inc||dec){const k=(inc||dec).dataset.cinc||(dec&&dec.dataset.cdec);G.calc[k]=Math.max(0,(G.calc[k]||0)+(inc?1:-1));write('game/state',G);renderPlay();return}
    const bk=x.closest('[data-bk]');if(bk){G.calc.bKind=bk.dataset.bk;write('game/state',G);renderPlay();return}
    if(x.id==='t-search'){doSearch();return}
    if(x.id==='t-ring'){commit(M("Frodo es posa l'Anell"),(s,log)=>{hopeDelta(s,-1,log,M("Frodo es posa l'Anell"));log.push({k:"Al tauler: desplaça l'Ull a la regió de Frodo."})});doSearch({ring:true,label:M("Cerca amb l'Anell")});return}
    if(x.id==='t-battle'){doBattle();return}
    const hv=x.closest('[data-hev]');if(hv){const d=+hv.dataset.hev,why=hv.dataset.why;commit(M('Esperança: {x}',{x:M(why)}),(s,log)=>hopeDelta(s,d,log,M(why)));return}
    if(x.id==='t-doom'){openModal(`<h2>${esc(t("Destruir l'Anell Únic"))}</h2><p style="margin:0">${t("Frodo és a la Muntanya del Destí i gasta <b>5 de Destí</b>. Si després de la tirada l'esperança és 1 o més, guanyeu.")}</p><div class="foot"><button class="btn" id="d-no">${esc(t('Encara no'))}</button><button class="btn pri" id="d-yes">${esc(t('Tirar'))}</button></div>`,(m,close)=>{$('#d-no',m).onclick=close;$('#d-yes',m).onclick=()=>{close();doSearch({doom:true,label:M("Intent de destruir l'Anell")})}});return}
  }
  // community tab
  if(st.tab==='comunitat'&&x.id==='re-setup'){armed(x,()=>{st.forceSetup=true;renderTab()},t('Segur? Prem de nou'));return}
  if(x.id==='sf-cancel'){st.forceSetup=false;renderTab();return}
});
document.addEventListener('change',e=>{
  const x=e.target;
  if(x.dataset.cchk&&G){G.calc[x.dataset.cchk]=x.checked;write('game/state',G);renderPlay();return}
  if(x.dataset.objdone&&G){const o=G.objectives.find(y=>y.id===x.dataset.objdone);commit(M(x.checked?'Completat: {x}':'Desmarcat: {x}',{x:o.name}),(s,log)=>{s.objectives.find(y=>y.id===o.id).done=x.checked;log.push({k:x.checked?'Objectiu completat: {x}. Aplica el seu «En completar-lo».':'Objectiu desmarcat: {x}.',v:{x:o.name},c:x.checked?'good':''})});return}
  if(x.dataset.setup!=null&&G){const i=+x.dataset.setup;G.setup[i]=x.checked;write('game/state',G);renderCommunity();return}
  if(!$('#setup-form'))return;
  if(x.id==='sf-np'){lsSet('cm-np',x.value);drawSetupPlayers()}
  if(x.id==='sf-level')drawSetupObjs();
  if(x.id==='sf-scen'&&x.value!==''){const sc=SCENARIOS[+x.value];$('#sf-level').value=sc.level[0];drawSetupObjs(sc.obj.map(i=>OBJECTIVES[i]))}
});
document.addEventListener('submit',async e=>{
  if(e.target.id==='setup-form'){
    e.preventDefault();
    const n=+$('#sf-np').value,players=[];
    if(n===1)players.push({name:$('#sp-name-0').value.trim(),chars:[0,1,2,3,4].map(i=>$(`#sp-c-0-${i}`).value)});
    else for(let i=0;i<n;i++)players.push({name:$(`#sp-name-${i}`).value.trim(),chars:[$(`#sp-c-${i}-0`).value,$(`#sp-c-${i}-1`).value]});
    const all=players.flatMap(p=>p.chars);
    if(new Set(all).size!==all.length){toast(t('Cada personatge només el pot portar un participant.'));return}
    if(!all.includes('frodosam')){toast(t('Algú ha de portar Frodo i Sam.'));return}
    const objs=$$('[data-obj]').map(s=>s.value).filter(Boolean),level=$('#sf-level').value;
    if(new Set(objs).size!==objs.length){toast(t('Hi ha objectius repetits.'));return}
    if(objs.length<LEVELS[level].obj-1){toast(t('Tria {n} objectius.',{n:LEVELS[level].obj-1}));return}
    const before=G;G=newGame({level,players,objectives:objs});
    UNDO=before?[{label:M('Preparar una partida nova'),state:before}]:[];
    LOG=[{k:'Partida preparada: {a}, {b}. Mazo de joc: {c} cartes. Mira la pestanya Comunitat per a preparar el tauler.',v:{a:LEVELS[level].name,b:M(n===1?'1 participant':'{n} participants',{n}),c:G.deck},ts:Date.now(),who:mem.get('users/'+S.uid)?.name||''}];
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
    if(du){drawCampList(await campApi({action:'duplicate',id:du.dataset.cdup}));toast(t('Partida duplicada.'))}
    if(de)armed(de,async()=>{try{drawCampList(await campApi({action:'delete',id:de.dataset.cdel}));toast(t('Partida esborrada. Està a la carpeta partides/esborrades si la necessites.'))}catch(err){toast(err.message)}},t('Prem de nou per a esborrar'));
  }catch(err){toast(err.message);if(o)o.disabled=false}
});
function nextTurn(){commit(M('Torn següent'),(s,log)=>{const np=(s.turn.p+1)%s.players.length;if(np===0)s.round++;s.turn={p:np,step:0,a:[0,0],shadow:0};log.push({k:'Torn de {x}.',v:{x:s.players[np].name||M('Participant {n}',{n:np+1})}})})}
$('.tabs').addEventListener('click',e=>{const x=e.target.closest('[data-tab]');if(!x)return;st.tab=x.dataset.tab;st.forceSetup=false;lsSet('cm-tab2',st.tab);renderHeader();renderTab()});
$('#camp-name').addEventListener('input',e=>{CAMP={...(CAMP||{}),name:e.target.value};clearTimeout(window.__cn);window.__cn=setTimeout(()=>write('campaign/main',CAMP),500)});
$('#who').addEventListener('click',e=>{if(e.target.id==='logout')armed(e.target,()=>{lsSet('cm-token','');location.reload()},t('Segur? Prem de nou'))});

/* ================= connection ================= */
let lanFirst=null,lanPoll=null,lanErrs=[],lanBannerT=null,lanLast=Date.now();
function showBanner(x){const b=$('#banner');if(b.classList.contains('endstate'))return;b.textContent=x;b.hidden=!x}
function lanOk(){clearTimeout(lanBannerT);lanBannerT=null;showBanner('')}
function lanTrouble(){if(!lanBannerT)lanBannerT=setTimeout(()=>showBanner(t("S'ha perdut la connexió amb el servidor. Tornant a connectar…")),5000)}
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
  es.addEventListener('campaign',()=>{showBanner(t("S'ha obert una altra partida. Carregant…"));setTimeout(()=>location.reload(),500)});
  es.addEventListener('doc',e=>{lanLast=Date.now();const d=JSON.parse(e.data);if(d.data==null)mem.delete(d.path);else mem.set(d.path,d.data);memNotify(d.path)});
  es.onerror=()=>{lanTrouble();const now=Date.now();lanErrs=lanErrs.filter(x=>now-x<60000);lanErrs.push(now);if(lanErrs.length>=3)startPolling();else if(es.readyState===2)setTimeout(lanConnect,3000)};
}
let joinResolve=null;
function joinRender(){
  const prev=$('#j-name')?.value||'';
  $('#main').innerHTML=`<form id="join" class="panel" style="max-width:440px;display:flex;flex-direction:column;gap:14px"><h2>${esc(t('Uneix-te a la Comunitat'))}</h2>
    <label class="field"><span>${esc(t('El teu nom'))}</span><input class="in" id="j-name" required maxlength="40" autocomplete="nickname"></label>
    <p class="small" id="j-err" style="margin:0;color:var(--blood)"></p><button class="btn pri" type="submit">${esc(t('Entrar'))}</button></form>`;
  $('#j-name').value=prev;$('#j-name').focus();
  $('#join').addEventListener('submit',async e=>{e.preventDefault();$('#j-err').textContent='';
    try{const r=await fetch('api/join',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:$('#j-name').value})});const d=await r.json();
      if(!r.ok){$('#j-err').textContent=t(d.error||"No s'ha pogut entrar.");return}lsSet('cm-token',d.token);$('.tabs').hidden=false;joinResolve(d)}
    catch(_){$('#j-err').textContent=t('No es pot contactar amb el servidor.')}});
}
function joinScreen(){return new Promise(resolve=>{joinResolve=resolve;$('.tabs').hidden=true;joinRender()})}
function startSubs(){
  watchDoc('campaign/main',d=>{CAMP=d;renderHeader()});
  watchDoc('game/state',d=>{const ng=d&&d.v===2?d:null;
    const focused=document.activeElement&&document.activeElement.closest('#main')&&document.activeElement.matches('input,select');
    G=ng;if(st.loaded){renderHeader();renderTracks();renderSide();if(!focused&&!$('.modal')&&st.tab!=='partides')renderTab()}checkResult()});
  watchDoc('game/log',d=>{LOG=d?.list||[];if(st.loaded)renderSide()});
  watchDoc('game/undo',d=>{UNDO=d?.stack||[];if(st.loaded)renderTracks()});
  setTimeout(()=>{st.loaded=true;renderAll();renderTab()},30);
  setInterval(()=>{if(document.visibilityState==='visible'&&st.loaded&&!$('.modal'))renderSide()},30000);
}
async function boot(){
  applyStatic();renderHeader();
  let ok=false;
  if(/^https?:$/.test(location.protocol)){try{const r=await fetch('api/hello',{cache:'no-store'});ok=r.ok}catch(_){}}
  if(!ok){
    S.uid='local';mem.set('users/local',{name:t('Tu')});
    mem.set('game/state',newGame({level:'intro',players:[{name:t('Tu'),chars:['frodosam','legolas']},{name:t('Company'),chars:['gandalf','aragorn']}],objectives:OBJECTIVES.slice(0,3)}));
    showBanner(t('Mode de prova: obri la pàgina a través del servidor (python3 comunitat.py) perquè es guarde i es compartisca.'));
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

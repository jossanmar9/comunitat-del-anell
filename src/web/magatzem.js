/* ================= magatzem ================= */
// On es guarda tot. La lògica (partides, historial, còpies de seguretat, exportar i importar) és la
// mateixa a totes les plataformes; només canvia el «disc» on van els fitxers JSON:
//   - a Windows i Linux, la carpeta de dades del programa (a través del servidor local, src/servidor.py);
//   - a la web i a Android, l'emmagatzematge del navegador (IndexedDB).
// Les rutes i els formats són els de sempre (partides/<id>.json, copies/<id>/…, historial.json…),
// així les dades de les versions anteriors es continuen llegint.
const RUTA_RE=/^(?:(?:partides|partides\/esborrades|copies\/[a-z0-9-]{1,60})\/[a-z0-9][a-z0-9._-]{0,120}\.json|historial\.json|comunitat\.json|mapa\.json)$/;
const CARPETA_RE=/^(?:partides|partides\/esborrades|copies\/[a-z0-9-]{1,60})$/;
const NO_PARTIDA='El fitxer no és una partida de La Comunitat.';
const esObj=v=>v!=null&&typeof v==='object'&&!Array.isArray(v);
const duplicat=v=>v===undefined?undefined:JSON.parse(JSON.stringify(v));

// Escriptori: el programa guarda els fitxers a la seua carpeta de dades.
function discServidor(){
  async function op(cos){
    let r;
    try{r=await fetch('api/disc',{method:'POST',headers:{'Content-Type':'application/json','X-Comunitat':'1'},body:JSON.stringify(cos),cache:'no-store'})}
    catch(_){throw new Error('No es pot contactar amb el programa. Torna a obrir La Comunitat.')}
    const d=await r.json().catch(()=>({}));
    if(!r.ok)throw new Error(d.error||"No s'ha pogut guardar.");
    return d;
  }
  return {
    nom:'servidor',
    llig:async ruta=>(await op({op:'llig',ruta})).obj??null,
    escriu:async(ruta,obj)=>{await op({op:'escriu',ruta,obj})},
    llista:async carpeta=>(await op({op:'llista',carpeta})).list||[],
    esborra:async ruta=>{await op({op:'esborra',ruta})},
    mou:async(ruta,a)=>{await op({op:'mou',ruta,a})},
  };
}

// Web i Android: els fitxers van a IndexedDB, dins del navegador o de l'app.
function discLocal(){
  let obert=null;
  const db=()=>obert||(obert=new Promise((res,rej)=>{
    const q=indexedDB.open('la-comunitat',1);
    q.onupgradeneeded=()=>q.result.createObjectStore('fitxers');
    q.onsuccess=()=>res(q.result);
    q.onerror=()=>rej(q.error||new Error("No s'ha pogut obrir l'emmagatzematge."));
  }));
  const peticio=r=>new Promise((res,rej)=>{r.onsuccess=()=>res(r.result);r.onerror=()=>rej(r.error)});
  async function magatzem(mode){
    const t=(await db()).transaction('fitxers',mode);
    return {s:t.objectStore('fitxers'),fet:new Promise((res,rej)=>{t.oncomplete=()=>res();t.onerror=t.onabort=()=>rej(t.error||new Error("No s'ha pogut guardar."))})};
  }
  const valida=ruta=>{if(!RUTA_RE.test(ruta))throw new Error('Ruta no vàlida.')};
  try{navigator.storage&&navigator.storage.persist&&navigator.storage.persist()}catch(_){}  // que el navegador no l'esborre per falta d'espai
  return {
    nom:'local',
    llig:async ruta=>{valida(ruta);const {s}=await magatzem('readonly');const v=await peticio(s.get(ruta));return v?duplicat(v.obj):null},
    escriu:async(ruta,obj)=>{valida(ruta);const {s,fet}=await magatzem('readwrite');s.put({obj:duplicat(obj),ts:Date.now()},ruta);await fet},
    llista:async carpeta=>{
      if(!CARPETA_RE.test(carpeta))throw new Error('Ruta no vàlida.');
      const p=carpeta+'/',out=[];const {s,fet}=await magatzem('readonly');
      const c=s.openCursor(IDBKeyRange.bound(p,p+'￿'));
      c.onsuccess=()=>{const cur=c.result;if(!cur)return;const nom=cur.key.slice(p.length);if(!nom.includes('/'))out.push({nom,ts:cur.value.ts||0});cur.continue()};
      await fet;return out;
    },
    esborra:async ruta=>{valida(ruta);const {s,fet}=await magatzem('readwrite');s.delete(ruta);await fet},
    mou:async(ruta,a)=>{valida(ruta);valida(a);const {s,fet}=await magatzem('readwrite');const v=await peticio(s.get(ruta));if(!v)throw new Error('Aquesta partida ja no existeix.');s.put({...v,ts:Date.now()},a);s.delete(ruta);await fet},
  };
}

const MAG=(()=>{
  const D=ENTORN==='escriptori'?discServidor():discLocal();
  const COPIES=15,CADA=30*60*1000;
  const COPIA_RE=/^\d{8}-\d{6}(?:-\d+)?-[a-z]+\.json$/;
  let actiu=null,ultimaCopia=0,hist=null;
  const fitxer=cid=>`partides/${cid}.json`;
  const nomDe=(docs,cid)=>String((docs&&docs['campaign/main']&&docs['campaign/main'].name)||'').trim()||cid;
  const idDe=nom=>nom.replace(/\.json$/,'');
  const pla=n=>String(n).normalize('NFKD').replace(/[̀-ͯ]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'').slice(0,40);
  async function idLliure(n){
    const base=pla(n)||'partida',ids=new Set((await D.llista('partides')).map(f=>idDe(f.nom)));
    let s=base,i=2;while(ids.has(s))s=`${base}-${i++}`;return s;
  }
  const segell=()=>{const d=new Date(),p=x=>String(x).padStart(2,'0');return `${d.getFullYear()}${p(d.getMonth()+1)}${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}`};
  const aleatori=()=>Math.random().toString(16).slice(2,8);

  // Els documents d'una partida: campaign/main, game/state, game/undo, game/log.
  const ruta_ok=k=>{const s=k.split('/');return s.length%2===0&&s.length<=16&&['game','map','campaign'].includes(s[0])&&s.every(x=>/^[A-Za-z0-9_.~:@+-]+$/.test(x)&&x!=='.'&&x!=='..')};
  function comprova(docs){
    if(!esObj(docs)||Object.keys(docs).length>5000)throw new Error(NO_PARTIDA);
    for(const [k,v] of Object.entries(docs))if(!ruta_ok(k)||!esObj(v))throw new Error(NO_PARTIDA);
    const g=docs['game/state'];
    if(g!=null&&(!esObj(g)||!Array.isArray(g.players)||!Array.isArray(g.objectives)||typeof g.hope!=='number'))throw new Error(NO_PARTIDA);
    return docs;
  }
  // En llegir, s'ignora el que no és de la partida (per exemple, jugadors de la sala de la v2).
  const neteja=docs=>Object.fromEntries(Object.entries(esObj(docs)?docs:{}).filter(([k,v])=>ruta_ok(k)&&esObj(v)));
  async function llegeix(cid){const f=await D.llig(fitxer(cid));if(!f)throw new Error('Aquesta partida ja no existeix.');return neteja(f.docs)}

  // ---- historial de partides acabades
  async function historial(){if(!hist){const h=await D.llig('historial.json');hist=Array.isArray(h&&h.list)?h.list:[]}return hist}
  async function anota(cid,docs){
    const g=docs['game/state'];if(!esObj(g)||!g.created)return;
    const h=await historial(),id=`${cid}:${g.created}`,i=h.findIndex(x=>x.id===id),res=g.result;
    if(res!=='win'&&res!=='lose'){if(i>=0){h.splice(i,1);await D.escriu('historial.json',{list:h})}return}
    if(i>=0&&h[i].result===res&&h[i].camp===nomDe(docs,cid))return;
    const objs=(g.objectives||[]).filter(esObj);
    const rec={id,camp:nomDe(docs,cid),result:res,level:g.level,players:(g.players||[]).map(p=>String((p&&p.name)||'')),
      chars:(g.chars||[]).map(c=>String((c&&c.id)||'')),objectives:objs.filter(o=>!o.ring).map(o=>String(o.name||'')),
      done:objs.filter(o=>o.done).length,rounds:g.round,hope:g.hope,created:g.created,ended:g.ended||Date.now()};
    if(i>=0)h[i]=rec;else h.push(rec);
    await D.escriu('historial.json',{list:h});
  }

  // ---- còpies de seguretat: copies/<partida>/<data>-<motiu>.json, les 15 últimes
  async function copia(cid,docs,motiu){
    if(!docs||Object.keys(docs).length<=1)return;   // una partida acabada de crear encara no té res a guardar
    const dir=`copies/${cid}`,ja=new Set((await D.llista(dir)).map(f=>f.nom));
    const s=segell();let nom=`${s}-${motiu}`,n=2;
    while(ja.has(nom+'.json'))nom=`${s}-${n++}-${motiu}`;
    await D.escriu(`${dir}/${nom}.json`,{docs});
    const totes=(await D.llista(dir)).filter(f=>COPIA_RE.test(f.nom)).sort((a,b)=>(a.ts-b.ts)||(a.nom<b.nom?-1:1));
    for(const f of totes.slice(0,-COPIES))await D.esborra(`${dir}/${f.nom}`).catch(()=>{});
  }

  async function obri(cid){
    const docs=await llegeix(cid);
    actiu=cid;ultimaCopia=Date.now();
    await D.escriu('comunitat.json',{versio:3,active:cid});
    try{await copia(cid,docs,'obrir')}catch(_){}
    try{await anota(cid,docs)}catch(_){}
    return {camp:cid,docs};
  }

  return {
    disc:D.nom,
    // La partida oberta l'última vegada (o la més recent). Sense cap partida: {camp:null}.
    async inici(){
      const meta=await D.llig('comunitat.json');
      let cid=meta&&typeof meta.active==='string'&&/^[a-z0-9-]{1,60}$/.test(meta.active)?meta.active:null;
      if(cid&&!(await D.llig(fitxer(cid))))cid=null;
      if(!cid){const fs=(await D.llista('partides')).sort((a,b)=>b.ts-a.ts);if(fs.length)cid=idDe(fs[0].nom)}
      if(!cid)return {camp:null,docs:{}};
      try{return await obri(cid)}catch(_){return {camp:null,docs:{}}}
    },
    obri,
    async guarda(docs){
      if(!actiu)throw new Error('No hi ha cap partida oberta.');
      const cid=actiu;comprova(docs);
      await D.escriu(fitxer(cid),{docs});
      await anota(cid,docs);
      if(Date.now()-ultimaCopia>CADA){ultimaCopia=Date.now();try{await copia(cid,docs,'partida')}catch(_){}}
    },
    async crea(nom){
      nom=String(nom||'').trim().slice(0,80);if(!nom)throw new Error('Posa-li un nom a la partida.');
      const cid=await idLliure(nom);
      await D.escriu(fitxer(cid),{docs:{'campaign/main':{name:nom}}});
      return obri(cid);
    },
    async partides(){
      const list=[];
      for(const f of await D.llista('partides')){
        const id=idDe(f.nom);let docs;
        try{docs=neteja((await D.llig(fitxer(id))||{}).docs)}catch(_){continue}
        list.push({id,name:nomDe(docs,id),updated:f.ts,active:id===actiu});
      }
      list.sort((a,b)=>(b.active-a.active)||(b.updated-a.updated));
      const trash=[];
      for(const f of (await D.llista('partides/esborrades')).sort((a,b)=>b.ts-a.ts)){
        try{trash.push({id:idDe(f.nom),name:nomDe(neteja(((await D.llig('partides/esborrades/'+f.nom))||{}).docs),idDe(f.nom))})}catch(_){}
      }
      return {active:actiu,list,trash};
    },
    async duplica(cid){
      const docs=await llegeix(cid),nom=nomDe(docs,cid)+' (còpia)';
      docs['campaign/main']={...(docs['campaign/main']||{}),name:nom};
      await D.escriu(fitxer(await idLliure(nom)),{docs});
    },
    async esborra(cid){
      if(cid===actiu)throw new Error("No pots esborrar la partida oberta. Obri'n una altra primer.");
      await D.mou(fitxer(cid),`partides/esborrades/${cid}-${segell()}-${aleatori()}.json`);
    },
    async recupera(id){
      const f=await D.llig(`partides/esborrades/${id}.json`);if(!f)throw new Error('Aquesta partida ja no existeix.');
      const docs=neteja(f.docs);
      await D.mou(`partides/esborrades/${id}.json`,fitxer(await idLliure(nomDe(docs,'Partida recuperada'))));
    },
    async historial(){return [...await historial()].reverse()},
    async llevaHistorial(id){const h=await historial(),i=h.findIndex(x=>x.id===id);if(i>=0){h.splice(i,1);await D.escriu('historial.json',{list:h})}return [...h].reverse()},
    async copies(cid){
      return (await D.llista(`copies/${cid}`)).filter(f=>COPIA_RE.test(f.nom)).sort((a,b)=>(b.ts-a.ts)||(a.nom<b.nom?1:-1))
        .map(f=>({id:idDe(f.nom),ts:f.ts,reason:idDe(f.nom).split('-').pop()}));
    },
    async fesCopia(cid){await copia(cid,await llegeix(cid),'ma')},
    // Torna els documents restaurats (per a recarregar-los si és la partida oberta).
    async restaura(cid,bid){
      if(!/^\d{8}-\d{6}(?:-\d+)?-[a-z]+$/.test(bid))throw new Error('Aquesta còpia ja no existeix.');
      const f=await D.llig(`copies/${cid}/${bid}.json`);if(!f)throw new Error('Aquesta còpia ja no existeix.');
      let docs;try{docs=comprova(neteja(f.docs))}catch(_){throw new Error('La còpia està danyada.')}
      await copia(cid,await llegeix(cid),'abans');   // per si de cas, una còpia del que hi havia
      await D.escriu(fitxer(cid),{docs});
      if(cid===actiu)await anota(cid,docs);
      return docs;
    },
    async exporta(cid){
      const docs=await llegeix(cid),nom=nomDe(docs,cid),d=new Date(),p=x=>String(x).padStart(2,'0');
      const info={format:'comunitat-del-anell',versio:1,programa:VERSIO,nom,exportada:`${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`,docs};
      return {fitxer:`${pla(nom)||'partida'}-${d.getFullYear()}${p(d.getMonth()+1)}${p(d.getDate())}.json`,text:JSON.stringify(info,null,1)};
    },
    // Una partida exportada (o un fitxer de partides/ o de copies/) es crea com a partida nova.
    async importa(text){
      let info;try{info=JSON.parse(String(text).replace(/^﻿/,''))}catch(_){throw new Error(NO_PARTIDA)}
      if(!esObj(info))throw new Error(NO_PARTIDA);
      const docs=comprova(info.docs);
      let nom=nomDe(docs,'')||String(info.nom||'').slice(0,80)||'Partida importada';
      if((await this.partides()).list.some(c=>c.name===nom))nom=`${nom} (importada)`;
      docs['campaign/main']={...(docs['campaign/main']||{}),name:nom};
      const cid=await idLliure(nom);
      await D.escriu(fitxer(cid),{docs});
      return cid;
    },
    // Mapa propi (una imatge en data:URL), per a totes les partides.
    async mapa(){const m=await D.llig('mapa.json').catch(()=>null);return m&&typeof m.img==='string'&&m.img.startsWith('data:image/')?m.img:null},
    async posaMapa(img){if(img)await D.escriu('mapa.json',{img});else await D.esborra('mapa.json').catch(()=>{})},
  };
})();

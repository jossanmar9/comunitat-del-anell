#!/usr/bin/env python3
"""Proves de src/web/magatzem.js (partides, historial, còpies, exportar i importar) contra el
programa d'escriptori de veritat. Cal Node.js 18 o més nou.

Ús:  python3 build.py && python3 tests/prova_magatzem.py
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
from prova_servidor import Programa  # noqa: E402

PROVA = r"""
const assert=require('assert');
const port=process.argv[2];
const real=globalThis.fetch;
globalThis.fetch=(url,opt)=>real(`http://127.0.0.1:${port}/${url}`,opt);
const ENTORN='escriptori',VERSIO='prova';
eval(require('fs').readFileSync(process.argv[3],'utf8')+';globalThis.MAG=MAG');
const partida=(v={})=>({v:2,hope:6,created:111,round:3,level:'intro',players:[{name:'Jugador1'}],
  chars:[{id:'frodosam',player:0}],objectives:[{id:'ring',name:'Anell',ring:true,done:false},{id:'o1',name:'Un',done:true}],result:null,...v});
(async()=>{
  assert.deepStrictEqual(await MAG.inici(),{camp:null,docs:{}});
  // Crear: l'identificador ve del nom
  const a=await MAG.crea('  Divendres amb la colla  ');
  assert.strictEqual(a.camp,'divendres-amb-la-colla');
  assert.strictEqual(a.docs['campaign/main'].name,'Divendres amb la colla');
  assert.strictEqual((await MAG.crea('Divendres amb la colla')).camp,'divendres-amb-la-colla-2');
  assert.strictEqual((await MAG.crea('Àèíòú ç')).camp,'aeiou-c');
  await assert.rejects(MAG.crea('   '),/nom/);
  // Guardar i tornar a obrir
  await MAG.obri('divendres-amb-la-colla');
  const docs={'campaign/main':{name:'Divendres amb la colla'},'game/state':partida(),'game/undo':{list:[]},'game/log':{list:[]}};
  await MAG.guarda(docs);
  assert.deepStrictEqual((await MAG.obri('divendres-amb-la-colla')).docs,docs);
  await assert.rejects(MAG.guarda({'../x':{}}),/no és una partida/);
  await assert.rejects(MAG.guarda({'game/state':{hope:'molta'}}),/no és una partida/);
  // En tornar a arrancar, s'obri l'última partida oberta
  assert.strictEqual((await MAG.inici()).camp,'divendres-amb-la-colla');
  // Historial: es guarda en acabar i es lleva si es desfà
  await MAG.guarda({...docs,'game/state':partida({result:'win',ended:222})});
  let h=await MAG.historial();
  assert.strictEqual(h.length,1);
  assert.deepStrictEqual([h[0].id,h[0].camp,h[0].result,h[0].done,h[0].players[0],h[0].objectives],
    ['divendres-amb-la-colla:111','Divendres amb la colla','win',1,'Jugador1',['Un']]);
  await MAG.guarda(docs);
  assert.strictEqual((await MAG.historial()).length,0);
  await MAG.guarda({...docs,'game/state':partida({result:'lose'})});
  assert.strictEqual((await MAG.llevaHistorial('divendres-amb-la-colla:111')).length,0);
  await MAG.guarda(docs);
  // Llistat de partides: l'oberta primer
  let p=await MAG.partides();
  assert.strictEqual(p.active,'divendres-amb-la-colla');
  assert.strictEqual(p.list[0].id,'divendres-amb-la-colla');
  assert.strictEqual(p.list.length,3);
  // Duplicar, esborrar (no l'oberta) i recuperar
  await MAG.duplica('divendres-amb-la-colla');
  p=await MAG.partides();
  assert.ok(p.list.some(c=>c.name==='Divendres amb la colla (còpia)'));
  await assert.rejects(MAG.esborra('divendres-amb-la-colla'),/oberta/);
  await MAG.esborra('aeiou-c');
  p=await MAG.partides();
  assert.ok(!p.list.some(c=>c.id==='aeiou-c'));
  assert.strictEqual(p.trash.length,1);
  await MAG.recupera(p.trash[0].id);
  p=await MAG.partides();
  assert.ok(p.list.some(c=>c.name==='Àèíòú ç'));
  assert.strictEqual(p.trash.length,0);
  // Còpies de seguretat: a mà, restaurar (i abans, una còpia del que hi havia), màxim 15
  await MAG.fesCopia('divendres-amb-la-colla');
  let c=await MAG.copies('divendres-amb-la-colla');
  assert.ok(c.some(x=>x.reason==='ma'));
  await MAG.guarda({...docs,'game/state':partida({hope:1})});
  const restaurats=await MAG.restaura('divendres-amb-la-colla',c.find(x=>x.reason==='ma').id);
  assert.strictEqual(restaurats['game/state'].hope,6);
  assert.strictEqual((await MAG.obri('divendres-amb-la-colla')).docs['game/state'].hope,6);
  assert.ok((await MAG.copies('divendres-amb-la-colla')).some(x=>x.reason==='abans'));
  await assert.rejects(MAG.restaura('divendres-amb-la-colla','../../x'),/ja no existeix/);
  for(let i=0;i<20;i++)await MAG.fesCopia('divendres-amb-la-colla');
  assert.strictEqual((await MAG.copies('divendres-amb-la-colla')).length,15);
  // Exportar i importar
  const e=await MAG.exporta('divendres-amb-la-colla');
  assert.match(e.fitxer,/^divendres-amb-la-colla-\d{8}\.json$/);
  const info=JSON.parse(e.text);
  assert.strictEqual(info.format,'comunitat-del-anell');
  assert.deepStrictEqual(info.docs['game/state'],partida());
  const nova=await MAG.importa('﻿'+e.text);
  assert.strictEqual(nova,'divendres-amb-la-colla-importada');
  assert.strictEqual((await MAG.obri(nova)).docs['campaign/main'].name,'Divendres amb la colla (importada)');
  await assert.rejects(MAG.importa('no és json'),/no és una partida/);
  await assert.rejects(MAG.importa('{"docs":{"/etc/passwd":{}}}'),/no és una partida/);
  await assert.rejects(MAG.importa('[1]'),/no és una partida/);
  // Mapa propi
  assert.strictEqual(await MAG.mapa(),null);
  await MAG.posaMapa('data:image/jpeg;base64,AAAA');
  assert.strictEqual(await MAG.mapa(),'data:image/jpeg;base64,AAAA');
  await MAG.posaMapa(null);
  assert.strictEqual(await MAG.mapa(),null);
  console.log('OK');
})().catch(e=>{console.error(e);process.exit(1)});
"""


@unittest.skipUnless(shutil.which("node"), "cal Node.js")
class Magatzem(unittest.TestCase):
    def test_magatzem(self):
        with tempfile.TemporaryDirectory() as d:
            p = Programa(Path(d))
            try:
                script = Path(d) / "prova.js"
                script.write_text(PROVA, encoding="utf-8")
                r = subprocess.run(["node", str(script), str(p.port), str(ROOT / "src" / "web" / "magatzem.js")],
                                   capture_output=True, text=True, encoding="utf-8", timeout=120)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                self.assertIn("OK", r.stdout)
                # Els fitxers són els mateixos que les versions anteriors
                f = json.loads((Path(d) / "partides" / "divendres-amb-la-colla.json").read_text(encoding="utf-8"))
                self.assertIn("game/state", f["docs"])
            finally:
                p.tanca()


if __name__ == "__main__":
    unittest.main(verbosity=2)

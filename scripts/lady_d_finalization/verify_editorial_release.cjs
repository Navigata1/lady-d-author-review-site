const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const assert=require('node:assert/strict');
const {chromium}=require('playwright');
const {execFileSync}=require('node:child_process');
const {assertInventory}=require('./editorial_inventory.cjs');
const root=path.resolve(__dirname,'../..');
const quality=path.join(root,'quality/editorial-2026-10-20');
const base=process.env.BASE_URL||'https://lady-d-author-review-site.vercel.app';
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const report={base,checkedAt:new Date().toISOString(),routes:[],downloads:[],readers:[]};
function publicResponse(response,route){
 assert.equal(new URL(response.url).origin,new URL(base).origin,`${route}: redirected outside the publishing site`);
 assert(response.ok,`${route}: ${response.status}`);
}

(async()=>{
 fs.writeFileSync(path.join(quality,'live-release.json'),JSON.stringify({status:'RUNNING'})+'\n');
 const build=JSON.parse(fs.readFileSync(path.join(quality,'pdf-build.json')));
 assertInventory(build);
 const archive=JSON.parse(execFileSync('python3',['-B',path.join(__dirname,'package_editorial.py'),'--verify-web-archive'],{encoding:'utf8'}));
 const offline=JSON.parse(fs.readFileSync(path.join(quality,'offline-package.json')));
 assert.equal(offline.status,'PASS');assert.equal(offline.archive.sha256,archive.sha256,'Offline test covered a different ZIP');
 assert.equal(sha(fs.readFileSync(path.join(root,'public/downloads/lady-d-finalization/Lady-D-Trilogy-Web-Review-Package-2026-10-20.zip'))),archive.sha256);
 report.archive=archive;
 const routes=['/','/susan-damon-hub.html','/lady-d-finalization-review.html','/assets/lady-d-hub-polish.css','/assets/lady-d-interiors/interiors.css','/assets/lady-d-interiors/interiors.js',...['regular','italic','semibold'].map(s=>`/assets/fonts/spectral-${s}.ttf`),...build.results.map(r=>'/downloads/lady-d-finalization/'+r.html),...[1,2,3].map(v=>`/downloads/lady-d-finalization/audiobook/lady-d-volume-${v}-audiobook-manifest.json`)];
 for(const route of routes){
  const response=await fetch(base+route,{signal:AbortSignal.timeout(45000)});publicResponse(response,route);
  const bytes=Buffer.from(await response.arrayBuffer());
  const filename=route==='/'?'susan-damon-hub.html':route.slice(1);
  assert.equal(sha(bytes),sha(fs.readFileSync(path.join(root,'public',filename))),`${route}: stale bytes`);
  report.routes.push({route,status:response.status,sha256:sha(bytes)});
 }
 for(const route of ['/ops/mission/state.json','/source/finalization/author-voice-contract.json','/quality/editorial-2026-10-20/editorial-audit.json','/scripts/lady_d_finalization/build_interiors.py']){
  const response=await fetch(base+route);assert.equal(response.status,404,`${route}: internal data exposed`);
 }
 for(const day of ['30','31']){
  const response=await fetch(base+`/downloads/lady-d-finalization/Lady-D-Trilogy-Web-Review-Package-2026-08-${day}.zip`,{method:'HEAD',redirect:'manual'});
  assert.equal(response.status,307,'Old review package must redirect to the current edition');
  assert.equal(response.headers.get('location'),'/downloads/lady-d-finalization/Lady-D-Trilogy-Web-Review-Package-2026-10-20.zip');
 }
 for(const filename of [...build.results.map(r=>r.pdf),'Lady-D-Trilogy-Web-Review-Package-2026-10-20.zip']){
  const route='/downloads/lady-d-finalization/'+filename;
  const response=await fetch(base+route,{signal:AbortSignal.timeout(180000)});publicResponse(response,route);
  const hash=crypto.createHash('sha256');let bytes=0;
  for await(const chunk of response.body){hash.update(chunk);bytes+=chunk.length}
  const actual=hash.digest('hex');
  assert.equal(actual,sha(fs.readFileSync(path.join(root,'public'+route))),`${filename}: download differs`);
  report.downloads.push({filename,bytes,sha256:actual});
 }
 const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 try{
  const page=await browser.newPage({viewport:{width:390,height:844}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base+'/');await page.evaluate(()=>document.fonts.ready);
  const checkout=page.locator('a[href^="https://buy.stripe.com/"]');
  assert.equal(await checkout.count(),1);
  assert.equal(await checkout.getAttribute('href'),'https://buy.stripe.com/fZu28t5WpchE73EbnA0VO0a');
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.screenshot({path:path.join(quality,'live-hub-mobile.png')});
  for(const item of build.results){
   await page.goto(base+'/downloads/lady-d-finalization/'+item.html);await page.evaluate(()=>document.fonts.ready);
   assert.equal(await page.locator('#reading-day option').count(),366);
   for(const width of [390,1440]){
    await page.setViewportSize({width,height:900});
    await page.selectOption('#reading-day',item.journal?'j218':'dA218');
    assert.equal(new URL(page.url()).hash,item.journal?'#j218':'#dA218');
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${item.html} overflows`);
    assert(await page.evaluate(()=>document.activeElement.id===document.querySelector('#reading-day').value));
   }
   report.readers.push({file:item.html,dateOptions:366,widths:[390,1440],navigation:'PASS'});
  }
  assert.deepEqual(errors,[]);
 }finally{await browser.close()}
 report.status='PASS';
 assert.equal(report.readers.length,6);assert.equal(report.downloads.length,7);
 fs.writeFileSync(path.join(quality,'live-release.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify(report,null,2));
})().catch(e=>{fs.writeFileSync(path.join(quality,'live-release.json'),JSON.stringify({status:'FAIL',error:e.message},null,2)+'\n');console.error(e);process.exitCode=1});

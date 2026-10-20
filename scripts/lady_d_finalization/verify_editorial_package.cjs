const fs=require('node:fs');
const path=require('node:path');
const os=require('node:os');
const assert=require('node:assert/strict');
const {execFileSync}=require('node:child_process');
const {pathToFileURL}=require('node:url');
const {chromium}=require('playwright');
const {expected}=require('./editorial_inventory.cjs');
const root=path.resolve(__dirname,'../..');
const quality=path.join(root,'quality/editorial-2026-10-20');

(async()=>{
 const extracted=fs.mkdtempSync(path.join(os.tmpdir(),'lady-d-october-package-'));
 const report={files:[],networkDependencies:[]};
 fs.writeFileSync(path.join(quality,'offline-package.json'),JSON.stringify({status:'RUNNING'})+'\n');
 report.archive=JSON.parse(execFileSync('python3',['-B',path.join(__dirname,'package_editorial.py'),'--verify-web-archive'],{encoding:'utf8'}));
 const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 try{
  execFileSync('unzip',['-q',path.join(root,'output/Lady-D-Trilogy-Web-Review-Package-2026-10-20.zip'),'-d',extracted]);
  const inventory=fs.readdirSync(path.join(extracted,'downloads/lady-d-finalization')).filter(n=>/^volume-.*\.html$/.test(n)).sort();
  assert.deepEqual(inventory,expected.map(r=>r.html).sort(),'Exactly the six expected readers must be bundled');
  const page=await browser.newPage({viewport:{width:390,height:844}});
  const failures=[];
  page.on('requestfailed',r=>{if(r.url().startsWith('file:'))failures.push(r.url())});
  page.on('pageerror',e=>failures.push(e.message));
  await page.route(/^https?:/,route=>{report.networkDependencies.push(route.request().url());return route.abort()});
  for(const filename of ['susan-damon-hub.html','lady-d-cover-decision-deck.html','lady-d-31-day-visual-journal.html',...expected.map(r=>'downloads/lady-d-finalization/'+r.html)]){
   await page.goto(pathToFileURL(path.join(extracted,filename)).href);
   await page.evaluate(async()=>{for(const image of document.images){image.loading='eager';await image.decode()}await document.fonts.ready});
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${filename} overflows`);
   const backgrounds=await page.evaluate(()=>[...new Set([...document.querySelectorAll('*')].flatMap(e=>[...getComputedStyle(e).backgroundImage.matchAll(/url\("?([^"\)]+)"?\)/g)].map(m=>m[1])))].filter(url=>url.startsWith('file:')));
   for(const url of backgrounds)assert(await page.evaluate(url=>new Promise(resolve=>{const image=new Image();image.onload=()=>resolve(true);image.onerror=()=>resolve(false);image.src=url}),url),`${filename}: background missing ${url}`);
   if(filename.includes('polished-')){
    const journal=filename.includes('journal');await page.selectOption('#reading-day',journal?'j366':'dA366');
    assert.equal(new URL(page.url()).hash,journal?'#j366':'#dA366');
    await page.locator('.interior-skip').focus();await page.keyboard.press('Enter');
    await page.waitForFunction(value=>document.querySelector('#reading-day').value===value,journal?'j1':'dA1');
    assert.equal(await page.evaluate(()=>document.activeElement.id),journal?'j1':'dA1');
   }
   report.files.push({filename,localBackgrounds:backgrounds.length,images:await page.locator('img').count()});
  }
  assert.deepEqual(failures,[]);
  assert.equal(report.files.length,9);
  assert.deepEqual(report.networkDependencies,[],'Portable reading pages requested external resources');
  report.status='PASS';
  fs.writeFileSync(path.join(quality,'offline-package.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify(report,null,2));
 }finally{await browser.close();fs.rmSync(extracted,{recursive:true,force:true})}
})().catch(e=>{fs.writeFileSync(path.join(quality,'offline-package.json'),JSON.stringify({status:'FAIL',error:e.message},null,2)+'\n');console.error(e);process.exitCode=1});

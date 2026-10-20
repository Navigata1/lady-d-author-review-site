const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..');
const out=path.join(root,'quality/editorial-2026-10-20');
const names=fs.readdirSync(path.join(root,'public/downloads/lady-d-finalization')).filter(name=>/^volume-.*-polished-.*\.html$/.test(name)).sort();

(async()=>{
 const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
 const report={status:'RUNNING',files:[]};
 try{
  for(const name of names){
   const page=await browser.newPage({viewport:{width:1100,height:1000}});
   const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
   await page.goto(pathToFileURL(path.join(root,'public/downloads/lady-d-finalization',name)).href);
   await page.emulateMedia({media:'print'});await page.evaluate(()=>document.fonts.ready);
   const result=await page.evaluate(async()=>{
    for(const image of document.images){image.loading='eager';await image.decode()}
    const leaves=[...document.querySelectorAll('.leaf')];
    const bad=leaves.flatMap((leaf,index)=>{
      const r=leaf.getBoundingClientRect(),flow=leaf.querySelector('.flow'),f=leaf.querySelector('.folio').getBoundingClientRect();
      const items=flow?[...flow.children].filter(e=>getComputedStyle(e).display!=='none'):[];
      const bottom=items.length?Math.max(...items.map(e=>e.getBoundingClientRect().bottom)):r.top;
      const overflow=flow&&(flow.scrollHeight>flow.clientHeight+2||flow.scrollWidth>flow.clientWidth+2);
      return overflow||r.width!==576||r.height!==864||bottom>f.top-4?[{page:index+1,id:leaf.id,overflow,contentBottom:bottom-r.top,footerTop:f.top-r.top}]:[];
    });
    return {pages:leaves.length,bad,monthlyImages:document.querySelectorAll('.monthly-art').length,fontsReady:document.fonts.check('12px Spectral')};
   });
   assert.equal(result.bad.length,0,`${name}: ${JSON.stringify(result.bad.slice(0,15))}`);
   assert(result.fontsReady,`${name}: body font missing`);
   const journal=name.includes('companion-journal');
   assert.equal(result.pages,journal?420:756);
   if(journal)assert.equal(result.monthlyImages,12);
   const proof=journal?page.locator('.mdiv').first().locator('xpath=ancestor::section'):page.locator('#dB3');
   await proof.screenshot({path:path.join(out,name.replace('.html','-print.png'))});
   for(const width of [320,390]){
    await page.emulateMedia({media:'screen'});await page.setViewportSize({width,height:844});
    await page.selectOption('#reading-day',journal?'j3':'dA3');
    assert.equal(new URL(page.url()).hash,journal?'#j3':'#dA3');
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${name} overflows at ${width}`);
    assert(await page.evaluate(()=>document.activeElement.id===document.querySelector('#reading-day').value));
    if(width===390)await page.screenshot({path:path.join(out,name.replace('.html','-mobile.png')),fullPage:false});
   }
   await page.locator('.interior-skip').focus();
   await page.keyboard.press('Enter');
   await page.waitForFunction(expected=>document.querySelector('#reading-day').value===expected,journal?'j1':'dA1');
   assert.equal(await page.evaluate(()=>document.activeElement.id),journal?'j1':'dA1');
   assert.deepEqual(errors,[]);
   report.files.push({name,...result,mobileWidths:[320,390],errors:0});
   await page.close();
  }
  report.status='PASS';
  fs.writeFileSync(path.join(out,'layout-audit.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify(report,null,2));
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1;});

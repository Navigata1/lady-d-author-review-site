const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
const base = process.env.BASE_URL || 'http://127.0.0.1:8794';
const out = path.join(root, 'quality/polish-2026-09-07');
const sha = file => crypto.createHash('sha256').update(fs.readFileSync(path.join(root,file))).digest('hex');
fs.mkdirSync(path.join(out,'print-pages'),{recursive:true});

(async () => {
  const browser = await chromium.launch();
  const report = {status:'RUNNING', base, checkedAt:new Date().toISOString(), viewports:[], print:[], controls:[]};
  try {
    for (const width of [320,390,768,1440]) {
      const page = await browser.newPage({viewport:{width,height:1000}});
      const errors=[];
      page.on('pageerror',e=>errors.push(e.message));
      page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
      assert((await page.goto(`${base}/lady-d-31-day-visual-journal.html#day-01`)).ok());
      await page.evaluate(()=>document.fonts.ready);
      assert.equal(await page.locator('.is-current').getAttribute('data-day'),'1');
      assert(await page.locator('#previous-day').isDisabled());
      await page.locator('#next-day').click();
      assert.equal(await page.locator('.is-current').getAttribute('data-day'),'2');
      await page.reload();
      assert.equal(await page.locator('.is-current').getAttribute('data-day'),'2');
      for(let day=1;day<=31;day++) {
        await page.selectOption('#day-select',String(day));
        await page.locator('body').click({position:{x:2,y:2}});
        assert.equal(await page.locator('.is-current').getAttribute('data-day'),String(day));
        const fit=await page.evaluate(async()=>{
          const leaf=document.querySelector('.is-current'),copy=leaf.querySelector('.copy');
          const r=leaf.getBoundingClientRect(),c=copy.getBoundingClientRect(),f=leaf.querySelector('footer').getBoundingClientRect();
          const src=leaf.querySelector('.art').style.backgroundImage.match(/url\(["']?(.*?)["']?\)/)[1];
          const img=new Image();img.src=src;await img.decode();
          return {inside:c.left>=r.left-1&&c.right<=r.right+1&&c.top>=r.top-1&&c.bottom<f.top-2,overflow:document.documentElement.scrollWidth>innerWidth,loaded:img.naturalWidth>0};
        });
        assert(fit.inside,`Day ${day} does not fit at ${width}`);
        assert(!fit.overflow,`Horizontal overflow at ${width}`);
        assert(fit.loaded,`Day ${day} art did not load`);
      }
      assert(await page.locator('#next-day').isDisabled());
      await page.selectOption('#day-select','19');
      await page.locator('[data-view=text]').click();
      assert(await page.locator('.reading-panel').isVisible());
      assert(await page.locator('.reading-panel').innerText().then(t=>t.includes('The Comforter Will Teach You')));
      assert(await page.locator('.reading-panel .encouragement').evaluate(e=>parseFloat(getComputedStyle(e).fontSize)>=20));
      await page.screenshot({path:path.join(out,`reader-text-${width}.png`),fullPage:true});
      await page.locator('[data-view=page]').click();
      await page.selectOption('#day-select','1');
      await page.screenshot({path:path.join(out,`reader-${width}.png`),fullPage:true});
      assert.equal(errors.length,0,errors.join('\n'));
      report.viewports.push({width,days:31,artLoaded:true,copyFits:true,errors:0});
      await page.close();
    }
    const page=await browser.newPage({viewport:{width:576,height:864}});
    await page.goto(`${base}/lady-d-31-day-visual-journal.html#day-31`);
    await page.locator('[data-view=text]').click();
    await page.emulateMedia({media:'print'});
    await page.evaluate(()=>document.fonts.ready);
    assert.equal(await page.locator('.journal-page:visible').count(),31);
    const dimensions=await page.locator('.journal-page').evaluateAll(leaves=>leaves.map(leaf=>{
      const r=leaf.getBoundingClientRect(),copy=leaf.querySelector('.copy'),c=copy.getBoundingClientRect(),f=leaf.querySelector('footer').getBoundingClientRect();
      return {day:leaf.dataset.day,width:r.width,height:r.height,transform:getComputedStyle(leaf).transform,prayerPt:parseFloat(getComputedStyle(copy.querySelector('.prayer')).fontSize)*.75,inside:c.left>=r.left&&c.right<=r.right&&c.top>=r.top&&c.bottom<f.top-2};
    }));
    for(const row of dimensions){assert.equal(row.width,576);assert.equal(row.height,864);assert.equal(row.transform,'none');assert(row.inside,`Print day ${row.day} overflow`);assert(row.prayerPt>=10.2);}
    for(let i=0;i<31;i++)await page.locator('.journal-page').nth(i).screenshot({path:path.join(out,'print-pages',`day-${String(i+1).padStart(2,'0')}.png`)});
    report.print=dimensions;
    await page.emulateMedia({media:'screen'});
    await page.setViewportSize({width:390,height:667});
    await page.goto(`${base}/lady-d-31-day-visual-journal.html#day-19`);
    await page.locator('.skip-link').focus();
    await page.keyboard.press('Enter');
    assert.equal(await page.locator('.is-current').getAttribute('data-day'),'19');
    assert.equal(await page.evaluate(()=>localStorage.getItem('lady-d-mornings-last-day')),'18');
    assert.equal(await page.evaluate(()=>document.activeElement.id),'main');
    await page.locator('[data-view=text]').click();
    await page.locator('#next-day').scrollIntoViewIfNeeded();
    await page.locator('#next-day').click();
    assert.equal(await page.locator('.is-current').getAttribute('data-day'),'20');
    assert(await page.locator('.reading-panel h2').evaluate(e=>{const r=e.getBoundingClientRect();return r.top>=0&&r.bottom<innerHeight&&document.activeElement===e;}));
    await page.emulateMedia({media:'screen',reducedMotion:'reduce'});
    await page.goto(`${base}/lady-d-31-day-visual-journal-scene-console.html`);
    assert.equal(await page.locator('.gallery-day').count(),31);
    await page.locator('.gallery-day').last().scrollIntoViewIfNeeded();
    await page.locator('.gallery-day').last().locator('a').click();
    assert.equal(await page.locator('.is-current').getAttribute('data-day'),'31');
    assert.equal(await page.evaluate(()=>getComputedStyle(document.documentElement).scrollBehavior),'auto');
    report.controls=['previous/next boundaries','31-day selector','permalinks and reload','large text view','gallery-to-day navigation','reduced motion','print all days from text mode','skip link preserves day and saved progress','text-mode page turns focus the new heading at 390x667'];
    report.inputs=Object.fromEntries(['assets/lady-d-reader/reader.css','assets/lady-d-reader/reader.js','scripts/lady_d_finalization/journal_presentation.py','source/finalization/31-day-visual-journal-v2/visual-journal-plan.json'].map(file=>[file,sha(file)]));
    report.status='PASS';
    fs.writeFileSync(path.join(out,'reader-gauntlet.json'),JSON.stringify(report,null,2)+'\n');
    fs.writeFileSync(path.join(root,'quality/31-day-visual-journal-v2/browser-gauntlet.json'),JSON.stringify(report,null,2)+'\n');
    console.log(JSON.stringify({status:report.status,viewports:report.viewports,printPages:report.print.length,controls:report.controls},null,2));
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});

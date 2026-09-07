const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
const base = process.env.BASE_URL || 'https://lady-d-author-review-site.vercel.app';

(async () => {
  const browser = await chromium.launch();
  const report = {base, checkedAt:new Date().toISOString(), viewports:[]};
  try {
    for (const width of [390,1440]) {
      const page = await browser.newPage({viewport:{width,height:900}});
      const errors = [];
      page.on('pageerror',error=>errors.push(error.message));
      page.on('console',message=>{if(message.type()==='error')errors.push(message.text());});
      const response = await page.goto(base+'/');
      assert(response.ok());
      assert.equal(new URL(page.url()).origin,base);
      await page.evaluate(()=>document.fonts.ready);
      assert(!(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)));
      assert.equal(await page.locator('a[href="https://buy.stripe.com/fZu28t5WpchE73EbnA0VO0a"]').count(),1);
      await page.screenshot({path:path.join(root,`quality/polish-2026-09-07/live-hub-${width}.png`)});
      await page.goto(base+'/lady-d-31-day-visual-journal.html#day-19');
      assert.equal(await page.locator('.is-current').getAttribute('data-day'),'19');
      await page.locator('.skip-link').focus();
      await page.keyboard.press('Enter');
      assert.equal(await page.locator('.is-current').getAttribute('data-day'),'19');
      await page.locator('[data-view=text]').click();
      await page.locator('#next-day').click();
      assert.equal(await page.locator('.is-current').getAttribute('data-day'),'20');
      assert(await page.locator('.reading-panel h2').evaluate(e=>{const r=e.getBoundingClientRect();return document.activeElement===e&&r.top>=0&&r.bottom<innerHeight;}));
      await page.locator('[data-view=page]').click();
      await page.selectOption('#day-select','1');
      await page.evaluate(async()=>{
        const source=document.querySelector('.is-current .art').style.backgroundImage.match(/url\(["']?(.*?)["']?\)/)[1];
        const image=new Image();image.src=source;await image.decode();
        if(image.naturalWidth<1000)throw new Error('Current scene is missing or undersized');
        await document.fonts.ready;
      });
      await page.screenshot({path:path.join(root,`quality/polish-2026-09-07/live-reader-${width}.png`),fullPage:true});
      await page.goto(base+'/lady-d-31-day-visual-journal-scene-console.html');
      assert.equal(await page.locator('.gallery-day').count(),31);
      await page.locator('.gallery-day').last().locator('a').click();
      assert.equal(await page.locator('.is-current').getAttribute('data-day'),'31');
      assert(await page.locator('#next-day').isDisabled());
      assert(!(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)));
      assert.deepEqual(errors,[]);
      report.viewports.push({width,home:true,reader:true,gallery:true,skipLink:true,textFocus:true,errors:0});
      await page.close();
    }
    report.status='PASS';
    fs.writeFileSync(path.join(root,'quality/polish-2026-09-07/live-browser.json'),JSON.stringify(report,null,2)+'\n');
    console.log(JSON.stringify(report,null,2));
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});

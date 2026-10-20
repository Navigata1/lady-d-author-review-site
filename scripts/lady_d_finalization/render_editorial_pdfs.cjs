const {chromium} = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {createHash} = require('node:crypto');
const root = path.resolve(__dirname,'../..');
const directory = path.join(root,'public/downloads/lady-d-finalization');
const {execFileSync} = require('node:child_process');
const {assertInventory}=require('./editorial_inventory.cjs');
const names = [['surrendering-to-gods-love','Surrendering-to-Gods-Love'],['walking-with-jesus','Walking-with-Jesus'],['filled-with-the-holy-spirit','Filled-with-the-Holy-Spirit']];

(async()=>{
  fs.mkdirSync(path.join(root,'output/pdf'),{recursive:true});
  const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
  const results=[];
  try{
    for(let volume=1;volume<=3;volume++)for(const journal of [false,true]){
      const [slug,label]=names[volume-1];
      const html=`volume-${volume}-${slug}-polished-${journal?'companion-journal':'devotional'}.html`;
      const pdf=`Lady-D-Volume-${volume}-${label}-${journal?'Companion-Journal-Deep-Dive':'Polished'}-6x9.pdf`;
      const page=await browser.newPage({viewport:{width:900,height:1200}});
      await page.goto(pathToFileURL(path.join(directory,html)).href,{waitUntil:'load'});
      await page.emulateMedia({media:'print'});
      await page.evaluate(async()=>{
        for(const image of document.images){image.loading='eager';await image.decode();}
        await document.fonts.ready;
      });
      const count=await page.locator('.leaf').count();
      const output=path.join(root,'output/pdf',pdf);
      await page.pdf({path:output,width:'6in',height:'9in',printBackground:true,preferCSSPageSize:true,tagged:true,outline:true,margin:{top:'0',right:'0',bottom:'0',left:'0'}});
      const info=execFileSync('pdfinfo',[output],{encoding:'utf8'});
      if(Number(info.match(/^Pages:\s+(\d+)/m)?.[1])!==count)throw new Error(`${pdf} page count mismatch`);
      for(const destination of [path.join(directory,pdf),path.join(root,'downloads/lady-d-finalization',pdf)])fs.copyFileSync(output,destination);
      const sha256=createHash('sha256').update(fs.readFileSync(output)).digest('hex');
      results.push({volume,journal,html,pdf,pages:count,bytes:fs.statSync(output).size,sha256});
      console.log(JSON.stringify(results.at(-1)));
      await page.close();
    }
    assertInventory({status:'PASS',results});
    fs.writeFileSync(path.join(root,'quality/editorial-2026-10-20/pdf-build.json'),JSON.stringify({status:'PASS',results},null,2)+'\n');
  }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});

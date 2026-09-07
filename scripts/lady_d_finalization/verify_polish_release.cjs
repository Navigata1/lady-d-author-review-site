const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..');
const base=process.env.BASE_URL || 'https://lady-d-author-review-site.vercel.app';
const report={base,checkedAt:new Date().toISOString(),routes:[],downloads:[]};
const sha=buffer=>crypto.createHash('sha256').update(buffer).digest('hex');
function assertPublicResponse(response,route){
  assert.equal(new URL(response.url).origin,new URL(base).origin,`${route}: redirected outside the publishing site`);
  assert(response.ok,`${route}: ${response.status}`);
}
(async()=>{
  const hub=fs.readFileSync(path.join(root,'public/susan-damon-hub.html'),'utf8');
  const routes=new Set(['/','/susan-damon-hub.html','/lady-d-31-day-visual-journal.html','/lady-d-31-day-visual-journal-scene-console.html','/assets/lady-d-hub-polish.css','/assets/lady-d-reader/reader.css','/assets/lady-d-reader/reader.js','/assets/lady-d-reader/chevron-right.svg']);
  for(const [,href] of hub.matchAll(/(?:href|src)="([^"]+)"/g)){
    if(!/^(https?:|#)/.test(href))routes.add('/'+href.replace(/^\//,'').split('#')[0]);
  }
  for(const route of routes){
    const response=await fetch(base+route,{method:'HEAD',signal:AbortSignal.timeout(30000)});
    assertPublicResponse(response,route);report.routes.push({route,status:response.status});
  }
  for(const [route,file] of [['/','public/susan-damon-hub.html'],['/susan-damon-hub.html','public/susan-damon-hub.html'],['/lady-d-31-day-visual-journal.html','public/lady-d-31-day-visual-journal.html'],['/lady-d-31-day-visual-journal-scene-console.html','public/lady-d-31-day-visual-journal-scene-console.html'],['/assets/lady-d-reader/reader.js','public/assets/lady-d-reader/reader.js'],['/assets/lady-d-reader/reader.css','public/assets/lady-d-reader/reader.css']]){
    const response=await fetch(base+route);assertPublicResponse(response,route);const bytes=Buffer.from(await response.arrayBuffer());assert.equal(sha(bytes),sha(fs.readFileSync(path.join(root,file))),`Live bytes differ: ${route}`);
  }
  for(const filename of ['Lady-D-Thirty-One-Mornings-of-Light-Visual-Journal-6x9.pdf','Lady-D-Thirty-One-Mornings-of-Light-Complete-Package-2026-09-07.zip']){
    const route='/downloads/lady-d-finalization/'+filename;
    const response=await fetch(base+route,{signal:AbortSignal.timeout(180000)});assertPublicResponse(response,route);
    const hash=crypto.createHash('sha256');let count=0;
    for await(const chunk of response.body){hash.update(chunk);count+=chunk.length;}
    const actual=hash.digest('hex'),expected=sha(fs.readFileSync(path.join(root,'public'+route)));
    assert.equal(actual,expected,`Download checksum differs: ${filename}`);
    report.downloads.push({filename,bytes:count,sha256:actual});
  }
  report.status='PASS';
  fs.writeFileSync(path.join(root,'quality/polish-2026-09-07/live-release.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify(report,null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});

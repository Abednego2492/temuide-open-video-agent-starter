import {existsSync,readFileSync,mkdirSync,writeFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
const project=JSON.parse(readFileSync('src/project.json','utf8'));
const findings=[];const filename='output/final.mp4';
let video={exists:existsSync(filename)};
if(!video.exists)findings.push({severity:'BLOCKER',detail:'Final MP4 missing'});
for(const s of project.scenes){
 if(s.startFrame<0||s.durationFrames<=0||s.startFrame+s.durationFrames>project.durationFrames)findings.push({severity:'BLOCKER',scene:s.id,detail:'Invalid scene range'});
 if(s.asset&&!existsSync('public/'+s.asset))findings.push({severity:'BLOCKER',scene:s.id,detail:'Asset not found: '+s.asset});
}
if(video.exists)try{
 const probe=JSON.parse(execFileSync('ffprobe',['-v','error','-show_format','-show_streams','-of','json',filename],{encoding:'utf8'}));
 const v=probe.streams.find(s=>s.codec_type==='video');
 video={...video,width:v?.width,height:v?.height,duration:Number(probe.format?.duration)};
 if(v?.width!==project.width||v?.height!==project.height)findings.push({severity:'BLOCKER',detail:'Wrong dimensions'});
}catch(e){findings.push({severity:'BLOCKER',detail:'FFprobe failure: '+e.message})}
const report={timestamp:new Date().toISOString(),video,findings,technicalStatus:findings.length?'FAIL':'TECHNICAL_CHECKS_PASS',creativeApproval:'PENDING_REAL_VISUAL_AND_AUDIO_REVIEW'};
mkdirSync('output',{recursive:true});writeFileSync('output/critic-report.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
if(findings.length)process.exitCode=1;

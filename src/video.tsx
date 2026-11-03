import React from 'react';
import { AbsoluteFill, interpolate, Sequence, staticFile, useCurrentFrame, spring, Img } from 'remotion';
import { Video } from '@remotion/media';
import project from './project.json';

type Scene = typeof project.scenes[number];
const isVideo = (p: string) => /\.(mp4|mov|webm)$/i.test(p);
const isImage = (p: string) => /\.(png|jpe?g|webp)$/i.test(p);

const SceneView: React.FC<{ scene: Scene; sceneIndex: number }> = ({scene, sceneIndex}) => {
  const frame = useCurrentFrame();
  const p = spring({frame, fps: project.fps, config: {damping: 22, stiffness: 125, mass: 0.9}});
  const end = Math.max(0, scene.durationFrames - 12);
  const visibility = interpolate(frame, [0, 10, end, scene.durationFrames],
    [0, 1, 1, 0], {extrapolateLeft:'clamp', extrapolateRight:'clamp'});
  const filename = scene.asset?.replace(/^\/+/, '').trim();
  const mediaSrc = filename ? staticFile(filename) : null;
  return (
    <AbsoluteFill style={{background:project.palette.background, overflow:'hidden'}}>
      {mediaSrc && isVideo(filename) ? <Video src={mediaSrc} style={{width:'100%',height:'100%',objectFit:'cover'}} muted /> : null}
      {mediaSrc && isImage(filename) ? <Img src={mediaSrc} style={{width:'100%',height:'100%',objectFit:'cover'}} /> : null}
      <AbsoluteFill style={{background:'linear-gradient(180deg, rgba(0,0,0,.25),rgba(0,0,0,.08) 50%,rgba(0,0,0,.68))'}} />
      <AbsoluteFill style={{padding:'0 84px',justifyContent:'center',alignItems:'flex-start'}}>
        <div style={{color:project.palette.accent,letterSpacing:6,fontSize:32,fontWeight:800,opacity:visibility,marginBottom:22}}>
          {`0${sceneIndex + 1} / 0${project.scenes.length}`}
        </div>
        <div style={{maxWidth:900,fontFamily:project.fontFamily,color:project.palette.foreground,fontWeight:900,letterSpacing:-4,lineHeight:0.94,fontSize:100,opacity:visibility,transform:`translateY(${(1-p)*45}px)`}}>
          {scene.headline}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const DynamicEdit: React.FC = () => (
  <AbsoluteFill style={{background:project.palette.background}}>
    {project.scenes.map((scene,index) => (
      <Sequence key={scene.id} from={scene.startFrame} durationInFrames={scene.durationFrames}>
        <SceneView scene={scene} sceneIndex={index} />
      </Sequence>
    ))}
  </AbsoluteFill>
);

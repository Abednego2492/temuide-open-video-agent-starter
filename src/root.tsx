import React from 'react';
import { Composition } from 'remotion';
import { DynamicEdit } from './video';
import project from './project.json';

export const VideoRoot: React.FC = () => (
  <Composition id="DynamicEdit" component={DynamicEdit}
    durationInFrames={project.durationFrames} fps={project.fps}
    width={project.width} height={project.height} />
);

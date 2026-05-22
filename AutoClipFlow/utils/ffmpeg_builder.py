"""
ffmpeg_builder.py - FFmpeg 命令构建器与执行器
使用 filter_complex 实现片段拼接与变速
"""

import subprocess
from pathlib import Path
from typing import List, Dict, Any


class FFmpegBuilder:
    def __init__(self, config: Dict[str, Any], segments: List[Dict[str, Any]]):
        self.config = config
        self.segments = segments
        self.speed_factor = config['speed']['factor']
        self.output_path = Path(config['output']['filename'])

    def build(self) -> 'FFmpegBuilder':
        if not self.output_path.parent.exists():
            self.output_path.parent.mkdir(parents=True)

        inputs = []
        filter_parts = []
        concat_inputs = []

        for i, seg in enumerate(self.segments):
            clip_start = seg.get('clip_start', 0)
            clip_duration = seg['duration']
            clip_speed = seg.get('speed', 1.0)
            effective_speed = self.speed_factor * clip_speed
            inputs.extend(['-ss', str(clip_start), '-i', str(seg['path'])])

            filter_parts.append(
                f"[{i}:v]trim=0:{clip_duration},setpts=PTS/{effective_speed},"
                f"scale={self.config['video']['width']}:{self.config['video']['height']},"
                f"fps={self.config['video']['fps']}[v{i}]"
            )
            concat_inputs.append(f"[v{i}]")

        filter_str = '; '.join(filter_parts) + f'; {"".join(concat_inputs)} concat=n={len(self.segments)}:v=1:a=0 [out]'

        self.cmd = [
            'ffmpeg', '-y'
        ] + inputs + [
            '-filter_complex', filter_str,
            '-map', '[out]',
            '-c:v', self.config['video']['codec'],
            '-b:v', self.config['video']['bitrate'],
            '-an',
            str(self.output_path)
        ]

        return self

    def execute(self) -> Path:
        result = subprocess.run(self.cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg 执行失败: {result.stderr}")
        return self.output_path
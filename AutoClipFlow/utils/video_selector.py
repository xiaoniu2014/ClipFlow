"""
video_selector.py - 视频素材选择器
从各目录随机挑选视频片段，拼接成指定时长的段落
"""

import random
import subprocess
from pathlib import Path
from typing import List, Dict, Any


class VideoSelector:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.segments: List[Dict[str, Any]] = []

    def get_video_duration(self, video_path: Path) -> float:
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'json', str(video_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        import json
        data = json.loads(result.stdout)
        return float(data['format']['duration'])

    def get_valid_videos(self, source_dir: Path, min_dur: float, max_dur: float) -> List[Path]:
        """筛选时长在 [min_dur, max_dur] 区间的视频"""
        videos = list(source_dir.glob('*.mp4')) + list(source_dir.glob('*.MOV'))
        valid = []
        for video in videos:
            try:
                dur = self.get_video_duration(video)
                if min_dur <= dur <= max_dur:
                    valid.append(video)
            except Exception:
                continue
        return valid

    def build_segment(self, clip_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """为一个段落（A/B/C）挑选足够的视频片段"""
        source_dir = Path(clip_config['source_dir'])
        min_dur = clip_config.get('min_duration', 3)
        max_dur = clip_config.get('max_duration', 8)
        target_duration = clip_config.get('end', 0) - clip_config.get('start', 0)

        valid_videos = self.get_valid_videos(source_dir, min_dur, max_dur)
        if not valid_videos:
            return []

        clips = []
        accumulated = 0.0

        while accumulated < target_duration:
            video = random.choice(valid_videos)
            dur = self.get_video_duration(video)

            remaining = target_duration - accumulated
            if dur > remaining:
                # 取部分片段
                clips.append({'path': video, 'start': 0, 'duration': remaining})
                accumulated = target_duration
            else:
                clips.append({'path': video, 'start': 0, 'duration': dur})
                accumulated += dur

        return clips

    def prepare_segments(self) -> List[Dict[str, Any]]:
        """构建所有段落（A、B、C）并拼接"""
        all_clips = []
        global_start = 0.0

        for clip_config in self.config['clips']:
            segment_clips = self.build_segment(clip_config)
            target_duration = clip_config.get('end', 0) - clip_config.get('start', 0)

            # 计算该段落在全局时间线上的起始位置
            segment_start = global_start

            for clip in segment_clips:
                clip['start'] = segment_start
                clip['end'] = segment_start + clip['duration']
                all_clips.append(clip)
                segment_start += clip['duration']

            global_start += target_duration

        return all_clips
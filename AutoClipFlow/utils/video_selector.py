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

    def build_segment(self, clip_config: Dict[str, Any], used_videos: set) -> List[Dict[str, Any]]:
        """为一个段落（A/B/C）挑选足够的视频片段

        Args:
            clip_config: 段落配置
            used_videos: 当前已使用的视频集合（跨段落共享）
        """
        source_dir = Path(clip_config['source_dir'])
        min_dur = clip_config.get('min_duration', 3)
        max_dur = clip_config.get('max_duration', 8)
        target_duration = clip_config.get('end', 0) - clip_config.get('start', 0)

        if not source_dir.exists():
            print(f"⚠️  警告: 素材目录不存在: {source_dir}")
            return []

        valid_videos = self.get_valid_videos(source_dir, min_dur, max_dur)
        if not valid_videos:
            print(f"⚠️  警告: 目录 '{source_dir}' 中没有找到符合时长要求({min_dur}~{max_dur}秒)的视频")
            return []

        clips = []
        accumulated = 0.0

        while accumulated < target_duration:
            # Filter out videos that have already been used in this batch
            available = [v for v in valid_videos if v not in used_videos]
            if not available:
                print(f"⚠️  警告: 目录 '{source_dir}' 中可用视频不足（所有视频已在当前批次中使用）")
                break

            video = random.choice(available)
            used_videos.add(video)
            dur = self.get_video_duration(video)

            remaining = target_duration - accumulated
            # Skip if remaining duration is too small (floating point precision issue)
            if remaining < 0.05:
                break

            if dur > remaining:
                clips.append({'path': video, 'start': 0, 'duration': round(remaining, 3)})
                accumulated = target_duration
            else:
                clips.append({'path': video, 'start': 0, 'duration': round(dur, 3)})
                accumulated += dur

        return clips

    def prepare_segments(self) -> List[Dict[str, Any]]:
        """构建所有段落（A、B、C）并拼接"""
        all_clips = []
        global_start = 0.0
        used_videos = set()  # Track used videos across all segments in this batch

        for clip_config in self.config['clips']:
            segment_clips = self.build_segment(clip_config, used_videos)
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
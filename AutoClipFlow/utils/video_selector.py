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

    def get_all_videos(self, source_dir: Path, min_dur: float, max_dur: float) -> tuple:
        """获取所有视频，按时长分类

        Returns:
            tuple: (short_videos, valid_videos, long_videos)
        """
        videos = list(source_dir.glob('*.mp4')) + list(source_dir.glob('*.MOV'))
        short_videos = []
        valid_videos = []
        long_videos = []
        for video in videos:
            try:
                dur = self.get_video_duration(video)
                if dur < min_dur:
                    short_videos.append(video)
                elif dur <= max_dur:
                    valid_videos.append(video)
                else:
                    long_videos.append(video)
            except Exception:
                continue
        return short_videos, valid_videos, long_videos

    def make_video_fit_duration(self, video: Path, target_dur: float, used_videos: set) -> Dict[str, Any]:
        """使视频符合目标时长，随机选择策略：

        Args:
            video: 视频路径
            target_dur: 目标时长
            used_videos: 已使用视频集合

        Returns:
            Dict: {'path': video, 'start': start_time, 'duration': duration, 'speed': speed}
        """
        dur = self.get_video_duration(video)
        strategy = random.choice(['cut', 'speed'])

        if strategy == 'cut':
            # 策略1：随机裁剪片段
            max_start = dur - target_dur
            if max_start <= 0:
                start = 0
            else:
                start = random.uniform(0, max_start)
            return {
                'path': video,
                'start': round(start, 3),
                'duration': round(target_dur, 3),
                'speed': 1.0
            }
        else:
            # 策略2：变速处理
            speed = dur / target_dur
            return {
                'path': video,
                'start': 0,
                'duration': round(target_dur, 3),
                'speed': round(speed, 2)
            }

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

        short_vids, valid_vids, long_vids = self.get_all_videos(source_dir, min_dur, max_dur)

        # 合并有效视频和长视频（长视频通过裁剪/变速处理后可使用）
        usable_videos = valid_vids + long_vids

        if not usable_videos:
            print(f"⚠️  警告: 目录 '{source_dir}' 中没有可用视频（时长不足 {min_dur} 秒的视频已舍弃）")
            return []

        clips = []
        accumulated = 0.0

        while accumulated < target_duration:
            # Filter out videos that have already been used in this batch
            available = [v for v in usable_videos if v not in used_videos]
            if not available:
                print(f"⚠️  警告: 目录 '{source_dir}' 中可用视频不足（所有视频已在当前批次中使用）")
                break

            video = random.choice(available)
            dur = self.get_video_duration(video)

            remaining = target_duration - accumulated
            # Skip if remaining duration is too small (floating point precision issue)
            if remaining < 0.05:
                break

            if dur > remaining:
                # 从剩余部分裁剪
                clips.append({'path': video, 'start': 0, 'duration': round(remaining, 3), 'speed': 1.0})
                used_videos.add(video)
                accumulated = target_duration
            elif min_dur <= dur <= max_dur:
                # 时长符合要求，直接使用
                clips.append({'path': video, 'start': 0, 'duration': round(dur, 3), 'speed': 1.0})
                used_videos.add(video)
                accumulated += dur
            else:
                # dur > max_dur，通过裁剪或变速处理
                clip_info = self.make_video_fit_duration(video, remaining if remaining < dur else dur, used_videos)
                clips.append(clip_info)
                used_videos.add(video)
                accumulated += clip_info['duration']

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
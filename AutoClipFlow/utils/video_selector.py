"""
video_selector.py - 视频素材选择器
从各目录随机挑选视频片段，拼接成指定时长的段落
"""

import random
import subprocess
from pathlib import Path
from typing import List, Dict, Any


class VideoPool:
    """视频池，按顺序均匀使用视频素材"""

    def __init__(self, videos: List[Path]):
        self.videos = videos
        self.index = 0
        if videos:
            random.shuffle(self.videos)

    def get_next(self) -> Path:
        """获取下一个视频（循环）"""
        if not self.videos:
            return None
        video = self.videos[self.index]
        self.index = (self.index + 1) % len(self.videos)
        # 当转回起点时，重新洗牌
        if self.index == 0:
            random.shuffle(self.videos)
        return video

    def __len__(self):
        return len(self.videos)


class VideoSelector:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.segments: List[Dict[str, Any]] = []
        # 每个source_dir维护一个独立的视频池
        self.pools: Dict[str, VideoPool] = {}

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

    def _get_or_create_pool(self, source_dir: Path, min_dur: float, max_dur: float) -> VideoPool:
        """获取或创建指定目录的视频池"""
        dir_key = str(source_dir.resolve())
        if dir_key not in self.pools:
            short_vids, valid_vids, long_vids = self.get_all_videos(source_dir, min_dur, max_dur)
            usable_videos = valid_vids + long_vids
            if usable_videos:
                self.pools[dir_key] = VideoPool(usable_videos)
            else:
                self.pools[dir_key] = VideoPool([])
        return self.pools[dir_key]

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

    def make_video_fit_duration(self, video: Path, target_dur: float) -> Dict[str, Any]:
        """使视频符合目标时长，随机选择策略：

        Args:
            video: 视频路径
            target_dur: 目标时长

        Returns:
            Dict: {'path': video, 'start': start_time, 'duration': duration, 'speed': speed}
        """
        dur = self.get_video_duration(video)
        # 如果目标时长过短（<0.5秒），强制使用变速策略，避免产生过短片段
        if target_dur < 0.5:
            strategy = 'speed'
        else:
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

    def build_segment(self, clip_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """为一个段落挑选足够的视频片段

        Args:
            clip_config: 段落配置
        """
        source_dir = Path(clip_config['source_dir'])
        min_dur = clip_config.get('min_duration', 3)
        max_dur = clip_config.get('max_duration', 8)
        target_duration = clip_config.get('end', 0) - clip_config.get('start', 0)

        if not source_dir.exists():
            print(f"⚠️  警告: 素材目录不存在: {source_dir}")
            return []

        pool = self._get_or_create_pool(source_dir, min_dur, max_dur)
        if len(pool) == 0:
            print(f"⚠️  警告: 目录 '{source_dir}' 中没有可用视频（时长不足 {min_dur} 秒的视频已舍弃）")
            return []

        clips = []
        accumulated = 0.0

        while accumulated < target_duration:
            video = pool.get_next()
            if video is None:
                print(f"⚠️  警告: 目录 '{source_dir}' 中可用视频不足")
                break
            dur = self.get_video_duration(video)

            remaining = target_duration - accumulated
            if remaining < 0.5:
                break

            # 如果剩余时长过短（<0.5秒），不再裁剪短片段，而是通过变速处理
            if remaining < 0.5 and dur > remaining:
                # 将该视频通过变速处理来填补剩余（不放慢所有片段，只放慢这一个）
                clip_info = self.make_video_fit_duration(video, remaining)
                clips.append(clip_info)
                accumulated += clip_info['duration']
            elif dur > remaining:
                # 从剩余部分裁剪
                clips.append({'path': video, 'start': 0, 'duration': round(remaining, 3), 'speed': 1.0})
                accumulated = target_duration
            elif min_dur <= dur <= max_dur:
                # 时长符合要求，直接使用
                clips.append({'path': video, 'start': 0, 'duration': round(dur, 3), 'speed': 1.0})
                accumulated += dur
            else:
                # dur > max_dur，通过裁剪或变速处理
                clip_info = self.make_video_fit_duration(video, remaining if remaining < dur else dur)
                clips.append(clip_info)
                accumulated += clip_info['duration']

        # 如果剩余时长 < 0.5 秒，对前面所有片段做变速处理，避免产生过短片段
        if accumulated < target_duration:
            remaining = target_duration - accumulated
            if remaining < 0.5 and clips:
                # 内容总时长 < 目标时长，需放慢速度（speed < 1）
                speed_factor = accumulated / target_duration
                for clip in clips:
                    current_speed = clip.get('speed', 1.0)
                    clip['speed'] = round(current_speed * speed_factor, 2)
                accumulated = target_duration

        return clips

    def prepare_segments(self) -> List[Dict[str, Any]]:
        """构建所有段落（A、B、C）并拼接"""
        all_clips = []
        global_start = 0.0
        # 重置视频池，保证批次间独立
        self.pools = {}

        for clip_config in self.config['clips']:
            segment_clips = self.build_segment(clip_config)
            target_duration = clip_config.get('end', 0) - clip_config.get('start', 0)

            # 计算该段落在全局时间线上的起始位置
            segment_start = global_start

            for clip in segment_clips:
                clip['clip_start'] = clip.get('start', 0)  # 保留视频内截取起始位置
                clip['start'] = segment_start  # 全局时间线起始位置
                clip['end'] = segment_start + clip['duration']
                all_clips.append(clip)
                segment_start += clip['duration']

            global_start += target_duration

        return all_clips
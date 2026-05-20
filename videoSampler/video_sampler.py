"""
视频随机抽样算法
根据目标时长从素材池中随机抽取视频片段，生成剪辑计划
"""

import random
import os
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class VideoClip:
    """单个视频片段信息"""
    file: str
    trim_start: float
    trim_duration: float
    original_duration: float

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "trim_start": self.trim_start,
            "trim_duration": self.trim_duration,
            "original_duration": self.original_duration
        }


class VideoSampler:
    """视频随机抽样器"""

    MAX_CLIP_DURATION = 2.0  # 单个片段最长时长

    def __init__(self, video_dir: str, seed: Optional[int] = None):
        """
        初始化抽样器

        Args:
            video_dir: 视频素材目录
            seed: 随机种子（可选，用于复现）
        """
        self.video_dir = video_dir
        if seed is not None:
            random.seed(seed)
        self._videos: List[str] = []
        self._last_video: Optional[str] = None

    def discover_videos(self, extensions: tuple = ('.mp4', '.mov', '.MOV')) -> List[str]:
        """发现目录下所有视频文件"""
        self._videos = []
        for root, _, files in os.walk(self.video_dir):
            for f in files:
                if f.lower().endswith(extensions):
                    self._videos.append(os.path.join(root, f))
        return self._videos

    def get_video_duration(self, video_path: str) -> float:
        """获取视频时长（秒）- 需要外部实现，支持 ffprobe 或直接返回文件级时长估算"""
        # 简单实现：可通过子类重写或依赖外部元数据
        raise NotImplementedError("需要实现获取视频时长的方法")

    def sample_clips(
        self,
        target_duration: float,
        video_durations: Optional[dict] = None
    ) -> List[VideoClip]:
        """
        随机抽取视频片段直到达到目标时长

        Args:
            target_duration: 目标总时长（秒）
            video_durations: 视频时长字典 {"path": duration}，如果为 None 则假设所有视频>=2秒

        Returns:
            剪辑计划列表
        """
        if not self._videos:
            self.discover_videos()

        clips: List[VideoClip] = []
        total_duration = 0.0
        attempts = 0
        max_attempts = len(self._videos) * 100  # 防止无限循环

        while total_duration < target_duration and attempts < max_attempts:
            attempts += 1

            # 随机选择视频（避免连续重复）
            available = [v for v in self._videos if v != self._last_video]
            if not available:
                break

            video_path = random.choice(available)
            self._last_video = video_path

            # 获取视频时长
            if video_durations and video_path in video_durations:
                duration = video_durations[video_path]
            else:
                # 默认假设 >= 2 秒
                duration = self.MAX_CLIP_DURATION + 0.1

            # 计算片段时长和起始位置
            if duration > self.MAX_CLIP_DURATION:
                max_start = duration - self.MAX_CLIP_DURATION
                trim_start = random.uniform(0, max_start)
                trim_duration = self.MAX_CLIP_DURATION
            else:
                trim_start = 0.0
                trim_duration = duration

            clip = VideoClip(
                file=video_path,
                trim_start=round(trim_start, 2),
                trim_duration=trim_duration,
                original_duration=round(duration, 2)
            )
            clips.append(clip)
            total_duration += trim_duration

        return clips

    def generate_plan(
        self,
        target_duration: float,
        video_durations: Optional[dict] = None
    ) -> List[dict]:
        """
        生成剪辑计划

        Args:
            target_duration: 目标总时长
            video_durations: 视频时长字典

        Returns:
            剪辑计划字典列表
        """
        clips = self.sample_clips(target_duration, video_durations)
        return [clip.to_dict() for clip in clips]


def load_video_durations(meta_file: str) -> dict:
    """
    从元数据文件加载视频时长

    Args:
        meta_file: 元数据文件路径（每行: path\tduration）

    Returns:
        {video_path: duration}
    """
    durations = {}
    if os.path.exists(meta_file):
        with open(meta_file, 'r') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) == 2:
                    durations[parts[0]] = float(parts[1])
    return durations


# === 示例用法 ===
if __name__ == "__main__":
    # 示例：假设有一些视频文件
    sampler = VideoSampler(video_dir="/path/to/videos", seed=42)

    # 如果有 ffprobe，可以这样获取时长
    # import subprocess
    # def get_duration(path):
    #     result = subprocess.run(
    #         ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
    #          '-of', 'default=noprint_wrappers=1:nokey=1', path],
    #         capture_output=True, text=True
    #     )
    #     return float(result.stdout.strip())

    # 示例剪辑计划
    target = 30.0  # 目标 30 秒

    # 假设已知的视频时长（实际使用时从 ffprobe 获取）
    durations = {
        "/path/to/video1.mp4": 3.7,
        "/path/to/video2.mp4": 8.2,
        "/path/to/video3.mp4": 1.5,
        "/path/to/video4.mp4": 12.0,
    }

    plan = sampler.generate_plan(target, durations)

    print(f"目标时长: {target}s")
    print(f"生成片段数: {len(plan)}")
    print(f"实际总时长: {sum(p['trim_duration'] for p in plan):.1f}s")
    print("\n剪辑计划:")
    for i, clip in enumerate(plan, 1):
        print(f"  {i}. {clip['file']} | start={clip['trim_start']}s | duration={clip['trim_duration']}s")

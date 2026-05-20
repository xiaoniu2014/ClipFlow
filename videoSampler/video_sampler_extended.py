"""
视频随机抽样算法 - 完整实现
支持 ffprobe 获取视频时长，支持批量生成剪辑计划
"""

import random
import json
import os
import subprocess
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class VideoClip:
    """单个视频片段信息"""
    file: str
    trim_start: float
    trim_duration: float
    original_duration: float

    def to_dict(self) -> dict:
        return asdict(self)


class FFProbeHelper:
    """ffprobe 工具封装"""

    @staticmethod
    def get_duration(video_path: str) -> float:
        """使用 ffprobe 获取视频时长"""
        try:
            result = subprocess.run(
                [
                    'ffprobe', '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    video_path
                ],
                capture_output=True, text=True, timeout=30
            )
            return float(result.stdout.strip())
        except Exception as e:
            print(f"获取时长失败 {video_path}: {e}")
            return 0.0

    @staticmethod
    def batch_get_durations(video_paths: List[str], workers: int = 4) -> Dict[str, float]:
        """批量获取视频时长"""
        durations = {}
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_path = {
                executor.submit(FFProbeHelper.get_duration, p): p
                for p in video_paths
            }
            for future in as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    durations[path] = future.result()
                except Exception:
                    durations[path] = 0.0
        return durations


class VideoSampler:
    """视频随机抽样器"""

    MAX_CLIP_DURATION = 2.0

    def __init__(
        self,
        video_dir: str,
        seed: Optional[int] = None,
        use_ffprobe: bool = False
    ):
        """
        Args:
            video_dir: 视频素材目录
            seed: 随机种子
            use_ffprobe: 是否使用 ffprobe 获取真实时长
        """
        self.video_dir = video_dir
        self.use_ffprobe = use_ffprobe
        if seed is not None:
            random.seed(seed)
        self._videos: List[str] = []
        self._last_video: Optional[str] = None
        self._durations: Dict[str, float] = {}

    def discover_videos(
        self,
        extensions: tuple = ('.mp4', '.mov', '.MOV', '.avi', '.mkv')
    ) -> List[str]:
        """发现目录下所有视频文件"""
        self._videos = []
        for root, _, files in os.walk(self.video_dir):
            for f in files:
                if f.lower().endswith(extensions):
                    self._videos.append(os.path.join(root, f))
        return self._videos

    def load_durations(self, durations: Optional[Dict[str, float]] = None):
        """手动设置或从 ffprobe 加载视频时长"""
        if durations:
            self._durations = durations
        elif self.use_ffprobe:
            print("正在通过 ffprobe 获取视频时长...")
            self._durations = FFProbeHelper.batch_get_durations(self._videos)
            print(f"已获取 {len(self._durations)} 个视频时长")

    def get_duration(self, video_path: str) -> float:
        """获取单个视频时长"""
        return self._durations.get(video_path, 0.0)

    def sample_clips(
        self,
        target_duration: float,
        durations: Optional[Dict[str, float]] = None
    ) -> List[VideoClip]:
        """
        随机抽取视频片段直到达到目标时长

        Args:
            target_duration: 目标总时长（秒）
            durations: 可选，覆盖已加载的时长数据

        Returns:
            VideoClip 列表
        """
        if durations:
            self._durations = durations

        if not self._videos:
            self.discover_videos()

        clips: List[VideoClip] = []
        total_duration = 0.0
        attempts = 0
        max_attempts = len(self._videos) * 100

        while total_duration < target_duration and attempts < max_attempts:
            attempts += 1

            # 选择可用的视频（排除上一次选中的）
            available = [v for v in self._videos if v != self._last_video]
            if not available:
                break

            video_path = random.choice(available)
            self._last_video = video_path

            # 获取时长
            duration = self._durations.get(video_path, 0.0)

            # 时长为 0 或未找到，默认按 >= 2 秒处理
            if duration <= 0:
                duration = self.MAX_CLIP_DURATION + random.uniform(0, 5)

            # 计算截取参数
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
                trim_duration=round(trim_duration, 2),
                original_duration=round(duration, 2)
            )
            clips.append(clip)
            total_duration += trim_duration

        return clips

    def generate_plan(
        self,
        target_duration: float,
        durations: Optional[Dict[str, float]] = None
    ) -> List[dict]:
        """生成剪辑计划（字典格式）"""
        clips = self.sample_clips(target_duration, durations)
        return [clip.to_dict() for clip in clips]

    def save_plan(self, plan: List[dict], output_path: str):
        """保存剪辑计划到 JSON 文件"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)


# === 批量生成支持 ===
class BatchVideoSampler:
    """批量生成多个剪辑计划"""

    def __init__(self, video_dir: str, seed: Optional[int] = None):
        self.sampler = VideoSampler(video_dir, seed, use_ffprobe=False)
        self.sampler.discover_videos()

    def generate_multiple_plans(
        self,
        targets: List[float],
        durations: Dict[str, float]
    ) -> List[List[dict]]:
        """生成多个不同的剪辑计划"""
        plans = []
        for target in targets:
            # 每次重置随机状态以获得不同结果
            plan = self.sampler.generate_plan(target, durations)
            plans.append(plan)
        return plans

    def generate_with_exclusions(
        self,
        targets: List[float],
        durations: Dict[str, float],
        exclude_videos: List[str]
    ) -> List[List[dict]]:
        """生成时排除指定视频"""
        original_videos = self.sampler._videos.copy()
        self.sampler._videos = [v for v in original_videos if v not in exclude_videos]

        plans = self.generate_multiple_plans(targets, durations)

        self.sampler._videos = original_videos
        return plans


# === 命令行入口 ===
def main():
    import argparse

    parser = argparse.ArgumentParser(description='视频随机抽样算法')
    parser.add_argument('video_dir', help='视频素材目录')
    parser.add_argument('-t', '--target', type=float, default=30.0,
                        help='目标总时长（秒），默认 30')
    parser.add_argument('-o', '--output', default='clip_plan.json',
                        help='输出文件路径')
    parser.add_argument('--seed', type=int, help='随机种子')
    parser.add_argument('--ffprobe', action='store_true',
                        help='使用 ffprobe 获取真实时长')
    parser.add_argument('--scan', action='store_true',
                        help='仅扫描视频文件，不生成计划')

    args = parser.parse_args()

    sampler = VideoSampler(args.video_dir, seed=args.seed, use_ffprobe=args.ffprobe)
    videos = sampler.discover_videos()

    print(f"发现 {len(videos)} 个视频文件")

    if args.scan:
        return

    if args.ffprobe:
        sampler.load_durations()
        durations = sampler._durations
    else:
        # 使用模拟时长（实际应通过 ffprobe 获取）
        durations = {v: random.uniform(1.0, 15.0) for v in videos}
        print("注意：使用随机模拟时长，请用 --ffprobe 获取真实时长")

    plan = sampler.generate_plan(args.target, durations)
    sampler.save_plan(plan, args.output)

    print(f"\n剪辑计划已保存到: {args.output}")
    print(f"目标时长: {args.target}s | 实际时长: {sum(p['trim_duration'] for p in plan):.1f}s")
    print(f"片段数量: {len(plan)}")


if __name__ == "__main__":
    main()

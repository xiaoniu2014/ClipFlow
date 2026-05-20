"""
VideoOnlyExporter - 纯视频导出模式

只处理视频轨道，所有音频相关处理全部禁用：
- 无 BGM
- 无原视频音频
- 无混音
- 无 atempo
- 无音频同步
- 所有速度变化仅作用于视频 (setpts)
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class VideoClip:
    """单个视频剪辑片段"""
    file: str
    trim_start: float
    trim_duration: float

    @property
    def trim_end(self) -> float:
        return self.trim_start + self.trim_duration


@dataclass
class VideoSpeed:
    """视频速度因子（仅作用于视频）"""
    factor: float = 1.0


@dataclass
class VideoOnlyExporter:
    """纯视频导出 FFmpeg 命令构建器"""
    clips: list[VideoClip] = field(default_factory=list)
    global_speed: Optional[VideoSpeed] = None
    target_resolution: Optional[tuple[int, int]] = None
    target_fps: Optional[int] = None

    def add_clip(self, clip: VideoClip) -> "VideoOnlyExporter":
        """添加剪辑片段"""
        self.clips.append(clip)
        return self

    def set_global_speed(self, factor: float) -> "VideoOnlyExporter":
        """设置全局速度因子"""
        self.global_speed = VideoSpeed(factor=factor)
        return self

    def set_resolution(self, width: int, height: int) -> "VideoOnlyExporter":
        """设置目标分辨率"""
        self.target_resolution = (width, height)
        return self

    def set_fps(self, fps: int) -> "VideoOnlyExporter":
        """设置目标帧率"""
        self.target_fps = fps
        return self

    def _build_inputs(self) -> str:
        """生成 -i 参数"""
        return " ".join(f"-i {clip.file}" for clip in self.clips)

    def _build_filter_complex(self) -> str:
        """生成 filter_complex 部分（纯视频）"""
        filters = []
        n = len(self.clips)

        # 1. Trim + setpts for each video clip
        for i, clip in enumerate(self.clips):
            filters.append(f"[{i}:v]trim=start={clip.trim_start}:end={clip.trim_end},setpts=PTS-STARTPTS[v{i}]")

        # 2. Concat video
        v_labels = "".join(f"[v{i}]" for i in range(n))
        filters.append(f"{v_labels}concat=n={n}:v=1:a=0[outv]")

        # 3. Apply global speed (setpts only for video)
        if self.global_speed and self.global_speed.factor != 1.0:
            speed_expr = f"1/{self.global_speed.factor}"
            filters.append(f"[outv]setpts=PTS*{speed_expr}[outv_speeded]")

        # 4. Scale (统一分辨率)
        current_v = "[outv_speeded]" if self.global_speed else "[outv]"

        if self.target_resolution:
            w, h = self.target_resolution
            filters.append(f"{current_v}scale={w}:{h}[outv_scaled]")
            current_v = "[outv_scaled]"

        # 5. FPS (统一帧率)
        if self.target_fps:
            filters.append(f"{current_v}fps={self.target_fps}[outv_final]")
            current_v = "[outv_final]"

        return "; ".join(filters)

    def _get_final_video_label(self) -> str:
        """获取最终输出的视频标签"""
        v_label = "[outv]"

        if self.global_speed:
            v_label = "[outv_speeded]"

        if self.target_resolution:
            v_label = "[outv_scaled]"

        if self.target_fps:
            v_label = "[outv_final]"

        return v_label

    def build(self) -> str:
        """构建完整的 ffmpeg 命令（纯视频，无音频）"""
        if not self.clips:
            raise ValueError("No clips added")

        inputs = self._build_inputs()
        filter_complex = self._build_filter_complex()
        v_label = self._get_final_video_label()

        # -an: 禁用音频
        maps = f"-map {v_label} -an"

        return f"ffmpeg -y -hide_banner {inputs} -filter_complex '{filter_complex}' {maps} output.mp4"


def build_video_only_command(
    clips: list[dict],
    global_speed: float = 1.0,
    resolution: Optional[tuple[int, int]] = None,
    fps: Optional[int] = None,
) -> str:
    """
    从 clips 数据构建纯视频 ffmpeg 命令

    Args:
        clips: [{"file": "a.mp4", "trim_start": 0.3, "trim_duration": 2.0}, ...]
        global_speed: 全局速度因子
        resolution: 目标分辨率 (width, height)
        fps: 目标帧率

    Returns:
        ffmpeg 命令字符串（无音频）
    """
    exporter = VideoOnlyExporter()

    for c in clips:
        exporter.add_clip(VideoClip(
            file=c["file"],
            trim_start=c["trim_start"],
            trim_duration=c["trim_duration"],
        ))

    if global_speed != 1.0:
        exporter.set_global_speed(global_speed)

    if resolution:
        exporter.set_resolution(*resolution)

    if fps:
        exporter.set_fps(fps)

    return exporter.build()


if __name__ == "__main__":
    # 示例
    clips = [
        {"file": "a.mp4", "trim_start": 0.3, "trim_duration": 2.0},
        {"file": "b.mp4", "trim_start": 1.1, "trim_duration": 1.7},
    ]

    cmd = build_video_only_command(
        clips=clips,
        global_speed=1.03,
        resolution=(1080, 1920),
        fps=30,
    )
    print(cmd)
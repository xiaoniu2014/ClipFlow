"""
FFmpeg filter_complex builder for ClipFlow.

Generates a single ffmpeg command that performs:
- trim, setpts, concat, speed, scale in one pass
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Clip:
    """单个视频剪辑片段"""
    file: str
    trim_start: float
    trim_duration: float

    @property
    def trim_end(self) -> float:
        return self.trim_start + self.trim_duration


@dataclass
class GlobalSpeed:
    """全局速度因子"""
    factor: float = 1.0


@dataclass
class Transition:
    """转场效果（预留）"""
    type: str  # cut, fade, wipe, etc.
    duration: float = 0.5


@dataclass
class FFmpegBuilder:
    """FFmpeg 命令构建器"""
    clips: list[Clip] = field(default_factory=list)
    global_speed: Optional[GlobalSpeed] = None
    target_resolution: Optional[tuple[int, int]] = None  # (width, height)
    target_fps: Optional[int] = None
    has_audio: bool = True

    # 扩展字段（预留）
    mirror: bool = False
    scale_factor: Optional[float] = None
    transitions: list[Transition] = field(default_factory=list)
    bgm: Optional[str] = None  # BGM 文件路径

    def add_clip(self, clip: Clip) -> "FFmpegBuilder":
        """添加剪辑片段"""
        self.clips.append(clip)
        return self

    def set_global_speed(self, factor: float) -> "FFmpegBuilder":
        """设置全局速度因子"""
        self.global_speed = GlobalSpeed(factor=factor)
        return self

    def set_resolution(self, width: int, height: int) -> "FFmpegBuilder":
        """设置目标分辨率"""
        self.target_resolution = (width, height)
        return self

    def set_fps(self, fps: int) -> "FFmpegBuilder":
        """设置目标帧率"""
        self.target_fps = fps
        return self

    def set_mirror(self, enabled: bool = True) -> "FFmpegBuilder":
        """设置镜像（预留）"""
        self.mirror = enabled
        return self

    def set_bgm(self, file: str) -> "FFmpegBuilder":
        """设置BGM文件（预留）"""
        self.bgm = file
        return self

    def add_transition(self, transition: Transition) -> "FFmpegBuilder":
        """添加转场（预留）"""
        self.transitions.append(transition)
        return self

    def _build_inputs(self) -> str:
        """生成 -i 参数"""
        return " ".join(f"-i {clip.file}" for clip in self.clips)

    def _build_filter_complex(self) -> str:
        """生成 filter_complex 部分"""
        filters = []
        n = len(self.clips)

        # 1. Trim + setpts for each video clip
        for i, clip in enumerate(self.clips):
            filters.append(f"[{i}:v]trim=start={clip.trim_start}:end={clip.trim_end},setpts=PTS-STARTPTS[v{i}]")

        # 2. Trim + asetpts for each audio clip
        if self.has_audio:
            for i, clip in enumerate(self.clips):
                filters.append(f"[{i}:a]atrim=start={clip.trim_start}:end={clip.trim_end},asetpts=PTS-STARTPTS[a{i}]")

        # 3. Concat video
        v_labels = "".join(f"[v{i}]" for i in range(n))
        filters.append(f"{v_labels}concat=n={n}:v=1:a=0[outv]")

        # 4. Concat audio
        if self.has_audio:
            a_labels = "".join(f"[a{i}]" for i in range(n))
            filters.append(f"{a_labels}concat=n={n}:v=0:a=1[outa]")

        # 5. Apply global speed (setpts for video, atempo for audio)
        if self.global_speed and self.global_speed.factor != 1.0:
            speed_expr = f"1/{self.global_speed.factor}"
            filters.append(f"[outv]setpts=PTS*{speed_expr}[outv_speeded]")

            if self.has_audio:
                atempo = self._build_atempo_chain(self.global_speed.factor)
                filters.append(f"[outa]{atempo}[outa_speeded]")

        # 6. Scale (统一分辨率)
        current_v = "[outv_speeded]" if self.global_speed else "[outv]"
        current_a = "[outa_speeded]" if (self.global_speed and self.has_audio) else "[outa]"

        if self.target_resolution:
            w, h = self.target_resolution
            filters.append(f"{current_v}scale={w}:{h}[outv_scaled]")
            current_v = "[outv_scaled]"

            if self.has_audio:
                filters.append(f"{current_a}aresample=48000[outa_scaled]")
                current_a = "[outa_scaled]"

        # 7. FPS (统一帧率)
        if self.target_fps:
            filters.append(f"{current_v}fps={self.target_fps}[outv_final]")
            current_v = "[outv_final]"

            if self.has_audio:
                filters.append(f"{current_a}aresample=48000[outa_final]")
                current_a = "[outa_final]"

        # 8. 镜像（预留）
        if self.mirror:
            filters.append(f"{current_v}hflip[outv_mirrored]")
            current_v = "[outv_mirrored]"

        return "; ".join(filters)

    def _build_atempo_chain(self, speed_factor: float) -> str:
        """生成 atempo 过滤器链（因为 atempo 范围 0.5-2.0）"""
        filters = []
        factor = speed_factor

        while factor > 2.0:
            filters.append("atempo=2.0")
            factor /= 2.0

        while factor < 0.5:
            filters.append("atempo=0.5")
            factor *= 2.0

        if factor != 1.0:
            filters.append(f"atempo={factor:.2f}")

        return ",".join(filters)

    def _get_final_labels(self) -> tuple[str, str]:
        """获取最终输出的 video 和 audio 标签"""
        v_label = "[outv]"
        a_label = "[outa]"

        if self.global_speed:
            v_label = "[outv_speeded]"
            if self.has_audio:
                a_label = "[outa_speeded]"

        if self.target_resolution:
            v_label = "[outv_scaled]"
            if self.has_audio:
                a_label = "[outa_scaled]"

        if self.target_fps:
            v_label = "[outv_final]"
            if self.has_audio:
                a_label = "[outa_final]"

        if self.mirror:
            v_label = "[outv_mirrored]"

        return v_label, a_label

    def build(self) -> str:
        """构建完整的 ffmpeg 命令"""
        if not self.clips:
            raise ValueError("No clips added")

        inputs = self._build_inputs()
        filter_complex = self._build_filter_complex()
        v_label, a_label = self._get_final_labels()

        maps = f"-map {v_label}"
        if self.has_audio:
            maps += f" -map {a_label}"

        return f"ffmpeg -y -hide_banner {inputs} -filter_complex '{filter_complex}' {maps} output.mp4"


def build_ffmpeg_command(
    clips: list[dict],
    global_speed: float = 1.0,
    resolution: Optional[tuple[int, int]] = None,
    fps: Optional[int] = None,
    has_audio: bool = True,
) -> str:
    """
    从 clips 数据构建 ffmpeg 命令

    Args:
        clips: [{"file": "a.mp4", "trim_start": 0.3, "trim_duration": 2.0}, ...]
        global_speed: 全局速度因子
        resolution: 目标分辨率 (width, height)
        fps: 目标帧率
        has_audio: 是否有音频

    Returns:
        ffmpeg 命令字符串
    """
    builder = FFmpegBuilder(has_audio=has_audio)

    for c in clips:
        builder.add_clip(Clip(
            file=c["file"],
            trim_start=c["trim_start"],
            trim_duration=c["trim_duration"],
        ))

    if global_speed != 1.0:
        builder.set_global_speed(global_speed)

    if resolution:
        builder.set_resolution(*resolution)

    if fps:
        builder.set_fps(fps)

    return builder.build()


if __name__ == "__main__":
    # 示例
    clips = [
        {"file": "a.mp4", "trim_start": 0.3, "trim_duration": 2.0},
        {"file": "b.mp4", "trim_start": 1.1, "trim_duration": 1.7},
    ]

    cmd = build_ffmpeg_command(
        clips=clips,
        global_speed=1.03,
        resolution=(1080, 1920),
        fps=30,
    )
    print(cmd)
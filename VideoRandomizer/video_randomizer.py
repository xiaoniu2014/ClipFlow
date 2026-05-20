"""
Advanced Video Randomizer for ClipFlow.

Provides subtle randomization effects via ffmpeg filters:
- Random mirror (hflip)
- Random slight zoom (1.00 ~ 1.08)
- Random slight position offset (crop)
- Random slight speed change (0.97 ~ 1.03)
- Random brightness change
- Random contrast change
"""

import random
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RandomRange:
    """可配置的随机范围"""
    min_val: float
    max_val: float

    def get_random_value(self) -> float:
        return random.uniform(self.min_val, self.max_val)


@dataclass
class RandomizationConfig:
    """随机化配置（所有变化都是轻微的）"""
    enable_mirror: bool = True
    mirror_probability: float = 0.5  # 镜像概率

    # 缩放范围 1.00 ~ 1.08 (轻微缩放)
    scale_range: RandomRange = field(
        default_factory=lambda: RandomRange(1.00, 1.08)
    )

    # 裁剪偏移范围 (轻微移动)
    crop_offset_range: RandomRange = field(
        default_factory=lambda: RandomRange(0.0, 0.05)  # 0% ~ 5% 的偏移
    )

    # 速度范围 0.97 ~ 1.03 (轻微速度变化)
    speed_range: RandomRange = field(
        default_factory=lambda: RandomRange(0.97, 1.03)
    )

    # 亮度范围 (轻微变化)
    brightness_range: RandomRange = field(
        default_factory=lambda: RandomRange(-0.1, 0.1)
    )

    # 对比度范围 (轻微变化)
    contrast_range: RandomRange = field(
        default_factory=lambda: RandomRange(0.9, 1.1)
    )

    # 饱和度范围 (轻微变化)
    saturation_range: RandomRange = field(
        default_factory=lambda: RandomRange(0.9, 1.1)
    )


@dataclass
class RandomizationResult:
    """随机化结果"""
    mirror: bool
    scale_factor: float
    crop_x_offset: float
    crop_y_offset: float
    speed_factor: float
    brightness: float
    contrast: float
    saturation: float
    filter_complex: str
    input_label: str


class VideoRandomizer:
    """视频随机化处理器"""

    def __init__(self, config: Optional[RandomizationConfig] = None):
        self.config = config or RandomizationConfig()

    def generate_randomization(self, input_label: str = "[0:v]") -> RandomizationResult:
        """
        生成随机化参数和 filter_complex

        Args:
            input_label: 输入视频的标签，如 "[0:v]"

        Returns:
            RandomizationResult: 包含所有随机参数和生成的 filter_complex
        """
        # 生成随机值
        mirror = self._should_apply_mirror()
        scale_factor = self.config.scale_range.get_random_value()
        crop_x_offset = self.config.crop_offset_range.get_random_value()
        crop_y_offset = self.config.crop_offset_range.get_random_value()
        speed_factor = self.config.speed_range.get_random_value()
        brightness = self.config.brightness_range.get_random_value()
        contrast = self.config.contrast_range.get_random_value()
        saturation = self.config.saturation_range.get_random_value()

        # 构建 filter_complex
        filter_complex = self._build_filter_complex(
            input_label=input_label,
            mirror=mirror,
            scale_factor=scale_factor,
            crop_x_offset=crop_x_offset,
            crop_y_offset=crop_y_offset,
            speed_factor=speed_factor,
            brightness=brightness,
            contrast=contrast,
            saturation=saturation,
        )

        return RandomizationResult(
            mirror=mirror,
            scale_factor=scale_factor,
            crop_x_offset=crop_x_offset,
            crop_y_offset=crop_y_offset,
            speed_factor=speed_factor,
            brightness=brightness,
            contrast=contrast,
            saturation=saturation,
            filter_complex=filter_complex,
            input_label=input_label,
        )

    def _should_apply_mirror(self) -> bool:
        """根据概率决定是否应用镜像"""
        if not self.config.enable_mirror:
            return False
        return random.random() < self.config.mirror_probability

    def _build_filter_complex(
        self,
        input_label: str,
        mirror: bool,
        scale_factor: float,
        crop_x_offset: float,
        crop_y_offset: float,
        speed_factor: float,
        brightness: float,
        contrast: float,
        saturation: float,
    ) -> str:
        """构建完整的 filter_complex 链"""
        filters = []
        current_label = input_label

        # 1. Scale up (zoom in slightly, then crop to original size)
        # 如果 scale_factor > 1.0，先放大再裁剪
        if scale_factor > 1.0:
            # 计算放大后的尺寸
            scaled_label = "[v_scaled]"
            filters.append(
                f"{current_label}scale=iw*{scale_factor}:ih*{scale_factor}{scaled_label}"
            )
            current_label = scaled_label

        # 2. Crop with offset (slight position adjustment)
        if scale_factor > 1.0 or crop_x_offset != 0 or crop_y_offset != 0:
            # 使用电影术语：x 和 y 偏移基于中心点的偏移量
            # crop=width:height:x:y 其中 x,y 是左上角坐标
            # 为了实现轻微移动效果，使用表达式基于输入尺寸计算
            crop_label = "[v_cropped]"

            if scale_factor > 1.0:
                # 从放大后的画面中裁剪出原始尺寸，实现"放大后裁剪"效果
                # x 和 y 使用随机偏移，将中心点轻微移动
                # in_w 和 in_h 是当前输入的尺寸
                x_expr = f"(in_w-{int(1000)})/2+in_w*{crop_x_offset}"
                y_expr = f"(in_h-{int(1000)})/2+in_h*{crop_y_offset}"

                # 更精确的表达式：基于实际放大后的尺寸
                w_expr = "iw/{0}".format(scale_factor)
                h_expr = "ih/{0}".format(scale_factor)
                x_expr = f"(iw-{w_expr})/2+iw*{crop_x_offset}"
                y_expr = f"(ih-{h_expr})/2+ih*{crop_y_offset}"

                filters.append(
                    f"{current_label}crop={w_expr}:{h_expr}:{x_expr}:{y_expr}{crop_label}"
                )
            else:
                # 没有缩放时，也可以轻微裁剪移动（实际上是用 eq 或 crop 实现）
                # 这里用轻微的裁剪移动效果
                w_expr = "iw"
                h_expr = "ih"
                x_expr = f"iw*{crop_x_offset}"
                y_expr = f"ih*{crop_y_offset}"
                filters.append(
                    f"{current_label}crop={w_expr}:{h_expr}:{x_expr}:{y_expr}{crop_label}"
                )

            current_label = crop_label

        # 3. Mirror (hflip)
        if mirror:
            mirror_label = "[v_mirrored]"
            filters.append(f"{current_label}hflip{mirror_label}")
            current_label = mirror_label

        # 5. Speed adjustment (setpts)
        if abs(speed_factor - 1.0) > 0.001:
            speed_label = "[v_speed]"
            speed_expr = f"1/{speed_factor}"
            filters.append(f"{current_label}setpts=PTS*{speed_expr}{speed_label}")
            current_label = speed_label

        # 6. Brightness, Contrast, Saturation (eq filter)
        has_color_adjust = (
            abs(brightness) > 0.01
            or abs(contrast - 1.0) > 0.01
            or abs(saturation - 1.0) > 0.01
        )

        if has_color_adjust:
            eq_label = "[v_color]"
            eq_params = []
            if abs(brightness) > 0.01:
                eq_params.append(f"brightness={brightness:.4f}")
            if abs(contrast - 1.0) > 0.01:
                eq_params.append(f"contrast={contrast:.4f}")
            if abs(saturation - 1.0) > 0.01:
                eq_params.append(f"saturation={saturation:.4f}")

            filters.append(f"{current_label}eq={','.join(eq_params)}{eq_label}")
            current_label = eq_label

        # 7. Final output (null passthrough)
        if current_label == input_label:
            filters.append(f"{current_label}null[out]")

        return "; ".join(filters) if filters else f"{input_label}null[out]"


class RandomizedFFmpegBuilder:
    """
    集成随机化功能的 FFmpegBuilder 扩展
    在现有 FFmpegBuilder 的基础上添加随机化效果
    """

    def __init__(self, base_builder, randomizer: Optional[VideoRandomizer] = None):
        """
        Args:
            base_builder: FFmpegBuilder 实例
            randomizer: VideoRandomizer 实例
        """
        self.base_builder = base_builder
        self.randomizer = randomizer or VideoRandomizer()

    def build_with_randomization(self) -> tuple[str, RandomizationResult]:
        """
        构建带有随机化效果的 ffmpeg 命令

        Returns:
            (command, randomization_result): ffmpeg 命令和随机化参数
        """
        rand_result = self.randomizer.generate_randomization()

        # 获取基础 builder 的 filter_complex
        base_filter = self.base_builder._build_filter_complex()

        # 将随机化 filter 插入到基础 filter 之前
        # 随机化通常应用于最终输出之前
        final_filter = f"{rand_result.filter_complex}; {base_filter}"

        # 构建完整命令
        inputs = self.base_builder._build_inputs()
        maps = "-map [outv]"
        if self.base_builder.has_audio:
            maps += " -map [outa]"

        command = f"ffmpeg -y -hide_banner {inputs} -filter_complex '{final_filter}' {maps} output.mp4"

        return command, rand_result


def generate_randomized_filter_complex(
    input_label: str = "[0:v]",
    mirror: Optional[bool] = None,
    scale_range: tuple[float, float] = (1.00, 1.08),
    crop_offset_range: tuple[float, float] = (0.0, 0.05),
    speed_range: tuple[float, float] = (0.97, 1.03),
    brightness_range: tuple[float, float] = (-0.1, 0.1),
    contrast_range: tuple[float, float] = (0.9, 1.1),
    saturation_range: tuple[float, float] = (0.9, 1.1),
) -> str:
    """
    快速生成随机化的 filter_complex（便捷函数）

    Args:
        input_label: 输入视频标签
        mirror: 是否镜像 (None=随机)
        scale_range: 缩放范围
        crop_offset_range: 裁剪偏移范围
        speed_range: 速度变化范围
        brightness_range: 亮度变化范围
        contrast_range: 对比度变化范围
        saturation_range: 饱和度变化范围

    Returns:
        filter_complex 字符串
    """
    config = RandomizationConfig(
        enable_mirror=mirror is not None,
        mirror_probability=1.0 if mirror else 0.5,
    )
    config.scale_range = RandomRange(*scale_range)
    config.crop_offset_range = RandomRange(*crop_offset_range)
    config.speed_range = RandomRange(*speed_range)
    config.brightness_range = RandomRange(*brightness_range)
    config.contrast_range = RandomRange(*contrast_range)
    config.saturation_range = RandomRange(*saturation_range)

    randomizer = VideoRandomizer(config)
    result = randomizer.generate_randomization(input_label)
    return result.filter_complex


if __name__ == "__main__":
    # 示例用法
    print("=== VideoRandomizer 示例 ===\n")

    # 1. 基本用法
    randomizer = VideoRandomizer()
    result = randomizer.generate_randomization("[0:v]")
    print(f"随机化参数:")
    print(f"  镜像: {result.mirror}")
    print(f"  缩放: {result.scale_factor:.4f}")
    print(f"  裁剪偏移: x={result.crop_x_offset:.4f}, y={result.crop_y_offset:.4f}")
    print(f"  速度: {result.speed_factor:.4f}")
    print(f"  亮度: {result.brightness:.4f}")
    print(f"  对比度: {result.contrast:.4f}")
    print(f"  饱和度: {result.saturation:.4f}")
    print(f"\nFilter Complex:\n{result.filter_complex}")

    print("\n" + "=" * 50 + "\n")

    # 2. 多次生成看效果
    print("=== 连续3次随机化 ===")
    for i in range(3):
        result = randomizer.generate_randomization("[0:v]")
        print(f"\n第 {i+1} 次:")
        print(f"  镜像={result.mirror}, 缩放={result.scale_factor:.3f}, "
              f"速度={result.speed_factor:.3f}, "
              f"亮度={result.brightness:.3f}, 对比度={result.contrast:.3f}")

    print("\n" + "=" * 50 + "\n")

    # 3. 便捷函数
    print("=== 便捷函数示例 ===")
    fc = generate_randomized_filter_complex(
        input_label="[0:v]",
        scale_range=(1.00, 1.05),
        speed_range=(0.98, 1.02),
    )
    print(f"Filter Complex:\n{fc}")

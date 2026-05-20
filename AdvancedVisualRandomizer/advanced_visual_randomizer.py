"""
Advanced Visual Randomizer for ClipFlow.

Provides subtle visual randomization effects via ffmpeg filters:
- Random mirror (hflip)
- Random slight zoom (1.00 ~ 1.08)
- Random slight position offset (crop)
- Random brightness change
- Random contrast change

All changes are kept subtle to maintain video quality.
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
class VisualRandomizationConfig:
    """视觉随机化配置（所有变化都是轻微的）"""
    enable_mirror: bool = True
    mirror_probability: float = 0.5  # 镜像概率

    # 缩放范围 1.00 ~ 1.08 (轻微缩放)
    scale_range: RandomRange = field(
        default_factory=lambda: RandomRange(1.00, 1.08)
    )

    # 裁剪偏移范围 (轻微移动, 0% ~ 5% 的偏移)
    crop_offset_range: RandomRange = field(
        default_factory=lambda: RandomRange(0.0, 0.05)
    )

    # 亮度范围 (轻微变化)
    brightness_range: RandomRange = field(
        default_factory=lambda: RandomRange(-0.1, 0.1)
    )

    # 对比度范围 (轻微变化)
    contrast_range: RandomRange = field(
        default_factory=lambda: RandomRange(0.9, 1.1)
    )


@dataclass
class VisualRandomizationResult:
    """视觉随机化结果"""
    mirror: bool
    scale_factor: float
    crop_x_offset: float
    crop_y_offset: float
    brightness: float
    contrast: float
    filter_complex: str
    input_label: str


class AdvancedVisualRandomizer:
    """高级视觉随机化处理器"""

    def __init__(self, config: Optional[VisualRandomizationConfig] = None):
        self.config = config or VisualRandomizationConfig()

    def generate_randomization(self, input_label: str = "[0:v]") -> VisualRandomizationResult:
        """
        生成随机化参数和 filter_complex

        Args:
            input_label: 输入视频的标签，如 "[0:v]"

        Returns:
            VisualRandomizationResult: 包含所有随机参数和生成的 filter_complex
        """
        # 生成随机值
        mirror = self._should_apply_mirror()
        scale_factor = self.config.scale_range.get_random_value()
        crop_x_offset = self.config.crop_offset_range.get_random_value()
        crop_y_offset = self.config.crop_offset_range.get_random_value()
        brightness = self.config.brightness_range.get_random_value()
        contrast = self.config.contrast_range.get_random_value()

        # 构建 filter_complex
        filter_complex = self._build_filter_complex(
            input_label=input_label,
            mirror=mirror,
            scale_factor=scale_factor,
            crop_x_offset=crop_x_offset,
            crop_y_offset=crop_y_offset,
            brightness=brightness,
            contrast=contrast,
        )

        return VisualRandomizationResult(
            mirror=mirror,
            scale_factor=scale_factor,
            crop_x_offset=crop_x_offset,
            crop_y_offset=crop_y_offset,
            brightness=brightness,
            contrast=contrast,
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
        brightness: float,
        contrast: float,
    ) -> str:
        """构建完整的 filter_complex 链"""
        filters = []
        current_label = input_label

        # 1. Scale up slightly (zoom in), then crop to original size
        if scale_factor > 1.0:
            scaled_label = "[v_scaled]"
            filters.append(
                f"{current_label}scale=iw*{scale_factor}:ih*{scale_factor}{scaled_label}"
            )
            current_label = scaled_label

        # 2. Crop with slight position offset
        if scale_factor > 1.0 or crop_x_offset != 0 or crop_y_offset != 0:
            crop_label = "[v_cropped]"

            if scale_factor > 1.0:
                # From scaled picture, crop to original size with slight offset
                w_expr = "iw/{0}".format(scale_factor)
                h_expr = "ih/{0}".format(scale_factor)
                x_expr = f"(iw-{w_expr})/2+iw*{crop_x_offset}"
                y_expr = f"(ih-{h_expr})/2+ih*{crop_y_offset}"
            else:
                # No scale, just apply position offset via crop
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

        # 4. Brightness and Contrast (eq filter)
        has_color_adjust = (
            abs(brightness) > 0.01 or abs(contrast - 1.0) > 0.01
        )

        if has_color_adjust:
            eq_label = "[v_color]"
            eq_params = []
            if abs(brightness) > 0.01:
                eq_params.append(f"brightness={brightness:.4f}")
            if abs(contrast - 1.0) > 0.01:
                eq_params.append(f"contrast={contrast:.4f}")

            filters.append(f"{current_label}eq={','.join(eq_params)}{eq_label}")
            current_label = eq_label

        # 5. Final output
        if current_label == input_label:
            filters.append(f"{current_label}null[out]")

        return "; ".join(filters) if filters else f"{input_label}null[out]"


def generate_visual_filter_complex(
    input_label: str = "[0:v]",
    mirror: Optional[bool] = None,
    scale_range: tuple[float, float] = (1.00, 1.08),
    crop_offset_range: tuple[float, float] = (0.0, 0.05),
    brightness_range: tuple[float, float] = (-0.1, 0.1),
    contrast_range: tuple[float, float] = (0.9, 1.1),
) -> str:
    """
    快速生成视觉随机化的 filter_complex（便捷函数）

    Args:
        input_label: 输入视频标签
        mirror: 是否镜像 (None=随机)
        scale_range: 缩放范围
        crop_offset_range: 裁剪偏移范围
        brightness_range: 亮度变化范围
        contrast_range: 对比度变化范围

    Returns:
        filter_complex 字符串
    """
    config = VisualRandomizationConfig(
        enable_mirror=mirror is not None,
        mirror_probability=1.0 if mirror else 0.5,
    )
    config.scale_range = RandomRange(*scale_range)
    config.crop_offset_range = RandomRange(*crop_offset_range)
    config.brightness_range = RandomRange(*brightness_range)
    config.contrast_range = RandomRange(*contrast_range)

    randomizer = AdvancedVisualRandomizer(config)
    result = randomizer.generate_randomization(input_label)
    return result.filter_complex


if __name__ == "__main__":
    print("=== AdvancedVisualRandomizer 示例 ===\n")

    # 1. 基本用法
    randomizer = AdvancedVisualRandomizer()
    result = randomizer.generate_randomization("[0:v]")
    print(f"随机化参数:")
    print(f"  镜像: {result.mirror}")
    print(f"  缩放: {result.scale_factor:.4f}")
    print(f"  裁剪偏移: x={result.crop_x_offset:.4f}, y={result.crop_y_offset:.4f}")
    print(f"  亮度: {result.brightness:.4f}")
    print(f"  对比度: {result.contrast:.4f}")
    print(f"\nFilter Complex:\n{result.filter_complex}")

    print("\n" + "=" * 50 + "\n")

    # 2. 连续生成看效果
    print("=== 连续3次随机化 ===")
    for i in range(3):
        result = randomizer.generate_randomization("[0:v]")
        print(f"\n第 {i+1} 次:")
        print(f"  镜像={result.mirror}, 缩放={result.scale_factor:.3f}, "
              f"亮度={result.brightness:.3f}, 对比度={result.contrast:.3f}")

    print("\n" + "=" * 50 + "\n")

    # 3. 便捷函数
    print("=== 便捷函数示例 ===")
    fc = generate_visual_filter_complex(
        input_label="[0:v]",
        scale_range=(1.00, 1.05),
    )
    print(f"Filter Complex:\n{fc}")

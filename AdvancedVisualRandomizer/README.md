# Advanced Visual Randomizer

通过 ffmpeg filter 实现高级视觉随机化效果，为视频添加自然的视觉变化。

## 特性

- **随机镜像**：水平翻转，50% 概率应用
- **随机轻微缩放**：1.00 ~ 1.08 范围，避免视觉疲劳
- **随机轻微移动**：crop 偏移 0% ~ 5%，模拟手持效果
- **随机亮度变化**：-0.1 ~ 0.1，保持自然观感
- **随机对比度变化**：0.9 ~ 1.1，增强画面层次
- **纯 ffmpeg filter**：无需额外依赖

## 安装

```python
from AdvancedVisualRandomizer import AdvancedVisualRandomizer, generate_visual_filter_complex
```

## 快速开始

### 便捷函数

```python
from AdvancedVisualRandomizer import generate_visual_filter_complex

# 生成随机 filter_complex
fc = generate_visual_filter_complex("[0:v]")
print(fc)
```

### 完整类方式

```python
from AdvancedVisualRandomizer import AdvancedVisualRandomizer, VisualRandomizationConfig

config = VisualRandomizationConfig(
    enable_mirror=True,
    mirror_probability=0.5,
)
config.scale_range = RandomRange(1.00, 1.08)
config.brightness_range = RandomRange(-0.1, 0.1)

randomizer = AdvancedVisualRandomizer(config)
result = randomizer.generate_randomization("[0:v]")

print(f"镜像: {result.mirror}")
print(f"缩放: {result.scale_factor:.4f}")
print(f"亮度: {result.brightness:.4f}")
print(f"对比度: {result.contrast:.4f}")
print(f"Filter: {result.filter_complex}")
```

## 参数说明

### VisualRandomizationConfig

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enable_mirror` | `bool` | `True` | 是否启用镜像 |
| `mirror_probability` | `float` | `0.5` | 镜像概率 |
| `scale_range` | `RandomRange` | `1.00~1.08` | 缩放范围 |
| `crop_offset_range` | `RandomRange` | `0.0~0.05` | 裁剪偏移范围 |
| `brightness_range` | `RandomRange` | `-0.1~0.1` | 亮度变化范围 |
| `contrast_range` | `RandomRange` | `0.9~1.1` | 对比度变化范围 |

### generate_visual_filter_complex

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `input_label` | `str` | `"[0:v]"` | 输入视频标签 |
| `mirror` | `bool\|None` | `None` | 是否镜像（None=随机） |
| `scale_range` | `tuple` | `(1.00, 1.08)` | 缩放范围 |
| `crop_offset_range` | `tuple` | `(0.0, 0.05)` | 裁剪偏移范围 |
| `brightness_range` | `tuple` | `(-0.1, 0.1)` | 亮度变化范围 |
| `contrast_range` | `tuple` | `(0.9, 1.1)` | 对比度变化范围 |

## 输出示例

```
[0:v]scale=iw*1.04:ih*1.04[v_scaled]; [v_scaled]crop=iw/1.04:ih/1.04:(iw-iw/1.04)/2+iw*0.04:(ih-ih/1.04)/2+ih*0.02[v_cropped]; [v_cropped]eq=brightness=-0.08,contrast=1.06[v_color]
```

## Filter 链路说明

```
输入视频
    │
    ├── 1. scale (放大 1.00~1.08 倍)
    │         │
    │         ▼
    ├── 2. crop (从放大画面裁剪回原始尺寸 + 轻微偏移)
    │         │
    │         ▼
    ├── 3. hflip (50% 概率水平镜像)
    │         │
    │         ▼
    ├── 4. eq (亮度/对比度调整)
    │         │
    │         ▼
    └── 输出
```

## 与 FFmpegBuilder 集成

```python
from FFmpegBuilder import FFmpegBuilder, Clip
from AdvancedVisualRandomizer import AdvancedVisualRandomizer

# 构建基础视频处理
builder = FFmpegBuilder()
builder.add_clip(Clip(file="input.mp4", trim_start=0, trim_duration=10))
builder.set_resolution(1080, 1920)

# 生成随机化
randomizer = AdvancedVisualRandomizer()
rand_result = randomizer.generate_randomization()

# 组合 filter
base_filter = builder._build_filter_complex()
final_filter = f"{rand_result.filter_complex}; {base_filter}"

print(f"ffmpeg -y -hide_banner -i input.mp4 -filter_complex '{final_filter}' -map [outv] output.mp4")
```

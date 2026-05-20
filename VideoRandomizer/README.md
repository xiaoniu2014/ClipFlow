# Video Randomizer

视频随机化模块，为自动混剪系统提供高级随机化功能。

## 功能

| 功能 | 范围 | FFmpeg Filter |
|------|------|---------------|
| 随机镜像 | 50% 概率 | `hflip` |
| 随机缩放 | 1.00 ~ 1.08 | `scale` → `crop` 组合 |
| 随机移动 | 0% ~ 5% 偏移 | `crop` 偏移 |
| 随机速度 | 0.97 ~ 1.03 | `setpts=PTS*1/x` |
| 随机亮度 | -0.1 ~ 0.1 | `eq=brightness` |
| 随机对比度 | 0.9 ~ 1.1 | `eq=contrast` |
| 随机饱和度 | 0.9 ~ 1.1 | `eq=saturation` |

所有变化都是轻微的，避免视频看起来不自然。

## 安装

无需额外依赖，直接使用：

```python
from video_randomizer import VideoRandomizer, generate_randomized_filter_complex
```

## 使用方法

### 基本用法

```python
from video_randomizer import VideoRandomizer

randomizer = VideoRandomizer()
result = randomizer.generate_randomization("[0:v]")

print(result.mirror)        # True / False
print(result.scale_factor)  # 1.00 ~ 1.08
print(result.speed_factor)  # 0.97 ~ 1.03
print(result.filter_complex)  # 完整 filter_complex 字符串
```

### 便捷函数

```python
from video_randomizer import generate_randomized_filter_complex

fc = generate_randomized_filter_complex(
    input_label="[0:v]",
    scale_range=(1.00, 1.05),
    speed_range=(0.98, 1.02),
)
```

### 自定义配置

```python
from video_randomizer import VideoRandomizer, RandomizationConfig, RandomRange

config = RandomizationConfig(
    enable_mirror=True,
    mirror_probability=0.5,
    scale_range=RandomRange(1.00, 1.08),
    crop_offset_range=RandomRange(0.0, 0.05),
    speed_range=RandomRange(0.97, 1.03),
    brightness_range=RandomRange(-0.1, 0.1),
    contrast_range=RandomRange(0.9, 1.1),
    saturation_range=RandomRange(0.9, 1.1),
)

randomizer = VideoRandomizer(config)
result = randomizer.generate_randomization("[0:v]")
```

### 集成到 FFmpegBuilder

```python
from video_randomizer import VideoRandomizer, RandomizedFFmpegBuilder
from ffmpeg_builder import FFmpegBuilder, Clip

# 创建基础 builder
builder = FFmpegBuilder()
builder.add_clip(Clip(file="input.mp4", trim_start=0, trim_duration=5))

# 创建随机化 builder
randomized_builder = RandomizedFFmpegBuilder(builder)
command, rand_result = randomized_builder.build_with_randomization()

print(command)
```

## 输出格式

生成的 filter_complex 示例：

```
[0:v]scale=iw*1.04:ih*1.04[v_scaled]; [v_scaled]crop=iw/1.04:ih/1.04:(iw-iw/1.04)/2+iw*0.01:(ih-ih/1.04)/2+ih*0.02[v_cropped]; [v_cropped]setpts=PTS*1/0.98[v_speed]; [v_speed]eq=brightness=-0.01,contrast=1.05,saturation=0.97[v_color]
```

## RandomizationResult 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `mirror` | bool | 是否应用镜像 |
| `scale_factor` | float | 缩放因子 |
| `crop_x_offset` | float | 裁剪 X 偏移量 |
| `crop_y_offset` | float | 裁剪 Y 偏移量 |
| `speed_factor` | float | 速度因子 |
| `brightness` | float | 亮度调整值 |
| `contrast` | float | 对比度调整值 |
| `saturation` | float | 饱和度调整值 |
| `filter_complex` | str | 生成的 FFmpeg filter_complex |
| `input_label` | str | 输入标签 |
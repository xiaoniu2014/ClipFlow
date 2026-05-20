# 全局轻微变速算法 (Speed Factor)

根据实际时长与目标时长的比例，自动计算 `speed_factor`，并对整个区间统一变速。

## 原理

当随机抽样的视频总时长与目标时长不一致时，通过变速来匹配：

```
speed_factor = actual_duration / target_duration
```

- `speed_factor > 1`：加速（时间变短）
- `speed_factor < 1`：减速（时间变长）

## 限制

| 参数 | 值 | 说明 |
|------|-----|------|
| `SPEED_FACTOR_MIN` | 0.92 | 最多慢 8% |
| `SPEED_FACTOR_MAX` | 1.08 | 最多快 8% |

## 函数列表

### `calculate_speed_factor(actual_duration, target_duration)`

基础函数，直接计算并限制 speed_factor。

**参数：**
- `actual_duration`: 实际生成的视频总时长（秒）
- `target_duration`: 目标时长（秒）

**返回：** `speed_factor`（限制在 0.92-1.08 范围内）

**示例：**
```python
from speed_factor import calculate_speed_factor

speed = calculate_speed_factor(5.21, 5.03)
# speed ≈ 1.036
```

### `calculate_speed_factor_with_resample(actual_duration, target_duration)`

计算 speed_factor，并标记是否需要重新抽样。

**返回：** `(speed_factor, needs_resample)` 元组

### `build_segment_with_speed(valid_videos, get_video_duration_fn, target_duration, max_retries=10)`

为一个段落挑选视频片段，如果 speed_factor 超出范围则自动重试。

**参数：**
- `valid_videos`: 有效视频路径列表
- `get_video_duration_fn`: 获取视频时长的函数
- `target_duration`: 目标时长（秒）
- `max_retries`: 最大重试次数（默认 10）

**返回：** `(clips, speed_factor, actual_duration, target_duration)`

### `prepare_segments_with_speed(config, get_valid_videos_fn, get_video_duration_fn, max_retries=10)`

**主函数** - 构建所有段落并计算全局变速因子。

**参数：**
- `config`: 配置对象，包含 `clips` 列表
- `get_valid_videos_fn`: 获取有效视频的函数
- `get_video_duration_fn`: 获取视频时长的函数
- `max_retries`: 每个段落的最大重试次数

**返回：** `(all_clips, speed_factor, actual_duration, target_duration)`

## 与 AutoClipFlow 集成

```python
from utils.video_selector import VideoSelector
from speed_factor import prepare_segments_with_speed

selector = VideoSelector(config)

# 使用全局变速算法准备素材
clips, speed_factor, actual_duration, target_duration = prepare_segments_with_speed(
    config,
    selector.get_valid_videos,
    selector.get_video_duration,
    max_retries=10
)

# 将计算出的 speed_factor 传给 FFmpegBuilder
config['speed']['factor'] = speed_factor
builder = FFmpegBuilder(config, clips)
```

## 算法流程

1. **随机抽样**：从有效视频中随机挑选片段，拼接直到达到目标时长
2. **计算比例**：计算 `speed_factor = actual_duration / target_duration`
3. **检查范围**：如果 speed_factor 不在 [0.92, 1.08] 范围内，重新抽样
4. **重试机制**：最多重试 10 次，记录最接近目标的结果
5. **全局统一**：汇总所有段落，计算统一的 speed_factor
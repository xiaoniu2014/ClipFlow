# 视频随机抽样算法

根据目标时长从素材池中随机抽取视频片段，生成剪辑计划。

## 规则

1. 单个片段最长 2 秒
2. 原视频 > 2 秒：随机截取 2 秒内容
3. 原视频 <= 2 秒：直接使用整个视频
4. 持续抽取直到 total_duration >= target_duration
5. 禁止连续两次抽到同一个视频

## 文件结构

```
video_sampler.py           # 核心模块
video_sampler_extended.py  # 完整实现（含 ffprobe 支持）
```

## 快速开始

### Python API

```python
from video_sampler_extended import VideoSampler

sampler = VideoSampler("/path/to/videos", seed=42)
sampler.discover_videos()

# 获取真实时长
sampler.load_durations()

# 生成剪辑计划
plan = sampler.generate_plan(target_duration=30.0)

# 保存
sampler.save_plan(plan, "plan.json")
```

### 返回格式

```json
[
  {
    "file": "xxx.mp4",
    "trim_start": 0.3,
    "trim_duration": 2.0,
    "original_duration": 3.7
  }
]
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `file` | string | 视频文件的绝对路径 |
| `trim_start` | float | 截取起始位置（秒），从原视频的哪个时间点开始截取 |
| `trim_duration` | float | 截取时长（秒），该片段的实际使用时长，最大为 2.0 |
| `original_duration` | float | 原视频的总时长（秒），未经截取前的时长 |

**计算规则：**
- `trim_start` 范围：`0 ~ (original_duration - trim_duration)`
- `trim_duration`：原视频 > 2 秒时固定为 2.0，原视频 <= 2 秒时等于原视频时长

## 命令行

```bash
# 基础用法
python video_sampler_extended.py /path/to/videos -t 30 -o plan.json

# 使用 ffprobe 获取真实时长
python video_sampler_extended.py /path/to/videos -t 30 --ffprobe

# 指定随机种子
python video_sampler_extended.py /path/to/videos -t 30 --seed 123

# 仅扫描文件
python video_sampler_extended.py /path/to/videos --scan
```

## 命令行参数

| 参数 | 缩写 | 说明 |
|------|------|------|
| `video_dir` | 位置参数 | 视频素材目录路径（必填） |
| `--target` | `-t` | 目标总时长（秒），默认 30 |
| `--output` | `-o` | 输出文件路径，默认 clip_plan.json |
| `--seed` | - | 随机种子，用于复现相同结果 |
| `--ffprobe` | - | 使用 ffprobe 获取视频真实时长（默认使用模拟时长） |
| `--scan` | - | 仅扫描目录中的视频文件，不生成剪辑计划 |

## 批量生成

```python
from video_sampler_extended import BatchVideoSampler

batch = BatchVideoSampler("/path/to/videos", seed=42)
plans = batch.generate_multiple_plans(
    targets=[15.0, 30.0, 60.0],  # 多个目标时长
    durations={...}
)
```

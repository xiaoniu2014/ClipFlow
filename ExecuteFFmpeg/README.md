# FFmpeg Executor

执行 ffmpeg 命令的 Python 模块，支持实时日志输出、GPU 编码、超时处理等功能。

## 功能特性

- 实时打印 ffmpeg 日志
- 错误处理与超时控制
- 自动创建输出目录
- 自动生成唯一文件名 (`output_001.mp4` 递增)
- 自动检测 ffmpeg 是否安装
- 导出参数: h264 / yuv420p / crf 18 / faststart
- 支持 GPU 加速编码 (VideoToolbox / NVENC)

## 安装依赖

```bash
# macOS
brew install ffmpeg

# Ubuntu
sudo apt install ffmpeg

# 检测是否安装成功
ffmpeg -version
```

## 快速开始

```python
from execute_ffmpeg import FFmpegExecutor

# CPU 编码
executor = FFmpegExecutor(output_dir="output", crf=18)
success, path = executor.execute("input.mp4")

# GPU 编码 (macOS VideoToolbox)
executor = FFmpegExecutor(use_gpu=True, gpu_encoder="videotoolbox")
success, path = executor.execute("input.mp4")

# GPU 编码 (NVIDIA NVENC)
executor = FFmpegExecutor(use_gpu=True, gpu_encoder="nvenc")
success, path = executor.execute("input.mp4")

# 自定义参数 + 超时
executor = FFmpegExecutor(
    output_dir="output",
    encoder="libx264",
    crf=20,
    use_gpu=True,
    gpu_encoder="videotoolbox",
    timeout=3600,
)
success, path = executor.execute("input.mp4")
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `output_dir` | str | `"output"` | 输出目录 |
| `encoder` | str | `"libx264"` | CPU 编码器 |
| `crf` | int | `18` | 质量参数 (0-51，越低越好) |
| `use_gpu` | bool | `False` | 是否启用 GPU 编码 |
| `gpu_encoder` | str | `None` | GPU 编码器: `videotoolbox` / `nvenc` |
| `timeout` | int | `None` | 超时秒数 |

## 返回值

- `tuple[bool, Path]`: (是否成功, 输出文件路径)

## GPU 编码器

| 平台 | 编码器 | 说明 |
|------|--------|------|
| macOS | `videotoolbox` | Apple VideoToolbox 硬件加速 |
| NVIDIA | `nvenc` | NVIDIA NVENC 硬件加速 |

## 示例输出

```
Input #0, mov, from 'input.mp4':
  Duration: 00:01:30.50, start: 0.000000, bitrate: 5000 kb/s
Stream mapping:
  Stream #0:0 -> #0:0 (h264_videotoolbox -> h264_videotoolbox)
Output #0, mp4, to 'output/output_001.mp4':
  ...
```

## 错误处理

```python
from execute_ffmpeg import FFmpegExecutor

executor = FFmpegExecutor(timeout=60)

try:
    success, path = executor.execute("input.mp4")
except FileNotFoundError as e:
    print(f"输入文件不存在: {e}")
except RuntimeError as e:
    print(f"ffmpeg 执行失败: {e}")
except TimeoutError as e:
    print(f"执行超时: {e}")
```
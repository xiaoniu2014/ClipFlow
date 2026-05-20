# 视频扫描工具

扫描指定目录下所有 mp4/mov 视频，获取视频时长信息。

## 安装依赖

```bash
pip install ffprobe
```

确保系统已安装 ffprobe：

```bash
# macOS
brew install ffprobe

# Ubuntu/Debian
sudo apt install ffprobe

# Windows
# 从 https://ffmpeg.org 下载安装
```

## 使用方法

```bash
python scan_videos.py /path/to/videos
```

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `directory` | 扫描目录（必填） | - |
| `--no-cache` | 禁用缓存 | 使用缓存 |
| `--min-duration` | 最小视频时长（秒） | 0.3 |
| `--no-recursive` | 不递归扫描子目录 | 递归扫描 |

### 示例

```bash
# 扫描当前目录
python scan_videos.py .

# 扫描指定目录，不使用缓存
python scan_videos.py /path/to/videos --no-cache

# 设置最小视频时长为 1 秒
python scan_videos.py /path/to/videos --min-duration 1

# 不递归扫描子目录
python scan_videos.py /path/to/videos --no-recursive
```

## 输出格式

```json
[
  {
    "path": "/path/to/video.mp4",
    "duration": 2.31
  }
]
```

## Python API

```python
from scan_videos import scan_videos, VideoInfo

# 基本用法
videos = scan_videos("/path/to/videos")

# 自定义参数
videos = scan_videos(
    directory="/path/to/videos",
    recursive=True,           # 是否递归扫描
    min_duration=0.3,         # 最小视频时长（秒）
    cache_file=".cache.json"  # 缓存文件，None 禁用缓存
)

# 遍历结果
for video in videos:
    print(f"{video.path}: {video.duration}s")
```

## 缓存机制

- 首次执行会遍历所有视频并通过 ffprobe 获取时长
- 结果保存到 `.video_scan_cache.json` 文件
- 后续执行直接读取缓存，只有新增或修改的视频才重新获取时长
- 有效提高重复扫描的速度

## 注意事项

- 视频时长小于 0.3 秒的会被自动过滤
- 只扫描 mp4 和 mov 格式的视频
- ffprobe 命令超时时间为 30 秒
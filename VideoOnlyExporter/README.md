# VideoOnlyExporter

纯视频导出模式 FFmpeg 命令构建器。

## 功能特性

- **纯视频输出**：最终视频不包含音频
- **全局 `-an`**：所有 ffmpeg 命令禁用音频输入输出
- **无音频处理**：不处理 BGM、原视频音频、混音、atempo、音频同步
- **视频速度变化**：所有速度调整仅使用 `setpts` 滤镜（无 `atempo`）
- **支持分辨率/帧率调整**：可选统一输出分辨率和帧率

## 使用方法

### 基础用法

```python
from video_only_exporter import VideoOnlyExporter, VideoClip, build_video_only_command

# 方式一：使用构建器
exporter = VideoOnlyExporter()
exporter.add_clip(VideoClip(file="a.mp4", trim_start=0.3, trim_duration=2.0))
exporter.add_clip(VideoClip(file="b.mp4", trim_start=1.1, trim_duration=1.7))
exporter.set_global_speed(1.03)
exporter.set_resolution(1080, 1920)
exporter.set_fps(30)

print(exporter.build())
```

### 使用便捷函数

```python
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
```

## 输出示例

```
ffmpeg -y -hide_banner -i a.mp4 -i b.mp4 -filter_complex '[0:v]trim=start=0.3:end=2.3,setpts=PTS-STARTPTS[v0]; [1:v]trim=start=1.1:end=2.8,setpts=PTS-STARTPTS[v1]; [v0][v1]concat=n=2:v=1:a=0[outv]; [outv]setpts=PTS*1/1.03[outv_speeded]; [outv_speeded]scale=1080:1920[outv_scaled]; [outv_scaled]fps=30[outv_final]' -map [outv_final] -an output.mp4
```

## 滤镜链路

| 步骤 | 滤镜 | 说明 |
|------|------|------|
| 1 | `trim` + `setpts` | 裁剪视频片段 |
| 2 | `concat` | 拼接所有片段 |
| 3 | `setpts` | 全局速度调整 |
| 4 | `scale` | 分辨率统一（可选） |
| 5 | `fps` | 帧率统一（可选） |
| 6 | `-an` | 移除音频流 |
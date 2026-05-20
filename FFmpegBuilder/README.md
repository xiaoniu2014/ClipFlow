# FFmpeg Builder

根据 clips plan 动态生成 ffmpeg filter_complex，一次性完成 trim、setpts、concat、speed、scale。

## 特性

- **零中间导出**：单次 ffmpeg 完成所有处理
- **链式 API**：支持 builder 模式构建命令
- **音频支持**：自动生成 atempo 链条（0.5-2.0 范围自动串联）
- **预留扩展**：镜像、缩放、转场、BGM

## 安装

```python
# 直接导入
from ffmpeg_builder import FFmpegBuilder, build_ffmpeg_command
```

## 快速开始

### 便捷函数

```python
from ffmpeg_builder import build_ffmpeg_command

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
```

### Builder 模式

```python
from ffmpeg_builder import FFmpegBuilder, Clip

builder = (
    FFmpegBuilder()
    .add_clip(Clip(file="a.mp4", trim_start=0.3, trim_duration=2.0))
    .add_clip(Clip(file="b.mp4", trim_start=1.1, trim_duration=1.7))
    .set_global_speed(1.03)
    .set_resolution(1080, 1920)
    .set_fps(30)
)

print(builder.build())
```

## 参数说明

| 参数 | 类型 | 说明 |
|------|------|------|
| `clips` | `list[dict]` | 剪辑片段列表 |
| `global_speed` | `float` | 全局速度因子（1.0 = 正常速度） |
| `resolution` | `tuple[int, int]` | 目标分辨率 (width, height) |
| `fps` | `int` | 目标帧率 |
| `has_audio` | `bool` | 是否有音频，默认 True |

## 输出示例

```bash
ffmpeg -y -hide_banner -i a.mp4 -i b.mp4 -filter_complex '[0:v]trim=start=0.3:end=2.3,setpts=PTS-STARTPTS[v0]; [1:v]trim=start=1.1:end=2.8,setpts=PTS-STARTPTS[v1]; [0:a]atrim=start=0.3:end=2.3,asetpts=PTS-STARTPTS[a0]; [1:a]atrim=start=1.1:end=2.8,asetpts=PTS-STARTPTS[a1]; [v0][v1]concat=n=2:v=1:a=0[outv]; [a0][a1]concat=n=2:v=0:a=1[outa]; [outv]setpts=PTS*1/1.03[outv_speeded]; [outa]atempo=1.03[outa_speeded]; [outv_speeded]scale=1080:1920[outv_scaled]; [outa_speeded]aresample=48000[outa_scaled]; [outv_scaled]fps=30[outv_final]; [outa_scaled]aresample=48000[outa_final]' -map [outv_final] -map [outa_final] output.mp4
```

## 预留扩展

以下接口已预留实现空间：

| 功能 | API |
|------|-----|
| 镜像 | `set_mirror(True)` |
| 缩放 | `scale_factor` |
| 转场 | `add_transition(Transition("fade", 0.5))` |
| BGM | `set_bgm("bgm.mp3")` |
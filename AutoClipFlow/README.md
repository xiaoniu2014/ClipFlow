# AutoClipFlow 自动混剪工具

根据配置文件自动从不同素材目录随机抽取视频片段，拼接成完整视频。

## 项目结构

```
AutoClipFlow/
├── config/
│   └── config.json      # 配置文件
├── utils/
│   ├── __init__.py
│   ├── config_loader.py  # 配置加载与验证
│   ├── video_selector.py # 视频扫描与片段选择
│   ├── ffmpeg_builder.py # FFmpeg 命令构建与执行
│   └── batch_generator.py # 批量生成
├── clips/               # 素材目录（按段落分组）
│   ├── 1/              # 段落1素材
│   ├── 2/              # 段落2素材
│   └── 3/              # 段落3素材
├── output/              # 输出目录
├── logs/                # 日志目录
├── main.py              # 入口文件
├── requirements.txt     # 依赖
└── README.md
```

## 依赖

- Python 3.11+
- ffmpeg & ffprobe（需安装到系统 PATH）

## 安装

```bash
pip install -r requirements.txt
# macOS 安装 ffmpeg
brew install ffmpeg
```

## 配置

编辑 `config/config.json`：

```json
{
  "project": { "name": "AutoClipFlow", "version": "1.0.0" },
  "video": {
    "width": 1080,
    "height": 1920,
    "fps": 30,
    "codec": "h264_videotoolbox",
    "bitrate": "8M"
  },
  "speed": {
    "factor": 1.0,
    "audio_speed": 1.0
  },
  "clips": [
    {
      "source_dir": "clips/1",
      "min_duration": 0,
      "max_duration": 2,
      "start": 0.0,
      "end": 5.03
    },
    {
      "source_dir": "clips/2",
      "min_duration": 0.5,
      "max_duration": 2,
      "start": 5.03,
      "end": 6.12
    },
    {
      "source_dir": "clips/3",
      "min_duration": 0.5,
      "max_duration": 2,
      "start": 6.12,
      "end": 8.0
    }
  ],
  "output": {
    "duration": 8,
    "filename": "output/final.mp4",
    "batch_prefix": "batch_",
    "batch_count": 1
  },
  "filters": {
    "scale": "1080:1920",
    "fps": "30",
    "色彩": "hue=s=1.02",
    "对比度": "eq=contrast=1.05"
  }
}
```

**配置说明：**

| 字段 | 说明 |
|------|------|
| `project.name` | 项目名称 |
| `project.version` | 版本号 |
| `video.width/height` | 输出视频分辨率 |
| `video.fps` | 输出帧率 |
| `video.codec` | 编码器（macOS 硬件加速） |
| `video.bitrate` | 视频比特率 |
| `speed.factor` | 视频变速系数（1.0 为原速） |
| `speed.audio_speed` | 音频变速系数（需与 factor 同步） |
| `clips[].source_dir` | 素材来源目录 |
| `clips[].min_duration` | 素材最短时长（秒） |
| `clips[].max_duration` | 素材最长时长（秒） |
| `clips[].start` | 该片段在最终视频中的开始时间 |
| `clips[].end` | 该片段在最终视频中的结束时间 |
| `output.duration` | 最终视频总时长（秒） |
| `output.filename` | 输出文件路径 |
| `output.batch_prefix` | 批量生成文件名前缀 |
| `output.batch_count` | 批量生成数量 |
| `filters.scale` | 视频缩放滤镜 |
| `filters.fps` | 帧率滤镜 |
| `filters.色彩` | 色彩饱和度滤镜 |
| `filters.对比度` | 对比度滤镜 |

## 运行

```bash
python main.py
```

## 功能

- 随机截取视频片段（按配置的时间区间筛选）
- 统一变速（视频+音频同步变速）
- filter_complex 一次性完成拼接（不导出中间视频）
- 批量生成多个不同版本
- macOS 硬件加速编码（h264_videotoolbox）
- 素材时长自动探针（ffprobe）
# ClipFlow

视频处理工具集，包含视频扫描和自动混剪功能。

## 目录结构

```
ClipFlow/
├── scan_videos.py          # 视频扫描模块
├── AutoClipFlow/           # 自动混剪工具
│   ├── config/             # 配置文件
│   ├── clips/              # 素材目录
│   ├── output/             # 输出目录
│   ├── logs/               # 日志目录
│   ├── utils/              # 工具函数
│   ├── main.py             # 入口文件
│   └── requirements.txt    # 依赖
└── README.md
```

## 模块

### scan_videos.py

扫描指定目录下所有 mp4/mov 视频，获取时长信息。

**功能：**
- 使用 ffprobe 获取视频时长
- 支持递归扫描子目录
- 自动过滤无效视频
- 跳过时长小于 0.3 秒的视频
- 输出 JSON 缓存加速后续执行

**用法：**

```bash
# 基本用法
python scan_videos.py /path/to/videos

# 禁用缓存
python scan_videos.py /path/to/videos --no-cache

# 设置最小视频时长
python scan_videos.py /path/to/videos --min-duration 1.0

# 不递归扫描子目录
python scan_videos.py /path/to/videos --no-recursive
```

**输出示例：**

```json
[
  {
    "path": "/path/to/video.mp4",
    "duration": 5.23
  }
]
```

### AutoClipFlow

根据配置文件自动从不同素材目录随机抽取视频片段，拼接成完整视频。

详细文档参见 [AutoClipFlow/README.md](./AutoClipFlow/README.md)

## 依赖

- Python 3.11+
- ffmpeg & ffprobe

```bash
# 安装依赖
pip install -r AutoClipFlow/requirements.txt
```
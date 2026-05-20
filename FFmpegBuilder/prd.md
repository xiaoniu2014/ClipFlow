请帮我根据 clips plan 动态生成 ffmpeg filter_complex。

目标：

不要中间导出视频。

而是：

一次性 ffmpeg 完成：

- trim
- setpts
- concat
- speed
- scale

输入：

clips:

[
  {
    "file": "a.mp4",
    "trim_start": 0.3,
    "trim_duration": 2.0
  },
  {
    "file": "b.mp4",
    "trim_start": 1.1,
    "trim_duration": 1.7
  }
]

要求：

1. 自动生成 ffmpeg inputs

例如：

-i a.mp4 -i b.mp4

2. 自动生成 trim

例如：

trim=start=0.3:end=2.3

1. 自动生成：

setpts=PTS-STARTPTS

4. 自动 concat

5. 自动应用全局 speed factor

例如：

setpts=PTS/1.03

6. 如果有音频：

自动生成 atempo

7. 自动统一分辨率

例如：

1080x1920

8. 自动统一 fps

例如：

30fps

9. 输出：

完整 ffmpeg command string

10. 不要真正执行 ffmpeg

11. 仅生成 command

12. 代码必须结构清晰

13. 必须支持后续扩展：

- 镜像
- 缩放
- 转场
- BGM

请生成完整 Python 代码。
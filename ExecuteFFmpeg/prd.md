第六阶段：真正执行 ffmpeg


请帮我实现 execute_ffmpeg.py。

目标：

执行生成的 ffmpeg command。

要求：

1. 使用 subprocess

2. 实时打印 ffmpeg 日志

3. 支持错误处理

4. 支持超时处理

5. 自动创建 output 目录

6. 自动生成唯一文件名

例如：

output_001.mp4

7. 自动检测 ffmpeg 是否安装

8. 导出编码参数：

- h264
- yuv420p
- crf 18
- faststart

9. 支持 GPU 编码（可选）

例如：

videotoolbox
nvenc

10. 输出最终导出时间。

请生成完整 Python 代码。
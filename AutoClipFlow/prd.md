第一阶段：初始化项目

请帮我创建一个 Python 自动混剪项目。

技术要求：

- 使用 Python 3.11
- 使用 ffmpeg 和 ffprobe
- 不要使用 moviepy
- 所有视频处理都通过 ffmpeg 完成
- 项目结构清晰
- 适合后续扩展批量生成

请帮我：

1. 设计项目目录结构
2. 生成 requirements.txt
3. 生成 config.json 示例
4. 生成 main.py
5. 生成 utils/
6. 生成 README.md

项目目标：

根据配置文件，自动从不同素材目录随机抽取视频片段，拼接成完整视频。

要求：

- 支持随机截取视频
- 支持统一轻微变速
- 支持 ffmpeg filter_complex
- 支持批量生成
- 不允许中间重复导出视频

请生成完整项目结构。
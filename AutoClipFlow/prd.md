# Claude Code 自动混剪项目 —— 高质量提示词（可直接复制使用）

下面这些提示词，不是“让 Claude 一次性生成整个项目”。

而是：

# 按工程模块拆分

这样 Claude Code 的代码质量会高非常多。

这是非常重要的。

因为：

* 一次生成整个项目 → 很容易混乱
* 分阶段生成 → Claude 会稳定很多
* 更容易调试
* 更容易迭代

推荐顺序：

```text
1. 扫描素材
2. 获取视频时长
3. 随机抽样算法
4. 时长控制
5. 生成 ffmpeg filter_complex
6. 执行导出
7. 批量生成
```

你应该一轮一轮让 Claude Code 写。

不要一步到位。

---

# 第一阶段：初始化项目

# 提示词

```text
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
```

---

# 第二阶段：扫描素材 + 获取视频时长

# 提示词

```text
请帮我编写一个 Python 模块：

scan_videos.py

功能：

扫描指定目录下所有 mp4/mov 视频。

要求：

1. 使用 ffprobe 获取视频时长
2. 返回结构化数据
3. 支持递归扫描
4. 自动过滤无效视频
5. 自动跳过时长小于 0.3 秒的视频
6. 输出 json 缓存
7. 提高后续执行速度

返回结构：

[
  {
    "path": "xxx.mp4",
    "duration": 2.31
  }
]

要求：

- 使用 subprocess 调用 ffprobe
- 不要使用 moviepy
- 要有异常处理
- 要有日志输出
- 要有类型注解
- 代码结构清晰

请生成完整代码。
```

---

# 第三阶段：随机抽样算法（核心）

# 提示词（非常重要）

```text
请帮我实现一个“视频随机抽样算法”。

目标：

根据目标时长，从素材池中随机抽取多个视频片段。

规则：

1. 单个片段最长只能使用 2 秒

2. 如果原视频时长超过 2 秒：

随机截取其中一段 2 秒内容。

例如：

原视频：
3.7 秒

则：

随机 start：
0 ~ 1.7

duration 固定：
2 秒

3. 如果原视频时长小于 2 秒：

直接使用整个视频。

4. 持续随机抽取：

直到：

total_duration >= target_duration

5. 禁止连续两次抽到同一个视频

6. 返回 clips plan

返回结构：

[
  {
    "file": "xxx.mp4",
    "trim_start": 0.3,
    "trim_duration": 2.0,
    "original_duration": 3.7
  }
]

7. 不要在这个阶段做 ffmpeg 导出

8. 仅生成剪辑计划

9. 代码必须模块化

10. 必须支持后续批量生成

请生成完整 Python 实现。
```

---

# 第四阶段：全局轻微变速算法（最关键）

# 提示词

```text
请帮我实现“全局轻微变速算法”。

目标：

不要对单个视频强制变速。

而是：

对整个区间统一做轻微变速。

例如：

目标时长：
5.03 秒

实际随机生成：
5.21 秒

则：

speed_factor = 5.21 / 5.03

然后：

对整个区间统一加速。

要求：

1. 自动计算 speed_factor

2. 自动限制速度变化：

最大：
1.08

最小：
0.92

避免变速太明显。

3. 如果超出太多：

自动重新随机抽样。

4. 提供：

calculate_speed_factor()

函数。

5. 返回：

- 最终 clips
- speed_factor
- actual_duration
- target_duration

6. 代码必须带详细注释。

请生成完整 Python 实现。
```

---

# 第五阶段：生成 ffmpeg filter_complex（核心）

# 提示词（极其重要）

```text
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

3. 自动生成：

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
```

---

# 第六阶段：真正执行 ffmpeg

# 提示词

```text
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
```

---

# 第七阶段：批量生成系统

# 提示词

```text
请帮我实现批量生成系统。

目标：

自动生成多个不同版本的视频。

要求：

1. 支持：

for i in range(100)

2. 每次随机结果不同

3. 自动避免重复组合

4. 自动记录：

- 使用了哪些素材
- 每段时间
- 最终 speed factor

5. 自动输出 metadata json

例如：

output_001.json

6. 支持随机种子

7. 支持失败重试

8. 支持多线程生成

9. 支持进度条

10. 支持日志系统

请生成完整 Python 实现。
```

---

# 第八阶段：高级随机化（推荐）

# 提示词

```text
请帮我为自动混剪系统增加高级随机化功能。

要求：

1. 随机镜像

例如：

hflip

2. 随机轻微缩放

例如：

1.00 ~ 1.08

3. 随机轻微移动

例如：

crop 偏移

4. 随机轻微速度变化

例如：

0.97 ~ 1.03

5. 随机亮度变化

6. 随机对比度变化

7. 禁止变化太夸张

8. 所有变化都通过 ffmpeg filter 实现

9. 输出最终 filter_complex

请生成完整 Python 代码。
```

---

# 第九阶段：纯视频模式（无音频）

# 提示词

```text
请帮我实现“纯视频导出模式”。

要求：

1. 最终视频不需要音频

2. 所有 ffmpeg 命令都使用：

-an

3. 不需要处理：

- BGM
- 原视频音频
- 混音
- atempo
- 音频同步

4. 只处理视频轨道

5. 所有速度变化仅作用于视频：

setpts

6. 输出最终 ffmpeg command

请生成完整 Python 代码。
```

---

# 第十阶段：高级视觉随机化（后期扩展）

# 提示词

```text
请帮我为自动混剪系统增加高级视觉随机化功能。

要求：

1. 随机镜像

例如：

hflip

2. 随机轻微缩放

例如：

1.00 ~ 1.08

3. 随机轻微移动

例如：

crop 偏移

4. 随机亮度变化

5. 随机对比度变化

6. 禁止变化太夸张

7. 所有变化都通过 ffmpeg filter 实现

8. 输出最终 filter_complex

请生成完整 Python 实现。
```

````

---

# 十一、真正重要的一点（很关键）

# 不要一次让 Claude 写整个项目

而是：

# 一轮一轮写

这是 Claude Code 最佳实践。

因为：

Claude：

- 非常擅长模块开发
- 不擅长一次性超大工程

所以：

# 每次只做一个模块

质量会高很多。

---

# 十二、你最推荐的开发顺序（重要）

# 推荐顺序

```text
1. 扫描视频
2. 获取时长
3. 随机抽样
4. speed factor
5. filter_complex
6. ffmpeg 执行
7. 批量生成
8. BGM
9. 字幕
````

不要跳步骤。

---

# 十三、你这个项目真正的核心

真正核心不是 ffmpeg。

而是：

# clips plan

也就是：

```python
[
  {
    "file": "a.mp4",
    "trim_start": 0.3,
    "trim_duration": 2.0
  }
]
```

这是整个系统的大脑。

只要 clips plan 做好了：

后面：

* 转场
* 字幕
* BGM
* 特效

都只是 append filter。

---

# 十四、最终推荐（非常重要）

# 你应该让 Claude：

先输出：

```text
clips plan
```

确认逻辑正确。

再：

```text
生成 ffmpeg command
```

不要一开始就让它直接导出视频。

否则调试会非常痛苦。

---

# 十五、最终你会得到什么

你最后会得到一个：

# 工业级自动混剪流水线

后续还能扩展：

* AI 配音
* AI 字幕
* AI 文案
* AI 镜头节奏
* AI BGM
* 自动发小红书
* 自动发 TikTok

所以：

你现在这个架构方向是对的。

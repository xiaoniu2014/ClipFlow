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

1. 提供：

calculate_speed_factor()

函数。

5. 返回：

- 最终 clips
- speed_factor
- actual_duration
- target_duration

6. 代码必须带详细注释。

请生成完整 Python 实现。
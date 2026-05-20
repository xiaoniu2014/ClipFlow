"""
speed_factor.py - 全局轻微变速算法
根据实际时长与目标时长的比例，自动计算 speed_factor，并对整个区间统一变速

原理：
    当随机抽样的视频总时长 > 目标时长时，需要对整个区间统一加速
    speed_factor = actual_duration / target_duration
    - speed_factor > 1 表示加速（时间变短）
    - speed_factor < 1 表示减速（时间变长）

限制：
    - 最大速度因子: 1.08（最多快 8%）
    - 最小速度因子: 0.92（最多慢 8%）
    - 避免变速过于明显

如果 speed_factor 超出允许范围，会自动重新随机抽样，最多重试 10 次
"""

import random
from typing import List, Dict, Any, Tuple

# 速度因子边界限制，避免变速过于明显
SPEED_FACTOR_MIN = 0.92  # 最多慢 8%
SPEED_FACTOR_MAX = 1.08  # 最多快 8%


def calculate_speed_factor(actual_duration: float, target_duration: float) -> float:
    """
    根据实际时长与目标时长计算速度因子（speed_factor）

    原理：
        当实际生成的视频总时长 > 目标时长时，需要对整个区间统一加速
        speed_factor = actual_duration / target_duration > 1 表示加速
        speed_factor < 1 表示减速

    参数：
        actual_duration: 实际随机生成的视频总时长（秒）
        target_duration: 目标时长（秒）

    返回：
        speed_factor: 速度因子，会自动限制在 [0.92, 1.08] 范围内

    示例：
        target_duration = 5.03
        actual_duration = 5.21
        speed_factor = 5.21 / 5.03 ≈ 1.036
    """
    if target_duration <= 0:
        raise ValueError(f"目标时长必须大于 0，实际为 {target_duration}")

    speed_factor = actual_duration / target_duration

    # 限制速度因子在安全范围内，避免变速过于明显
    if speed_factor < SPEED_FACTOR_MIN:
        speed_factor = SPEED_FACTOR_MIN
    elif speed_factor > SPEED_FACTOR_MAX:
        speed_factor = SPEED_FACTOR_MAX

    return speed_factor


def calculate_speed_factor_with_resample(
    actual_duration: float,
    target_duration: float,
    max_retries: int = 10
) -> Tuple[float, bool]:
    """
    计算速度因子，如果超出范围则标记需要重新抽样

    参数：
        actual_duration: 实际随机生成的视频总时长（秒）
        target_duration: 目标时长（秒）
        max_retries: 最大重试次数（未使用，保留兼容性）

    返回：
        Tuple[speed_factor, needs_resample]
        - speed_factor: 计算出的速度因子（在 0.92-1.08 范围内）
        - needs_resample: True 表示超出范围需要重新抽样
    """
    if target_duration <= 0:
        raise ValueError(f"目标时长必须大于 0，实际为 {target_duration}")

    speed_factor = actual_duration / target_duration

    # 检查是否超出允许范围
    needs_resample = speed_factor < SPEED_FACTOR_MIN or speed_factor > SPEED_FACTOR_MAX

    # 限制速度因子在安全范围内
    if speed_factor < SPEED_FACTOR_MIN:
        speed_factor = SPEED_FACTOR_MIN
    elif speed_factor > SPEED_FACTOR_MAX:
        speed_factor = SPEED_FACTOR_MAX

    return speed_factor, needs_resample


def build_segment_with_speed(
    valid_videos: List[Any],
    get_video_duration_fn,
    target_duration: float,
    max_retries: int = 10
) -> Tuple[List[Dict[str, Any]], float, float, float]:
    """
    为一个段落挑选视频片段，并计算全局变速因子

    核心算法：
        1. 随机抽样视频片段，拼接直到达到目标时长
        2. 计算实际总时长与目标时长的比例作为 speed_factor
        3. 如果 speed_factor 超出 [0.92, 1.08] 范围，重新抽样
        4. 最多重试 max_retries 次

    参数：
        valid_videos: 有效视频路径列表
        get_video_duration_fn: 获取视频时长的函数，接收视频路径参数
        target_duration: 目标时长（秒）
        max_retries: 最大重试次数

    返回：
        Tuple[clips, speed_factor, actual_duration, target_duration]
        - clips: 视频片段列表
        - speed_factor: 速度因子（限制在 0.92-1.08）
        - actual_duration: 实际抽样的总时长
        - target_duration: 目标时长
    """
    if not valid_videos:
        return [], 1.0, 0.0, target_duration

    best_clips = []
    best_speed_factor = 1.0
    best_actual_duration = 0.0
    min_diff = float('inf')

    for retry in range(max_retries):
        clips = []
        accumulated = 0.0

        # 随机抽样直到达到目标时长
        while accumulated < target_duration:
            video = random.choice(valid_videos)
            dur = get_video_duration_fn(video)

            remaining = target_duration - accumulated
            if dur > remaining:
                # 取部分片段
                clips.append({'path': video, 'start': 0, 'duration': remaining})
                accumulated = target_duration
            else:
                clips.append({'path': video, 'start': 0, 'duration': dur})
                accumulated += dur

        # 计算当前抽样的速度因子
        current_speed_factor = accumulated / target_duration if target_duration > 0 else 1.0
        speed_factor, needs_resample = calculate_speed_factor_with_resample(
            accumulated, target_duration
        )

        # 如果 speed_factor 在允许范围内，直接返回
        if not needs_resample:
            return clips, speed_factor, accumulated, target_duration

        # 记录最接近目标的结果（speed_factor 最接近 1.0）
        diff = abs(speed_factor - 1.0)
        if diff < min_diff:
            min_diff = diff
            best_clips = clips
            best_speed_factor = speed_factor
            best_actual_duration = accumulated

    # 如果多次重试都无法得到理想结果，使用最接近的结果
    return best_clips, best_speed_factor, best_actual_duration, target_duration


def prepare_segments_with_speed(
    config: Dict[str, Any],
    get_valid_videos_fn,
    get_video_duration_fn,
    max_retries: int = 10
) -> Tuple[List[Dict[str, Any]], float, float, float]:
    """
    构建所有段落并计算全局变速因子

    流程：
        1. 为每个段落随机抽样视频片段
        2. 汇总所有段落的实际总时长和目标总时长
        3. 计算统一的 speed_factor 应用于整个视频

    参数：
        config: 配置对象，包含 clips 列表
        get_valid_videos_fn: 获取有效视频的函数，接收 (source_dir, min_dur, max_dur) 参数
        get_video_duration_fn: 获取视频时长的函数
        max_retries: 每个段落的最大重试次数

    返回：
        Tuple[all_clips, speed_factor, actual_duration, target_duration]
        - all_clips: 所有视频片段（包含全局时间线位置）
        - speed_factor: 统一的全局速度因子
        - actual_duration: 实际总时长
        - target_duration: 目标总时长
    """
    all_clips = []
    global_start = 0.0
    total_actual_duration = 0.0
    total_target_duration = 0.0

    for clip_config in config['clips']:
        source_dir = clip_config['source_dir']
        min_dur = clip_config.get('min_duration', 3)
        max_dur = clip_config.get('max_duration', 8)
        target_duration = clip_config.get('end', 0) - clip_config.get('start', 0)

        # 获取有效视频列表
        valid_videos = get_valid_videos_fn(source_dir, min_dur, max_dur)

        # 使用带变速计算的片段构建
        segment_clips, _, segment_actual, segment_target = build_segment_with_speed(
            valid_videos,
            get_video_duration_fn,
            target_duration,
            max_retries
        )

        # 计算该段落在全局时间线上的起始位置
        segment_start = global_start

        for clip in segment_clips:
            clip['start'] = segment_start
            clip['end'] = segment_start + clip['duration']
            all_clips.append(clip)
            segment_start += clip['duration']

        # 累加实际时长和目标时长
        total_actual_duration += segment_actual
        total_target_duration += segment_target
        global_start += segment_target  # 使用目标时长推进全局时间

    # 计算全局统一的 speed_factor
    speed_factor, _ = calculate_speed_factor_with_resample(
        total_actual_duration, total_target_duration
    )

    return all_clips, speed_factor, total_actual_duration, total_target_duration
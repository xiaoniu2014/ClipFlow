"""
视频扫描模块 - 扫描指定目录下所有 mp4/mov 视频并获取时长
"""

import json
import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class VideoInfo:
    """视频信息数据结构"""
    path: str
    duration: float


def is_valid_video(file_path: Path) -> bool:
    """检查文件是否为有效的 mp4/mov 视频"""
    suffix = file_path.suffix.lower()
    return suffix in (".mp4", ".mov")


def get_video_duration(file_path: Path) -> Optional[float]:
    """
    使用 ffprobe 获取视频时长

    Args:
        file_path: 视频文件路径

    Returns:
        视频时长（秒），失败返回 None
    """
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(file_path),
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            logger.warning(f"ffprobe 失败: {file_path}, 错误: {result.stderr.strip()}")
            return None

        duration_str = result.stdout.strip()
        duration = float(duration_str)
        return duration

    except subprocess.TimeoutExpired:
        logger.warning(f"ffprobe 超时: {file_path}")
        return None
    except ValueError:
        logger.warning(f"解析时长失败: {file_path}, 输出: {duration_str}")
        return None
    except Exception as e:
        logger.warning(f"获取视频时长异常: {file_path}, 错误: {e}")
        return None


def load_cache(cache_path: Path) -> dict[str, float]:
    """加载 JSON 缓存"""
    if not cache_path.exists():
        return {}

    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {item["path"]: item["duration"] for item in data}
    except (json.JSONDecodeError, KeyError, IOError) as e:
        logger.warning(f"加载缓存失败: {cache_path}, 错误: {e}")
        return {}


def save_cache(cache_path: Path, videos: list[VideoInfo]) -> None:
    """保存 JSON 缓存"""
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        data = [{"path": v.path, "duration": v.duration} for v in videos]
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"缓存已保存: {cache_path}")
    except IOError as e:
        logger.error(f"保存缓存失败: {cache_path}, 错误: {e}")


def scan_videos(
    directory: str | Path,
    recursive: bool = True,
    min_duration: float = 0.3,
    cache_file: str | Path | None = ".video_scan_cache.json",
) -> list[VideoInfo]:
    """
    扫描目录下所有视频文件并获取时长

    Args:
        directory: 扫描目录
        recursive: 是否递归扫描子目录
        min_duration: 最小视频时长（秒），低于此值会被过滤
        cache_file: 缓存文件路径，None 则不使用缓存

    Returns:
        视频信息列表
    """
    directory = Path(directory)
    if not directory.exists():
        logger.error(f"目录不存在: {directory}")
        return []

    cache: dict[str, float] = {}
    cache_path = Path(cache_file) if cache_file else None

    if cache_path:
        cache = load_cache(cache_path)
        logger.info(f"已加载缓存条目: {len(cache)}")

    videos: list[VideoInfo] = []
    new_count = 0
    cached_count = 0

    pattern = "**/*" if recursive else "*"
    for file_path in directory.glob(pattern):
        if not file_path.is_file() or not is_valid_video(file_path):
            continue

        path_str = str(file_path)

        if path_str in cache:
            duration = cache[path_str]
            cached_count += 1
            logger.debug(f"缓存命中: {path_str} -> {duration}s")
        else:
            duration = get_video_duration(file_path)
            if duration is not None:
                cache[path_str] = duration

        if duration is not None and duration >= min_duration:
            videos.append(VideoInfo(path=path_str, duration=duration))
            if path_str not in cache:
                new_count += 1

    logger.info(
        f"扫描完成: 找到 {len(videos)} 个有效视频 "
        f"(缓存命中 {cached_count} 个, 新增 {new_count} 个)"
    )

    if cache_path and (new_count > 0 or not cache_path.exists()):
        save_cache(cache_path, videos)

    return videos


def main() -> None:
    """命令行入口"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    import argparse

    parser = argparse.ArgumentParser(description="扫描视频文件并获取时长")
    parser.add_argument("directory", help="扫描目录")
    parser.add_argument("--no-cache", action="store_true", help="禁用缓存")
    parser.add_argument("--min-duration", type=float, default=0.3, help="最小视频时长(秒)")
    parser.add_argument("--no-recursive", action="store_true", help="不递归扫描子目录")

    args = parser.parse_args()

    videos = scan_videos(
        directory=args.directory,
        recursive=not args.no_recursive,
        min_duration=args.min_duration,
        cache_file=None if args.no_cache else ".video_scan_cache.json",
    )

    print(json.dumps([{"path": v.path, "duration": v.duration} for v in videos], indent=2))


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
BatchGenerator - 批量视频生成系统
支持多线程批量生成多个不同版本视频，自动去重、记录metadata
"""

import hashlib
import json
import logging
import os
import random
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.progress import Progress, TaskID, BarColumn, TextColumn, TimeRemainingColumn
from rich.logging import RichHandler
from rich.table import Table

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from FFmpegBuilder.ffmpeg_builder import FFmpegBuilder, Clip
from ExecuteFFmpeg.execute_ffmpeg import FFmpegExecutor


console = Console()


def setup_logging(log_file: Optional[Path] = None, level: int = logging.INFO) -> logging.Logger:
    """配置日志系统"""
    logger = logging.getLogger("BatchGenerator")
    logger.setLevel(level)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    ch = RichHandler(console=console, rich_tracebacks=True)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger


@dataclass
class VideoSegmentRecord:
    """视频片段记录"""
    file: str
    trim_start: float
    trim_duration: float
    trim_end: float
    file_hash: str = ""


@dataclass
class GenerationMetadata:
    """生成元数据"""
    version_id: str
    seed: int
    timestamp: str
    speed_factor: float
    segments: list
    total_duration: float
    output_filename: str
    combination_hash: str


@dataclass
class GenerationResult:
    """单次生成结果"""
    success: bool
    version_id: str
    output_path: Optional[Path]
    metadata: Optional[GenerationMetadata]
    error: Optional[str] = None
    retry_count: int = 0


class CombinationDeduplicator:
    """组合去重器 - 使用hash记录已生成的组合"""

    def __init__(self, history_file: Optional[Path] = None):
        self.history_file = history_file or Path("output/combination_history.json")
        self.seen_hashes: set[str] = set()
        self._lock = threading.Lock()
        self._load_history()

    def _load_history(self):
        """加载历史记录"""
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.seen_hashes = set(data.get("hashes", []))
            except (json.JSONDecodeError, IOError):
                self.seen_hashes = set()

    def _save_history(self):
        """保存历史记录"""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump({"hashes": list(self.seen_hashes)}, f, indent=2, ensure_ascii=False)

    def compute_hash(self, segments: list, seed: int) -> str:
        """计算组合hash"""
        seg_data = []
        for seg in segments:
            seg_data.append(f"{seg.file}:{seg.trim_start:.3f}:{seg.trim_duration:.3f}")
        content = f"{'|'.join(seg_data)}|{seed}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def is_duplicate(self, combination_hash: str) -> bool:
        """检查是否重复"""
        with self._lock:
            return combination_hash in self.seen_hashes

    def mark_generated(self, combination_hash: str):
        """标记为已生成"""
        with self._lock:
            self.seen_hashes.add(combination_hash)
            self._save_history()


class BatchVideoGenerator:
    """批量视频生成器"""

    def __init__(
        self,
        config: dict,
        output_dir: str = "output/batches",
        metadata_dir: str = "output/metadata",
        max_workers: int = 4,
        seed: Optional[int] = None,
        max_retries: int = 3,
        retry_delay: float = 2.0,
        log_file: Optional[Path] = None,
    ):
        self.config = config
        self.output_dir = Path(output_dir)
        self.metadata_dir = Path(metadata_dir)
        self.max_workers = max_workers
        self.base_seed = seed if seed is not None else int(time.time())
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

        self.logger = setup_logging(log_file)
        self.deduplicator = CombinationDeduplicator()

        self._counter_lock = threading.Lock()
        self._counter = 0
        self._total_generated = 0
        self._total_failed = 0
        self._skipped_duplicates = 0

    def _get_next_counter(self) -> int:
        """线程安全的计数器"""
        with self._counter_lock:
            self._counter += 1
            return self._counter

    def _generate_random_segments(self, rng: random.Random) -> list[Clip]:
        """根据配置生成随机片段"""
        clips_config = self.config.get("clips", [])
        segments = []

        for clip_cfg in clips_config:
            source_dir = Path(clip_cfg["source_dir"])
            min_dur = clip_cfg.get("min_duration", 3)
            max_dur = clip_cfg.get("max_duration", 8)
            target_dur = clip_cfg.get("duration", 5)

            videos = list(source_dir.glob("*.mp4")) + list(source_dir.glob("*.MOV"))
            if not videos:
                continue

            valid_videos = [v for v in videos if min_dur <= self._get_duration(v) <= max_dur]
            if not valid_videos:
                valid_videos = videos

            accumulated = 0.0
            while accumulated < target_dur:
                video = rng.choice(valid_videos)
                dur = self._get_duration(video)

                if accumulated + dur > target_dur:
                    dur = target_dur - accumulated
                    segments.append(Clip(
                        file=str(video),
                        trim_start=0.0,
                        trim_duration=dur
                    ))
                    accumulated = target_dur
                else:
                    start = rng.uniform(0, max(0, self._get_duration(video) - dur))
                    segments.append(Clip(
                        file=str(video),
                        trim_start=start,
                        trim_duration=dur
                    ))
                    accumulated += dur

        return segments

    def _get_duration(self, video_path: Path) -> float:
        """获取视频时长（简单实现，使用ffprobe）"""
        try:
            import subprocess
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "json", str(video_path)],
                capture_output=True, text=True, timeout=10
            )
            data = json.loads(result.stdout)
            return float(data["format"]["duration"])
        except Exception:
            return 5.0

    def _generate_version(
        self,
        version_num: int,
        seed: int,
        progress: Optional[Progress] = None,
        task_id: Optional[TaskID] = None,
    ) -> GenerationResult:
        """生成单个版本"""
        version_id = f"v{version_num:03d}_{uuid.uuid4().hex[:8]}"
        rng = random.Random(seed)

        for attempt in range(self.max_retries + 1):
            try:
                segments = self._generate_random_segments(rng)

                if not segments:
                    return GenerationResult(
                        success=False,
                        version_id=version_id,
                        output_path=None,
                        metadata=None,
                        error="No valid segments generated",
                        retry_count=attempt
                    )

                combo_hash = self.deduplicator.compute_hash(segments, seed)

                if self.deduplicator.is_duplicate(combo_hash):
                    self.logger.debug(f"跳过重复组合: {combo_hash}")
                    return GenerationResult(
                        success=False,
                        version_id=version_id,
                        output_path=None,
                        metadata=None,
                        error=f"Duplicate combination: {combo_hash}",
                        retry_count=attempt
                    )

                speed_factor = self.config.get("speed", {}).get("factor", 1.0)
                if self.config.get("speed", {}).get("random_range"):
                    min_s, max_s = self.config["speed"]["random_range"]
                    speed_factor = rng.uniform(min_s, max_s)

                builder = FFmpegBuilder(segments=segments, has_audio=True)
                if speed_factor != 1.0:
                    builder.set_global_speed(speed_factor)

                target_res = self.config.get("video", {}).get("resolution")
                if target_res:
                    builder.set_resolution(*target_res)

                output_filename = f"output_{version_num:03d}.mp4"
                output_path = self.output_dir / output_filename

                cmd = builder.build().replace("output.mp4", str(output_path))
                self.logger.info(f"执行: {cmd[:100]}...")

                executor = FFmpegExecutor(output_dir=str(self.output_dir))
                success, result_path = executor.execute(
                    input_path=segments[0].file,
                    output_ext="mp4"
                )

                if success:
                    self.deduplicator.mark_generated(combo_hash)

                    total_dur = sum(s.trim_duration for s in segments)
                    metadata = GenerationMetadata(
                        version_id=version_id,
                        seed=seed,
                        timestamp=datetime.now().isoformat(),
                        speed_factor=speed_factor,
                        segments=[asdict(s) for s in segments],
                        total_duration=total_dur,
                        output_filename=output_filename,
                        combination_hash=combo_hash
                    )

                    self._save_metadata(version_num, metadata)

                    if progress and task_id:
                        progress.update(task_id, advance=1)

                    return GenerationResult(
                        success=True,
                        version_id=version_id,
                        output_path=result_path,
                        metadata=metadata,
                        retry_count=attempt
                    )
                else:
                    if attempt < self.max_retries:
                        self.logger.warning(f"生成失败，重试 {attempt + 1}/{self.max_retries}")
                        time.sleep(self.retry_delay)
                        continue

            except Exception as e:
                self.logger.error(f"生成异常: {e}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                    continue
                return GenerationResult(
                    success=False,
                    version_id=version_id,
                    output_path=None,
                    metadata=None,
                    error=str(e),
                    retry_count=attempt
                )

        return GenerationResult(
            success=False,
            version_id=version_id,
            output_path=None,
            metadata=None,
            error="Max retries exceeded",
            retry_count=self.max_retries
        )

    def _save_metadata(self, version_num: int, metadata: GenerationMetadata):
        """保存metadata到JSON"""
        filename = f"output_{version_num:03d}.json"
        filepath = self.metadata_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(asdict(metadata), f, indent=2, ensure_ascii=False)

        self.logger.info(f"Metadata已保存: {filepath}")

    def run(self, count: int, progress_callback=None) -> list[GenerationResult]:
        """运行批量生成"""
        self.logger.info(f"开始批量生成: {count} 个版本")
        self.logger.info(f"工作线程数: {self.max_workers}")
        self.logger.info(f"基础随机种子: {self.base_seed}")

        results = []
        duplicate_results = []

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.completed]{task.completed}"),
            TextColumn("/"),
            TextColumn("[progress.total]{task.total}"),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            main_task = progress.add_task(
                f"[cyan]生成中 ({self.max_workers}线程)...",
                total=count
            )

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {}

                for i in range(count):
                    seed = self.base_seed + i
                    future = executor.submit(
                        self._generate_version,
                        i + 1,
                        seed,
                        progress,
                        main_task
                    )
                    futures[future] = i

                for future in as_completed(futures):
                    result = future.result()
                    results.append(result)

                    if result.success:
                        self._total_generated += 1
                    elif "Duplicate" in (result.error or ""):
                        self._skipped_duplicates += 1
                    else:
                        self._total_failed += 1

                    if progress_callback:
                        progress_callback(result)

        return results

    def print_summary(self, results: list[GenerationResult]):
        """打印生成摘要"""
        table = Table(title="批量生成结果摘要")
        table.add_column("指标", style="cyan")
        table.add_column("数值", style="magenta")

        table.add_row("总任务数", str(len(results)))
        table.add_row("成功", f"[green]{self._total_generated}[/green]")
        table.add_row("失败", f"[red]{self._total_failed}[/red]")
        table.add_row("跳过(重复)", f"[yellow]{self._skipped_duplicates}[/yellow]")

        console.print(table)


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="批量视频生成系统")
    parser.add_argument("-c", "--count", type=int, default=10, help="生成数量")
    parser.add_argument("-w", "--workers", type=int, default=4, help="工作线程数")
    parser.add_argument("-s", "--seed", type=int, default=None, help="随机种子")
    parser.add_argument("-o", "--output", type=str, default="output/batches", help="输出目录")
    parser.add_argument("-m", "--metadata", type=str, default="output/metadata", help="Metadata目录")
    parser.add_argument("--retries", type=int, default=3, help="最大重试次数")
    parser.add_argument("--log", type=str, default=None, help="日志文件")

    args = parser.parse_args()

    config = {
        "clips": [
            {
                "source_dir": "素材/A",
                "min_duration": 2,
                "max_duration": 10,
                "duration": 10
            },
            {
                "source_dir": "素材/B",
                "min_duration": 2,
                "max_duration": 10,
                "duration": 10
            }
        ],
        "speed": {
            "factor": 1.0,
            "random_range": [0.8, 1.2]
        },
        "video": {
            "resolution": [1080, 1920]
        }
    }

    generator = BatchVideoGenerator(
        config=config,
        output_dir=args.output,
        metadata_dir=args.metadata,
        max_workers=args.workers,
        seed=args.seed,
        max_retries=args.retries,
        log_file=Path(args.log) if args.log else None
    )

    console.print(f"\n[bold cyan]批量生成系统启动[/bold cyan]")
    console.print(f"  生成数量: {args.count}")
    console.print(f"  工作线程: {args.workers}")
    console.print(f"  随机种子: {args.seed or generator.base_seed}")
    console.print(f"  输出目录: {args.output}")
    console.print()

    results = generator.run(args.count)
    generator.print_summary(results)

    success_count = sum(1 for r in results if r.success)
    console.print(f"\n[bold {'green' if success_count == args.count else 'yellow'}]完成! 成功: {success_count}/{args.count}[/bold]")


if __name__ == "__main__":
    main()

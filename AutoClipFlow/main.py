#!/usr/bin/env python3
"""
AutoClipFlow - 自动混剪工具
根据配置文件从不同素材目录随机抽取视频片段，拼接成完整视频
"""

import json
import sys
import random
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from utils.config_loader import ConfigLoader
from utils.video_selector import VideoSelector
from utils.ffmpeg_builder import FFmpegBuilder
from utils.batch_generator import BatchGenerator

console = Console()


def print_banner():
    banner = """
    ╔═══════════════════════════════════════╗
    ║         AutoClipFlow v1.0.0          ║
    ║         自动混剪工具                   ║
    ╚═══════════════════════════════════════╝
    """
    console.print(banner, style="cyan bold")


def main():
    print_banner()

    config_path = Path("config/config.json")
    if not config_path.exists():
        console.print(f"[red]错误: 配置文件 {config_path} 不存在[/red]")
        sys.exit(1)

    loader = ConfigLoader(config_path)
    config = loader.load()

    console.print(f"[green]✓[/green] 配置加载成功: {config['project']['name']}")
    console.print(f"  - 视频尺寸: {config['video']['width']}x{config['video']['height']}")
    console.print(f"  - 变速系数: {config['speed']['factor']}")
    console.print(f"  - 片段配置: {len(config['clips'])} 个类别")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("准备素材...", total=None)

        selector = VideoSelector(config)
        segments = selector.prepare_segments()
        progress.update(task, description=f"准备完成，共 {len(segments)} 个片段")

    console.print(f"[green]✓[/green] 素材准备完成")

    console.print("[cyan]开始生成视频...[/cyan]")

    builder = FFmpegBuilder(config, segments)
    output_path = builder.build().execute()

    console.print(f"\n[green bold]✓ 视频生成完成![/green bold]")
    console.print(f"  输出路径: {output_path}")


if __name__ == "__main__":
    main()
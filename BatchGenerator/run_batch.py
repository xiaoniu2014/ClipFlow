#!/usr/bin/env python3
"""
批量生成系统运行器
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from batch_generator import BatchVideoGenerator, console


def load_config(config_path: str = "config.json") -> dict:
    """加载配置文件"""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="批量视频生成")
    parser.add_argument("-c", "--config", type=str, default="config.json", help="配置文件路径")
    parser.add_argument("--count", type=int, default=None, help="覆盖配置中的生成数量")
    parser.add_argument("--workers", type=int, default=None, help="覆盖工作线程数")
    parser.add_argument("--seed", type=int, default=None, help="覆盖随机种子")
    parser.add_argument("--dry-run", action="store_true", help="仅测试配置不生成")

    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except FileNotFoundError as e:
        console.print(f"[red]错误: {e}[/red]")
        console.print("\n使用默认配置示例...")
        config = {
            "clips": [
                {"source_dir": "素材/A", "min_duration": 2, "max_duration": 10, "duration": 10},
                {"source_dir": "素材/B", "min_duration": 3, "max_duration": 8, "duration": 8}
            ],
            "speed": {"factor": 1.0, "random_range": [0.9, 1.1]},
            "video": {"resolution": [1080, 1920]},
            "output": {"batch_dir": "output/batches", "metadata_dir": "output/metadata"},
            "generation": {"count": 10, "workers": 4, "seed": None, "max_retries": 3}
        }

    gen_config = config.get("generation", {})
    output_config = config.get("output", {})

    count = args.count if args.count is not None else gen_config.get("count", 10)
    workers = args.workers if args.workers is not None else gen_config.get("workers", 4)
    seed = args.seed if args.seed is not None else gen_config.get("seed")
    max_retries = gen_config.get("max_retries", 3)

    console.print("\n[bold cyan]╔═══════════════════════════════════════╗[/bold cyan]")
    console.print("[bold cyan]║      BatchGenerator 批量生成系统       ║[/bold cyan]")
    console.print("[bold cyan]╚═══════════════════════════════════════╝[/bold cyan]\n")

    console.print(f"[green]✓[/green] 配置加载成功")
    console.print(f"  - 生成数量: [cyan]{count}[/cyan]")
    console.print(f"  - 工作线程: [cyan]{workers}[/cyan]")
    console.print(f"  - 随机种子: [cyan]{seed or '自动'}[/cyan]")
    console.print(f"  - 最大重试: [cyan]{max_retries}[/cyan]")
    console.print(f"  - 输出目录: [cyan]{output_config.get('batch_dir', 'output/batches')}[/cyan]")

    if args.dry_run:
        console.print("\n[yellow]Dry-run 模式，仅测试配置[/yellow]")
        console.print(f"\n[green]配置测试通过![/green]")
        return

    generator = BatchVideoGenerator(
        config=config,
        output_dir=output_config.get("batch_dir", "output/batches"),
        metadata_dir=output_config.get("metadata_dir", "output/metadata"),
        max_workers=workers,
        seed=seed,
        max_retries=max_retries,
        log_file=Path(output_config.get("log_file")) if output_config.get("log_file") else None
    )

    results = generator.run(count)
    generator.print_summary(results)

    success_count = sum(1 for r in results if r.success)
    if success_count == count:
        console.print(f"\n[bold green]✓ 全部 {count} 个视频生成成功![/bold green]")
    else:
        console.print(f"\n[bold yellow]⚠ 生成完成，部分失败: {success_count}/{count}[/bold yellow]")


if __name__ == "__main__":
    main()

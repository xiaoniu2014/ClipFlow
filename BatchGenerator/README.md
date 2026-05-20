# BatchGenerator - 批量视频生成系统

批量生成多个不同版本的视频，自动去重、记录 metadata、支持多线程和失败重试。

## 功能特性

| 特性 | 说明 |
|------|------|
| 批量生成 | 支持 `for i in range(100)` 批量生成任意数量视频 |
| 随机多样性 | 每次生成结果不同，支持随机种子 |
| 自动去重 | SHA256 hash 记录已生成组合，避免重复 |
| Metadata 记录 | 自动输出 JSON，记录素材、时间、speed factor |
| 失败重试 | 可配置重试次数和间隔 |
| 多线程生成 | ThreadPoolExecutor 并行处理 |
| 进度条 | Rich 库实时进度显示 |
| 日志系统 | 文件日志 + 控制台输出 |

## 安装依赖

```bash
pip install rich
```

需要已安装 `ffmpeg` 和 `ffprobe`。

## 快速开始

```bash
# 使用配置文件生成
python run_batch.py --config config.json --count 100 --workers 4

# 命令行参数覆盖
python run_batch.py --count 50 --workers 8 --seed 42

# 测试模式（不实际生成）
python run_batch.py --dry-run
```

## 配置文件

参考 `config_example.json`:

```json
{
  "clips": [
    {
      "source_dir": "素材/A",
      "min_duration": 2,
      "max_duration": 10,
      "duration": 10
    },
    {
      "source_dir": "素材/B",
      "min_duration": 3,
      "max_duration": 8,
      "duration": 8
    }
  ],
  "speed": {
    "factor": 1.0,
    "random_range": [0.9, 1.1]
  },
  "video": {
    "resolution": [1080, 1920],
    "fps": 30
  },
  "output": {
    "batch_dir": "output/batches",
    "metadata_dir": "output/metadata",
    "log_file": "output/batch_generator.log"
  },
  "generation": {
    "count": 100,
    "workers": 4,
    "seed": null,
    "max_retries": 3,
    "retry_delay": 2.0
  }
}
```

### 配置项说明

| 字段 | 说明 |
|------|------|
| `clips[].source_dir` | 素材目录路径 |
| `clips[].min_duration` | 最小视频时长（秒） |
| `clips[].max_duration` | 最大视频时长（秒） |
| `clips[].duration` | 该类别目标总时长（秒） |
| `speed.factor` | 固定 speed factor |
| `speed.random_range` | speed factor 随机范围 `[min, max]` |
| `video.resolution` | 输出分辨率 `[width, height]` |
| `generation.count` | 生成数量 |
| `generation.workers` | 工作线程数 |
| `generation.seed` | 随机种子，`null` 表示自动 |
| `generation.max_retries` | 最大重试次数 |

## 输出文件

### 视频文件

```
output/batches/output_001.mp4
output/batches/output_002.mp4
...
```

### Metadata JSON

```json
{
  "version_id": "v001_a1b2c3d4",
  "seed": 12345,
  "timestamp": "2026-05-20T10:30:00.000000",
  "speed_factor": 1.05,
  "segments": [
    {
      "file": "素材/A/video1.mp4",
      "trim_start": 0.5,
      "trim_duration": 3.2,
      "trim_end": 3.7
    }
  ],
  "total_duration": 18.5,
  "output_filename": "output_001.mp4",
  "combination_hash": "a1b2c3d4e5f6"
}
```

### 组合去重历史

```
output/combination_history.json
```

## Python API

```python
from batch_generator import BatchVideoGenerator

config = {
    "clips": [
        {"source_dir": "素材/A", "min_duration": 2, "max_duration": 10, "duration": 10},
        {"source_dir": "素材/B", "min_duration": 3, "max_duration": 8, "duration": 8}
    ],
    "speed": {"factor": 1.0, "random_range": [0.9, 1.1]},
    "video": {"resolution": [1080, 1920]},
}

generator = BatchVideoGenerator(
    config=config,
    output_dir="output/batches",
    metadata_dir="output/metadata",
    max_workers=4,
    seed=42,
    max_retries=3
)

results = generator.run(count=100)

# 打印摘要
generator.print_summary(results)

# 检查结果
for r in results:
    if r.success:
        print(f"生成成功: {r.output_path}")
    else:
        print(f"生成失败: {r.error}")
```

## 命令行参数

| 参数 | 说明 |
|------|------|
| `-c, --config` | 配置文件路径 |
| `--count` | 生成数量（覆盖配置） |
| `--workers` | 工作线程数（覆盖配置） |
| `--seed` | 随机种子（覆盖配置） |
| `--dry-run` | 测试模式，不实际生成 |

## 目录结构

```
.
├── batch_generator.py    # 核心模块
├── run_batch.py         # 运行入口
├── config_example.json  # 配置示例
├── __init__.py
├── prd.md              # 需求文档
└── README.md
```

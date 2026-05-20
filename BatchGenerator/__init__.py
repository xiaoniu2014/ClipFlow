"""
BatchGenerator - 批量视频生成系统

Usage:
    python run_batch.py --config config.json --count 100 --workers 4
"""

from .batch_generator import BatchVideoGenerator, GenerationResult, GenerationMetadata, CombinationDeduplicator

__all__ = [
    "BatchVideoGenerator",
    "GenerationResult",
    "GenerationMetadata",
    "CombinationDeduplicator",
]

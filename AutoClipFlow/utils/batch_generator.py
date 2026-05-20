"""
batch_generator.py - 批量生成器
支持生成多个视频批次
"""

import random
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from .video_selector import VideoSelector
from .ffmpeg_builder import FFmpegBuilder


class BatchGenerator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.selector = VideoSelector(config)

    def generate_batch(self, batch_id: int) -> Path:
        segments = self.selector.prepare_segments()
        builder = FFmpegBuilder(self.config, segments)

        output_path = self._get_batch_output_path(batch_id)
        builder.output_path = output_path

        return builder.build().execute()

    def _get_batch_output_path(self, batch_id: int) -> Path:
        prefix = self.config['output'].get('batch_prefix', 'batch_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{prefix}{batch_id}_{timestamp}.mp4"
        return Path(self.config['output']['filename']).parent / filename

    def run(self) -> List[Path]:
        count = self.config['output'].get('batch_count', 1)
        outputs = []

        for i in range(count):
            path = self.generate_batch(i + 1)
            outputs.append(path)
            print(f"批次 {i + 1}/{count} 完成: {path}")

        return outputs
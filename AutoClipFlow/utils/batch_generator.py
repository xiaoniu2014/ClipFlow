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

        result = builder.build().execute()
        self._write_log(output_path, segments)
        return result

    def _write_log(self, video_path: Path, segments: List[Dict[str, Any]]):
        """写入素材使用日志"""
        output_dir = Path(self.config['output']['filename']).parent / 'log'
        output_dir.mkdir(parents=True, exist_ok=True)
        log_path = output_dir / f"{video_path.stem}.log"
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(f"视频: {video_path.name}\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"使用素材:\n")
            for i, seg in enumerate(segments, 1):
                clip_path = Path(seg['path'])
                f.write(f"  {i}. {clip_path.name} - 时长: {seg['duration']:.2f}秒\n")

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
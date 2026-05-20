import subprocess
import os
import time
import shutil
from pathlib import Path
from typing import Optional


class FFmpegExecutor:
    def __init__(
        self,
        output_dir: str = "output",
        encoder: str = "libx264",
        crf: int = 18,
        use_gpu: bool = False,
        gpu_encoder: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self.output_dir = Path(output_dir)
        self.encoder = encoder
        self.crf = crf
        self.use_gpu = use_gpu
        self.gpu_encoder = gpu_encoder
        self.timeout = timeout

    @staticmethod
    def check_ffmpeg_installed() -> bool:
        return shutil.which("ffmpeg") is not None

    def _ensure_output_dir(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _generate_output_path(self, ext: str = "mp4") -> Path:
        self._ensure_output_dir()
        counter = 1
        while True:
            filename = f"output_{counter:03d}.{ext}"
            path = self.output_dir / filename
            if not path.exists():
                return path
            counter += 1

    def _build_ffmpeg_args(self, input_path: str, output_path: str) -> list[str]:
        args = ["ffmpeg", "-i", input_path]

        if self.use_gpu and self.gpu_encoder:
            if self.gpu_encoder == "videotoolbox":
                args.extend(["-vcodec", "h264_videotoolbox"])
            elif self.gpu_encoder == "nvenc":
                args.extend(["-vcodec", "h264_nvenc"])
        else:
            args.extend(["-vcodec", self.encoder])

        args.extend([
            "-crf", str(self.crf),
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
        ])

        args.extend(["-y", str(output_path)])
        return args

    def execute(self, input_path: str, output_ext: str = "mp4") -> tuple[bool, Path]:
        if not self.check_ffmpeg_installed():
            raise RuntimeError("ffmpeg is not installed or not found in PATH")

        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        output_path = self._generate_output_path(ext=output_ext)
        cmd = self._build_ffmpeg_args(input_path, output_path)

        start_time = time.time()
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        try:
            for line in process.stdout:
                print(line, end="")

            returncode = process.wait(timeout=self.timeout)

            elapsed = time.time() - start_time

            if returncode != 0:
                raise RuntimeError(f"ffmpeg failed with return code {returncode}")

            print(f"\nExport completed in {elapsed:.2f} seconds")
            print(f"Output: {output_path}")
            return True, output_path

        except subprocess.TimeoutExpired:
            process.kill()
            raise TimeoutError(f"ffmpeg timed out after {self.timeout} seconds")

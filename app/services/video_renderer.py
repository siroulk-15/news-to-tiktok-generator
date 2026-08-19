"""Render approved script drafts as simple vertical MP4 videos."""

import subprocess
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy.orm import Session

from app.database import ScriptDraftDB, StoryDB
from app.logger import setup_logger

logger = setup_logger(__name__)


class VideoRenderer:
    """Render local, silent 1080x1920 videos without external services."""

    WIDTH = 1080
    HEIGHT = 1920
    FPS = 30
    SLIDE_SECONDS = 2

    def __init__(self, db: Session):
        self.db = db

    def render_approved(self, output_dir: str | Path, limit: int | None = None) -> dict:
        """Render only stories and drafts that are both approved."""
        destination = Path(output_dir)
        destination.mkdir(parents=True, exist_ok=True)
        query = self.db.query(StoryDB).filter(StoryDB.status == "APPROVED")
        if limit is not None:
            query = query.limit(limit)

        rendered = 0
        for story in query.all():
            draft = self.db.query(ScriptDraftDB).filter(
                ScriptDraftDB.story_id == story.id,
                ScriptDraftDB.status == "APPROVED",
            ).first()
            if draft is None:
                continue
            self.render_draft(draft, destination / f"{story.id}.mp4")
            rendered += 1

        logger.info("Rendered %d approved video(s) to %s", rendered, destination)
        return {"videos_rendered": rendered, "output_dir": str(destination)}

    def render_draft(
        self,
        draft: ScriptDraftDB,
        output_path: str | Path,
        width: int = WIDTH,
        height: int = HEIGHT,
        fps: int = FPS,
        slide_seconds: int = SLIDE_SECONDS,
    ) -> None:
        """Render hook, context, and call-to-action slides into an H.264 MP4."""
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        command = [
            ffmpeg, "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
            "-pix_fmt", "rgb24", "-s", f"{width}x{height}", "-r", str(fps),
            "-i", "-", "-an", "-c:v", "libx264", "-preset", "fast",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output),
        ]
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            slides = [draft.hook, draft.context, draft.call_to_action]
            for index, text in enumerate(slides):
                frame = self._make_slide(text, index, width, height)
                for _ in range(max(1, fps * slide_seconds)):
                    process.stdin.write(frame.tobytes())
            process.stdin.close()
            stderr = process.stderr.read().decode("utf-8", errors="replace")
            if process.wait() != 0:
                raise RuntimeError(f"FFmpeg rendering failed: {stderr[-500:]}")
        except Exception:
            if process.stdin and not process.stdin.closed:
                process.stdin.close()
            process.kill()
            process.wait()
            raise

    @staticmethod
    def _make_slide(text: str, index: int, width: int, height: int) -> Image.Image:
        colors = [(22, 34, 31), (212, 93, 56), (245, 241, 232)]
        foreground = (255, 253, 248) if index < 2 else (23, 34, 31)
        image = Image.new("RGB", (width, height), colors[index])
        draw = ImageDraw.Draw(image)
        font = VideoRenderer._font(max(30, width // 15), bold=index == 0)
        lines = VideoRenderer._wrap(text, 24 if width >= 700 else 16)
        line_height = font.size + max(12, width // 80)
        top = (height - line_height * len(lines)) // 2
        for line_index, line in enumerate(lines):
            box = draw.textbbox((0, 0), line, font=font)
            x = (width - (box[2] - box[0])) // 2
            draw.text((x, top + line_index * line_height), line, fill=foreground, font=font)
        return image

    @staticmethod
    def _font(size: int, bold: bool) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        for path in candidates:
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
        return ImageFont.load_default()

    @staticmethod
    def _wrap(text: str, width: int) -> list[str]:
        words = (text or "").split()
        lines = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if current and len(candidate) > width:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        return lines or [""]
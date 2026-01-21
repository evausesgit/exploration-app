"""HTTP download utilities with progress tracking."""
import asyncio
from pathlib import Path
from typing import Optional, Callable
import httpx
from loguru import logger


class Downloader:
    """Async HTTP downloader with progress tracking and resume support."""

    def __init__(
        self,
        timeout: int = 300,
        chunk_size: int = 8192,
        retry_attempts: int = 3,
    ):
        self.timeout = timeout
        self.chunk_size = chunk_size
        self.retry_attempts = retry_attempts

    async def download(
        self,
        url: str,
        destination: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Path:
        """Download a file from URL to destination.

        Args:
            url: URL to download from.
            destination: Path to save the file.
            progress_callback: Optional callback(downloaded_bytes, total_bytes).

        Returns:
            Path to downloaded file.
        """
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)

        for attempt in range(1, self.retry_attempts + 1):
            try:
                return await self._download_with_resume(
                    url, destination, progress_callback
                )
            except Exception as e:
                logger.warning(f"Download attempt {attempt} failed: {e}")
                if attempt == self.retry_attempts:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        raise RuntimeError("Download failed after all retries")

    async def _download_with_resume(
        self,
        url: str,
        destination: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Path:
        """Download with resume support."""
        headers = {}
        mode = "wb"
        downloaded = 0

        # Check for partial download
        if destination.exists():
            downloaded = destination.stat().st_size
            headers["Range"] = f"bytes={downloaded}-"
            mode = "ab"
            logger.info(f"Resuming download from byte {downloaded}")

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            async with client.stream("GET", url, headers=headers) as response:
                # Handle resume response
                if response.status_code == 416:
                    # Range not satisfiable - file already complete
                    logger.info("File already fully downloaded")
                    return destination

                if response.status_code == 206:
                    # Partial content - resuming
                    content_range = response.headers.get("content-range", "")
                    if "/" in content_range:
                        total = int(content_range.split("/")[1])
                    else:
                        total = downloaded + int(response.headers.get("content-length", 0))
                elif response.status_code == 200:
                    # Fresh download
                    total = int(response.headers.get("content-length", 0))
                    downloaded = 0
                    mode = "wb"
                else:
                    response.raise_for_status()

                logger.info(f"Downloading {url} ({total:,} bytes)")

                with open(destination, mode) as f:
                    async for chunk in response.aiter_bytes(chunk_size=self.chunk_size):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(downloaded, total)

        logger.info(f"Downloaded: {destination} ({downloaded:,} bytes)")
        return destination

    def download_sync(
        self,
        url: str,
        destination: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Path:
        """Synchronous wrapper for download."""
        return asyncio.run(self.download(url, destination, progress_callback))


def create_progress_bar(description: str = "Downloading"):
    """Create a Rich progress bar callback.

    Returns:
        Tuple of (progress, task_id, callback_function).
    """
    from rich.progress import Progress, BarColumn, DownloadColumn, TransferSpeedColumn

    progress = Progress(
        "[progress.description]{task.description}",
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
    )
    task_id = progress.add_task(description, total=None)

    def callback(downloaded: int, total: int):
        progress.update(task_id, completed=downloaded, total=total)

    return progress, task_id, callback

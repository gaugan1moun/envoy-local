"""File watcher that reloads and re-renders Envoy config on source changes."""

import time
import hashlib
import logging
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)


def _file_hash(path: Path) -> str:
    """Return MD5 hex digest of a file's contents."""
    return hashlib.md5(path.read_bytes()).hexdigest()


class ConfigWatcher:
    """Poll a config source file and invoke a callback when it changes."""

    def __init__(
        self,
        source_path: Path,
        on_change: Callable[[Path], None],
        poll_interval: float = 1.0,
    ) -> None:
        self.source_path = Path(source_path)
        self.on_change = on_change
        self.poll_interval = poll_interval
        self._last_hash: Optional[str] = None
        self._running = False

    def _current_hash(self) -> Optional[str]:
        try:
            return _file_hash(self.source_path)
        except OSError as exc:
            logger.warning("Cannot read %s: %s", self.source_path, exc)
            return None

    def check_once(self) -> bool:
        """Check for changes; return True if a change was detected."""
        current = self._current_hash()
        if current is None:
            return False
        if current != self._last_hash:
            if self._last_hash is not None:
                logger.info("Change detected in %s — reloading.", self.source_path)
                self.on_change(self.source_path)
            self._last_hash = current
            return True
        return False

    def start(self) -> None:
        """Block and poll until stop() is called."""
        self._running = True
        logger.info(
            "Watching %s every %.1fs", self.source_path, self.poll_interval
        )
        # Seed the initial hash without firing the callback.
        self._last_hash = self._current_hash()
        while self._running:
            self.check_once()
            time.sleep(self.poll_interval)

    def stop(self) -> None:
        """Signal the polling loop to exit."""
        self._running = False

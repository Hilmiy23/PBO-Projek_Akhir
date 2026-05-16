import json
import os
from settings import HIGHSCORE_FILE


class HighScoreManager:
    """Load, compare and persist the player's all-time high score."""

    def __init__(self):
        self.file_path  = HIGHSCORE_FILE
        self.high_score = self._load()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load(self) -> int:
        if not os.path.exists(self.file_path):
            return 0
        try:
            with open(self.file_path, "r") as fh:
                data = json.load(fh)
            return int(data.get("high_score", 0))
        except (json.JSONDecodeError, ValueError, OSError):
            return 0

    def _save(self) -> None:
        try:
            with open(self.file_path, "w") as fh:
                json.dump({"high_score": self.high_score}, fh, indent=2)
        except OSError:
            pass  # silently ignore write errors (read-only env, etc.)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(self, score: int) -> bool:
        """Submit a score; returns True if it is a new high score."""
        if score > self.high_score:
            self.high_score = score
            self._save()
            return True
        return False

    def reset(self) -> None:
        """Wipe the stored high score (useful for testing)."""
        self.high_score = 0
        self._save()
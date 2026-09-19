from pathlib import Path
import os
import tempfile
from typing import Callable


def atomic_write(
    path: str | Path,
    writer: Callable[[object], None],
) -> None:
    """Write a file through a temporary file and atomically replace path."""
    path = Path(path)

    fd, temp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )

    try:
        with os.fdopen(fd, "w") as f:
            writer(f)
            f.flush()
            os.fsync(f.fileno())

        os.replace(temp_path, path)

    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise

from __future__ import annotations

from services.worker import JobWorker


if __name__ == "__main__":
    JobWorker().run_forever(poll_seconds=1.0)

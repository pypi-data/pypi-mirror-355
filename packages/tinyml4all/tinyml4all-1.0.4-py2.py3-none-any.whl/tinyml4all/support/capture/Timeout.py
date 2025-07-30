from time import time
from durations import Duration

from tinyml4all.support.types import coalesce, cast


class Timeout:
    """
    Context manager to handle timeouts
    """

    def __init__(self, duration: Duration):
        """
        Constructor
        :param duration:
        """
        self.duration = duration
        self.started_at = 0
        self.ticks = 0
        self.value = 0 if duration is None else cast(duration, Duration).to_seconds()

    def __repr__(self):
        return f"Timeout(duration={self.duration})"

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def start(self):
        """
        Start timer
        :return:
        """
        self.started_at = time()
        self.ticks = 0
        return self

    def expired(self) -> bool:
        """
        Check if timer has expired
        :return:
        """
        if self.duration is None:
            return False

        return time() - self.started_at > self.duration.to_seconds()

    def decrement(self) -> int:
        """
        Decrement timer
        :return:
        """
        if self.duration is None:
            return 0

        delta = int(time() - self.started_at)
        update = delta - self.ticks

        if update > 0:
            self.ticks += update
            return update

        return 0

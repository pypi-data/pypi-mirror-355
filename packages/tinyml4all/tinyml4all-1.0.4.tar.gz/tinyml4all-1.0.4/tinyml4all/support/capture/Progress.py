import tqdm
from durations import Duration

from tinyml4all.support.capture.Counter import Counter
from tinyml4all.support.capture.Timeout import Timeout


class Progress:
    """
    Progress tracker for time-based and count-based progress
    """

    def __init__(self, duration: str | Duration = None, count: int = 0):
        """
        Constructor
        :param duration:
        :param count:
        """
        self.timeout = Timeout(Duration(duration) if duration else None)
        self.counter = Counter(count)

        assert self.timeout.value > 0 or self.counter.value > 0, (
            "You must set either the duration or the number of samples to capture"
        )

        self.tqdm = tqdm.tqdm(total=max(self.timeout.value, self.counter.value))

    def __enter__(self):
        """
        Start progress
        :return:
        """
        self.timeout.start()
        self.counter.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __iter__(self):
        return self

    def __next__(self):
        if self.expired():
            raise StopIteration

        return None

    def expired(self):
        """
        Check if progress has expired
        :return:
        """
        return self.timeout.expired() or self.counter.expired()

    def increment(self):
        """
        Increment counter
        :return:
        """
        if update := self.timeout.decrement() + self.counter.decrement():
            self.tqdm.update(update)

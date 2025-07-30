class Counter:
    """
    Countdown counter
    """

    def __init__(self, limit: int):
        """
        Constructor
        :param limit:
        """
        self.count = 0
        self.value = limit if limit > 0 else -1

    def __repr__(self):
        return f"Counter(value={self.value})"

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def start(self):
        """
        Start countdown
        :return:
        """
        self.count = 0
        return self

    def expired(self) -> bool:
        """
        Check if countdown has expired
        :return:
        """
        return 0 < self.value <= self.count

    def decrement(self) -> int:
        """
        Decrement counter
        :return:
        """
        if self.count < self.value:
            self.count += 1
            return 1

        return 0

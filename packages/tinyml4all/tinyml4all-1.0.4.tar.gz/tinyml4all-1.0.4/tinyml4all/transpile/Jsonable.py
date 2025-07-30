from tinyml4all.support import override


class Jsonable:
    """
    A class that can be converted to JSON
    """

    def to_json(self) -> dict:
        """
        Convert to JSON
        :return:
        """
        override(self)

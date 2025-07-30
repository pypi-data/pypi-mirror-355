from typing import Callable, Tuple
from os.path import sep

import jinja2


class Loader(jinja2.FileSystemLoader):
    """
    Override default Jinja2 FileSystemLoader
    """

    def get_source(
        self, environment: "Environment", template: str
    ) -> Tuple[str, str, Callable[[], bool]]:
        """
        Override source locator resolver
        :param environment:
        :param template:
        :return:
        """
        # normalize path separator for Windows and Unix
        template = template.replace(sep, "/")

        # always append .jinja extension
        if not template.endswith(".jinja"):
            template = f"{template}.jinja"

        return super().get_source(environment, template)

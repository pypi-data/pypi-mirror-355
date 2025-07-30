import os

from tinyml4all.support import override
from tinyml4all.support.types import TemplateDef
from tinyml4all.transpile.jinja.Environment import Environment


class Convertible:
    """
    Base class for all objects that can be converted to code
    """

    def get_template(self) -> TemplateDef:
        """
        Get template name and data
        :return:
        """
        return {}

    def convert_to(self, language: str, save_to: str = None, **kwargs) -> str:
        """
        Convert to given language
        :param language:
        :param save_to:
        :return:
        """
        env = Environment(language)
        code = env.render(self, **kwargs)

        # todo: beautify

        if save_to is not None:
            save_to = os.path.abspath(save_to)
            assert os.path.isdir(os.path.dirname(save_to)), (
                f"Directory {os.path.dirname(save_to)} does not exist"
            )

            with open(save_to, "w") as file:
                file.write(code)

        return code

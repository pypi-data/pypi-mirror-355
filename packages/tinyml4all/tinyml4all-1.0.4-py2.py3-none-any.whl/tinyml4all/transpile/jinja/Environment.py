import os
from os.path import normpath, join, dirname

import jinja2

from tinyml4all.support.types import TemplateDef
from tinyml4all.transpile.jinja.Loader import Loader
from tinyml4all.transpile.jinja.filters import get_filters
from tinyml4all.transpile.jinja.globals import get_globals


class Environment(jinja2.Environment):
    """
    Override default Jinja2 Environment
    """

    def __init__(self, language: str):
        """
        Constructor
        :param language:
        """
        cwd = dirname(os.path.realpath(__file__))
        root = join(cwd, "..", "templates", language)
        loader = Loader(root)

        super().__init__(
            loader=loader, extensions=["jinja2_workarounds.MultiLineInclude"]
        )

        self.filters.update(get_filters(language))
        self.globals.update(get_globals(language))

    def join_path(self, template: str, parent: str) -> str:
        """
        Build path to template
        :param template:
        :param parent:
        :return:
        """
        return normpath(join(dirname(parent), template))

    def render(self, target, **kwargs) -> str:
        """
        Render template
        :param target:
        :param kwargs:
        :return:
        """
        template = target.get_template()
        class_name = target.__class__.__name__
        public_data = target.__dict__

        # if no name is given, infer from class name
        if isinstance(template, dict):
            template_name = target.__module__.replace("tinyml4all.", "").replace(
                ".", "/"
            )
            template_data = template
        else:
            template_name, template_data = template

        return self.get_template(template_name).render(
            **{
                "this": target,
                "class_name": class_name,
                **public_data,
                **template_data,
                **kwargs,
            }
        )

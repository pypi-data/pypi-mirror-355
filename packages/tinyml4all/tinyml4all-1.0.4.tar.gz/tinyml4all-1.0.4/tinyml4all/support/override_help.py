import os.path
import pydoc

_original_help = pydoc.help


def override_help():
    """
    Override help()
    :return:
    """

    def custom_help(obj):
        """
        Get docstring
        :param obj:
        :return:
        """
        # if a doc file exists, use it
        if hasattr(obj, "__module__"):
            module = obj.__module__.replace("tinyml4all.", "")
            path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "transpile",
                "templates",
                "help",
                module + ".md",
            )

            if os.path.exists(path):
                with open(path, "r") as file:
                    return file.read()

        # otherwise, look for a custom help function
        if hasattr(obj, "__help__"):
            return obj.__help__()

        # default to pydoc
        return _original_help(obj)

    pydoc.help = custom_help

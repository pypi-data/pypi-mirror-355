import os.path
import pickle
from io import BytesIO


class IsPickleable:
    """
    Mixin for classes that can be pickled
    """

    def __getstate__(self):
        """
        Get state for pickling
        :return:
        """
        return self.__dict__

    def __setstate__(self, state):
        """
        Set state for unpickling
        :param state:
        :return:
        """
        self.__dict__ = state

    def save_to(self, folder: str, name: str):
        """
        Save to folder
        :param folder:
        :param name:
        :return:
        """
        with open(os.path.join(folder, f"{name}.pkl"), "wb") as f:
            pickle.dump(self, f)

    def reload(self):
        """
        Pickle/unpickle in memory to create a clone
        :return:
        """
        return pickle.loads(pickle.dumps(self))

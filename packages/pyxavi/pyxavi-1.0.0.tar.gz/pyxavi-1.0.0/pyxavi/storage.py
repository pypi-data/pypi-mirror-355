from pyxavi import Dictionary
from hashlib import sha256
from slugify import slugify
from pathlib import Path
import yaml
import os


class Storage(Dictionary):
    """Class to handle file-based simple storage

    Basic load/write, get/set behaviour for key/value
    file-based storage.

    :Authors:
        Xavier Arnaus <xavi@arnaus.net>

    """

    def __init__(self, filename, path_separator_char=None) -> None:
        self._filename = filename

        # Assuming that we initialise the parent Dictionary class
        #   content stack with {}
        super().__init__(path_separator_char=path_separator_char)

        # And now make this function to fill the self._content
        self.read_file()

    @staticmethod
    def _load_file_contents(filename: str) -> dict:
        with open(filename, 'r') as stream:
            return yaml.safe_load(stream)

    def read_file(self) -> None:
        if os.path.exists(self._filename):
            self._content = self._load_file_contents(self._filename)
            if self._content is None:
                self._content = {}
        else:
            Path(self._filename).touch()
            self._content = {}

    def write_file(self) -> None:
        with open(self._filename, 'w+') as stream:
            yaml.safe_dump(self._content, stream)

    def get_hashed(self, param_name: str = "", default_value: any = None) -> any:
        # if param_name.find(".") > 0:
        #     last = param_name[-1]
        #     param_name = param_name[0:-1]
        #     param_name = param_name + sha256(last.encode()).hexdigest()
        # else:
        param_name = sha256(param_name.encode()).hexdigest()

        return self.get(param_name, default_value)

    def set_hashed(self, param_name: str, value: any = None):
        # if param_name.find(".") > 0:
        #     last = param_name[-1]
        #     param_name = param_name[0:-1]
        #     param_name = param_name + sha256(last.encode()).hexdigest()
        # else:
        param_name = sha256(param_name.encode()).hexdigest()

        self.set(param_name, value)

    def get_slugged(self, param_name: str = "", default_value: any = None) -> any:
        param_name = slugify(param_name)

        return self.get(param_name, default_value)

    def set_slugged(self, param_name: str, value: any = None):
        param_name = slugify(param_name)

        self.set(param_name, value)

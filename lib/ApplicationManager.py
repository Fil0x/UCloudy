import os
import json

import strings
from lib.util import raw
from lib.DataManager import Manager

from configobj import ConfigObj

def check_file(f):
    def wrapper(*args):
        try:
            with open(args[0].config_path,'r') as file:
                pass
        except IOError:
            args[0]._create_config_file()
        return f(*args)
    return wrapper

class ApplicationManager(Manager):
    def __init__(self, config_path='app.ini'):
        super(ApplicationManager, self).__init__()

        self.config_path = os.path.join(self.basepath, raw(config_path))

        try:
            with open(self.config_path, 'r'):
                pass
        except IOError:
            self._create_config_file()

        self.config = ConfigObj(self.config_path)

    def _create_config_file(self):
        config = ConfigObj(self.config_path)

        config.write()

        self.config = ConfigObj(self.config_path)

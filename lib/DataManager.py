import os
import json
import errno
import inspect

import logger
from lib.util import raw

from configobj import ConfigObj


def checkFile(f):
    def wrapper(*args):
        try:
            with open(args[0].configPath,'r') as file:
                pass
        except IOError:
            args[0]._create_config_file()
        return f(*args)
    return wrapper

class Manager(object):
    filedir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    basepath =  os.path.join(os.path.dirname(filedir), 'Configuration')

    def __init__(self):
        try:
            os.makedirs(self.basepath)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

class LocalDataManager(Manager):
    def __init__(self, config_name='config.ini'):
        super(LocalDataManager, self).__init__()

        self.configPath = os.path.join(self.basepath,raw(config_name))

        try:
            with open(self.configPath,'r'):
                pass
        except IOError as e:
            self._create_config_file()

        self.config = ConfigObj(self.configPath)

    #Exposed functions
    @checkFile
    def get_token(self):
        try:
            return self.config['token']
        except KeyError:
            raise KeyError('No token.')

    def set_token(self, token):
        self.config['token'] = token
        self.config.write()

    def flush_token(self):
        try:
            del(self.config['token'])
            self.config.write()
        except KeyError:
            pass
    #End of Exposed functions

    def _create_config_file(self):
        config = ConfigObj(self.configPath)

        config.write()
        self.config = ConfigObj(self.configPath)

import os
import errno
import logging

import version


class DebugFilter(object):

    def __init__(self, level):
        self.__level = level

    def filter(self, logRecord):
        return logRecord.levelno <= self.__level

class LoggerFactory(object):

    def __init__(self):
        try:
            os.makedirs('logs')
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
    
        self.v = version.__version__
        fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fmt_dbg = logging.Formatter('%(asctime)s - %(name)s - %(message)s')

        #The application's root logger.
        logger = logging.getLogger(self.v)
        #Change this to logging.INFO to stop printing the loggging.debug messages.
        logger.setLevel(logging.DEBUG)

        #Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(fmt_dbg)
        #We want to print the debug messages only.
        ch.addFilter(DebugFilter(logging.DEBUG))

        #Main file handler
        fh = logging.FileHandler(os.path.join('logs', 'main.log'))
        fh.setLevel(logging.INFO)
        fh.setFormatter(fmt)

        #Error file handler
        eh = logging.FileHandler(os.path.join('logs', 'error.log'))
        eh.setLevel(logging.ERROR)
        eh.setFormatter(fmt)

        logger.addHandler(ch)
        logger.addHandler(fh)
        logger.addHandler(eh)

    def getLogger(self, name):
        return logging.getLogger('{}{}'.format(self.v, '.{}'.format(name) if name else ''))

#Call this to get a logger.
def logger_factory(name, _singleton=LoggerFactory()):
    ''' Returns a logger with root version.__version__.
        params:
        name: the logger's name. 
    '''
    return _singleton.getLogger(name)
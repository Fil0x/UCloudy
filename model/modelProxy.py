import sys
if ".." not in sys.path:
    sys.path.append("..")

import os
import Queue

import logger
import strings
import globals
from model import Model
from Threads import TaskThread
from lib.DataManager import LocalDataManager
from lib.ApplicationManager import ApplicationManager

import puremvc.patterns.proxy


class ModelProxy(puremvc.patterns.proxy.Proxy):

    NAME = 'MODELPROXY'

    task_queue = Queue.Queue()

    def __init__(self):
        super(ModelProxy, self).__init__(ModelProxy.NAME, [])

        self.model = Model()
        self.logger = logger.logger_factory(self.__class__.__name__)
        self.g = globals.get_globals()

        self.att = TaskThread(self.task_queue, self, self.g)
        self.att.start()

    #Exposed functions
    def initialize(self):
        self.task_queue.put('init')
    
    def add_token(self, token):
        dm = LocalDataManager()
        dm.set_token(service, credentials)

    def delete_token(self):
        dm = LocalDataManager()
        dm.flush_token(service)
    #End of exposed functions

    def authenticate(self, ):
        return self.model.am.authenticate()

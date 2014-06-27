import sys
if ".." not in sys.path:
    sys.path.append("..")

import os
import Queue

import local
import logger
import strings
import globals
from model import Model
from Threads import UploadThread
from Threads import AddTaskThread
from Threads import UploadSupervisorThread
from lib.DataManager import LocalDataManager
from lib.ApplicationManager import ApplicationManager

import puremvc.patterns.proxy


class ModelProxy(puremvc.patterns.proxy.Proxy):

    NAME = 'MODELPROXY'

    add_queue = Queue.Queue()

    def __init__(self):
        super(ModelProxy, self).__init__(ModelProxy.NAME, [])

        self.active_threads = {} # {'id':UploadThread, ...}
        self.model = Model()
        self.logger = logger.logger_factory(self.__class__.__name__)
        self.g = globals.get_globals()

        self.att = AddTaskThread(self.add_queue, self.upload_queue, self, self.g)
        self.upt = UploadSupervisorThread(self.upload_queue, self.history_queue, self, self.g)
        self.upt.start()
        self.att.start()

    #Exposed functions
    def add_service_credentials(self, service, credentials):
        dm = LocalDataManager()
        dm.set_credentials(service, credentials)

        p = ApplicationManager()
        p.add_service(service)

    def delete_service_credentials(self, service):
        dm = LocalDataManager()
        dm.flush_credentials(service)

        p = ApplicationManager()
        p.remove_service(service)

        #Remove the uploads of the service that was just removed.
        ids = self.model.uq.get_all_uploads()[service]
        if ids:
            for id in ids.iterkeys():
                self.upload_queue.put(('delete', service, id))
    #End of exposed functions

    def get(self, service, id):
        return self.model.uq.get(service, id)

    def add(self, service, path):
        return self.model.uq.add(service, path)

    def save(self):
        self.model.uq.save()

    def authenticate(self, service):
        return self.model.am.authenticate(service)

    def delete(self, service, id):
        self.model.uq.delete(service, id)

    def set_state(self, service, id, state):
        self.model.uq.set_state(service, id, state)

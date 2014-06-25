import sys
if ".." not in sys.path:
    sys.path.append("..")

import os
import Queue
import threading

import local
import logger
import strings
import globals
import AppFacade
import lib.Upload
from lib import faults
from model import Model
from lib.DataManager import LocalDataManager
from lib.ApplicationManager import ApplicationManager

import puremvc.patterns.proxy


class ModelProxy(puremvc.patterns.proxy.Proxy):

    NAME = 'MODELPROXY'

    add_queue = Queue.Queue()
    upload_queue = Queue.Queue()

    def __init__(self):
        super(ModelProxy, self).__init__(ModelProxy.NAME, [])

        self.active_threads = {} # {'id':UploadThread, ...}
        self.model = Model()
        self.logger = logger.logger_factory(self.__class__.__name__)
        self.g = globals.get_globals()

        self.upt = UploadSupervisorThread(self.upload_queue, self.history_queue, self, self.g)
        self.att = AddTaskThread(self.add_queue, self.upload_queue, self, self.g)
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

    def add_file(self, service, path):
        assert(service in local.services)

        self.add_queue.put(('add', service, path))


        return r

    def get_service_folders(self, used_services):
        dm = LocalDataManager()
        r = {}
        for s in local.services:
            r[s] = dm.get_service_root(s)
        return r
    #End of exposed functions

    def add(self, service, path):
        return self.model.uq.add(service, path)

    def save(self):
        self.model.uq.save()

    def authenticate(self, service):
        return self.model.am.authenticate(service)

class UploadSupervisorThread(threading.Thread):
    def __init__(self, in_queue, out_queue, proxy, globals, **kwargs):
        threading.Thread.__init__(self, **kwargs)

        self.in_queue = in_queue
        self.out_queue = out_queue #History queue for the upload threads
        self.proxy = proxy
        self.globals = globals
        self.daemon = True
        self.logger = logger.logger_factory(self.__class__.__name__)
        self.logger.debug('Initialized')

    def run(self):
        while True:
            msg = self.in_queue.get()
            if msg[0] in 'add':
                t = UploadThread(msg[3], msg[1], self.out_queue, msg[2],
                                 self.proxy, self.globals)
                self.proxy.active_threads[msg[2]] = t
                t.start()
                if msg[1] == 'Dropbox':
                    l = [self.globals,  msg[2], '{}{}'.format(local.Dropbox_APPFOLDER, msg[3].remote)[0:-1]]
                else:
                    l = [self.globals,  msg[2], msg[3].remote]
                self.proxy.set_state(msg[1], msg[2], 'Running')
                self.proxy.facade.sendNotification(AppFacade.AppFacade.UPLOAD_STARTED, l)
                self.logger.debug('Started {}.'.format(msg[2]))
            elif msg[0] in 'delete':
                if msg[2] in self.proxy.active_threads:
                    t = self.proxy.active_threads[msg[2]]
                    if not t.error: #Running->Removing
                        t.state = 2
                        self.proxy.set_state(msg[1], msg[2], 'Removing')
                        self.logger.debug('Removing {}'.format(msg[2]))
                        self.proxy.facade.sendNotification(AppFacade.AppFacade.UPLOAD_REMOVING,
                                                           [self.globals, msg[2]])
                    else: #Error->Removing
                        self.proxy.facade.sendNotification(AppFacade.AppFacade.UPLOAD_REMOVED,
                                                           [self.globals, msg[2]])
                        del self.proxy.active_threads[msg[2]]
                        self.proxy.delete(msg[1], msg[2])
                #(Paused, Error-2)->Removing
                else:
                    self.proxy.delete(msg[1], msg[2])
                    self.proxy.facade.sendNotification(AppFacade.AppFacade.UPLOAD_REMOVED,
                                                       [self.globals, msg[2]])

class AddTaskThread(threading.Thread):

    def __init__(self, in_queue, out_queue, proxy, globals, **kwargs):
        ''' in_queue=add_queue, out_queue=upload_queue '''
        threading.Thread.__init__(self, **kwargs)

        self.in_queue = in_queue
        self.out_queue = out_queue
        self.proxy = proxy
        self.globals = globals
        self.daemon = True
        self.logger = logger.logger_factory(self.__class__.__name__)
        self.logger.debug('Initialized')

    def run(self):
        while True:
            #Block here until we have an item to add.
            msg = self.in_queue.get()
            self.logger.debug('Authenticating with {}'.format(msg[1]))
            if msg[0] in 'add':
                id, d = self.proxy.add(msg[1], msg[2])
                filename = os.path.basename(msg[2])
                # [filename, progress, service, status, dest, conflict, (id)]
                l = [self.globals, filename, '0%', msg[1], 'Starting', '', 'Keep Both', id]
                self.proxy.facade.sendNotification(AppFacade.AppFacade.UPLOAD_STARTING, l)
                try:
                    client = self.proxy.authenticate(msg[1])
                except (faults.InvalidAuth, KeyError):
                    self.logger.debug('Authentication skipped')
                    self.proxy.set_state(msg[1], id, 'Error-12')
                    self.proxy.facade.sendNotification(AppFacade.AppFacade.INVALID_CREDENTIALS,
                                                       [self.globals, id])
                except faults.NetworkError:
                    self.logger.debug('Authentication skipped')
                    self.proxy.set_state(msg[1], id, 'Error-22')
                    self.proxy.facade.sendNotification(AppFacade.AppFacade.NETWORK_ERROR,
                                                       [self.globals, id])
                else:
                    self.logger.debug('Authentication done')
                    d['uploader'].client = client
                    self.logger.debug('Putting the uploader in queue.')
                    self.out_queue.put(('add', msg[1], id, d['uploader']))

class UploadThread(threading.Thread):
    def __init__(self, uploader, service, out_queue, id, proxy, globals, **kwargs):

        threading.Thread.__init__(self, **kwargs)
        self.worker = uploader #Uploader already has a validated client.
        self.service = service
        self.proxy = proxy
        self.globals = globals
        self.id = id
        self.out_queue = out_queue
        self.error = False
        self.logger = logger.logger_factory(self.__class__.__name__)

    def run(self):
        self.logger.debug('Starting:{}'.format(self.id))
        for i in self.worker.upload_chunked():
            elif i[0] == 12:
                self.proxy.set_state(self.service, self.id, 'Error-12')
                self.proxy.facade.sendNotification(AppFacade.AppFacade.INVALID_CREDENTIALS,
                                                   [self.globals, self.id])
                self.error = True
                return
            elif i[0] == 22:
                self.proxy.set_state(self.service, self.id, 'Error-22')
                self.proxy.facade.sendNotification(AppFacade.AppFacade.NETWORK_ERROR,
                                                   [self.globals, self.id])
                return
            else:
                self.logger.debug('Uploaded:{}'.format(i))
                progress = str(round(i[0], 3)*100) + '%'
                self.proxy.facade.sendNotification(AppFacade.AppFacade.UPLOAD_UPDATED,
                                                   [self.globals, self.id, progress])

                if self._state == 1:
                    self.logger.debug('Paused:{}'.format(i))
                    self.proxy.set_state(self.service, self.id, 'Paused')
                    self.proxy.facade.sendNotification(AppFacade.AppFacade.UPLOAD_PAUSED,
                                                       [self.globals, self.id])
                    return
                elif self.state == 2:
                    self.logger.debug('Deleted:{}'.format(i))
                    self.proxy.facade.sendNotification(AppFacade.AppFacade.UPLOAD_REMOVED,
                                                       [self.globals, self.id])
                    del self.proxy.active_threads[self.id]
                    self.proxy.delete(self.service, self.id)
                    return

        #If I reach this point, the upload is complete and it has to be saved to the history.
        self.logger.debug('Putting in queue {}.'.format(self.id))
        self.out_queue.put(('add', self.service, self.id, history_entry))

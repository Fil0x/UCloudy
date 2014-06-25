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
    history_queue = Queue.Queue()

    def __init__(self):
        super(ModelProxy, self).__init__(ModelProxy.NAME, [])

        self.active_threads = {} # {'id':UploadThread, ...}
        self.model = Model()
        self.logger = logger.logger_factory(self.__class__.__name__)
        self.g = globals.get_globals()

        self.upt = UploadSupervisorThread(self.upload_queue, self.history_queue, self, self.g)
        self.att = AddTaskThread(self.add_queue, self.upload_queue, self, self.g)
        self.ht  = HistoryThread(self.history_queue, self, self.g)
        self.upt.start()
        self.att.start()
        self.ht.start()

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

    def stop_file(self, data):
        for i in data:
            assert i[0] in self.active_threads, 'ID:{} not found'.format(i)
            self.upload_queue.put(('stop', i[1], i[0]))

    def delete_file(self, data):
        for i in data:
            self.upload_queue.put(('delete', i[1], i[0]))

    def resume_file(self, data):
        for i in data:
            #Skip files with status Running
            r = self.get(i[1], i[0])
            if r['status'] == 'Error-2':
                if 'error' in r:
                    path = r['path']
                else:
                    path = r['uploader'].path
                    self.facade.sendNotification(AppFacade.AppFacade.UPLOAD_UPDATED,
                                                       [self.g, i[0], '0%'])
                data = self.model.uq.add_from_error(i[1], i[0], path)
                self.add_queue.put(('resume', i[1], i[0], data))
            else:
                self.add_queue.put(('resume', i[1], i[0], r))

    def get_history(self):
        r = self.model.uq.get_history()
        self.logger.debug('History retrieved.')
        return r

    def get_service_folders(self, used_services):
        dm = LocalDataManager()
        r = {}
        for s in local.services:
            r[s] = dm.get_service_root(s)
        return r

    def set_service_root(self, service, new_folder):
        dm = LocalDataManager()
        dm.set_service_root(service, new_folder)

    def delete_history(self, data):
        for i in data:
            self.history_queue.put(('remove', i[1][0], i[0]))
        return data

    def get_status(self, service, id):
        return self.model.uq.get_status(service, id)

    def start_uploads(self):
        self.logger.debug('Starting uploads...')
        r = self.model.uq.get_all_uploads()

        for s, v in r.iteritems():
            for id, data in v.iteritems():
                if 'error' in data or data['status'] == 'Error-2': #File not found, case 2 not needed?
                    self.logger.debug('Item added(2): {}/{}'.format(s, id))
                    self.add_queue.put(('error_2', s, id, data))
                elif data['status'] == 'Error-3':
                    self.logger.debug('Item added(3): {}/{}'.format(s, id))
                    self.add_queue.put(('error_3', s, id, data))
                elif data['status'] == 'Error-12':
                    self.logger.debug('Item added(12): {}/{}'.format(s, id))
                    self.add_queue.put(('error_12', s, id, data))
                elif data['status'] == 'Error-22':
                    self.logger.debug('Item added(22): {}/{}'.format(s, id))
                    self.add_queue.put(('add_from_file', s, id, data))
                elif data['status'] == 'Starting':
                    self.logger.debug('Item added(R): {}/{}'.format(s, id))
                    self.add_queue.put(('add_from_file', s, id, data))
                elif data['status'] == 'Paused':
                    self.logger.debug('Item added(P): {}/{}'.format(s, id))
                    self.add_queue.put(('add_paused', s, id, data))
        self.logger.debug('Interrupted uploads started.')

    def stop_uploads(self):
        self.logger.debug('Stopping ALL uploads...')
        for k, v in self.active_threads.iteritems():
            self.logger.debug('Stopping: {}'.format(k))
            v.state = 1

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

class HistoryThread(threading.Thread):
    def __init__(self, in_queue, proxy, globals, **kwargs):
        threading.Thread.__init__(self, **kwargs)

        self.in_queue = in_queue
        self.proxy = proxy
        self.globals = globals
        self.daemon = True
        self.logger = logger.logger_factory(self.__class__.__name__)
        self.logger.debug('Initialized')

    def run(self):
        while True:
            msg = msg = self.in_queue.get()
            self.logger.debug('Got msg')
            if msg[0] in 'add':
                self.proxy.model.uq.add_history(msg[1], msg[2], **msg[3])
                self.logger.debug('added item:{}'.format(msg[2]))
                self.proxy.delete(msg[1], msg[2])
                del self.proxy.active_threads[msg[2]]
                #There is no other easy way to send the message to the main thread
                self.proxy.facade.sendNotification(AppFacade.AppFacade.HISTORY_UPDATE_COMPACT,
                                            [self.globals, msg[1], msg[3]])
                self.proxy.facade.sendNotification(AppFacade.AppFacade.HISTORY_UPDATE_DETAILED,
                                            [self.globals, msg[1], msg[2], msg[3]])
                self.proxy.facade.sendNotification(AppFacade.AppFacade.UPLOAD_DONE,
                                            [self.globals, msg[2]])
            elif msg[0] in 'remove':
                self.proxy.model.uq.delete_history(msg[1], [msg[2]])
                self.logger.debug('removed item:{}'.format(msg[2]))
                self.proxy.facade.sendNotification(AppFacade.AppFacade.DELETE_HISTORY_DETAILED,
                                                   [self.globals, msg[2]])
                self.proxy.facade.sendNotification(AppFacade.AppFacade.DELETE_HISTORY_COMPACT,
                                                   [self.globals])

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
            elif msg[0] in 'resume':
                t = UploadThread(msg[3], msg[1], self.out_queue, msg[2],
                                 self.proxy, self.globals)
                self.proxy.active_threads[msg[2]] = t
                t.start()
                # The row already exists, just update the status.
                self.proxy.set_state(msg[1], msg[2], 'Running')
                self.proxy.facade.sendNotification(AppFacade.AppFacade.UPLOAD_RESUMED,
                                                   [self.globals, msg[2]])
                self.logger.debug('Resumed {}.'.format(msg[2]))
            elif msg[0] in 'stop':
                self.proxy.active_threads[msg[2]].state = 1
                del self.proxy.active_threads[msg[2]]
                self.proxy.set_state(msg[1], msg[2], 'Pausing')
                self.proxy.facade.sendNotification(AppFacade.AppFacade.UPLOAD_PAUSING,
                                                   [self.globals, msg[2]])
                self.logger.debug('Pausing {}.'.format(msg[2]))
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
            elif msg[0] in 'add_from_file':
                self.logger.debug('Loading from file {}.'.format(msg[2]))
                # [filename, progress, service, status, dest, conflict, (id)]
                filename = os.path.basename(msg[3]['uploader'].path)
                try:
                    float_progess = float(msg[3]['uploader'].offset)/msg[3]['uploader'].target_length
                    progress = str(round(float_progess, 3)*100) + '%'
                except ZeroDivisionError:
                    progress = '0%'
                l = [self.globals, filename, progress, msg[1], 'Starting', '', 'Keep Both', msg[2]]
                self.proxy.facade.sendNotification(AppFacade.AppFacade.UPLOAD_STARTING, l)
                try:
                    client = self.proxy.authenticate(msg[1])
                except (faults.InvalidAuth, KeyError):
                    self.logger.debug('Authentication skipped')
                    self.proxy.set_state(msg[1], msg[2], 'Error-12')
                    self.proxy.facade.sendNotification(AppFacade.AppFacade.INVALID_CREDENTIALS,
                                                       [self.globals, msg[2]])
                except faults.NetworkError:
                    self.logger.debug('Authentication skipped')
                    self.proxy.set_state(msg[1], msg[2], 'Error-22')
                    self.proxy.facade.sendNotification(AppFacade.AppFacade.NETWORK_ERROR,
                                                       [self.globals, msg[2]])
                else:
                    self.logger.debug('Authentication done')
                    msg[3]['uploader'].client = client
                    self.logger.debug('Putting the uploader in queue.')
                    self.out_queue.put(('add', msg[1], msg[2], msg[3]['uploader']))
            elif msg[0] in 'resume':
                self.proxy.set_state(msg[1], msg[2], 'Resuming')
                self.proxy.facade.sendNotification(AppFacade.AppFacade.UPLOAD_RESUMING,
                                                   [self.globals, msg[2]])
                try:
                    client = self.proxy.authenticate(msg[1])
                except (faults.InvalidAuth, KeyError):
                    self.logger.debug('Authentication skipped')
                    self.proxy.set_state(msg[1], msg[2], 'Error-12')
                    self.proxy.facade.sendNotification(AppFacade.AppFacade.INVALID_CREDENTIALS,
                                                       [self.globals, msg[2]])
                except faults.NetworkError:
                    self.logger.debug('Authentication skipped')
                    self.proxy.set_state(msg[1], msg[2], 'Error-22')
                    self.proxy.facade.sendNotification(AppFacade.AppFacade.NETWORK_ERROR,
                                                       [self.globals, msg[2]])
                else:
                    self.logger.debug('Authentication done')
                    self.logger.debug('Resuming {}'.format(msg[2]))
                    msg[3]['uploader'].client = client
                    self.out_queue.put(('resume', msg[1], msg[2], msg[3]['uploader']))
            elif msg[0] in 'add_paused':
                self.logger.debug('Authentication skipped {}.'.format(msg[2]))
                filename = os.path.basename(msg[3]['uploader'].path)
                try:
                    float_progess = float(msg[3]['uploader'].offset)/msg[3]['uploader'].target_length
                    progress = str(round(float_progess, 3)*100) + '%'
                except ZeroDivisionError:
                    progress = '0%'
                if msg[1] == 'Dropbox':
                    remote_path = '{}{}'.format(local.Dropbox_APPFOLDER, msg[3]['uploader'].remote)[0:-1]
                else:
                    remote_path = msg[3]['uploader'].remote
                l = [self.globals, filename, progress, msg[1], 'Paused', remote_path, 'Keep Both', msg[2]]
                self.proxy.facade.sendNotification(AppFacade.AppFacade.UPLOAD_STARTING, l)
            elif msg[0] in 'error_2':
                self.logger.debug('Authentication skipped {}.'.format(msg[2]))
                filename = os.path.basename(msg[3]['path'])
                l = [self.globals, filename, '0%', msg[1], strings.file_not_found, '', 'Keep Both', msg[2]]
                self.proxy.facade.sendNotification(AppFacade.AppFacade.UPLOAD_STARTING, l)
            elif msg[0] in 'error_3':
                self.logger.debug('Authentication skipped {}.'.format(msg[2]))
                filename = os.path.basename(msg[3]['uploader'].path)
                try:
                    float_progess = float(msg[3]['uploader'].offset)/msg[3]['uploader'].target_length
                    progress = str(round(float_progess, 3)*100) + '%'
                except ZeroDivisionError:
                    progress = '0%'
                l = [self.globals, filename, progress, msg[1], strings.out_of_quota, '', 'Keep Both', msg[2]]
                self.proxy.facade.sendNotification(AppFacade.AppFacade.UPLOAD_STARTING, l)
            elif msg[0] in 'error_12':
                self.logger.debug('Authentication skipped {}.'.format(msg[2]))
                filename = os.path.basename(msg[3]['uploader'].path)
                try:
                    float_progess = float(msg[3]['uploader'].offset)/msg[3]['uploader'].target_length
                    progress = str(round(float_progess, 3)*100) + '%'
                except ZeroDivisionError:
                    progress = '0%'
                l = [self.globals, filename, progress, msg[1], strings.invalid_credentials, '', 'Keep Both', msg[2]]
                self.proxy.facade.sendNotification(AppFacade.AppFacade.UPLOAD_STARTING, l)

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
        self._state = 0

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        assert(value in range(3))

        self.logger.debug('{}:Changing state to {}'.format(self.id, value))
        self._state = value

    def run(self):
        self.logger.debug('Starting:{}'.format(self.id))
        for i in self.worker.upload_chunked():
            if i[0] == 2:
                self.proxy.set_state(self.service, self.id, 'Error-2')
                self.proxy.facade.sendNotification(AppFacade.AppFacade.FILE_NOT_FOUND,
                                                   [self.globals, self.id])
                self.error = True
                return
            elif i[0] == 3:
                self.proxy.set_state(self.service, self.id, 'Error-3')
                self.proxy.facade.sendNotification(AppFacade.AppFacade.OUT_OF_STORAGE,
                                                   [self.globals, self.id])
                self.error = True
                return
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
        history_entry = self.worker.complete_upload()

        self.logger.debug('Putting in queue {}.'.format(self.id))
        self.out_queue.put(('add', self.service, self.id, history_entry))

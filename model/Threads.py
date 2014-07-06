import sys
if ".." not in sys.path:
    sys.path.append("..")

import logger
import AppFacade
import threading
from lib import faults
from lib.ServiceUtilities import PithosUtilities
from lib.ServiceUtilities import PithosFile


class TaskThread(threading.Thread):

    def __init__(self, in_queue, proxy, globals, **kwargs):
        threading.Thread.__init__(self, **kwargs)

        self.in_queue = in_queue
        self.proxy = proxy
        self.globals = globals
        self.daemon = True
        self.logger = logger.logger_factory(self.__class__.__name__)
        self.logger.debug('Initialized')

        self.cached_client = None
        self.username = None

    def _authenticate(self):
        if not self.cached_client:
            self.logger.debug('No client available. Authenticating...')
            self.cached_client, self.username = self.proxy.authenticate()

    def run(self):
        while True:
            msg = self.in_queue.get()
            if msg[0] == 'init_folders':
                try:
                    self._authenticate()
                    self.folders = PithosUtilities(self.cached_client).get_containers()
                    self.proxy.facade.sendNotification(AppFacade.AppFacade.SET_FOLDERS,
                                                       [self.globals, self.folders, self.username])
                except (faults.InvalidAuth, KeyError):
                    self.logger.debug('Authentication skipped')
                    self.proxy.facade.sendNotification(AppFacade.AppFacade.INVALID_CREDENTIALS,
                                                       [self.globals, id])
                except faults.NetworkError:
                    self.logger.debug('Authentication skipped')
                    self.proxy.facade.sendNotification(AppFacade.AppFacade.NETWORK_ERROR,
                                                       [self.globals, id])
            elif msg[0] == 'init_objects':
                try:
                    self._authenticate()
                    for folder in self.folders:
                        objects = PithosUtilities(self.cached_client).get_objects(folder)
                        self.proxy.facade.sendNotification(AppFacade.AppFacade.SET_OBJECTS,
                                                           [self.globals, folder, objects])
                    self.proxy.facade.sendNotification(AppFacade.AppFacade.SET_ACTIVE_FOLDER,
                                                           [self.globals])
                except (faults.InvalidAuth, KeyError):
                    self.logger.debug('Authentication skipped')
                    self.proxy.facade.sendNotification(AppFacade.AppFacade.INVALID_CREDENTIALS,
                                                       [self.globals, id])
                except faults.NetworkError:
                    self.logger.debug('Authentication skipped')
                    self.proxy.facade.sendNotification(AppFacade.AppFacade.NETWORK_ERROR,
                                                       [self.globals, id])
            elif msg[0] == 'rename_file':
                try:
                    self._authenticate()
                    #msg[1] = [container, old-filename, new-filename]
                    pithos_file = PithosFile(msg[1][0], msg[1][1], self.cached_client)
                    pithos_file.rename(msg[1][2])
                    self.proxy.facade.sendNotification(AppFacade.AppFacade.RENAME_FILE_COMPLETED,
                                                       [self.globals])
                except (faults.InvalidAuth, KeyError):
                    self.logger.debug('Authentication skipped')
                    self.proxy.facade.sendNotification(AppFacade.AppFacade.INVALID_CREDENTIALS,
                                                       [self.globals, id])
                except faults.NetworkError:
                    self.logger.debug('Authentication skipped')
                    self.proxy.facade.sendNotification(AppFacade.AppFacade.NETWORK_ERROR,
                                                       [self.globals, id])
            elif msg[0] == 'delete_file':
                try:
                    self._authenticate()
                    #msg[1] = [folder, filename]
                    pithos_file = PithosFile(msg[1][0], msg[1][1], self.cached_client)
                    pithos_file.delete()
                    self.proxy.facade.sendNotification(AppFacade.AppFacade.DELETE_FILE_COMPLETED,
                                                       [self.globals])
                except (faults.InvalidAuth, KeyError):
                    self.logger.debug('Authentication skipped')
                    self.proxy.facade.sendNotification(AppFacade.AppFacade.INVALID_CREDENTIALS,
                                                       [self.globals, id])
                except faults.NetworkError:
                    self.logger.debug('Authentication skipped')
                    self.proxy.facade.sendNotification(AppFacade.AppFacade.NETWORK_ERROR,
                                                       [self.globals, id])
            elif msg[0] == 'move_file':
                try:
                    self._authenticate()
                    #msg[1] = [old-folder, new-folder, filename]
                    pithos_file = PithosFile(msg[1][0], msg[1][2], self.cached_client)
                    pithos_file.move(msg[1][1])
                    self.proxy.facade.sendNotification(AppFacade.AppFacade.MOVE_FILE_COMPLETED,
                                                       [self.globals])
                except (faults.InvalidAuth, KeyError):
                    self.logger.debug('Authentication skipped')
                    self.proxy.facade.sendNotification(AppFacade.AppFacade.INVALID_CREDENTIALS,
                                                       [self.globals, id])
                except faults.NetworkError:
                    self.logger.debug('Authentication skipped')
                    self.proxy.facade.sendNotification(AppFacade.AppFacade.NETWORK_ERROR,
                                                       [self.globals, id])

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
            if i[0] == 12:
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

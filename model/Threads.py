import logger
import AppFacade
import threading
from lib import faults


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

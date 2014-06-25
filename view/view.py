import os
import sys
import copy
import httplib2
import datetime
import webbrowser
from operator import itemgetter
if ".." not in sys.path:
    sys.path.append("..")

import local
import logger
import strings
import globals
import AppFacade
import model.modelProxy
from FileChooser import FileChooser
from lib.util import raw
from lib.Authentication import AuthManager
from lib.ApplicationManager import ApplicationManager

from PyQt4 import QtGui
from PyQt4 import QtCore
from dropbox import rest
import puremvc.interfaces
import puremvc.patterns.mediator
from astakosclient.errors import Unauthorized
from astakosclient.errors import AstakosClientException
from oauth2client.client import FlowExchangeError

#http://tinyurl.com/3pwv5u4
class VerifyThread(QtCore.QThread):
    def __init__(self, flow, auth_code, service):
        QtCore.QThread.__init__(self)

        self.flow = flow
        self.service = service
        self.auth_code = auth_code
        self.logger = logger.logger_factory(self.__class__.__name__)

    def run(self):
        try:
            r = self.flow.finish(self.auth_code)
        except (rest.ErrorResponse, FlowExchangeError, Unauthorized) as e:
            self.emit(QtCore.SIGNAL('done'), 'Error', [self.service, 'Invalid Code'])
        except (rest.RESTSocketError, httplib2.ServerNotFoundError, AstakosClientException) as e:
            self.emit(QtCore.SIGNAL('done'), 'Error', [self.service, 'Network Error'])
        except Exception as e:
            self.emit(QtCore.SIGNAL('done'), 'Error', [self.service, 'Unknown'])
        else:
            self.emit(QtCore.SIGNAL('done'), 'Success', [self.service, r])

def update_compact(f):
    def wrapper(*args):
        f(*args)
        args[0].proxy.facade.sendNotification(AppFacade.AppFacade.COMPACT_SET_STATE,
                                              args[0].viewComponent.get_states())
    return wrapper

class DetailedWindowMediator(puremvc.patterns.mediator.Mediator, puremvc.interfaces.IMediator):

    NAME = 'DetailedWindowMediator'

    def __init__(self, viewComponent):
        super(DetailedWindowMediator, self).__init__(DetailedWindowMediator.NAME, viewComponent)

        self.proxy = self.facade.retrieveProxy(model.modelProxy.ModelProxy.NAME)
        self.g = globals.get_globals()
        self.f = None #File chooser

        buttons = ['add', 'remove', 'play', 'stop']
        methods = [self.onAdd, self.onRemove, self.onPlay, self.onStop]
        for item in zip(buttons, methods):
            QtCore.QObject.connect(getattr(viewComponent, item[0] + 'Btn'), QtCore.SIGNAL('clicked()'),
                                   item[1], QtCore.Qt.QueuedConnection)

        self.viewComponent.clear_uploads()
        self.viewComponent.update_all_history(self._format_history())

        self.g.signals.network_error.connect(self.onNetworkError)
        self.g.signals.invalid_credentials.connect(self.onInvalidCredentials)

    @update_compact
    def onNetworkError(self, id):
        self.viewComponent.update_item_status([id, strings.network_error])

    @update_compact
    def onInvalidCredentials(self, id):
        self.viewComponent.update_item_status([id, strings.invalid_credentials])

    def listNotificationInterests(self):
        return [
            AppFacade.AppFacade.SERVICE_ADD,
        ]

    def handleNotification(self, notification):
        note_name = notification.getName()
        body = notification.getBody()
        if note_name == AppFacade.AppFacade.SERVICE_ADD:
            self.viewComponent.show_accounts()
            if not self.viewComponent.isVisible():
                self.viewComponent.setVisible(True)

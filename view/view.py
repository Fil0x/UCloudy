import os
import sys
import copy
import httplib2
import datetime
import webbrowser
from operator import itemgetter
if ".." not in sys.path:
    sys.path.append("..")

import logger
import strings
import globals
import AppFacade
import model.modelProxy
from lib.util import raw
from lib.Authentication import AuthManager
from lib.ApplicationManager import ApplicationManager

from PyQt4 import QtGui
from PyQt4 import QtCore
import puremvc.interfaces
import puremvc.patterns.mediator
from astakosclient.errors import Unauthorized
from astakosclient.errors import AstakosClientException

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

class MainWindowMediator(puremvc.patterns.mediator.Mediator, puremvc.interfaces.IMediator):

    NAME = 'MainWindowMediator'

    def __init__(self, viewComponent):
        super(MainWindowMediator, self).__init__(MainWindowMediator.NAME, viewComponent)

        self.proxy = self.facade.retrieveProxy(model.modelProxy.ModelProxy.NAME)
        self.g = globals.get_globals()

        self.viewComponent.exit_action.triggered.connect(self.onExit)

        self.g.signals.set_folders.connect(self.onSetFolders)

    def onSetFolders(self, folders):
        self.viewComponent.set_folders(folders)

    def onExit(self):
        self.facade.sendNotification(AppFacade.AppFacade.EXIT)
        
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

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
        except Unauthorized as e:
            self.emit(QtCore.SIGNAL('done'), 'Error', [self.service, 'Invalid Code'])
        except AstakosClientException as e:
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
        self.logger = logger.logger_factory(self.__class__.__name__)
        self.g = globals.get_globals()

        self.viewComponent.exit_action.triggered.connect(self.onExit)
        self.viewComponent.rename_signal.connect(self.onRename)
        self.viewComponent.delete_signal.connect(self.onDelete)
        self.viewComponent.move_signal.connect(self.onMove)

        self.g.signals.rename_completed.connect(self.onRenameComplete)
        self.g.signals.delete_completed.connect(self.onDeleteComplete)
        self.g.signals.move_completed.connect(self.onMoveComplete)
        self.g.signals.set_folders.connect(self.onSetFolders)
        self.g.signals.set_objects.connect(self.onSetObjects)
        self.g.signals.set_active_folder.connect(self.onSetActiveFolder)

    def onRenameComplete(self):
        self.viewComponent.onRenameComplete()
        
    def onDeleteComplete(self):
        self.viewComponent.onDeleteComplete()
        
    def onMoveComplete(self):
        self.viewComponent.onMoveComplete()
        
    def onSetFolders(self, data):
        #data = [[folder1, folder2, ...], username]
        self.viewComponent.set_folders(data)
        
    def onSetObjects(self, data):
        #data = [[folder_name, objects],...]
        self.viewComponent.set_objects(*data)
        
    def onSetActiveFolder(self):
        self.viewComponent.set_active_folder()

    def onRename(self, data):
        #data = [container, old-filename, new-filename]
        self.facade.sendNotification(AppFacade.AppFacade.RENAME_FILE, data)
        
    def onDelete(self, filename):
        folder = str(self.viewComponent.comboBox.currentText())
        self.facade.sendNotification(AppFacade.AppFacade.DELETE_FILE, 
                                     [folder, filename])
        
    def onMove(self, data):
        #data = [new-folder, filename]
        old_folder = str(self.viewComponent.comboBox.currentText())
        self.facade.sendNotification(AppFacade.AppFacade.MOVE_FILE, 
                                     [old_folder, data[0], data[1]])
        
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

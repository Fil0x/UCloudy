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

class SettingsMediator(puremvc.patterns.mediator.Mediator, puremvc.interfaces.IMediator):

    NAME = 'SettingsMediator'
    error_msg = r'Error: {}'

    def __init__(self, viewComponent):
        super(SettingsMediator, self).__init__(SettingsMediator.NAME, viewComponent)
        self.proxy = self.facade.retrieveProxy(model.modelProxy.ModelProxy.NAME)

        self.service_flows = {}
        self.verify_threads = {}

        self.viewComponent.general_page.saveSignal.connect(self.onGeneralSettingsSave)

        for s in local.services:
            self.viewComponent.accounts_page.notauth_panels[s].authorizeSignal.connect(self.onAuthorizeClicked)
            self.viewComponent.accounts_page.notauth_panels[s].verifySignal.connect(self.onVerifyClicked)
            self.viewComponent.accounts_page.auth_panels[s].removeSignal.connect(self.onRemoveClicked)
            self.viewComponent.accounts_page.auth_panels[s].saveSignal.connect(self.onSaveClicked)

    def onGeneralSettingsSave(self, settings):
        p = ApplicationManager()
        p.set_general_settings(settings)

        self.proxy.facade.sendNotification(AppFacade.AppFacade.SETTINGS_HISTORY_CLOSE_ON_SHARE,
                                           settings[strings.popup_checkbox])
        self.proxy.facade.sendNotification(AppFacade.AppFacade.SETTINGS_DETAILED_MINIMIZE_ON_CLOSE,
                                           settings[strings.close_checkbox])

    def onSaveClicked(self, service, new_folder):
        self.proxy.set_service_root(str(service), str(new_folder))

    def onRemoveClicked(self, service):
        service = str(service)
        self.proxy.delete_service_credentials(service)
        self.viewComponent.remove_service(service)
        self.proxy.facade.sendNotification(AppFacade.AppFacade.SERVICE_REMOVED, service)

    def onVerifyClicked(self, service, auth_code):
        v = VerifyThread(self.service_flows[str(service)], str(auth_code), service)
        QtCore.QObject.connect(v, QtCore.SIGNAL('done'), self.onVerifyFinished, QtCore.Qt.QueuedConnection)
        self.verify_threads[str(service)] = v
        v.start()

        #del self.service_flows[str(service)]

    def onVerifyFinished(self, result, details):
        service = str(details[0])
        self.verify_threads[service].wait() #Please don't wait for too long.
        del self.verify_threads[service]
        if result == 'Success':
            self.proxy.add_service_credentials(service, details[1])
            self.viewComponent.add_service(service)
            self.proxy.facade.sendNotification(AppFacade.AppFacade.SERVICE_ADDED, service)
        else:
            self.viewComponent.reset(service, self.error_msg.format(details[1]))

    def onAuthorizeClicked(self, service):
        flow = getattr(AuthManager(), 'get_flow')(str(service))
        webbrowser.open(flow.start())
        self.service_flows[str(service)] = flow

class SysTrayMediator(puremvc.patterns.mediator.Mediator, puremvc.interfaces.IMediator):

    NAME = 'SysTrayMediator'

    def __init__(self, viewComponent):
        super(SysTrayMediator, self).__init__(SysTrayMediator.NAME, viewComponent)

        actions = ['recentAction', 'exitAction', 'openAction', 'settingsAction', 'accountsAction']
        methods = [self.onActivate, self.onExit, self.onOpen, self.onSettings, self.onAddAccount]
        for item in zip(actions, methods):
            QtCore.QObject.connect(getattr(viewComponent, item[0]), QtCore.SIGNAL('triggered()'),
                               item[1], QtCore.Qt.QueuedConnection)
        viewComponent.activated.connect(self.onActivate)
        viewComponent.messageClicked.connect(self.onMessageClicked)

    def onActivate(self, reason=''):
        if not reason or reason == QtGui.QSystemTrayIcon.Trigger:
            self.facade.sendNotification(AppFacade.AppFacade.HISTORY_SHOW_COMPACT,
                                         [globals.get_globals()])

    def onMessageClicked(self):
        self.facade.sendNotification(AppFacade.AppFacade.SERVICE_ADD)

    def onOpen(self):
        self.facade.sendNotification(AppFacade.AppFacade.TOGGLE_DETAILED)

    def onSettings(self):
        self.facade.sendNotification(AppFacade.AppFacade.SHOW_SETTINGS)

    def onAddAccount(self):
        self.facade.sendNotification(AppFacade.AppFacade.SERVICE_ADD)

    def onExit(self):
        self.facade.sendNotification(AppFacade.AppFacade.EXIT)

class CompactWindowMediator(puremvc.patterns.mediator.Mediator, puremvc.interfaces.IMediator):

    NAME = 'CompactWindowMediator'

    def __init__(self, viewComponent):
        super(CompactWindowMediator, self).__init__(CompactWindowMediator.NAME, viewComponent)
        self.proxy = self.facade.retrieveProxy(model.modelProxy.ModelProxy.NAME)

        p = ApplicationManager()
        for s in p.get_services():
            self.viewComponent.items[s].droppedSignal.connect(self.onDrop)
        self.viewComponent.setVisible(True)

    def onDrop(self, data):
        m = data[1]
        if m.hasUrls() and len(m.urls()) < 4:
            for url in m.urls():
                p = raw(url.toLocalFile())
                if os.path.isfile(p):
                    self.proxy.add_file(data[0], str(p))

    def get_window_info(self):
        return self.viewComponent.get_window_info()

    def listNotificationInterests(self):
        return [
            AppFacade.AppFacade.COMPACT_SET_STATE,
            AppFacade.AppFacade.SERVICE_REMOVED,
            AppFacade.AppFacade.SERVICE_ADDED
        ]

    def handleNotification(self, notification):
        note_name = notification.getName()
        body = notification.getBody()
        if note_name == AppFacade.AppFacade.COMPACT_SET_STATE:
            self.viewComponent.set_service_states(body)
        elif note_name == AppFacade.AppFacade.SERVICE_ADDED:
            self.viewComponent.add_item(body)
            self.viewComponent.items[body].droppedSignal.connect(self.onDrop)
        elif note_name == AppFacade.AppFacade.SERVICE_REMOVED:
            self.viewComponent.remove_item(body)

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

        self.g.signals.history_detailed.connect(self.onHistoryAdd)
        self.g.signals.history_detailed_delete.connect(self.onHistoryDelete)
        self.g.signals.upload_detailed_starting.connect(self.onUploadStarting)
        self.g.signals.upload_detailed_start.connect(self.onUploadStart)
        self.g.signals.upload_detailed_update.connect(self.onUploadUpdate)
        self.g.signals.upload_detailed_finish.connect(self.onUploadComplete)
        self.g.signals.upload_detailed_pausing.connect(self.onUploadPausing)
        self.g.signals.upload_detailed_paused.connect(self.onUploadPaused)
        self.g.signals.upload_detailed_resuming.connect(self.onUploadResuming)
        self.g.signals.upload_detailed_resumed.connect(self.onUploadResumed)
        self.g.signals.upload_detailed_removing.connect(self.onUploadRemoving)
        self.g.signals.upload_detailed_removed.connect(self.onUploadRemoved)

        self.g.signals.network_error.connect(self.onNetworkError)
        self.g.signals.file_not_found.connect(self.onFileNotFound)
        self.g.signals.invalid_credentials.connect(self.onInvalidCredentials)
        self.g.signals.out_of_storage.connect(self.onOutOfStorage)

    def get_window_info(self):
        return self.viewComponent.get_window_info()

    @update_compact
    def onUploadStarting(self, body):
        self.viewComponent.add_upload_item(body)

    @update_compact
    def onUploadStart(self, body):
        self.viewComponent.update_remote_path(body)
        self.viewComponent.update_item_status([body[0], 'Running'])

    def onUploadUpdate(self, body):
        self.viewComponent.update_upload_item(body)

    @update_compact
    def onUploadComplete(self, id):
        self.viewComponent.delete_upload_item(id)

    @update_compact
    def onUploadPausing(self, id):
        self.viewComponent.update_item_status([id, 'Pausing'])

    @update_compact
    def onUploadPaused(self, id):
        self.viewComponent.update_item_status([id, 'Paused'])

    @update_compact
    def onUploadResuming(self, id):
        self.viewComponent.update_item_status([id, 'Resuming'])

    @update_compact
    def onUploadResumed(self, id):
        self.viewComponent.update_item_status([id, 'Running'])

    @update_compact
    def onUploadRemoving(self, id):
        self.viewComponent.update_item_status([id, 'Removing'])

    @update_compact
    def onUploadRemoved(self, id):
        self.viewComponent.delete_upload_item(id)

    def onHistoryAdd(self, body):
        self.viewComponent.add_history_item([body[2]['name'], body[2]['path'],
                                             (body[0], body[2]['link']), body[2]['date'], body[1]])

    def onHistoryDelete(self, body):
        self.viewComponent.delete_history_item(body)

    @update_compact
    def onNetworkError(self, id):
        self.viewComponent.update_item_status([id, strings.network_error])

    @update_compact
    def onFileNotFound(self, id):
        self.viewComponent.update_item_status([id, strings.file_not_found])

    @update_compact
    def onInvalidCredentials(self, id):
        self.viewComponent.update_item_status([id, strings.invalid_credentials])

    @update_compact
    def onOutOfStorage(self, id):
        self.viewComponent.update_item_status([id, strings.out_of_quota])

    def _format_history(self):
        l = []
        r = self.proxy.get_history()
        for k, v in r.iteritems():
            for id, item in v.iteritems():
                l.append([item['name'], item['path'], (k, item['link']), item['date'], id])
        return sorted(l, key=itemgetter(3))

    def onAdd(self):
        p = ApplicationManager()
        if not p.get_services():
            self.viewComponent.show_add_file_warning()
            return

        if not self.f:
            self.f = FileChooser(p.get_services(), self.viewComponent)
            self.f.okButton.clicked.connect(self.onFileDialogOK)
            self.f.cancelButton.clicked.connect(self.onFileDialogCancel)
            self.f.closeEvent = self.onFileDialogCancel
            self.f.show()
        else:
            self.f.activateWindow()

    def onFileDialogOK(self, event):
        paths = self.f.get_filenames()
        service = str(self.f.get_selected_service())

        self.f.close()
        self.f = None

        #TODO: Limit the uploaded files.
        for p in paths:
            self.proxy.add_file(service, p)

    def onFileDialogCancel(self, event):
        self.f.close()
        self.f = None

    def onPlay(self):
        items = self.viewComponent.get_selected_ids(0)

        if not items:
            return

        play = copy.copy(items)
        for d in items:
            state = self.proxy.get_status(d[1], d[0])
            if state == 'Error-2':
                data = self.proxy.get(d[1], d[0])
                if 'error' in data:
                    path = data['path']
                else:
                    path = data['uploader'].path

                try:
                    with open(path, 'rb'):
                        continue
                except IOError:
                    play.remove(d)
            elif state == 'Error-12':
                pass
            elif state == 'Error-22':
                pass
            elif state != 'Paused':
                play.remove(d)

        if len(play):
            self.proxy.resume_file(play)

    def onRemove(self):
        index = self.viewComponent.get_current_tab()
        #[[id, service],..]
        items = self.viewComponent.get_selected_ids(index)

        if not items:
            return

        delete = copy.copy(items)
        if index == 0:
            for d in items:
                state = self.proxy.get_status(d[1], d[0])
                if state not in ['Paused', 'Running'] and 'Error' not in state:
                    delete.remove(d)

            if len(delete):
                self.proxy.delete_file(delete)
        elif index == 1:
            self.proxy.delete_history(delete)

    def onStop(self):
        items = self.viewComponent.get_selected_ids(0)

        if not items:
            return

        stop = copy.copy(items)
        for d in items:
            state = self.proxy.get_status(d[1], d[0])
            if state != 'Running':
                stop.remove(d)

        if len(stop):
            self.proxy.stop_file(stop)

    def listNotificationInterests(self):
        return [
            AppFacade.AppFacade.TOGGLE_DETAILED,
            AppFacade.AppFacade.SHOW_SETTINGS,
            AppFacade.AppFacade.SERVICE_ADD,
            AppFacade.AppFacade.SETTINGS_DETAILED_MINIMIZE_ON_CLOSE
        ]

    def handleNotification(self, notification):
        note_name = notification.getName()
        body = notification.getBody()
        if note_name == AppFacade.AppFacade.TOGGLE_DETAILED:
            self.viewComponent.setVisible(not self.viewComponent.isVisible())
        elif note_name == AppFacade.AppFacade.SHOW_SETTINGS:
            self.viewComponent.show_settings()
            if not self.viewComponent.isVisible():
                self.viewComponent.setVisible(True)
        elif note_name == AppFacade.AppFacade.SERVICE_ADD:
            self.viewComponent.show_accounts()
            if not self.viewComponent.isVisible():
                self.viewComponent.setVisible(True)
        elif note_name == AppFacade.AppFacade.SETTINGS_DETAILED_MINIMIZE_ON_CLOSE:
            self.viewComponent.minimize_on_close = body

class HistoryWindowMediator(puremvc.patterns.mediator.Mediator, puremvc.interfaces.IMediator):

    NAME = 'HistoryWindowMediator'

    def __init__(self, viewComponent):
        super(HistoryWindowMediator, self).__init__(HistoryWindowMediator.NAME, viewComponent)

        self.proxy = self.facade.retrieveProxy(model.modelProxy.ModelProxy.NAME)
        self.g = globals.get_globals()

        self.logger = logger.logger_factory(self.__class__.__name__)
        #To avoid the constant reading from the disk.
        self.initialized = False

        self.g.signals.history_compact_show.connect(self.onShow)
        self.g.signals.history_compact_update.connect(self.onAdd)
        self.g.signals.history_compact_delete.connect(self.onDelete)

    def listNotificationInterests(self):
        return [AppFacade.AppFacade.SETTINGS_HISTORY_CLOSE_ON_SHARE]

    def handleNotification(self, notification):
        note_name = notification.getName()
        body = notification.getBody()
        if note_name == AppFacade.AppFacade.SETTINGS_HISTORY_CLOSE_ON_SHARE:
            self.viewComponent.close_on_share = body

    def onDelete(self):
        if self.viewComponent.isVisible():
            self.viewComponent.update_all(self._format_history())

    def _format_history(self):
        l = []
        r = self.proxy.get_history()
        for k, v in r.iteritems():
            for id, item in v.iteritems():
                l.append([k, item['name'], item['link'], item['date']])
        return sorted(l, key=itemgetter(3))

    def onShow(self):
        if not self.viewComponent.isVisible():
            self.viewComponent.update_all(self._format_history())
            self.viewComponent.setVisible(True)
            self.initialized = True
        else:
            self.viewComponent.setVisible(False)

    def onAdd(self, body):
        if self.initialized:
            self.viewComponent.add_item(body[0], body[1]['name'],
                                        body[1]['link'], body[1]['date'])
        else:
            self.viewComponent.update_all(self._format_history())
            self.initialized = True
        if not self.viewComponent.isVisible():
            self.viewComponent.setVisible(True)

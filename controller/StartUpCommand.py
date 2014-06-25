import sys
if ".." not in sys.path:
    sys.path.append("..")

import strings
import version
import AppFacade
import model.modelProxy
from view.Settings import Settings
from view.view import SysTrayMediator
from view.History import HistoryWindow
from view.Compact import CompactWindow
from view.view import SettingsMediator
from view.Detailed import DetailedWindow
from view.view import CompactWindowMediator
from view.view import HistoryWindowMediator
from view.view import DetailedWindowMediator
from lib.ApplicationManager import ApplicationManager

import puremvc.patterns
import puremvc.patterns.command


class StartUpCommand(puremvc.patterns.command.SimpleCommand, puremvc.interfaces.ICommand):

    no_service_title = 'Cloudy: No services active'
    no_service_body = r'You are not using any service, click here to activate them or ' + \
                       'right-click on the tray icon and click "Account Settings".'

    def execute(self, notification):
        proxy = model.modelProxy.ModelProxy()
        self.facade.registerProxy(proxy)

        # self.facade.registerMediator(SysTrayMediator(systray))

        p = ApplicationManager()

        service_folders = proxy.get_service_folders(used_services)

        self.facade.sendNotification(AppFacade.AppFacade.SETTINGS_DETAILED_MINIMIZE_ON_CLOSE,
                                     stored_settings[strings.close_checkbox])

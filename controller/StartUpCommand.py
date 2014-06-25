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
        systray = notification.getBody()

        self.facade.registerMediator(SysTrayMediator(systray))
        self.facade.registerMediator(HistoryWindowMediator(HistoryWindow()))

        p = ApplicationManager()

        used_services = p.get_services()
        service_folders = proxy.get_service_folders(used_services)

        if not used_services:
            systray.show_message(self.no_service_title, self.no_service_body, duration=5000)

        stored_settings = p.get_general_settings()
        s = Settings(used_services, service_folders, stored_settings)
        self.facade.registerMediator(SettingsMediator(s))

        #TODO:The compact window must not have a taskbar entry, the solution to this is to draw it
        #through a dummy parent widget that is never shown.
        c = CompactWindow(p.get_services(), p.get_orientation(),
                          p.get_pos('Compact'), 0)
        self.facade.registerMediator(CompactWindowMediator(c))

        d = DetailedWindow(version.__version__, p.get_pos('Detailed'),
                           p.get_size(), p.get_maximized(), 0, s)
        self.facade.registerMediator(DetailedWindowMediator(d))

        #Initialize the UI components to behave according to the stored settings.
        self.facade.sendNotification(AppFacade.AppFacade.SETTINGS_HISTORY_CLOSE_ON_SHARE,
                                     stored_settings[strings.popup_checkbox])
        self.facade.sendNotification(AppFacade.AppFacade.SETTINGS_DETAILED_MINIMIZE_ON_CLOSE,
                                     stored_settings[strings.close_checkbox])

        proxy.start_uploads()
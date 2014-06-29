import sys
if ".." not in sys.path:
    sys.path.append("..")

import strings
import version
import AppFacade
import model.modelProxy
from view.Settings import Settings
from view.MainWindow import MainWindow
from view.view import MainWindowMediator
from lib.ApplicationManager import ApplicationManager

import puremvc.patterns
import puremvc.patterns.command


class StartUpCommand(puremvc.patterns.command.SimpleCommand, puremvc.interfaces.ICommand):

    def execute(self, notification):
        proxy = model.modelProxy.ModelProxy()
        self.facade.registerProxy(proxy)

        d = MainWindow(version.__version__)
        self.facade.registerMediator(MainWindowMediator(d))

        proxy.initialize()

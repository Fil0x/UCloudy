import sys
if ".." not in sys.path:
    sys.path.append("..")

import model.modelProxy
from view.view import CompactWindowMediator
from view.view import DetailedWindowMediator
from lib.ApplicationManager import ApplicationManager

from PyQt4 import QtCore
import puremvc.patterns
import puremvc.patterns.command


class ExitAppCommand(puremvc.patterns.command.SimpleCommand, puremvc.interfaces.ICommand):
    def execute(self, notification):
        self.facade.retrieveProxy(model.modelProxy.ModelProxy.NAME).save()
        
        p = ApplicationManager()
        
        QtCore.QCoreApplication.instance().quit()
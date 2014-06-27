import sys
if ".." not in sys.path:
    sys.path.append("..")

import model.modelProxy
from view.view import MainWindowMediator
from lib.ApplicationManager import ApplicationManager

from PyQt4 import QtCore
import puremvc.patterns
import puremvc.patterns.command


class ExitAppCommand(puremvc.patterns.command.SimpleCommand, puremvc.interfaces.ICommand):
    def execute(self, notification):
        #self.facade.retrieveProxy(model.modelProxy.ModelProxy.NAME).save()
        
        QtCore.QCoreApplication.instance().quit()
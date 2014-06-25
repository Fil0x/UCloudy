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
        compact_info = self.facade.retrieveMediator(CompactWindowMediator.NAME).get_window_info()
        detailed_info = self.facade.retrieveMediator(DetailedWindowMediator.NAME).get_window_info()
        
        p.set_pos('Compact', compact_info[0])
        p.set_screen_id('Compact', compact_info[1])
        p.set_orientation(compact_info[2])
        
        p.set_pos('Detailed', detailed_info[0])
        p.set_size(detailed_info[1])
        p.set_maximized(detailed_info[2])
        p.set_screen_id('Detailed', detailed_info[3])
        
        QtCore.QCoreApplication.instance().quit()
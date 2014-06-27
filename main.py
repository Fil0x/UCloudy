import sys
from PyQt4 import QtGui

from AppFacade import AppFacade

if __name__ == '__main__':
    qtApp = QtGui.QApplication(sys.argv)

    app = AppFacade.getInstance()
    app.sendNotification(AppFacade.STARTUP)

    sys.exit(qtApp.exec_())
import os
import operator
from PyQt4 import QtCore, QtGui, Qt

class MainWindow(QtGui.QMainWindow):

    font = QtGui.QFont('Tahoma', 10)

    def __init__(self, title):
        QtGui.QWidget.__init__(self)

        self.setWindowTitle(title)
        self.setFixedSize(300, 400)

        self._create_menu_bar()
        self._create_status_bar()

    def _create_menu_bar(self):
        #Get QMainWindow's predefined menu bar
        menu_bar = self.menuBar()
        #File menu
        #@Mediator
        self.exit_action = QtGui.QAction('&Exit', self)
        self.exit_action.setShortcut('Ctrl+Q')
        self.exit_action.setStatusTip('Exit application')

        file_menu = menu_bar.addMenu('&File')
        file_menu.addAction(self.exit_action)

    def _create_status_bar(self):
        sb = QtGui.QStatusBar()
        sb.addWidget(QtGui.QLabel('asd'), 1)
        self.setStatusBar(sb)

from PyQt4 import QtCore

class Signals(QtCore.QObject):
    network_error = QtCore.pyqtSignal(str)
    out_of_storage = QtCore.pyqtSignal(str)
    service_offline = QtCore.pyqtSignal(str)
    invalid_credentials = QtCore.pyqtSignal(str)
    file_not_found = QtCore.pyqtSignal(str)

class Globals(object):
    def __init__(self):
        self.signals = Signals()

def get_globals(_singleton=Globals()):
    return _singleton

from PyQt4 import QtCore

class Signals(QtCore.QObject):
    history_compact_show = QtCore.pyqtSignal()
    history_compact_update = QtCore.pyqtSignal(list)
    history_compact_delete = QtCore.pyqtSignal()
    history_detailed = QtCore.pyqtSignal(list)
    history_detailed_delete = QtCore.pyqtSignal(str)

    upload_detailed_start = QtCore.pyqtSignal(list)
    upload_detailed_update = QtCore.pyqtSignal(list)
    upload_detailed_finish = QtCore.pyqtSignal(str)
    upload_detailed_pausing = QtCore.pyqtSignal(str)
    upload_detailed_paused = QtCore.pyqtSignal(str)
    upload_detailed_starting = QtCore.pyqtSignal(list)
    upload_detailed_resuming = QtCore.pyqtSignal(str)
    upload_detailed_resumed = QtCore.pyqtSignal(str)
    upload_detailed_removing = QtCore.pyqtSignal(str)
    upload_detailed_removed = QtCore.pyqtSignal(str)

    network_error = QtCore.pyqtSignal(str)
    out_of_storage = QtCore.pyqtSignal(str)
    service_offline = QtCore.pyqtSignal(str)
    invalid_credentials = QtCore.pyqtSignal(str)
    upload_expired = QtCore.pyqtSignal(str)
    file_not_found = QtCore.pyqtSignal(str)

class Globals(object):
    def __init__(self):
        self.signals = Signals()

def get_globals(_singleton=Globals()):
    return _singleton

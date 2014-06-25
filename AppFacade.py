import puremvc.patterns.facade
from controller.ErrorCommand import ErrorCommand
from controller.UploadCommand import UploadCommand
from controller.StartUpCommand import StartUpCommand
from controller.ExitAppCommand import ExitAppCommand
from controller.HistoryCommand import HistoryCommand


class AppFacade(puremvc.patterns.facade.Facade):
    STARTUP = 'startup'
    EXIT = 'exit'

    SERVICE_ADD = 'service_add'
    SERVICE_ADDED = 'service_added'
    SERVICE_REMOVED = 'service_removed'
    
    NETWORK_ERROR = 'network_error'
    OUT_OF_STORAGE = 'out_of_storage'
    SERVICE_OFFLINE = 'service_offline'
    FILE_NOT_FOUND = 'file_not_found'
    UPLOAD_EXPIRED = 'upload_expired'
    INVALID_CREDENTIALS = 'invalid_credentials'

    def __init__(self):
        self.initializeFacade()

    @staticmethod
    def getInstance():
        return AppFacade()

    def initializeFacade(self):
        super(AppFacade, self).initializeFacade()

        self.initializeController()

    def initializeController(self):
        super(AppFacade, self).initializeController()

        super(AppFacade, self).registerCommand(AppFacade.STARTUP, StartUpCommand)
        super(AppFacade, self).registerCommand(AppFacade.UPLOAD_REMOVED, UploadCommand)
        super(AppFacade, self).registerCommand(AppFacade.OUT_OF_STORAGE, ErrorCommand)
        super(AppFacade, self).registerCommand(AppFacade.SERVICE_OFFLINE, ErrorCommand)
        super(AppFacade, self).registerCommand(AppFacade.INVALID_CREDENTIALS, ErrorCommand)
        super(AppFacade, self).registerCommand(AppFacade.FILE_NOT_FOUND, ErrorCommand)
        super(AppFacade, self).registerCommand(AppFacade.EXIT, ExitAppCommand)

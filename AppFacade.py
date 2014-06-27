import puremvc.patterns.facade
from controller.ErrorCommand import ErrorCommand
from controller.UploadCommand import UploadCommand
from controller.StartUpCommand import StartUpCommand
from controller.ExitAppCommand import ExitAppCommand


class AppFacade(puremvc.patterns.facade.Facade):
    STARTUP = 'startup'
    EXIT = 'exit'

    SHOW_SETTINGS = 'show_settings'
    
    SERVICE_ADD = 'service_add'
    SERVICE_ADDED = 'service_added'
    SERVICE_REMOVED = 'service_removed'
    
    NETWORK_ERROR = 'network_error'
    SERVICE_OFFLINE = 'service_offline'
    FILE_NOT_FOUND = 'file_not_found'
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
        super(AppFacade, self).registerCommand(AppFacade.NETWORK_ERROR, ErrorCommand)
        super(AppFacade, self).registerCommand(AppFacade.SERVICE_OFFLINE, ErrorCommand)
        super(AppFacade, self).registerCommand(AppFacade.INVALID_CREDENTIALS, ErrorCommand)
        super(AppFacade, self).registerCommand(AppFacade.FILE_NOT_FOUND, ErrorCommand)
        super(AppFacade, self).registerCommand(AppFacade.EXIT, ExitAppCommand)

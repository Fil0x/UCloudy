import puremvc.patterns.facade
from controller.StartUpCommand import StartUpCommand
from controller.CommCommand import CommCommand
from controller.ErrorCommand import ErrorCommand
from controller.ExitAppCommand import ExitAppCommand


class AppFacade(puremvc.patterns.facade.Facade):
    STARTUP = 'startup'

    SET_FOLDERS = 'set_ui_folders'
    SET_OBJECTS = 'set_ui_objects_per_folder' 
    SET_ACTIVE_FOLDER = 'set_ui_active_folder'
    
    SHOW_SETTINGS = 'show_settings'

    SERVICE_ADD = 'service_add'
    SERVICE_ADDED = 'service_added'
    SERVICE_REMOVED = 'service_removed'

    NETWORK_ERROR = 'network_error'
    SERVICE_OFFLINE = 'service_offline'
    FILE_NOT_FOUND = 'file_not_found'
    INVALID_CREDENTIALS = 'invalid_credentials'
    
    EXIT = 'exit'

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

        super(AppFacade, self).registerCommand(AppFacade.SET_FOLDERS, CommCommand)
        super(AppFacade, self).registerCommand(AppFacade.SET_OBJECTS, CommCommand)
        super(AppFacade, self).registerCommand(AppFacade.SET_ACTIVE_FOLDER, CommCommand)

        super(AppFacade, self).registerCommand(AppFacade.NETWORK_ERROR, ErrorCommand)
        super(AppFacade, self).registerCommand(AppFacade.SERVICE_OFFLINE, ErrorCommand)
        super(AppFacade, self).registerCommand(AppFacade.INVALID_CREDENTIALS, ErrorCommand)
        super(AppFacade, self).registerCommand(AppFacade.FILE_NOT_FOUND, ErrorCommand)

        super(AppFacade, self).registerCommand(AppFacade.EXIT, ExitAppCommand)

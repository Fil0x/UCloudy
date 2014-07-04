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
    
    RENAME_FILE = 'ui_rename_file'
    RENAME_FILE_COMPLETED = 'ui_rename_file_completed'
    DELETE_FILE = 'ui_delete_file'
    DELETE_FILE_COMPLETED = 'ui_delete_file_completed'
    MOVE_FILE = 'ui_move_file'
    MOVE_FILE_COMPLETED = 'ui_move_file_completed'

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
        
        super(AppFacade, self).registerCommand(AppFacade.RENAME_FILE, CommCommand)
        super(AppFacade, self).registerCommand(AppFacade.RENAME_FILE_COMPLETED, CommCommand)
        super(AppFacade, self).registerCommand(AppFacade.DELETE_FILE, CommCommand)
        super(AppFacade, self).registerCommand(AppFacade.DELETE_FILE_COMPLETED, CommCommand)
        super(AppFacade, self).registerCommand(AppFacade.MOVE_FILE, CommCommand)
        super(AppFacade, self).registerCommand(AppFacade.MOVE_FILE_COMPLETED, CommCommand)

        super(AppFacade, self).registerCommand(AppFacade.NETWORK_ERROR, ErrorCommand)
        super(AppFacade, self).registerCommand(AppFacade.SERVICE_OFFLINE, ErrorCommand)
        super(AppFacade, self).registerCommand(AppFacade.INVALID_CREDENTIALS, ErrorCommand)
        super(AppFacade, self).registerCommand(AppFacade.FILE_NOT_FOUND, ErrorCommand)

        super(AppFacade, self).registerCommand(AppFacade.EXIT, ExitAppCommand)

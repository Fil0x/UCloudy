import puremvc.patterns.facade
from controller.ErrorCommand import ErrorCommand
from controller.UploadCommand import UploadCommand
from controller.StartUpCommand import StartUpCommand
from controller.ExitAppCommand import ExitAppCommand
from controller.HistoryCommand import HistoryCommand


class AppFacade(puremvc.patterns.facade.Facade):
    STARTUP = 'startup'
    EXIT = 'exit'

    TOGGLE_DETAILED = 'show_detailed'
    DELETE_HISTORY_DETAILED = 'delete_history_detailed'

    SHOW_COMPACT = 'show_compact'
    SHOW_SETTINGS = 'show_settings'
    DELETE_HISTORY_COMPACT = 'delete_history_compact'
    
    SETTINGS_HISTORY_CLOSE_ON_SHARE = 'settings_history_close_on_share'
    SETTINGS_DETAILED_MINIMIZE_ON_CLOSE = 'settings_detailed_minimize_on_close'

    COMPACT_SET_STATE = 'compact_set_state'

    HISTORY_SHOW_COMPACT = 'compact_show_history'
    HISTORY_UPDATE_COMPACT = 'compact_update_history'
    HISTORY_UPDATE_DETAILED = 'detailed_update_history'

    UPLOAD_DONE = 'upload_done'
    UPLOAD_PAUSED = 'upload_paused'
    UPLOAD_STARTED = 'upload_started'
    UPLOAD_UPDATED = 'upload_updated'
    UPLOAD_PAUSING = 'upload_pausing'
    UPLOAD_RESUMED = 'upload_resumed'
    UPLOAD_REMOVED = 'upload_removed'
    UPLOAD_STARTING = 'upload_starting'
    UPLOAD_RESUMING = 'upload_resuming'
    UPLOAD_REMOVING = 'upload_removing'
    
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
        super(AppFacade, self).registerCommand(AppFacade.HISTORY_UPDATE_COMPACT, HistoryCommand)
        super(AppFacade, self).registerCommand(AppFacade.HISTORY_UPDATE_DETAILED, HistoryCommand)
        super(AppFacade, self).registerCommand(AppFacade.HISTORY_SHOW_COMPACT, HistoryCommand)
        super(AppFacade, self).registerCommand(AppFacade.DELETE_HISTORY_COMPACT, HistoryCommand)
        super(AppFacade, self).registerCommand(AppFacade.DELETE_HISTORY_DETAILED, HistoryCommand)
        super(AppFacade, self).registerCommand(AppFacade.UPLOAD_STARTED, UploadCommand)
        super(AppFacade, self).registerCommand(AppFacade.UPLOAD_UPDATED, UploadCommand)
        super(AppFacade, self).registerCommand(AppFacade.UPLOAD_DONE, UploadCommand)
        super(AppFacade, self).registerCommand(AppFacade.UPLOAD_PAUSING, UploadCommand)
        super(AppFacade, self).registerCommand(AppFacade.UPLOAD_PAUSED, UploadCommand)
        super(AppFacade, self).registerCommand(AppFacade.UPLOAD_STARTING, UploadCommand)
        super(AppFacade, self).registerCommand(AppFacade.UPLOAD_RESUMING, UploadCommand)
        super(AppFacade, self).registerCommand(AppFacade.UPLOAD_RESUMED, UploadCommand)
        super(AppFacade, self).registerCommand(AppFacade.UPLOAD_REMOVING, UploadCommand)
        super(AppFacade, self).registerCommand(AppFacade.UPLOAD_REMOVED, UploadCommand)
        super(AppFacade, self).registerCommand(AppFacade.NETWORK_ERROR, ErrorCommand)
        super(AppFacade, self).registerCommand(AppFacade.OUT_OF_STORAGE, ErrorCommand)
        super(AppFacade, self).registerCommand(AppFacade.SERVICE_OFFLINE, ErrorCommand)
        super(AppFacade, self).registerCommand(AppFacade.INVALID_CREDENTIALS, ErrorCommand)
        super(AppFacade, self).registerCommand(AppFacade.FILE_NOT_FOUND, ErrorCommand)
        super(AppFacade, self).registerCommand(AppFacade.EXIT, ExitAppCommand)

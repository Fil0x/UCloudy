import model

import AppFacade
import puremvc.patterns
import puremvc.patterns.command

class ErrorCommand(puremvc.patterns.command.SimpleCommand, puremvc.interfaces.ICommand):
    def execute(self, notification):
        note_name = notification.getName()
        note_body = notification.getBody()                          #Error Codes
        if note_name == AppFacade.AppFacade.FILE_NOT_FOUND:         #2
            note_body[0].signals.file_not_found.emit(note_body[1])
        elif note_name == AppFacade.AppFacade.OUT_OF_STORAGE:       #3
            note_body[0].signals.out_of_storage.emit(note_body[1])
        elif note_name == AppFacade.AppFacade.UPLOAD_EXPIRED:       #4
            print note_name
        elif note_name == AppFacade.AppFacade.INVALID_CREDENTIALS:  #12
            note_body[0].signals.invalid_credentials.emit(note_body[1])
        elif note_name == AppFacade.AppFacade.SERVICE_OFFLINE:      #13
            print note_name
        elif note_name == AppFacade.AppFacade.NETWORK_ERROR:        #22
            note_body[0].signals.network_error.emit(note_body[1])

import model

import AppFacade
import puremvc.patterns
import puremvc.patterns.command

class ErrorCommand(puremvc.patterns.command.SimpleCommand, puremvc.interfaces.ICommand):
    def execute(self, notification):
        note_name = notification.getName()
        note_body = notification.getBody()                          #Error Codes
        if note_name == AppFacade.AppFacade.INVALID_CREDENTIALS:       #12
            note_body[0].signals.invalid_credentials.emit(note_body[1])
        elif note_name == AppFacade.AppFacade.SERVICE_OFFLINE:         #13
            print note_name
        elif note_name == AppFacade.AppFacade.NETWORK_ERROR:           #22
            note_body[0].signals.network_error.emit(note_body[1])

import AppFacade
import puremvc.patterns
import puremvc.patterns.command

class UploadCommand(puremvc.patterns.command.SimpleCommand, puremvc.interfaces.ICommand):
    def execute(self, notification):
        note_name = notification.getName()
        note_body = notification.getBody()
        if note_name == AppFacade.AppFacade.UPLOAD_STARTED:
            note_body[0].signals.upload_detailed_start.emit(note_body[1:])
        
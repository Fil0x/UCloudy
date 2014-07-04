import model.modelProxy

import AppFacade
import puremvc.patterns
import puremvc.patterns.command

class CommCommand(puremvc.patterns.command.SimpleCommand, puremvc.interfaces.ICommand):
    def execute(self, notification):
        model_proxy = self.facade.retrieveProxy(model.modelProxy.ModelProxy.NAME)
        note_name = notification.getName()
        note_body = notification.getBody()
        
        if note_name == AppFacade.AppFacade.SET_FOLDERS:
            note_body[0].signals.set_folders.emit(note_body[1])
        elif note_name == AppFacade.AppFacade.SET_OBJECTS:
            note_body[0].signals.set_objects.emit(note_body[1:])
        elif note_name == AppFacade.AppFacade.SET_ACTIVE_FOLDER:
            note_body[0].signals.set_active_folder.emit()
        elif note_name == AppFacade.AppFacade.RENAME_FILE:
            model_proxy.rename_file(note_body)
        elif note_name == AppFacade.AppFacade.RENAME_FILE_COMPLETED:
            note_body[0].signals.rename_completed.emit()
        
        

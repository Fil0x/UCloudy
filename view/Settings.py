import sys

import local
import strings

from PyQt4 import Qt
from PyQt4 import QtGui
from PyQt4 import QtCore


class GeneralPage(QtGui.QWidget):

    saveSignal = QtCore.pyqtSignal(dict)
    history_popup_label = r'Close History popup when a share link is clicked.'
    alwaysontop_label = r'Desktop widget always on top.'
    close_behaviour_label = r'Minimize Main window on pressing "Close(x)" button.'
    stopped_state_label = r'Add new files in the Paused state(add in queue, but do not upload).'

    def __init__(self, initial_settings, parent=None):
        QtGui.QWidget.__init__(self, parent)

        config_layout = QtGui.QVBoxLayout()
        upload_layout = QtGui.QVBoxLayout()
        buttons_layout = QtGui.QHBoxLayout()

        app_group = QtGui.QGroupBox("Application")
        upload_group = QtGui.QGroupBox("Upload Queue")
        
        self.popup_checkbox = QtGui.QCheckBox(self.history_popup_label)
        self.alwaysontop_checkbox = QtGui.QCheckBox(self.alwaysontop_label)
        self.close_checkbox = QtGui.QCheckBox(self.close_behaviour_label)
        self.stopped_checkbox = QtGui.QCheckBox(self.stopped_state_label)
        
        self.save_button = QtGui.QPushButton('Save')
        self.save_button.clicked.connect(self.onSaveClick)

        self.default_button = QtGui.QPushButton('Reset')
        self.default_button.clicked.connect(self.onDefaultClick)

        self.set_settings(initial_settings)

        config_layout.addWidget(self.alwaysontop_checkbox)
        config_layout.addWidget(self.popup_checkbox)
        config_layout.addWidget(self.close_checkbox)
        app_group.setLayout(config_layout)
        
        upload_layout.addWidget(self.stopped_checkbox)
        upload_group.setLayout(upload_layout)

        buttons_layout.addStretch(1)
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.default_button)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(app_group)
        mainLayout.addWidget(upload_group)
        mainLayout.addLayout(buttons_layout)
        mainLayout.addStretch(1)

        self.setLayout(mainLayout)

    def set_settings(self, settings):
        self.popup_checkbox.setChecked(settings[strings.popup_checkbox])
        self.alwaysontop_checkbox.setChecked(settings[strings.alwaysontop_checkbox])
        self.close_checkbox.setChecked(settings[strings.close_checkbox])
        self.stopped_checkbox.setChecked(settings[strings.stopped_checkbox])

    def get_settings(self):
        r = {}
        
        r[strings.popup_checkbox] = self.popup_checkbox.isChecked()
        r[strings.alwaysontop_checkbox] = self.alwaysontop_checkbox.isChecked()
        r[strings.close_checkbox] = self.close_checkbox.isChecked()
        r[strings.stopped_checkbox] = self.stopped_checkbox.isChecked()

        return r

    def onSaveClick(self, event):
        self.saveSignal.emit(self.get_settings())

    def onDefaultClick(self, event):
        self.alwaysontop_checkbox.setChecked(False)
        self.popup_checkbox.setChecked(False)
        self.close_checkbox.setChecked(False)
        self.stopped_checkbox.setChecked(False)

        self.saveSignal.emit(self.get_settings())

class AccountsPage(QtGui.QWidget):
    def __init__(self, used_services, service_folders, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.services = local.services
        self.used_services = used_services
        self.notauth_panels = {} #The key is the service.
        self.auth_panels = {} #The key is the service.

        mainLayout = QtGui.QVBoxLayout()
        for s in self.services:
            self.notauth_panels[s] = NotAuthorizedPanel(s)
            self.auth_panels[s] = getattr(sys.modules[__name__], '{}AuthorizedPanel'.format(s))(service_folders[s])
            setattr(self, '{}Group'.format(s.lower()), QtGui.QGroupBox(s))
            getattr(self, '{}Group'.format(s.lower())).setLayout(self._createServiceContent(s, True))
            mainLayout.addWidget(getattr(self, '{}Group'.format(s.lower())))
        mainLayout.addSpacing(12)
        mainLayout.addStretch(1)

        self.setLayout(mainLayout)

    def add_service(self, service):
        self.used_services.append(service)
        #self._clearLayout(service)
        self._createServiceContent(service)

    def remove_service(self, service):
        self.used_services.remove(service)
        #self._clearLayout(service)
        self._createServiceContent(service)

    def reset(self, service, msg):
        self.notauth_panels[service].reset(msg)

    #http://tinyurl.com/mcj4zpk
    def _clearLayout(self, service):
        layout = getattr(self, '{}Group'.format(service.lower())).layout()
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)

            if isinstance(item, QtGui.QWidgetItem):
                item.widget().setVisible(False)
            else:
                self.clearLayout(item.layout())

            layout.removeItem(item)

    def _createServiceContent(self, service, new=False):
        if new:
            layout = QtGui.QVBoxLayout()
        else:
            layout = getattr(self, '{}Group'.format(service.lower())).layout()
        layout.addWidget(self.notauth_panels[service])
        layout.addWidget(self.auth_panels[service])

        # if service in self.used_services:
            # layout.addWidget(self.auth_panels[service])
        # else:
            # layout.addWidget(self.notauth_panels[service])
        if service in self.used_services:
            self.notauth_panels[service].setVisible(False)
            self.auth_panels[service].setVisible(True)
        else:
            self.auth_panels[service].setVisible(False)
            self.notauth_panels[service].setVisible(True)

        return layout

class NotAuthorizedPanel(QtGui.QWidget):
    verifySignal = QtCore.pyqtSignal(str, str)
    authorizeSignal = QtCore.pyqtSignal(str)

    auth_not_clicked_msg = r'Click the "Authorize" button to start the authorization process.'

    def __init__(self, service, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.service = service

        layout = QtGui.QHBoxLayout()

        self.code_edit = QtGui.QLineEdit(self.auth_not_clicked_msg)
        self.code_edit.setEnabled(False)
        self.code_edit.textChanged.connect(self.onTextChanged)

        self.authorize_button = QtGui.QPushButton('Authorize')
        self.authorize_button.clicked.connect(self.onAuthorizeClicked)

        self.verify_button = QtGui.QPushButton('Verify')
        self.verify_button.setEnabled(False)
        self.verify_button.clicked.connect(self.onVerifyClicked)

        layout.addWidget(self.code_edit)
        layout.addWidget(self.authorize_button)
        layout.addWidget(self.verify_button)

        self.setLayout(layout)
        self.setVisible(False)

    def reset(self, msg):
        self.code_edit.setEnabled(False)
        self.code_edit.setText(msg)
        self.verify_button.setEnabled(False)

    def showEvent(self, event):
        self.code_edit.setText(self.auth_not_clicked_msg)
        self.code_edit.setEnabled(False)
        self.verify_button.setEnabled(False)

    def onTextChanged(self, text):
        if len(text):
            self.verify_button.setEnabled(True)
        else:
            self.verify_button.setEnabled(False)

    def onAuthorizeClicked(self, event):
        self.code_edit.clear()
        self.code_edit.setEnabled(True)
        self.authorizeSignal.emit(self.service)

    def onVerifyClicked(self, event):
        self.verify_button.setEnabled(False)
        self.verifySignal.emit(self.service, self.code_edit.text())

class DropboxAuthorizedPanel(QtGui.QWidget):
    removeSignal = QtCore.pyqtSignal(str)
    saveSignal = QtCore.pyqtSignal(str, str)
    warning_str = r'Path can have multiple levels e.g. foo/boo/zoo'
    warning_stylesheet = r'QLabel { color : red; }'

    def __init__(self, saved_folder='', parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.saved_folder = saved_folder.strip('/')

        main_layout = QtGui.QVBoxLayout()
        content_layout = QtGui.QHBoxLayout()
        buttons_layout = QtGui.QHBoxLayout()

        self.remove_button = QtGui.QPushButton('Unlink')
        self.remove_button.clicked.connect(self.onRemoveClick)

        self.save_button = QtGui.QPushButton('Save')
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.onSaveClick)

        self.folder_edit = QtGui.QLineEdit()
        self.folder_edit.textChanged.connect(self.onTextChanged)

        self.warning_label = QtGui.QLabel(self.warning_str)
        self.warning_label.setStyleSheet(self.warning_stylesheet)

        content_layout.addWidget(QtGui.QLabel('Path:'))
        content_layout.addWidget(self.folder_edit, 1)

        buttons_layout.addWidget(self.warning_label)
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.remove_button)

        main_layout.addLayout(content_layout)
        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)
        self.setVisible(False)

    def showEvent(self, event):
        self.folder_edit.setText(self.saved_folder)
        self.save_button.setEnabled(False)

    def onTextChanged(self, newtext):
        if self.saved_folder != newtext:
            self.save_button.setEnabled(True)
        else:
            self.save_button.setEnabled(False)

    def onSaveClick(self, event):
        folder = str(self.folder_edit.text()).strip()
        self.saved_folder = folder

        if folder == '':
            self.saveSignal.emit('Dropbox', '/')
        else:
            self.saveSignal.emit('Dropbox', '/{}/'.format(folder))
        self.save_button.setEnabled(False)

    def onRemoveClick(self, event):
        self.removeSignal.emit('Dropbox')

class PithosAuthorizedPanel(QtGui.QWidget):
    removeSignal = QtCore.pyqtSignal(str)
    saveSignal = QtCore.pyqtSignal(str, str)
    banned_words = ['trash', 'Trash', 'groups', 'Groups']
    warning_stylesheet = r'QLabel { color : red; }'
    warning_str = r'Folder name cannot be empty, default is cloudy'

    def __init__(self, saved_folder='', parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.saved_folder = saved_folder

        main_layout = QtGui.QVBoxLayout()
        content_layout = QtGui.QHBoxLayout()
        buttons_layout = QtGui.QHBoxLayout()

        self.remove_button = QtGui.QPushButton('Unlink')
        self.remove_button.clicked.connect(self.onRemoveClick)

        self.save_button = QtGui.QPushButton('Save')
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.onSaveClick)

        self.folder_edit = QtGui.QLineEdit()
        self.folder_edit.textChanged.connect(self.onTextChanged)

        self.warning_label = QtGui.QLabel(self.warning_str)
        self.warning_label.setStyleSheet(self.warning_stylesheet)

        content_layout.addWidget(QtGui.QLabel('Folder:'))
        content_layout.addWidget(self.folder_edit, 1)

        buttons_layout.addWidget(self.warning_label)
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.remove_button)

        main_layout.addLayout(content_layout)
        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)
        self.setVisible(False)

    def showEvent(self, event):
        self.folder_edit.setText(self.saved_folder)
        self.save_button.setEnabled(False)

    def onTextChanged(self, newtext):
        if (newtext in self.banned_words or
            not newtext or
            self.saved_folder == newtext):
            self.save_button.setEnabled(False)
        else:
            self.save_button.setEnabled(True)

    def onSaveClick(self, event):
        self.saved_folder = str(self.folder_edit.text()).strip()
        self.saveSignal.emit('Pithos', str(self.saved_folder))
        self.save_button.setEnabled(False)

    def onRemoveClick(self, event):
        self.removeSignal.emit('Pithos')

class GoogleDriveAuthorizedPanel(QtGui.QWidget):
    removeSignal = QtCore.pyqtSignal(str)
    saveSignal = QtCore.pyqtSignal(str, str)
    banned_words = ['trash', 'Trash', 'recent', 'Recent']
    warning_stylesheet = r'QLabel { color : red; }'
    warning_str = r'Folder name cannot contain "/"'

    def __init__(self, saved_folder='', parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.saved_folder = saved_folder

        main_layout = QtGui.QVBoxLayout()
        content_layout = QtGui.QHBoxLayout()
        buttons_layout = QtGui.QHBoxLayout()

        self.remove_button = QtGui.QPushButton('Unlink')
        self.remove_button.clicked.connect(self.onRemoveClick)

        self.save_button = QtGui.QPushButton('Save')
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.onSaveClick)

        self.folder_edit = QtGui.QLineEdit()
        self.folder_edit.textChanged.connect(self.onTextChanged)

        self.warning_label = QtGui.QLabel(self.warning_str)
        self.warning_label.setStyleSheet(self.warning_stylesheet)

        content_layout.addWidget(QtGui.QLabel('Folder:'))
        content_layout.addWidget(self.folder_edit, 1)

        buttons_layout.addWidget(self.warning_label)
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.remove_button)

        main_layout.addLayout(content_layout)
        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)
        self.setVisible(False)

    def showEvent(self, event):
        self.folder_edit.setText(self.saved_folder)
        self.save_button.setEnabled(False)

    def onTextChanged(self, newtext):
        if (newtext in self.banned_words or
            self.saved_folder == newtext):
            self.save_button.setEnabled(False)
        else:
            self.save_button.setEnabled(True)

    def onSaveClick(self, event):
        self.saved_folder = str(self.folder_edit.text()).strip()
        self.saveSignal.emit('GoogleDrive', str(self.saved_folder))
        self.save_button.setEnabled(False)

    def onRemoveClick(self, event):
        self.removeSignal.emit('GoogleDrive')

class Settings(QtGui.QWidget):
    def __init__(self, used_services, service_folders, general_settings, parent=None):
        super(Settings, self).__init__(parent)

        self.contentsWidget = QtGui.QListWidget()
        self.contentsWidget.setViewMode(QtGui.QListView.IconMode)
        self.contentsWidget.setIconSize(QtCore.QSize(55, 55))
        self.contentsWidget.setMovement(QtGui.QListView.Static)
        self.contentsWidget.setMaximumWidth(90)
        self.contentsWidget.setSpacing(12)

        self.general_page = GeneralPage(general_settings)
        self.accounts_page = AccountsPage(used_services, service_folders)

        self.pagesWidget = QtGui.QStackedWidget()
        self.pagesWidget.addWidget(self.general_page)
        self.pagesWidget.addWidget(self.accounts_page)

        self.createIcons()
        self.contentsWidget.setCurrentRow(0)

        horizontalLayout = QtGui.QHBoxLayout()
        horizontalLayout.addWidget(self.contentsWidget)
        horizontalLayout.addWidget(self.pagesWidget, 1)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addLayout(horizontalLayout)

        self.setLayout(mainLayout)

    def show_settings(self):
        self.contentsWidget.setCurrentRow(0)

    def show_accounts(self):
        self.contentsWidget.setCurrentRow(1)

    def add_service(self, service):
        self.accounts_page.add_service(service)

    def remove_service(self, service):
        self.accounts_page.remove_service(service)

    def reset(self, service, msg=''):
        self.accounts_page.reset(service, msg)

    def changePage(self, current, previous):
        if not current:
            current = previous

        self.pagesWidget.setCurrentIndex(self.contentsWidget.row(current))

    def createIcons(self):
        configButton = QtGui.QListWidgetItem(self.contentsWidget)
        configButton.setIcon(QtGui.QIcon(r'images/settings-general.png'))
        configButton.setText("General")
        configButton.setTextAlignment(QtCore.Qt.AlignHCenter)
        configButton.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

        updateButton = QtGui.QListWidgetItem(self.contentsWidget)
        updateButton.setIcon(QtGui.QIcon(r'images/settings-account.png'))
        updateButton.setText("Accounts")
        updateButton.setTextAlignment(QtCore.Qt.AlignHCenter)
        updateButton.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

        self.contentsWidget.currentItemChanged.connect(self.changePage)

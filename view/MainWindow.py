import os
import logger
import operator
from PyQt4 import QtCore, QtGui, Qt

class MyTableModel(QtCore.QAbstractTableModel):

    def __init__(self, header, rename_signal, delete_signal, move_signal,
                 data=None, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)

        #Hax
        self.folder = 'dummy'
        self.data = {self.folder:[['']*(len(header))]}

        self.rename_signal = rename_signal
        self.delete_signal = delete_signal
        self.move_signal = move_signal
        self.header = header
        self.logger = logger.logger_factory(self.__class__.__name__)

    def add_folders(self, folders):
        self.beginResetModel()
        for folder in folders:
            self.data[folder] = []
        self.endResetModel()

    def set_folder_data(self, folder, data):
        self.beginResetModel()
        self.data[folder] = data
        self.endResetModel()

    def set_folder(self, folder):
        self.beginResetModel()
        self.folder = folder
        self.endResetModel()

    def rowCount(self, parent):
        return len(self.data[self.folder])

    def columnCount(self, parent):
        return len(self.data[self.folder][0])

    def data(self, index, role):
        if not index.isValid():
            return QtCore.QVariant()
        elif role != Qt.Qt.DisplayRole and role != Qt.Qt.EditRole:
            return QtCore.QVariant()
        return QtCore.QVariant(self.data[self.folder][index.row()][index.column()])

    def headerData(self, col, orientation, role):
        if orientation == Qt.Qt.Horizontal and role == Qt.Qt.DisplayRole:
            return QtCore.QVariant(self.header[col])
        return QtCore.QVariant()

    def sort(self, Ncol, order):
        self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
        self.data[self.folder] = sorted(self.data[self.folder])
        if order == Qt.Qt.DescendingOrder:
            self.data[self.folder].reverse()
        self.emit(QtCore.SIGNAL("layoutChanged()"))

    def setData(self, index, value, role):
        #File renamed
        new_filename = str(value.toString())
        old_filename = self.data[self.folder][index.row()][index.column()]
        if not new_filename == old_filename:
            self.data[self.folder][index.row()][index.column()] = new_filename
            self.rename_signal.emit([self.folder, old_filename, new_filename])
        return True

    def flags(self, index):
        if not index.isValid():
            return 0
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable


class BaseDelegate(QtGui.QStyledItemDelegate):

    def __init__(self, device, font, alt_color, selected_color, images=None):
        QtGui.QStyledItemDelegate.__init__(self, device)

        self.font = font
        self.images = images
        self.alt_brush = QtGui.QBrush(alt_color)
        self.selected_brush = QtGui.QBrush(selected_color)

        self.logger = logger.logger_factory(self.__class__.__name__)

    def createEditor(self, parent, option, index):
        return None

class ListTableDelegate(BaseDelegate):

    def paint(self, painter, option, index):
        painter.save()
        model = index.model()
        d = model.data[model.folder][index.row()][index.column()]

        if index.row() % 2:
            painter.fillRect(option.rect, self.alt_brush)

        if option.state & QtGui.QStyle.State_Selected:
            painter.fillRect(option.rect, self.selected_brush)

        painter.translate(option.rect.topLeft())
        painter.setFont(self.font)
        painter.drawText(QtCore.QPoint(5, 20), d)

        painter.restore()

    def createEditor(self, parent, option, index):
        if index.column() == 0:
            return QtGui.QLineEdit('LOLasdasd', parent)
        else:
            return super(ListTableDelegate, self).createEditor(parent, option, index)

    def editorEvent(self, event, model, option, index):
        if event.type() == QtCore.QEvent.MouseButtonRelease:
            model = index.model()
            print model.data[model.folder][index.row()][0]

        return False

    def sizeHint(self, option, index):
        model = index.model()
        d = model.data[model.folder][index.row()]
        return QtCore.QSize(100, 40)

class MyTableView(QtGui.QTableView):

    def contextMenuEvent(self, event):
        menu = QtGui.QMenu(self)

        Action = menu.addAction("I am an Action")
        Action.triggered.connect(self.onClick)

        menu.exec_(event.globalPos())

    def onClick(self):
        print 'LOL'

class MainWindow(QtGui.QMainWindow):

    font = QtGui.QFont('Tahoma', 10)
    rename_signal = QtCore.pyqtSignal(list)
    delete_signal = QtCore.pyqtSignal(str)
    move_signal = QtCore.pyqtSignal(str)

    def __init__(self, title, parent=None):
        super(MainWindow, self).__init__(parent)

        self.logger = logger.logger_factory(self.__class__.__name__)
        self.setWindowTitle(title)
        self.resize(500, 400)
        self.center()
        self.headers = ['File', 'Size']

        centralWidget = QtGui.QWidget()

        #Status bar label
        self.sbLabel = QtGui.QLabel('Retrieving folders...')

        #Folder choice widgets
        self.comboBox = QtGui.QComboBox()
        #Block signals to prevent the firing of the first currentIndexChanged event.
        self.comboBox.blockSignals(True)
        self.comboBox.setEditable(False)
        self.comboBox.setEnabled(False)
        self.comboBox.setSizePolicy(QtGui.QSizePolicy.Expanding,
                QtGui.QSizePolicy.Preferred)
        #@Mediator
        self.comboBox.currentIndexChanged['QString'].connect(self.onSelectionChanged)

        folderLayout = QtGui.QHBoxLayout()
        folderLayout.addWidget(QtGui.QLabel('Choose folder:'))
        folderLayout.addWidget(self.comboBox)

        #Table that comprises the main widget of this window
        self.table = self._create_table()
        self.table.setItemDelegate(ListTableDelegate(self, self.font,
                                   QtGui.QColor('#E5FFFF'), QtGui.QColor('#47D1FF')))

        #Main(vertical) layout
        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addLayout(folderLayout)
        mainLayout.addWidget(self.table)

        centralWidget.setLayout(mainLayout)
        self.setCentralWidget(centralWidget)

        self._create_menu_bar()
        self._create_status_bar()
        self.show()

    def center(self):
        appRect = self.frameGeometry()
        clientArea = QtGui.QDesktopWidget().availableGeometry().center()
        appRect.moveCenter(clientArea)
        self.move(appRect.topLeft())

    def _create_menu_bar(self):
        #Get QMainWindow's predefined menu bar
        menu_bar = self.menuBar()
        #File menu
        #---Exit button
        self.exit_action = QtGui.QAction('&Exit', self)
        self.exit_action.setShortcut('Ctrl+Q')
        self.exit_action.setStatusTip('Exit application')
        self.exit_action.triggered.connect(self.onExit)

        file_menu = menu_bar.addMenu('&File')
        file_menu.addAction(self.exit_action)
        file_menu = menu_bar.addMenu('&Tools')

    def _create_status_bar(self):
        sb = QtGui.QStatusBar()
        sb.addWidget(self.sbLabel, 1)
        self.setStatusBar(sb)

    def _create_table(self):
        tbl = MyTableView()

        tm = MyTableModel(self.headers, self.rename_signal, self.delete_signal,
                          self.move_signal, parent=self)
        tbl.setModel(tm)

        # tbl.setEditTriggers(QtGui.QAbstractItemView.AllEditTriggers)
        tbl.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        tbl.setMouseTracking(True)
        tbl.setShowGrid(False)
        tbl.setFont(self.font)
        tbl.verticalHeader().setVisible(False)

        hh = tbl.horizontalHeader()
        hh.setResizeMode(0, QtGui.QHeaderView.Stretch)
        hh.setResizeMode(1, QtGui.QHeaderView.ResizeToContents)

        tbl.resizeColumnsToContents()
        tbl.setSortingEnabled(True)

        return tbl

    def onRenameComplete(self):
        self.statusBar().showMessage('Rename Completed', 2000)

    def onSelectionChanged(self, text):
        #@Mediator
        #Called on subsequent comboBox changes
        self.table.model().set_folder(str(text))
        file_count = self.table.model().rowCount(None)
        self.sbLabel.setText('{} file(s)'.format(file_count))

    def set_folders(self, folders):
        for item in folders:
            self.comboBox.addItem(item)
        self.table.model().add_folders(folders)
        self.sbLabel.setText('Retrieving files...')
        self.comboBox.blockSignals(False)

    def set_objects(self, folder_name, objects):
        self.sbLabel.setText('Retrieving files...{}'.format(folder_name))
        self.table.model().set_folder_data(folder_name, objects)

    def set_active_folder(self):
        #Called on app initialization(No choice has been made in the comboBox)
        self.table.model().set_folder(str(self.comboBox.currentText()))
        file_count = self.table.model().rowCount(None)
        self.sbLabel.setText('{} file(s)'.format(file_count))
        self.comboBox.setEnabled(True)

    def onExit(self):
        #@Mediator
        QtCore.QCoreApplication.instance().quit()

def main():
    import sys

    app = QtGui.QApplication(sys.argv)

    w = MainWindow('UCloudy')
    w.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
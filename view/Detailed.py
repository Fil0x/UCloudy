import re
import operator

from lib.util import shorten_str
from Settings import Settings

from PyQt4 import Qt
from PyQt4 import QtGui
from PyQt4 import QtCore


class MyTableModel(QtCore.QAbstractTableModel):
    def __init__(self, header, data=None, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)

        #Hax
        self.data = [['']*(len(header)+1)] if not data else data
        self.header = header
        self.hidden_col = len(header)

    def rowCount(self, parent):
        return len(self.data)

    def columnCount(self, parent):
        return len(self.data[0]) if len(self.data) else 0

    def data(self, index, role):
        if not index.isValid():
            return QtCore.QVariant()
        elif role != Qt.Qt.DisplayRole:
            return QtCore.QVariant()
        return QtCore.QVariant(self.data[index.row()][index.column()])

    def headerData(self, col, orientation, role):
        if col < self.hidden_col and orientation == Qt.Qt.Horizontal and role == Qt.Qt.DisplayRole:
            return QtCore.QVariant(self.header[col])
        return QtCore.QVariant()

    def sort(self, Ncol, order):
        if not self.data:
            return

        self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
        self.data = sorted(self.data, key=operator.itemgetter(Ncol))
        if order == Qt.Qt.DescendingOrder:
            self.data.reverse()
        self.emit(QtCore.SIGNAL("layoutChanged()"))

    def get_states(self, service=None):
        if not self.data:
            return

        r = []
        if not service:
            services = list(set(zip(*self.data)[2]))
        else:
            services = [service]
        for s in services:
            service_filter = lambda x: x[2] == s
            filtered_data = filter(service_filter, self.data)
            states = zip(*filtered_data)[3]
            if filter(lambda x:re.match('Error-*', x), states):
                r.append([s, 'Error'])
            elif len(filter(lambda x:x == 'Paused', states)) == len(states):
                r.append([s, 'Idle'])
            else:
                r.append([s, 'Active'])

        return r

    def add_item(self, item):
        if len(self.data) == 1 and self.data[0][0] == '':
            self.beginRemoveRows(QtCore.QModelIndex(), 0, 0)
            del self.data[0]
            self.endRemoveRows()

        self.beginInsertRows(QtCore.QModelIndex(), len(self.data), len(self.data))
        self.data.append(item)
        self.endInsertRows()

    def update_row(self, id, data, col):
        if len(self.data) == 1 and self.data[0][0] == '':
            return
        i = zip(*self.data)[-1].index(id)
        self.data[i][col] = data
        self.dataChanged.emit(self.index(i, col), self.index(i, col))

    def update_item(self, item):
        self.update_row(item[0], item[1], 1)

    def update_status(self, item):
        self.update_row(item[0], item[1], 3)

    def update_remote(self, item):
        self.update_row(item[0], item[1], 4)

    def remove(self, id):
        i = zip(*self.data)[-1].index(id)
        self.beginRemoveRows(QtCore.QModelIndex(), i, i)
        self.data = self.data[0:i] + self.data[i+1:]
        self.endRemoveRows()

    def remove_all(self):
        self.beginRemoveRows(QtCore.QModelIndex(), 0, len(self.data) - 1)
        del self.data[:]
        self.endRemoveRows()

class BaseDelegate(QtGui.QStyledItemDelegate):

    def __init__(self, device, font, color, images=None):
        QtGui.QStyledItemDelegate.__init__(self, device)

        self.font = font
        self.images = images
        self.brush = QtGui.QBrush(color)

    def createEditor(self, parent, option, index):
        return None

    def center_text(self, container_rect, text):
        center = container_rect.width() / 2
        metrics = QtGui.QFontMetrics(self.font)
        offset = metrics.boundingRect(text).width() / 2

        return QtCore.QPoint(center - offset, 20)

class UploadTableDelegate(BaseDelegate):

    def paint(self, painter, option, index):
        painter.save()
        model = index.model()
        col = index.column()
        d = model.data[index.row()][col]

        if option.state & QtGui.QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        elif index.row() % 2 == 1:
            painter.fillRect(option.rect, self.brush)

        painter.translate(option.rect.topLeft())
        painter.setFont(self.font)

        d = shorten_str(d, 25)

        if col == 0:
            painter.drawText(QtCore.QPoint(10, 20), d)
        elif col == 3:
            if 'Error' in d:
                error = d.split('-')[1]
                pos = self.center_text(option.rect, error)
                painter.drawImage(QtCore.QPoint(pos.x()-25, 7), self.images['Error'])
                painter.drawText(pos, error)
            else:
                painter.drawText(self.center_text(option.rect, d), d)
        elif col == 4:
            if d == '':
                pos = self.center_text(option.rect, d)
                painter.drawImage(QtCore.QPoint(pos.x()-25, 7), self.images['Loading'])
                painter.drawText(pos, d)
            else:
                painter.drawText(self.center_text(option.rect, d), d)
        elif col == 1:
            painter.drawText(self.center_text(option.rect, d), d)
        elif col == 5:
            pos = self.center_text(option.rect, d)
            painter.drawText(QtCore.QPoint(pos.x()-10, pos.y()), d)
        else:
            pos = self.center_text(option.rect, d)
            painter.drawImage(QtCore.QPoint(pos.x()-25, 7), self.images[d])
            painter.drawText(pos, d)

        painter.restore()

    def editorEvent(self, event, model, option, index):
        return False

    def sizeHint(self, option, index):
        model = index.model()
        d = model.data[index.row()]
        return QtCore.QSize(100, 40)

class HistoryTableDelegate(BaseDelegate):

    def paint(self, painter, option, index):
        painter.save()
        model = index.model()
        col = index.column()
        d = model.data[index.row()][col]

        if option.state & QtGui.QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        elif index.row() % 2 == 1:
            painter.fillRect(option.rect, self.brush)

        painter.translate(option.rect.topLeft())
        painter.setFont(self.font)

        d = shorten_str(d, 25)

        if col in [0, 3]:
            painter.drawText(QtCore.QPoint(10, 20), d)
        elif col == 1:
            painter.drawText(self.center_text(option.rect, d), d)
        elif col == 2:
            pos = self.center_text(option.rect, d[0])
            painter.drawImage(QtCore.QPoint(pos.x()-25, 7), self.images[d[0]])
            painter.drawText(pos, d[0])

        painter.restore()

    def editorEvent(self, event, model, option, index):
        return False

    def sizeHint(self, option, index):
        model = index.model()
        d = model.data[index.row()]
        return QtCore.QSize(100, 40)

class DetailedWindow(QtGui.QMainWindow):
    #http://www.jankoatwarpspeed.com/ultimate-guide-to-table-ui-patterns/

    alt_color = '#E5FFFF'
    font = QtGui.QFont('Tahoma', 10)
    db_path = r'images/dropbox-icon.png'
    pithos_path = r'images/pithos-icon.png'
    gd_path = r'images/googledrive-icon.png'
    error_path = r'images/detailed-x.png'
    loading_path = r'images/detailed-loading.png'
    addBtnPath = r'images/detailed-add.png'
    playBtnPath = r'images/detailed-play.png'
    stopBtnPath = r'images/detailed-stop.png'
    file_icon_path = r'images/detailed-doc.png'
    removeBtnPath = r'images/detailed-remove.png'
    copyBtnPath = r'images/detailed-copy.png'
    settingsBtnPath = r'images/detailed-configure.png'
    tableBackgroundPath = r'images/detailed-background.png'
    windowStyle = r'QMainWindow {background-color: rgba(223, 231, 232, 100%)}'
    no_services_error = r'You are not authenticated with any service.'
    upload_table_sb_msg = r'Files currently being uploaded.'
    history_table_sb_tmp = r'{} link(s) copied to clipboard.'
    history_table_sb_msg = r'Press Ctrl+C or click the "Copy" button to copy the share links of the selected entries.'

    def __init__(self, title, pos, size, maximized, screen_id, settings_page):
        QtGui.QWidget.__init__(self)
        self.setWindowTitle(title)
        self.setVisible(False)
        self.setStyleSheet(self.windowStyle)        
        QtGui.QToolTip.setFont(self.font)
        
        self.minimize_on_close = False

        if not maximized:
            d = QtGui.QApplication.desktop()
            pos_rect = d.availableGeometry(screen_id).adjusted(pos[0], pos[1], 0, 0)
            self.move(pos_rect.topLeft())
        else:
            self.showMaximized()

        file_image = QtGui.QImage(self.file_icon_path)

        self.history_header = ['Name', 'Destination', 'Service', 'Date']
        self.uploads_header = ['Name', 'Progress', 'Service', 'Status',
                               'Destination', 'Conflict']
                               
        c = QtGui.QColor(self.alt_color)
        dropbox_icon = QtGui.QImage(self.db_path)
        pithos_icon = QtGui.QImage(self.pithos_path)
        googledrive_icon = QtGui.QImage(self.gd_path)
        error_icon = QtGui.QImage(self.error_path)
        loading_icon = QtGui.QImage(self.loading_path)
        images = {'Dropbox':dropbox_icon, 'Pithos':pithos_icon,
                  'GoogleDrive': googledrive_icon, 'Error':error_icon,
                  'Loading':loading_icon}

        self.upload_table = self._create_table(self.uploads_header)
        self.upload_table.setItemDelegate(UploadTableDelegate(self, self.font, c, images))

        self.history_table = self._create_table(self.history_header)
        self.history_table.setItemDelegate(HistoryTableDelegate(self, self.font, c, images))

        self.settings_page = settings_page

        self._createRibbon()
        self._createSideSpaces()
        
        self.copyBtn.clicked.connect(self.onCopyClick)

        self.statusbar_label = QtGui.QLabel(self.upload_table_sb_msg)
        self.tab = QtGui.QTabWidget()
        QtCore.QObject.connect(self.tab, QtCore.SIGNAL('currentChanged(int)'),
                               self.onTabChanged)
        self.tab.insertTab(0, self.upload_table, 'Active')
        self.tab.insertTab(1, self.history_table, 'History')
        self.tab.insertTab(2, self.settings_page, 'Settings')

        self.setCentralWidget(self.tab)

        sb = QtGui.QStatusBar(self)
        sb.addWidget(self.statusbar_label)
        self.setStatusBar(sb)

    def onTabChanged(self, tabIndex):
        sb = self.statusBar()

        if tabIndex == 0:
            self.addBtn.setDisabled(False)
            self.playBtn.setDisabled(False)
            self.stopBtn.setDisabled(False)
            self.removeBtn.setDisabled(False)
            self.copyBtn.setDisabled(True)
            self.statusbar_label.setText(self.upload_table_sb_msg)
        elif tabIndex == 1:
            self.addBtn.setDisabled(False)
            self.playBtn.setDisabled(True)
            self.stopBtn.setDisabled(True)
            self.removeBtn.setDisabled(False)
            self.copyBtn.setDisabled(False)
            self.statusbar_label.setText(self.history_table_sb_msg)
        elif tabIndex == 2:
            self.addBtn.setDisabled(True)
            self.playBtn.setDisabled(True)
            self.stopBtn.setDisabled(True)
            self.removeBtn.setDisabled(True)
            self.copyBtn.setDisabled(True)
            self.statusbar_label.setText('')

    def onCopyClick(self):
        model = self.history_table.model()
        selection_model = self.history_table.selectionModel()
        clipboard = QtGui.QApplication.clipboard()
        clipboard.clear()

        links = []
        selections = selection_model.selectedRows()
        add_name = True if len(selections) != 1 else False
        for s in selections:
            name = model.data[s.row()][0]
            link = model.data[s.row()][2][1]
            if add_name:
                links.append('{}: {}'.format(shorten_str(name, 25), link))
            else:
                links.append(link)

        if links:
            self.statusBar().showMessage(self.history_table_sb_tmp.format(len(links)), 2000)
            clipboard.setText('\n'.join(links))
            
    def keyPressEvent(self, event):
        modifiers = QtGui.QApplication.keyboardModifiers()
        
        if (self.history_table.isVisible() and
            modifiers == QtCore.Qt.ControlModifier and
            event.key() == QtCore.Qt.Key_C):
            self.onCopyClick()

    def get_current_tab(self):
        return self.tab.currentIndex()

    def show_add_file_warning(self):
        msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning,
                "No Services added", self.no_services_error, QtGui.QMessageBox.NoButton, self)
        msgBox.addButton("&Close", QtGui.QMessageBox.AcceptRole)
        msgBox.exec_()

    def get_window_info(self):
        d = QtGui.QApplication.desktop()
        pos = [self.pos().x(), self.pos().y()]
        size = [self.size().width(), self.size().height()]
        screen_id = d.screenNumber(self)

        return [pos, size, self.isMaximized(), screen_id]

    def get_selected_ids(self, n):
        r = []
        if n == 0:
            index = len(self.uploads_header)
            m = self.upload_table.model()
            sm = self.upload_table.selectionModel()
            service_index = self.uploads_header.index('Service')
        elif n == 1:
            index = len(self.history_header)
            m = self.history_table.model()
            sm = self.history_table.selectionModel()
            service_index = self.history_header.index('Service')

        for i in sm.selectedRows():
            id = m.data[i.row()][index]
            service = m.data[i.row()][service_index]
            r.append([id, service])

        return r

    def get_states(self, service=None):
        return self.upload_table.model().get_states(service)

    def show_settings(self):
        self.tab.setCurrentIndex(2)
        self.settings_page.show_settings()

    def show_accounts(self):
        self.tab.setCurrentIndex(2)
        self.settings_page.show_accounts()

    def add_upload_item(self, item):
        # [filename, progress, service, status, dest, conflict]
        self.upload_table.model().add_item(item)

    def update_upload_item(self, item):
        self.upload_table.model().update_item(item)

    def update_item_status(self, item):
        self.upload_table.model().update_status(item)

    def update_remote_path(self, item):
        self.upload_table.model().update_remote(item)

    def delete_upload_item(self, id):
        self.upload_table.model().remove(id)

    def add_history_item(self, item):
        #[name, dest, (service, sharelink), date, id]
        self.history_table.model().add_item(item)

    def clear_uploads(self):
        #To get rid of the empty line.
        model = self.upload_table.model()
        if model.data[0][0] == '':
            self.upload_table.model().remove_all()

    def update_all_history(self, items):
        self.history_table.model().remove_all()
        for i in items:
            self.add_history_item(i)

    def delete_history_item(self, id):
        self.history_table.model().remove(id)

    def closeEvent(self, event):
        if not self.minimize_on_close:
            self.setVisible(False)
        else:
            self.showMinimized()
        event.ignore()

    def _createSideSpaces(self):
        '''
        Add some space on the left and right of the table.
        '''
        leftDockWidget = QtGui.QDockWidget()
        leftDockWidget.setTitleBarWidget(QtGui.QWidget())
        leftDockWidget.setWidget(QtGui.QLabel(' '))
        self.addDockWidget(Qt.Qt.LeftDockWidgetArea, leftDockWidget)

        rightDockWidget = QtGui.QDockWidget()
        rightDockWidget.setTitleBarWidget(QtGui.QWidget())
        rightDockWidget.setWidget(QtGui.QLabel(' '))
        self.addDockWidget(Qt.Qt.RightDockWidgetArea, rightDockWidget)

    def _createRibbon(self):
        def _createDockWidget(elem, tooltip):
            dockWidget = QtGui.QDockWidget()
            #Hide the dock title bar
            dockWidget.setTitleBarWidget(QtGui.QWidget())

            setattr(self, elem, QtGui.QPushButton())
            getattr(self, elem).setIcon(QtGui.QIcon(getattr(self, elem + 'Path')))
            getattr(self, elem).setIconSize(QtCore.QSize(30, 30))
            getattr(self, elem).setFlat(True)
            getattr(self, elem).setToolTip(tooltip)
            getattr(self, elem).setMaximumWidth(40)
            dockWidget.setWidget(getattr(self, elem))
            self.addDockWidget(Qt.Qt.TopDockWidgetArea, dockWidget)

        #@Mediator
        _createDockWidget('addBtn', 'Add files')
        _createDockWidget('playBtn', 'Resume file')
        _createDockWidget('stopBtn', 'Stop file')
        _createDockWidget('removeBtn', 'Remove file')
        _createDockWidget('copyBtn', 'Copy share link')

    def _create_table(self, header):
        tbl = QtGui.QTableView()

        tm = MyTableModel(header, parent=self)
        tbl.setModel(tm)

        tbl.setMinimumSize(700, 300)
        tbl.setShowGrid(False)
        tbl.setFont(self.font)
        tbl.hideColumn(len(header))

        vh = tbl.verticalHeader()
        vh.setVisible(False)

        hh = tbl.horizontalHeader()
        for i in range(len(header)):
            hh.setResizeMode(i, QtGui.QHeaderView.Stretch)

        # set column width to fit contents
        tbl.resizeColumnsToContents()
        tbl.setSortingEnabled(True)
        tbl.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)

        return tbl

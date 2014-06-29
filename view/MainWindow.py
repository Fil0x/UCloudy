import os
import operator
from PyQt4 import QtCore, QtGui, Qt

class MyTableModel(QtCore.QAbstractTableModel):
    def __init__(self, header, data=None, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)

        #Hax
        self.data = [['']*(len(header))] if not data else data
        self.header = header

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
        if orientation == Qt.Qt.Horizontal and role == Qt.Qt.DisplayRole:
            return QtCore.QVariant(self.header[col])
        return QtCore.QVariant()

    def sort(self, Ncol, order):
        self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
        self.data = sorted(self.data, key=operator.itemgetter(Ncol))
        if order == Qt.Qt.DescendingOrder:
            self.data.reverse()
        self.emit(QtCore.SIGNAL("layoutChanged()"))
        
    def add_item(self, item):
        self.beginInsertRows(QtCore.QModelIndex(), len(self.data), len(self.data))
        self.data.append(item)
        self.endInsertRows()
        
    def remove(self, id, index=None):
        i = 0
        if index:
            i = index
        else:
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
        
class ListTableDelegate(BaseDelegate):
        
    def paint(self, painter, option, index):
        painter.save()
        model = index.model()
        d = model.data[index.row()][index.column()]
        
        if index.row() % 2:
            painter.fillRect(option.rect, self.brush)
        
        painter.translate(option.rect.topLeft())
        painter.setFont(self.font)
        #painter.drawImage(QtCore.QPoint(5, 5), self.images[0])
        painter.drawText(QtCore.QPoint(5, 20), d)
        '''
        painter.setPen(self.date_color)
        painter.drawText(QtCore.QPoint(40, 30), str(d[3]))
        if option.state & QtGui.QStyle.State_MouseOver:
            painter.drawImage(self.sharelink_pos, self.sharelink_img)
        '''
        painter.restore()

    def editorEvent(self, event, model, option, index):
        '''sharelink_rect = self.sharelink_img.rect().translated(self.sharelink_pos.x(),
                                                option.rect.top() + self.sharelink_pos.y())
        if event.type() == QtCore.QEvent.MouseButtonRelease:
            if sharelink_rect.contains(event.pos()):
                model = index.model()
                link = model.data[index.row()][2]
                import webbrowser
                webbrowser.open(link)'''

        return False

    def sizeHint(self, option, index):
        model = index.model()
        d = model.data[index.row()]
        return QtCore.QSize(100, 40)

class MainWindow(QtGui.QMainWindow):

    font = QtGui.QFont('Tahoma', 10)

    def __init__(self, title, parent=None):
        super(MainWindow, self).__init__(parent)

        self.setWindowTitle(title)
        self.setFixedSize(300, 400)
        self.headers = ['File', 'Size']
        
        centralWidget = QtGui.QWidget()
        
        #Status bar label
        self.sbLabel = QtGui.QLabel('Initializing...')

        #Folder choice widgets
        self.comboBox = QtGui.QComboBox()
        self.comboBox.setEditable(False)
        self.comboBox.setSizePolicy(QtGui.QSizePolicy.Expanding,
                QtGui.QSizePolicy.Preferred)
        #@Mediator
        self.comboBox.currentIndexChanged.connect(self.onSelectionChanged)

        folderLayout = QtGui.QHBoxLayout()
        folderLayout.addWidget(QtGui.QLabel('Choose folder:'))
        folderLayout.addWidget(self.comboBox)
        
        #Table that comprises the main widget of this window
        self.table = self._create_table()
        self.table.setItemDelegate(ListTableDelegate(self, self.font, QtGui.QColor('#E5FFFF')))
        
        #Main(vertical) layout
        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addLayout(folderLayout)
        mainLayout.addWidget(self.table)
        
        centralWidget.setLayout(mainLayout)
        self.setCentralWidget(centralWidget)
        
        self._create_menu_bar()
        self._create_status_bar()
        self.show()
        
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
        tbl = QtGui.QTableView()
        
        tm = MyTableModel(self.headers, parent=self)
        tbl.setModel(tm)
        
        tbl.setShowGrid(False)
        tbl.setFont(self.font)
        tbl.hideColumn(len(self.headers))
        tbl.verticalHeader().setVisible(False)
        
        hh = tbl.horizontalHeader()
        for i in range(len(self.headers)):
            hh.setResizeMode(i, QtGui.QHeaderView.Stretch)
            
        tbl.resizeColumnsToContents()
        tbl.setSortingEnabled(True)
        
        return tbl
        
    def onSelectionChanged(self, text):
        #@Mediator
        #print self.comboBox.currentText()
        pass
        
    def set_folders(self, folders):
        for item in folders:
            self.comboBox.addItem(item)
        self.sbLabel.setText('Folders retrieved.')
        
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
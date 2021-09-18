from PyQt5.QtCore import QModelIndex, Qt, QAbstractTableModel, pyqtSlot
from PyQt5.QtWidgets import (
    QComboBox,
    QStyledItemDelegate,
    QInputDialog,
    QFileDialog,
    QPushButton
)
from pandas import DataFrame
import re
import os


class Settings(QAbstractTableModel):
    def __init__(self, data=[], parent=None):
        super().__init__(parent)
        self.data = data
        self.index_name = 0
        self.index_variableName = 1
        self.index_value = 2
        self.index_type = 3
        self.index_group = 4
        self.index_comment = 5 
        self.indexes_visible = [self.index_name, self.index_value]
        self.headers = ['Параметр', 'Переменная', 'Значение', 'Тип', 'Группа', 'Комментарий']
         

    def save(self, filename):
        df = DataFrame(self.data)
        df.to_excel(filename+'.xlsx')
        
    def headerData(self, section: int, orientation: Qt.Orientation, role: int):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.headers[section]
            else:
                return str(1+section)

    def columnCount(self, parent=None):
        return len(self.data[0])

    def rowCount(self, parent=None):
        return len(self.data)
    
    def data(self, index: QModelIndex, role: int):
        if role == Qt.ToolTipRole:
            row=index.row()
            return self.data[row][self.index_comment]
        if role == Qt.DisplayRole or role == Qt.EditRole:
            row = index.row()
            col = index.column()
            return str(self.data[row][col])
        
    def wrap(self):
        j = self.index_variableName
        k = self.index_value
        return {self.data[i][j]: self.data[i][k] for i in range(len(self.data))}
    
    def get(self, key):
        settings = self.settigs()
        return settings[key]
        
    def flags(self, index):
        if index.column()==self.index_value:
            return Qt.ItemIsEnabled | Qt.ItemIsEditable
        if index.column()==self.index_name:
            return Qt.ItemIsEnabled

    def setData(self, index, value, role):
        if role == Qt.EditRole and value!='':
            i = index.row()
            value, flag = self.suit(i, value)
            if flag:
                self.data[i][self.index_value] = value
            return True
        return False
        
    def suit(self, raw_index, value):
        value_type = self.data[raw_index][self.index_type] 
        flag = True
        if value_type == '+float':
            try: value = float(value)
            except: flag = False
            flag = flag and (value > 0)
        elif value_type == '0+float':
            try: value = float(value)
            except: flag = False
            flag = flag and (value >= 0)
        elif value_type == '+int':
            try: value = int(float(value))
            except: flag = False
            flag = flag and (value > 0)
        elif value_type == '%100':
            try: value = float(value)
            except: flag = False
            flag = flag and (value >= 0) and (value <= 1)
        elif value_type == 'bool':
            if value == 'True':
                value = True
            elif value == 'False':
                value = False
            elif (value == 0 or value == 1): 
                value = bool(value)
            else:
                flag = False
        elif re.match('cases', value_type):
            try:
                value = int(value)
            except:
                try: value = float(value)
                except: pass
        elif value_type == 'filename':
            value = str(value)
            t = re.match('.+\\..+', value)
            if t:
                value = t.group(0)
            else: 
                flag = False
        else:
            print(f'incorrect value {value} ({type(value)})')
            flag = False
        return value, flag 
    
class YesNoDelegate(QStyledItemDelegate):
    def __init__(self, wiget):
        super().__init__(wiget)
        self.labels = ['Да', 'Нет']
        self.items = [True, False]
        
    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.addItems(self.labels)
        combo.currentIndexChanged.connect(self.currentIndexChanged)
        return combo
        
    def setEditorData(self, editor, index):
        editor.blockSignals(True)
        if index.model().data(index) == 'True':
            i = 0
        elif index.model().data(index) == 'False':
            i = 1
        else:
            print(f'err: {index.model().data(index)}, {type(index.model().data(index))}')
        editor.setCurrentIndex(i)
        editor.blockSignals(False)
        
    def setModelData(self, editor, model, index):
        model.setData(index, self.items[editor.currentIndex()])
        
    @pyqtSlot()
    def currentIndexChanged(self):
        self.commitData.emit(self.sender())
    
    
class DropboxDelegate(QStyledItemDelegate):
    def __init__(self, wiget, items, labels=None):
        super().__init__(wiget)
        self.items = items
        if labels:
            self.labels = labels
        else:
            self.labels = items
        
    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.addItems(self.labels)
        combo.currentIndexChanged.connect(self.currentIndexChanged)
        return combo
        
    def setEditorData(self, editor, index):
        editor.blockSignals(True)
        editor.setCurrentIndex(self.items.index(index.model().data(index)))
        editor.blockSignals(False)
        
    def setModelData(self, editor, model, index):
        model.setData(index, self.items[editor.currentIndex()])
        
    @pyqtSlot()
    def currentIndexChanged(self):
        self.commitData.emit(self.sender())
        
class OpenFileDelegate(QStyledItemDelegate):
    def __init__(self, wiget):
        super().__init__(wiget)
        self.fname = ''
        
    def createEditor(self, parent, option, index):
        button = QPushButton(parent)
        button.clicked.connect(self.openFile)
        return button
        
    def setEditorData(self, editor, index):
        editor.blockSignals(True)
        editor.setText(str(index.model().data(index)))
        editor.blockSignals(False)
        
    def setModelData(self, editor, model, index):
        model.setData(index, self.fname)
        
    @pyqtSlot()
    def openFile(self):
        self.fname = QFileDialog.getOpenFileName(self.parent(), 'Open file')[0]
        self.commitData.emit(self.sender())

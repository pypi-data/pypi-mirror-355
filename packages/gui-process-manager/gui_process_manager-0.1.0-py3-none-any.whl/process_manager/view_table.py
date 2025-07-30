from PyQt6.QtWidgets import (QTableWidget, QTableWidgetItem, QMenu, QMessageBox, QWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

from .view_base import *
from .process_list import *

class CustomTableWidgetItem(QTableWidgetItem):
    
    def __init__(self, attr_key: str, value: ProcessItem):
        QTableWidgetItem.__init__(self)
        self.setValue(attr_key, value)
    
    def __lt__(self, other):
        if self.sort_key is not None:
            return self.sort_key < other.sort_key
        return super().__lt__(other)
    
    def setValue(self, attr_key: str, value: ProcessItem):
        self.setText(value.formatted_info.get(attr_key, ''))
        self.sort_key = value.info.get(attr_key, '')


class TableWidgetItemRowHelper:
    def __init__(self, value: ProcessItem):
        self.value = value

    def addToView(self, view: QTableWidget):
        row = view.rowCount()
        view.insertRow(row)
        for idx, column in enumerate(CONF_COLUMNS):
            item = CustomTableWidgetItem(column["key"], self.value)
            view.setItem(row, idx, item)
            item.setTextAlignment(CONF_COLUMNS[idx].get("textAlign", Qt.AlignmentFlag.AlignLeft))

    def updateToView(self, row: int, view: QTableWidget):
        for column_idx, column in enumerate(CONF_COLUMNS):
            if column.get("updateOnChanged", False):
                item: CustomTableWidgetItem = view.item(row, column_idx)
                item_pid = int(view.item(row, CONF_PID_COLUMN_IDX).text())
                if item_pid != self.value.pid:
                    raise ValueError(f"Row {row} PID mismatch: expected {self.value.pid}, found {item_pid}, may table reordered")
                item.setValue(column["key"], self.value)

class ProcessTableView(QTableWidget):

    def __init__(self, controller: ProcessListController, parent: QWidget=None):
        super().__init__(parent)
        self.controller = controller
        self.setColumnCount(len(CONF_COLUMNS))
        self.setHorizontalHeaderLabels(CONF_COLUMNS[i]["label"] for i in range(len(CONF_COLUMNS)))
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__show_context_menu)  # 使用新的上下文菜单处理函数
        self.setSortingEnabled(True)  # 启用排序
        self.verticalHeader().setDefaultSectionSize(15)  # 设置行高为15
        
        # 设置列宽
        for i in range(len(CONF_COLUMNS)):
            self.setColumnWidth(i, CONF_COLUMNS[i].get("columnWidth", 100))  # 其他列初始宽度为100
        self.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)


    def update_processes(self, filtered_processes: dict[int, ProcessItem]):
        # 禁用排序，避免在更新过程中触发排序，导致row索引变化问题
        self.setSortingEnabled(False)
        # 保存当前表格中的进程信息
        current_processes: dict[int, int] = {}
        for row in range(self.rowCount()):
            pid = int(self.item(row, CONF_PID_COLUMN_IDX).text())
            current_processes[pid] = row
        # 更新进程
        need_updated_pids = set(filtered_processes.keys()) & set(current_processes.keys())
        for pid in need_updated_pids:
            row = current_processes[pid]
            rowViewItem = TableWidgetItemRowHelper(filtered_processes[pid])
            rowViewItem.updateToView(row, self)
        # 移除不再存在的进程
        need_remove_pids = set(current_processes.keys()) - set(filtered_processes.keys())
        # 从后向前删除，避免索引变化问题
        for row in sorted([current_processes[pid] for pid in need_remove_pids], reverse=True):
            self.removeRow(row)
        # 添加新进程
        need_added_pids = set(filtered_processes.keys()) - set(current_processes.keys())
        for pid in need_added_pids:
            info = filtered_processes[pid]
            rowViewItem = TableWidgetItemRowHelper(filtered_processes[pid])
            rowViewItem.addToView(self)
        # 恢复排序功能
        self.setSortingEnabled(True)

    def __show_context_menu(self, position):
        item = self.itemAt(position)
        if item:
            menu = QMenu()
            kill_action = QAction("终止进程", self)
            kill_action.triggered.connect(lambda: self.__kill_process(item))
            menu.addAction(kill_action)
            menu.exec(self.viewport().mapToGlobal(position))

    def __kill_process(self, item):
        row = item.row()
        pid = int(self.item(row, CONF_PID_COLUMN_IDX).text())  # PID在第二列
        reply = QMessageBox.question(self, '确认终止',
                                    f'确定要终止进程 {pid} 及其所有子进程吗？',
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.controller.kill_process_and_children(pid)
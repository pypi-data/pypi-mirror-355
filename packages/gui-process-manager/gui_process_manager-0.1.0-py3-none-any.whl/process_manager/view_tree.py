from PyQt6.QtWidgets import (QTreeWidget, QTreeWidgetItem, QMenu, QMessageBox, QWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

from .view_base import *
from .process_list import *

class CustomTreeWidgetItem(QTreeWidgetItem):
    def __init__(self, parent: QTreeWidgetItem, value: ProcessItem):
        super().__init__(parent)
        self.value = value

    def __lt__(self, other):
        other: CustomTreeWidgetItem = other
        if self.value.pid == other.value.pid:
            return False
        column = self.treeWidget().sortColumn()
        return self.__get_value_for_sorting(column) < other.__get_value_for_sorting(column)
    
    def __get_value_for_sorting(self, column_idx: int):
        key = CONF_COLUMNS[column_idx]["key"]
        return self.value.info.get(key, '')

class TreeWidgetItemHelper:
    def __init__(self, value: ProcessItem):
        self.value = value

    def addToView(self, parent: QTreeWidgetItem) -> QTreeWidgetItem:
        item = CustomTreeWidgetItem(parent, self.value)
        for column_idx, column in enumerate(CONF_COLUMNS):
            item.setText(column_idx, self.value.formatted_info.get(column["key"], ''))
            item.setTextAlignment(column_idx, column.get("textAlign", Qt.AlignmentFlag.AlignLeft))
        return item

    def updateToView(self, target: QTreeWidgetItem):
        item = target
        for column_idx, column in enumerate(CONF_COLUMNS):
            if column.get("updateOnChanged", False):
                item.setText(column_idx, self.value.formatted_info.get(column["key"], ''))

class ProcessTreeView(QTreeWidget):

    def __init__(self, controller: ProcessListController, parent: QWidget=None):
        super().__init__(parent)
        self.controller = controller
        self.setHeaderLabels(CONF_COLUMNS[i]["label"] for i in range(len(CONF_COLUMNS)))
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__show_context_menu)
        self.setSortingEnabled(True)  # 启用排序

        # 设置列宽
        for i in range(len(CONF_COLUMNS)):
            self.setColumnWidth(i, CONF_COLUMNS[i].get("columnWidth", 100))  # 其他列初始宽度为100
        self.setHorizontalScrollMode(QTreeWidget.ScrollMode.ScrollPerPixel)

    def __show_context_menu(self, position):
        item = self.itemAt(position)
        if item:
            menu = QMenu()
            kill_action = QAction("终止进程", self)
            kill_action.triggered.connect(lambda: self.__kill_process(item))
            menu.addAction(kill_action)
            menu.exec(self.viewport().mapToGlobal(position))

    def __kill_process(self, item):
        pid = int(item.text(CONF_PID_COLUMN_IDX))  # PID在第二列
        reply = QMessageBox.question(self, '确认终止',
                                   f'确定要终止进程 {pid} 及其所有子进程吗？',
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.controller.kill_process_and_children(pid)

    def __get_process_item(self, pid: int) -> ProcessItem | None:
        return self.controller.processes.get(pid)

    def update_processes(self, filtered_processes: dict[int, ProcessItem]):
        all_processes: dict[int, ProcessItem] = self.controller.processes
        avaliable_parent_processes = None

        if all_processes == filtered_processes:
            avaliable_parent_processes = all_processes
        else:
            avaliable_parent_processes = {
                ** filtered_processes
            }
            def __collect_parent_processes(sub_process: ProcessItem):
                parent_item = all_processes.get(sub_process.ppid)
                if parent_item:
                    avaliable_parent_processes[parent_item.pid] = parent_item
                    __collect_parent_processes(parent_item)
            
            for proc in filtered_processes.values():
                __collect_parent_processes(proc)

        def __update_process_subtree(sub_processes: list[ProcessItem], parent_item: QTreeWidgetItem, includeAllChildren: bool = False):
            # 保存当前树的状态
            current_items: dict[int, QTreeWidgetItem] = {}

            for idx in range(parent_item.childCount()):
                item = parent_item.child(idx)
                pid = int(item.text(CONF_PID_COLUMN_IDX))  # 获取PID
                current_items[pid] = item
            
            # 更新或添加新进程
            
            for proc in sub_processes:
                widget_item = None
                if proc.pid not in current_items:
                    # 新进程，添加到树中
                    helper = TreeWidgetItemHelper(proc)
                    widget_item = helper.addToView(parent_item)
                else:
                    # 更新现有进程信息
                    widget_item = current_items[proc.pid]
                    helper = TreeWidgetItemHelper(proc)
                    helper.updateToView(widget_item)
                
                if includeAllChildren or proc.pid in filtered_processes:
                    __update_process_subtree(proc.children, widget_item, True)
                else:
                    children = [proc for proc in proc.children if proc.pid in avaliable_parent_processes]
                    __update_process_subtree(children, widget_item, False)

            # 移除不再存在的进程
            need_remove_pids = set(current_items.keys()) - set(proc.pid for proc in sub_processes)
            for pid in need_remove_pids:
                parent_item.removeChild(current_items[pid])
            
        # 获取顶层进程，如果进程的父进程是1或None，则认为它是顶层进程
        top_processes = [proc for proc in avaliable_parent_processes.values() if proc.ppid == 1 or proc.ppid == None]
        __update_process_subtree(top_processes, self.invisibleRootItem(), False)
        
        if all_processes != filtered_processes:
            self.expandAll()  # 展开所有节点
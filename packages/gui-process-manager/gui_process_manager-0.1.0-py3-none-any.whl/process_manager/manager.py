from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QLineEdit, QLabel, QSpinBox, QCheckBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor

from .process_list import *
from .view_base import *
from .view_table import *
from .view_tree import *

class ProcessManager(QMainWindow):
    def __init__(self):
        super().__init__()

        self.search_filter = ""

        self.controller = ProcessListController()
        self.controller.onProcessListChanged.connect(self.__update_process_list_for_view)
        self.controller.start()
        
        self.setWindowTitle("进程管理器")
        self.setGeometry(100, 100, 1600, 800)
        self.setup_ui()
        self.setup_dark_theme()

    def setup_dark_theme(self):
        # 设置深色主题
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        self.setPalette(palette)

    def setup_ui(self):

        default_tree_mode = False  # 默认使用树形视图模式

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 创建搜索框
        search_layout = QHBoxLayout()
        search_label = QLabel("搜索进程:")
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.__on_search_change)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # 创建树形视图
        self.tree = ProcessTreeView(self.controller)
        self.tree.setVisible(default_tree_mode)  # 根据默认模式设置可见性
        layout.addWidget(self.tree)

        # 创建普通表格视图
        self.table = ProcessTableView(self.controller)
        self.table.setVisible(not default_tree_mode)  # 根据默认模式设置可见性
        layout.addWidget(self.table)

        # 创建刷新间隔控制
        refresh_layout = QHBoxLayout()
        refresh_label = QLabel("刷新间隔(秒):")
        self.refresh_interval = QSpinBox()
        self.refresh_interval.setRange(1, 60)
        self.refresh_interval.setValue(5)
        self.refresh_interval.valueChanged.connect(self.__update_refresh_interval)
        refresh_layout.addWidget(refresh_label)
        refresh_layout.addWidget(self.refresh_interval)
        refresh_layout.addStretch()
        self.switch_checkbox = QCheckBox("树表模式")
        self.switch_checkbox.setChecked(default_tree_mode)
        self.switch_checkbox.stateChanged.connect(self.__toggle_view_mode)
        refresh_layout.addWidget(self.switch_checkbox)
        layout.addLayout(refresh_layout)

    def __update_refresh_interval(self, value: int):
        self.controller.interval = value

    def __on_search_change(self, text):
        self.search_filter = text.lower()
        self.__update_process_list_for_view(self.controller.processes)

    def __toggle_view_mode(self, state):
        if state == Qt.CheckState.Checked.value:
            self.table.hide()
            self.tree.show()
        else:
            self.tree.hide()
            self.table.show()
        self.__update_process_list_for_view(self.controller.processes)

    def __filter_matched_search_processes(self, processes: dict[int, ProcessItem]) -> dict[int, ProcessItem]:
        filteredProcesses = {}
        if self.search_filter:
            columnsForFilter = ['pid', 'name', 'command']
            for pid, item in processes.items():
                for column in columnsForFilter:
                    if self.search_filter in str(item.formatted_info[column]).lower():
                        filteredProcesses[pid] = item
                        break
        else:
            filteredProcesses = processes
        return filteredProcesses

    def __update_process_list_for_view(self, processes: dict[int, ProcessItem]):
        self.controller.processes = processes
        filtered_processes = self.__filter_matched_search_processes(processes)
        if self.switch_checkbox.isChecked():
            self.tree.update_processes(filtered_processes)
        else:
            self.table.update_processes(filtered_processes)
        
    def closeEvent(self, event):
        # 设置停止标志
        self.controller.stop()
        # 等待线程自然结束，最多等待1秒
        if not self.controller.wait(1000):
            # 如果超时，强制终止线程
            self.controller.terminate()
        event.accept()
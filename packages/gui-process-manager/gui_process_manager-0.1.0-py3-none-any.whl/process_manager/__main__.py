import logging
import sys
import warnings

from PyQt6.QtWidgets import QApplication

from .manager import ProcessManager

# 过滤掉所有 sipPyTypeDict 相关的弃用警告
warnings.filterwarnings("ignore", message=".*sipPyTypeDict.*")

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ProcessManager()
    window.show()
    sys.exit(app.exec()) 
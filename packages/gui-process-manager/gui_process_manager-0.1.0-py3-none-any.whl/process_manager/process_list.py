import psutil
import time
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal
import signal


class ProcessItem:

    def __init__(self, proc: psutil.Process):
        self.pid = proc.pid
        self.ppid = proc.info['ppid']
        self.proc = proc
        self.info = self.__gen_info()
        self.formatted_info = self.__gen_formatted_info()
        self.children: list[ProcessItem] = []

    def __gen_info(self):
        try:
            return {
                'pid': self.proc.info['pid'],
                'ppid': self.proc.info['ppid'],
                'name': self.proc.info['name'],
                'cpu_time': self.proc.info['cpu_times'].user,
                'cpu_percent': self.proc.info['cpu_percent'],
                'start_time': self.proc.info['create_time'],
                'avg_time': (self.proc.info['cpu_times'].user / (datetime.now().timestamp() - self.proc.info['create_time'])) * 1000,
                'memory': self.proc.info['memory_info'].rss / 1024 / 1024,
                'memory_percent': self.proc.info['memory_percent'],
                'command': self.proc.info['cmdline'],
                'username': self.proc.info['username'],
                'duration_time': datetime.now().timestamp() - self.proc.info['create_time']
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {}
        
    def __gen_formatted_info(self):
        if not self.info:
            return {}
        duration_seconds = int(datetime.now().timestamp() - self.info['start_time'])
        days, remainder = divmod(duration_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        duration_time = f"{days:02d}d{hours:02d}h{minutes:02d}m{seconds:02d}s"

        return {
            ** self.info,
            'pid': str(self.info['pid']),
            'ppid': str(self.info['ppid']),
            'cpu_time': f"{self.info['cpu_time']:.2f}s",
            'cpu_percent': f"{self.proc.info['cpu_percent']}%",
            'start_time': datetime.fromtimestamp(self.info['start_time']).strftime('%m-%d %H:%M'),
            'avg_time': f"{self.info['avg_time']:.3f}ms",
            'memory': f"{self.info['memory']:.1f}MB",
            'command': ' '.join(self.info['command']),
            'duration_time': duration_time,
        }
    
class ProcessListController(QThread):

    onProcessListChanged = pyqtSignal(dict)
    processes: dict[int, ProcessItem] = {}
    interval: int = 5  # 默认刷新间隔为5秒

    def __init__(self):
        super().__init__()
        self.running = True

    def query_processes(self):
        _processes: dict[int, ProcessItem] = {}
        for proc in psutil.process_iter(['name', 'pid', 'ppid', 'cpu_times', 'cpu_percent', 'create_time', 'memory_info', 'memory_percent', 'cmdline', 'username']):
            try:
                _processes[proc.pid] = ProcessItem(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        for pid, process in _processes.items():
            parent_proc = _processes.get(process.ppid)
            if parent_proc and parent_proc.pid != 1:
                if parent_proc.pid != pid:
                    parent_proc.children.append(process)
        self.processes = _processes
        self.onProcessListChanged.emit(_processes)

    def run(self):
        while self.running:
            self.query_processes()
            time.sleep(self.interval)

    def stop(self):
        self.running = False
        self.wait()

    def kill_process_and_children(self, pid):
        try:
            process = psutil.Process(pid)
            children = process.children(recursive=True)
            
            # 首先尝试使用SIGTERM
            for child in children:
                try:
                    child.send_signal(signal.SIGTERM)
                except psutil.NoSuchProcess:
                    pass
            
            try:
                process.send_signal(signal.SIGTERM)
            except psutil.NoSuchProcess:
                pass
            
            # 等待10秒
            time.sleep(10)
            
            # 检查进程是否还存在，如果存在则使用SIGKILL
            for child in children:
                try:
                    if child.is_running():
                        child.kill()
                except psutil.NoSuchProcess:
                    pass
            
            try:
                if process.is_running():
                    process.kill()
            except psutil.NoSuchProcess:
                pass
                
        except psutil.NoSuchProcess:
            pass
        self.query_processes()
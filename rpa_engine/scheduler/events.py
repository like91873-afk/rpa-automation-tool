"""
RPA自动化工具 - 事件管理系统

提供文件监控、条件触发等事件驱动功能
"""

import fnmatch
import hashlib
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from ..models.schemas import (
    ExecutionHistory,
    FileWatchEvent,
    Schedule,
    ScheduleStatus,
    TriggerType,
)


class FileChangeEvent:
    """文件变化事件"""

    def __init__(self, path: str, event_type: FileWatchEvent,
                 timestamp: datetime = None, old_path: str = None):
        self.path = path
        self.event_type = event_type
        self.timestamp = timestamp or datetime.now()
        self.old_path = old_path
        self.is_directory = os.path.isdir(path)
        self.file_size = os.path.getsize(path) if os.path.exists(path) and not self.is_directory else 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "old_path": self.old_path,
            "is_directory": self.is_directory,
            "file_size": self.file_size,
        }


class FileWatcher:
    """文件监控器

    监控指定目录的文件变化（创建、修改、删除、移动）。
    使用轮询方式实现，兼容所有操作系统。
    """

    def __init__(self, watch_path: str, pattern: str = "*",
                 recursive: bool = False, poll_interval: float = 2.0):
        """
        Args:
            watch_path: 监控的目录路径
            pattern: 文件匹配模式 (*.txt, data_*.csv)
            recursive: 是否递归监控子目录
            poll_interval: 轮询间隔（秒）
        """
        self.watch_path = os.path.abspath(watch_path)
        self.pattern = pattern
        self.recursive = recursive
        self.poll_interval = poll_interval

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._file_states: Dict[str, float] = {}  # path -> mtime
        self._callbacks: List[Callable[[FileChangeEvent], None]] = []
        self._watched_events: Set[FileWatchEvent] = set()

    def on_change(self, callback: Callable[[FileChangeEvent], None]):
        """注册变化回调"""
        self._callbacks.append(callback)

    def set_watched_events(self, events: List[FileWatchEvent]):
        """设置监控的事件类型"""
        self._watched_events = set(events)

    def start(self):
        """开始监控"""
        if self._running:
            return

        if not os.path.exists(self.watch_path):
            raise FileNotFoundError(f"监控路径不存在: {self.watch_path}")

        self._running = True
        self._scan_initial_state()
        self._thread = threading.Thread(
            target=self._watch_loop,
            daemon=True,
            name=f"file-watcher-{self.watch_path}"
        )
        self._thread.start()

    def stop(self):
        """停止监控"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=self.poll_interval * 2)
            self._thread = None

    def is_running(self) -> bool:
        return self._running

    def _scan_initial_state(self):
        """扫描初始文件状态"""
        self._file_states.clear()
        for file_path in self._iter_files():
            try:
                self._file_states[file_path] = os.path.getmtime(file_path)
            except OSError:
                pass

    def _iter_files(self):
        """遍历监控文件"""
        if self.recursive:
            for root, dirs, files in os.walk(self.watch_path):
                for f in files:
                    full_path = os.path.join(root, f)
                    if fnmatch.fnmatch(f, self.pattern):
                        yield full_path
        else:
            try:
                for f in os.listdir(self.watch_path):
                    full_path = os.path.join(self.watch_path, f)
                    if os.path.isfile(full_path) and fnmatch.fnmatch(f, self.pattern):
                        yield full_path
            except PermissionError:
                pass

    def _watch_loop(self):
        """监控主循环"""
        while self._running:
            try:
                self._check_changes()
            except Exception as e:
                print(f"文件监控异常: {e}")
            time.sleep(self.poll_interval)

    def _check_changes(self):
        """检查文件变化"""
        current_files: Dict[str, float] = {}

        for file_path in self._iter_files():
            try:
                mtime = os.path.getmtime(file_path)
                current_files[file_path] = mtime

                if file_path not in self._file_states:
                    # 新文件
                    self._fire_event(file_path, FileWatchEvent.CREATED)
                elif mtime != self._file_states[file_path]:
                    # 文件修改
                    self._fire_event(file_path, FileWatchEvent.MODIFIED)

            except OSError:
                pass

        # 检查删除的文件
        for old_path in set(self._file_states.keys()) - set(current_files.keys()):
            self._fire_event(old_path, FileWatchEvent.DELETED)

        self._file_states = current_files

    def _fire_event(self, path: str, event_type: FileWatchEvent):
        """触发事件"""
        # 检查是否在监控列表中
        if self._watched_events and event_type not in self._watched_events:
            return

        event = FileChangeEvent(path=path, event_type=event_type)

        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                print(f"文件事件回调执行失败: {e}")

    def get_watched_files(self) -> List[str]:
        """获取当前监控的文件列表"""
        return list(self._file_states.keys())


class EventManager:
    """事件管理器

    统一管理文件监控、条件触发等事件系统。
    将事件与调度器连接，实现事件驱动的流程执行。
    """

    def __init__(self, scheduler=None):
        """
        Args:
            scheduler: FlowScheduler实例，用于触发流程执行
        """
        self._scheduler = scheduler
        self._watchers: Dict[str, FileWatcher] = {}  # schedule_id -> watcher
        self._event_log: List[Dict[str, Any]] = []
        self._max_log_size = 1000

    def set_scheduler(self, scheduler):
        """设置调度器"""
        self._scheduler = scheduler

    def start_file_watch(self, schedule: Schedule) -> bool:
        """为调度任务启动文件监控"""
        if not schedule.watch_path:
            return False

        watcher_key = schedule.id
        if watcher_key in self._watchers:
            self.stop_file_watch(schedule.id)

        try:
            watcher = FileWatcher(
                watch_path=schedule.watch_path,
                pattern=schedule.watch_pattern,
                recursive=schedule.watch_recursive,
            )
            watcher.set_watched_events(schedule.watch_events)

            # 注册回调
            def on_file_change(event: FileChangeEvent):
                self._handle_file_event(schedule, event)

            watcher.on_change(on_file_change)
            watcher.start()

            self._watchers[watcher_key] = watcher
            return True

        except Exception as e:
            print(f"启动文件监控失败: {e}")
            return False

    def stop_file_watch(self, schedule_id: str) -> bool:
        """停止文件监控"""
        watcher = self._watchers.pop(schedule_id, None)
        if watcher:
            watcher.stop()
            return True
        return False

    def stop_all(self):
        """停止所有监控"""
        for watcher in self._watchers.values():
            watcher.stop()
        self._watchers.clear()

    def get_active_watchers(self) -> Dict[str, Dict[str, Any]]:
        """获取所有活跃的监控器信息"""
        result = {}
        for schedule_id, watcher in self._watchers.items():
            result[schedule_id] = {
                "watch_path": watcher.watch_path,
                "pattern": watcher.pattern,
                "recursive": watcher.recursive,
                "is_running": watcher.is_running(),
                "file_count": len(watcher.get_watched_files()),
            }
        return result

    def _handle_file_event(self, schedule: Schedule, event: FileChangeEvent):
        """处理文件事件"""
        # 记录事件日志
        log_entry = {
            "timestamp": event.timestamp.isoformat(),
            "schedule_id": schedule.id,
            "event_type": event.event_type.value,
            "path": event.path,
            "file_size": event.file_size,
        }
        self._event_log.append(log_entry)
        if len(self._event_log) > self._max_log_size:
            self._event_log = self._event_log[-self._max_log_size:]

        # 触发流程执行
        if self._scheduler:
            try:
                variables = dict(schedule.initial_variables)
                variables["event_type"] = event.event_type.value
                variables["event_path"] = event.path
                variables["event_timestamp"] = event.timestamp.isoformat()
                variables["event_file_size"] = event.file_size

                self._scheduler._execute_schedule(
                    schedule=schedule,
                    trigger_type=TriggerType.FILE_WATCH,
                    trigger_info=f"文件{event.event_type.value}: {event.path}",
                    extra_variables=variables,
                )
            except Exception as e:
                print(f"文件事件触发执行失败: {e}")

    def get_event_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取事件日志"""
        return self._event_log[-limit:]

    def clear_event_log(self):
        """清空事件日志"""
        self._event_log.clear()

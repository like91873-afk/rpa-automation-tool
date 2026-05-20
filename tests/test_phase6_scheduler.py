"""
Phase 6 测试 - 调度系统

测试调度引擎、Cron解析、事件管理、文件监控等
"""

import os
import sys
import time
import tempfile
import threading
from datetime import datetime, timedelta

import pytest

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rpa_engine.models.schemas import (
    ExecutionHistory,
    ExecutionStatus,
    Flow,
    NodeInstance,
    NodeType,
    Schedule,
    ScheduleStatus,
    TriggerType,
    FileWatchEvent,
)
from rpa_engine.scheduler.scheduler import FlowScheduler, CronExpression
from rpa_engine.scheduler.events import FileWatcher, EventManager, FileChangeEvent


# ============= Cron表达式测试 =============

class TestCronExpression:
    """Cron表达式解析和匹配测试"""

    def test_parse_wildcard(self):
        """测试通配符解析"""
        cron = CronExpression("* * * * *")
        now = datetime(2024, 6, 15, 10, 30)
        assert cron.matches(now)

    def test_parse_specific_values(self):
        """测试精确值解析"""
        cron = CronExpression("30 10 * * *")
        # 10:30 匹配
        assert cron.matches(datetime(2024, 6, 15, 10, 30))
        # 10:31 不匹配
        assert not cron.matches(datetime(2024, 6, 15, 10, 31))
        # 11:30 不匹配
        assert not cron.matches(datetime(2024, 6, 15, 11, 30))

    def test_parse_step_values(self):
        """测试步长值解析"""
        cron = CronExpression("*/15 * * * *")
        assert cron.matches(datetime(2024, 6, 15, 10, 0))
        assert cron.matches(datetime(2024, 6, 15, 10, 15))
        assert cron.matches(datetime(2024, 6, 15, 10, 30))
        assert cron.matches(datetime(2024, 6, 15, 10, 45))
        assert not cron.matches(datetime(2024, 6, 15, 10, 10))

    def test_parse_range(self):
        """测试范围解析"""
        cron = CronExpression("0 9-17 * * *")
        assert cron.matches(datetime(2024, 6, 15, 9, 0))
        assert cron.matches(datetime(2024, 6, 15, 12, 0))
        assert cron.matches(datetime(2024, 6, 15, 17, 0))
        assert not cron.matches(datetime(2024, 6, 15, 8, 0))
        assert not cron.matches(datetime(2024, 6, 15, 18, 0))

    def test_parse_list(self):
        """测试列表值解析"""
        cron = CronExpression("0 9,12,18 * * *")
        assert cron.matches(datetime(2024, 6, 15, 9, 0))
        assert cron.matches(datetime(2024, 6, 15, 12, 0))
        assert cron.matches(datetime(2024, 6, 15, 18, 0))
        assert not cron.matches(datetime(2024, 6, 15, 10, 0))

    def test_parse_weekday(self):
        """测试星期解析"""
        # 周一到周五 (1-5)
        cron = CronExpression("0 9 * * 1-5")
        # 2024-06-17 是周一
        assert cron.matches(datetime(2024, 6, 17, 9, 0))
        # 2024-06-15 是周六
        assert not cron.matches(datetime(2024, 6, 15, 9, 0))
        # 2024-06-16 是周日
        assert not cron.matches(datetime(2024, 6, 16, 9, 0))

    def test_parse_invalid_expression(self):
        """测试无效表达式"""
        with pytest.raises(ValueError):
            CronExpression("invalid")

        with pytest.raises(ValueError):
            CronExpression("* * *")  # 字段不足

    def test_parse_out_of_range(self):
        """测试超出范围的值"""
        with pytest.raises(ValueError):
            CronExpression("60 * * * *")  # 分钟最大59

        with pytest.raises(ValueError):
            CronExpression("* 24 * * *")  # 小时最大23

    def test_next_run_time(self):
        """测试下次运行时间计算"""
        cron = CronExpression("30 10 * * *")
        after = datetime(2024, 6, 15, 8, 0)
        next_run = cron.next_run_time(after)
        assert next_run == datetime(2024, 6, 15, 10, 30)

    def test_next_run_time_next_day(self):
        """测试跨天的下次运行时间"""
        cron = CronExpression("30 10 * * *")
        after = datetime(2024, 6, 15, 11, 0)
        next_run = cron.next_run_time(after)
        assert next_run == datetime(2024, 6, 16, 10, 30)


# ============= FlowScheduler测试 =============

class TestFlowScheduler:
    """流程调度器测试"""

    @pytest.fixture
    def sample_schedule(self):
        """创建示例调度任务"""
        return Schedule(
            id="test-schedule-1",
            name="测试调度任务",
            flow_id="test-flow-1",
            trigger_type=TriggerType.CRON,
            cron_expression="*/5 * * * *",
            initial_variables={"test_var": "hello"},
        )

    @pytest.fixture
    def scheduler(self):
        """创建调度器实例"""
        execution_results = []

        def mock_executor(flow_id, variables):
            result = {
                "flow_id": flow_id,
                "variables": variables,
                "status": "completed",
            }
            execution_results.append(result)
            return result

        sched = FlowScheduler(flow_executor=mock_executor)
        sched._execution_results = execution_results
        return sched

    def test_add_schedule(self, scheduler, sample_schedule):
        """测试添加调度任务"""
        result = scheduler.add_schedule(sample_schedule)
        assert result.id == sample_schedule.id
        assert scheduler.get_schedule(sample_schedule.id) is not None

    def test_remove_schedule(self, scheduler, sample_schedule):
        """测试删除调度任务"""
        scheduler.add_schedule(sample_schedule)
        assert scheduler.remove_schedule(sample_schedule.id)
        assert scheduler.get_schedule(sample_schedule.id) is None

    def test_update_schedule(self, scheduler, sample_schedule):
        """测试更新调度任务"""
        scheduler.add_schedule(sample_schedule)
        updated = scheduler.update_schedule(sample_schedule.id, {
            "name": "更新后的任务",
            "cron_expression": "*/10 * * * *"
        })
        assert updated.name == "更新后的任务"
        assert updated.cron_expression == "*/10 * * * *"

    def test_pause_resume(self, scheduler, sample_schedule):
        """测试暂停和恢复"""
        scheduler.add_schedule(sample_schedule)

        paused = scheduler.pause_schedule(sample_schedule.id)
        assert paused.status == ScheduleStatus.PAUSED

        resumed = scheduler.resume_schedule(sample_schedule.id)
        assert resumed.status == ScheduleStatus.ACTIVE

    def test_list_schedules(self, scheduler, sample_schedule):
        """测试列出调度任务"""
        scheduler.add_schedule(sample_schedule)

        all_schedules = scheduler.list_schedules()
        assert len(all_schedules) == 1

        active_schedules = scheduler.list_schedules(ScheduleStatus.ACTIVE)
        assert len(active_schedules) == 1

        paused_schedules = scheduler.list_schedules(ScheduleStatus.PAUSED)
        assert len(paused_schedules) == 0

    def test_trigger_manual(self, scheduler, sample_schedule):
        """测试手动触发"""
        scheduler.add_schedule(sample_schedule)
        history = scheduler.trigger_schedule(sample_schedule.id)

        assert history.schedule_id == sample_schedule.id
        assert history.trigger_type == TriggerType.MANUAL

    def test_trigger_webhook(self, scheduler):
        """测试Webhook触发"""
        schedule = Schedule(
            id="webhook-schedule",
            name="Webhook任务",
            flow_id="test-flow",
            trigger_type=TriggerType.WEBHOOK,
            webhook_token="test-token-123",
            webhook_secret="secret-key",
        )
        scheduler.add_schedule(schedule)

        # 使用正确的token和secret触发
        history = scheduler.trigger_webhook("test-token-123", {"key": "value"}, "secret-key")
        assert history.schedule_id == schedule.id
        assert history.trigger_type == TriggerType.WEBHOOK

    def test_webhook_wrong_token(self, scheduler):
        """测试错误的Webhook token"""
        with pytest.raises(ValueError, match="无效的Webhook令牌"):
            scheduler.trigger_webhook("invalid-token")

    def test_webhook_wrong_secret(self, scheduler):
        """测试错误的Webhook密钥"""
        schedule = Schedule(
            id="webhook-schedule-2",
            name="Webhook任务2",
            flow_id="test-flow",
            trigger_type=TriggerType.WEBHOOK,
            webhook_token="valid-token",
            webhook_secret="correct-secret",
        )
        scheduler.add_schedule(schedule)

        with pytest.raises(ValueError, match="Webhook密钥验证失败"):
            scheduler.trigger_webhook("valid-token", secret="wrong-secret")

    def test_interval_schedule(self, scheduler):
        """测试间隔触发配置"""
        schedule = Schedule(
            id="interval-schedule",
            name="间隔任务",
            flow_id="test-flow",
            trigger_type=TriggerType.INTERVAL,
            interval_seconds=60,
        )
        result = scheduler.add_schedule(schedule)
        assert result.next_run_at is not None
        assert result.next_run_at > datetime.now()

    def test_once_schedule(self, scheduler):
        """测试单次触发配置"""
        future_time = datetime.now() + timedelta(hours=1)
        schedule = Schedule(
            id="once-schedule",
            name="单次任务",
            flow_id="test-flow",
            trigger_type=TriggerType.ONCE,
            run_at=future_time,
        )
        result = scheduler.add_schedule(schedule)
        assert result.next_run_at is not None

    def test_validation_cron_without_expression(self, scheduler):
        """测试Cron触发器缺少表达式"""
        schedule = Schedule(
            id="invalid-cron",
            name="无效Cron",
            flow_id="test-flow",
            trigger_type=TriggerType.CRON,
        )
        with pytest.raises(ValueError, match="必须设置cron_expression"):
            scheduler.add_schedule(schedule)

    def test_validation_interval_without_seconds(self, scheduler):
        """测试间隔触发器缺少间隔"""
        schedule = Schedule(
            id="invalid-interval",
            name="无效间隔",
            flow_id="test-flow",
            trigger_type=TriggerType.INTERVAL,
        )
        with pytest.raises(ValueError, match="必须设置大于0的interval_seconds"):
            scheduler.add_schedule(schedule)

    def test_validation_once_without_time(self, scheduler):
        """测试单次触发器缺少时间"""
        schedule = Schedule(
            id="invalid-once",
            name="无效单次",
            flow_id="test-flow",
            trigger_type=TriggerType.ONCE,
        )
        with pytest.raises(ValueError, match="必须设置run_at时间"):
            scheduler.add_schedule(schedule)

    def test_validation_filewatch_without_path(self, scheduler):
        """测试文件监控缺少路径"""
        schedule = Schedule(
            id="invalid-watch",
            name="无效监控",
            flow_id="test-flow",
            trigger_type=TriggerType.FILE_WATCH,
        )
        with pytest.raises(ValueError, match="必须设置watch_path"):
            scheduler.add_schedule(schedule)

    def test_get_history(self, scheduler, sample_schedule):
        """测试获取执行历史"""
        scheduler.add_schedule(sample_schedule)
        scheduler.trigger_schedule(sample_schedule.id)

        history = scheduler.get_history(sample_schedule.id)
        assert len(history) == 1
        assert history[0].schedule_id == sample_schedule.id

    def test_clear_history(self, scheduler, sample_schedule):
        """测试清空执行历史"""
        scheduler.add_schedule(sample_schedule)
        scheduler.trigger_schedule(sample_schedule.id)

        scheduler.clear_history(sample_schedule.id)
        history = scheduler.get_history(sample_schedule.id)
        assert len(history) == 0

    def test_statistics(self, scheduler, sample_schedule):
        """测试统计信息"""
        scheduler.add_schedule(sample_schedule)
        stats = scheduler.get_statistics()

        assert stats["total_schedules"] == 1
        assert stats["active"] == 1
        assert stats["paused"] == 0
        assert "total_executions" in stats
        assert "is_running" in stats

    def test_callbacks(self, scheduler, sample_schedule):
        """测试事件回调"""
        callback_called = []

        def on_schedule_added(schedule):
            callback_called.append(schedule.id)

        scheduler.on("schedule_added", on_schedule_added)
        scheduler.add_schedule(sample_schedule)

        assert len(callback_called) == 1
        assert callback_called[0] == sample_schedule.id

    def test_start_stop(self, scheduler):
        """测试启动和停止"""
        assert not scheduler.is_running()
        scheduler.start(check_interval=1.0)
        assert scheduler.is_running()
        scheduler.stop()
        assert not scheduler.is_running()

    def test_execute_with_retry(self, scheduler):
        """测试重试机制"""
        call_count = [0]

        def failing_executor(flow_id, variables):
            call_count[0] += 1
            if call_count[0] < 3:
                raise RuntimeError("模拟失败")
            return {"status": "completed"}

        sched = FlowScheduler(flow_executor=failing_executor)

        schedule = Schedule(
            id="retry-schedule",
            name="重试任务",
            flow_id="test-flow",
            trigger_type=TriggerType.INTERVAL,
            interval_seconds=60,
            max_retries=3,
            retry_delay_seconds=0,  # 不等待
        )
        sched.add_schedule(schedule)

        history = sched.trigger_schedule(schedule.id)
        assert history.status == ExecutionStatus.COMPLETED
        assert call_count[0] == 3


# ============= FileWatcher测试 =============

class TestFileWatcher:
    """文件监控器测试"""

    def test_scan_initial_state(self, tmp_path):
        """测试初始状态扫描"""
        # 创建测试文件
        (tmp_path / "test1.txt").write_text("hello")
        (tmp_path / "test2.csv").write_text("data")

        watcher = FileWatcher(str(tmp_path), pattern="*.txt")
        watcher._scan_initial_state()

        assert len(watcher._file_states) == 1
        assert str(tmp_path / "test1.txt") in watcher._file_states

    def test_detect_created(self, tmp_path):
        """测试检测文件创建"""
        watcher = FileWatcher(str(tmp_path), pattern="*.txt", poll_interval=0.1)
        events = []
        watcher.on_change(lambda e: events.append(e))

        watcher._scan_initial_state()

        # 创建新文件
        (tmp_path / "new.txt").write_text("new content")
        watcher._check_changes()

        assert len(events) == 1
        assert events[0].event_type == FileWatchEvent.CREATED

    def test_detect_modified(self, tmp_path):
        """测试检测文件修改"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("original")

        watcher = FileWatcher(str(tmp_path), pattern="*.txt", poll_interval=0.1)
        events = []
        watcher.on_change(lambda e: events.append(e))

        watcher._scan_initial_state()

        # 修改文件
        time.sleep(0.05)  # 确保mtime变化
        test_file.write_text("modified")
        watcher._check_changes()

        assert len(events) == 1
        assert events[0].event_type == FileWatchEvent.MODIFIED

    def test_detect_deleted(self, tmp_path):
        """测试检测文件删除"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("to be deleted")

        watcher = FileWatcher(str(tmp_path), pattern="*.txt", poll_interval=0.1)
        events = []
        watcher.on_change(lambda e: events.append(e))

        watcher._scan_initial_state()

        # 删除文件
        test_file.unlink()
        watcher._check_changes()

        assert len(events) == 1
        assert events[0].event_type == FileWatchEvent.DELETED

    def test_recursive_watch(self, tmp_path):
        """测试递归监控"""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "deep.txt").write_text("deep file")

        watcher = FileWatcher(str(tmp_path), pattern="*.txt", recursive=True)
        watcher._scan_initial_state()

        assert len(watcher._file_states) == 1

    def test_filter_by_events(self, tmp_path):
        """测试事件类型过滤"""
        watcher = FileWatcher(str(tmp_path), pattern="*.txt", poll_interval=0.1)
        watcher.set_watched_events([FileWatchEvent.CREATED])

        events = []
        watcher.on_change(lambda e: events.append(e))
        watcher._scan_initial_state()

        # 创建文件 - 应该触发
        (tmp_path / "new.txt").write_text("new")
        watcher._check_changes()
        assert len(events) == 1

    def test_start_stop(self, tmp_path):
        """测试启动和停止"""
        watcher = FileWatcher(str(tmp_path), poll_interval=0.1)
        watcher.start()
        assert watcher.is_running()
        watcher.stop()
        assert not watcher.is_running()

    def test_nonexistent_path(self):
        """测试不存在的路径"""
        watcher = FileWatcher("/nonexistent/path")
        with pytest.raises(FileNotFoundError):
            watcher.start()


# ============= EventManager测试 =============

class TestEventManager:
    """事件管理器测试"""

    @pytest.fixture
    def manager_with_scheduler(self):
        """创建带调度器的事件管理器"""
        scheduler = FlowScheduler(flow_executor=lambda fid, vars: {"status": "ok"})
        manager = EventManager(scheduler=scheduler)
        return manager, scheduler

    def test_start_stop_file_watch(self, manager_with_scheduler, tmp_path):
        """测试启动和停止文件监控"""
        manager, scheduler = manager_with_scheduler

        schedule = Schedule(
            id="watch-schedule",
            name="监控任务",
            flow_id="test-flow",
            trigger_type=TriggerType.FILE_WATCH,
            watch_path=str(tmp_path),
            watch_pattern="*.txt",
            watch_events=[FileWatchEvent.CREATED],
        )
        scheduler.add_schedule(schedule)

        result = manager.start_file_watch(schedule)
        assert result is True

        watchers = manager.get_active_watchers()
        assert "watch-schedule" in watchers

        manager.stop_file_watch("watch-schedule")
        watchers = manager.get_active_watchers()
        assert "watch-schedule" not in watchers

    def test_file_event_triggers_flow(self, manager_with_scheduler, tmp_path):
        """测试文件事件触发流程执行"""
        manager, scheduler = manager_with_scheduler

        schedule = Schedule(
            id="watch-schedule-2",
            name="监控任务2",
            flow_id="test-flow",
            trigger_type=TriggerType.FILE_WATCH,
            watch_path=str(tmp_path),
            watch_pattern="*.txt",
            watch_events=[FileWatchEvent.CREATED],
            initial_variables={"env": "test"},
        )
        scheduler.add_schedule(schedule)
        manager.start_file_watch(schedule)

        # 模拟文件事件
        event = FileChangeEvent(
            path=str(tmp_path / "test.txt"),
            event_type=FileWatchEvent.CREATED,
        )
        manager._handle_file_event(schedule, event)

        # 检查事件日志
        logs = manager.get_event_log()
        assert len(logs) >= 1
        assert logs[0]["event_type"] == "created"

    def test_stop_all(self, tmp_path):
        """测试停止所有监控"""
        scheduler = FlowScheduler()
        manager = EventManager(scheduler=scheduler)

        for i in range(3):
            schedule = Schedule(
                id=f"watch-{i}",
                name=f"监控{i}",
                flow_id="test-flow",
                trigger_type=TriggerType.FILE_WATCH,
                watch_path=str(tmp_path),
            )
            scheduler.add_schedule(schedule)
            manager.start_file_watch(schedule)

        manager.stop_all()
        assert len(manager.get_active_watchers()) == 0

    def test_event_log_limit(self, tmp_path):
        """测试事件日志限制"""
        scheduler = FlowScheduler()
        manager = EventManager(scheduler=scheduler)
        manager._max_log_size = 5

        schedule = Schedule(
            id="log-test",
            name="日志测试",
            flow_id="test-flow",
            trigger_type=TriggerType.FILE_WATCH,
            watch_path=str(tmp_path),
            watch_events=[FileWatchEvent.CREATED],
        )
        scheduler.add_schedule(schedule)

        # 触发多个事件
        for i in range(10):
            event = FileChangeEvent(
                path=f"/test/file{i}.txt",
                event_type=FileWatchEvent.CREATED,
            )
            manager._handle_file_event(schedule, event)

        # 应该被截断到5条
        assert len(manager.get_event_log()) == 5


# ============= 集成测试 =============

class TestSchedulerIntegration:
    """调度系统集成测试"""

    def test_cron_schedule_full_cycle(self):
        """测试Cron调度完整生命周期"""
        execution_log = []

        def mock_executor(flow_id, variables):
            execution_log.append({"flow_id": flow_id, "vars": variables})
            return {"status": "completed"}

        scheduler = FlowScheduler(flow_executor=mock_executor)

        schedule = Schedule(
            id="integration-cron",
            name="集成测试Cron",
            flow_id="test-flow",
            trigger_type=TriggerType.CRON,
            cron_expression="*/5 * * * *",
            initial_variables={"env": "test"},
        )

        # 添加
        scheduler.add_schedule(schedule)
        assert scheduler.get_schedule("integration-cron") is not None

        # 暂停
        scheduler.pause_schedule("integration-cron")
        assert scheduler.get_schedule("integration-cron").status == ScheduleStatus.PAUSED

        # 恢复
        scheduler.resume_schedule("integration-cron")
        assert scheduler.get_schedule("integration-cron").status == ScheduleStatus.ACTIVE

        # 手动触发
        history = scheduler.trigger_schedule("integration-cron")
        assert history.status == ExecutionStatus.COMPLETED
        assert len(execution_log) == 1

        # 检查历史
        records = scheduler.get_history("integration-cron")
        assert len(records) == 1

        # 统计
        stats = scheduler.get_statistics()
        assert stats["total_schedules"] == 1
        assert stats["total_executions"] == 1

        # 删除
        scheduler.remove_schedule("integration-cron")
        assert scheduler.get_schedule("integration-cron") is None

    def test_webhook_flow(self):
        """测试Webhook触发流程"""
        execution_log = []

        def mock_executor(flow_id, variables):
            execution_log.append({"flow_id": flow_id, "vars": variables})
            return {"status": "completed"}

        scheduler = FlowScheduler(flow_executor=mock_executor)

        schedule = Schedule(
            id="webhook-integration",
            name="Webhook集成测试",
            flow_id="test-flow",
            trigger_type=TriggerType.WEBHOOK,
            webhook_token="my-webhook-token",
            webhook_secret="my-secret",
            initial_variables={"base": "value"},
        )
        scheduler.add_schedule(schedule)

        # Webhook触发
        history = scheduler.trigger_webhook(
            "my-webhook-token",
            {"data": "test"},
            "my-secret"
        )

        assert history.status == ExecutionStatus.COMPLETED
        assert len(execution_log) == 1
        assert execution_log[0]["vars"]["base"] == "value"
        assert execution_log[0]["vars"]["webhook_payload"] == {"data": "test"}

    def test_file_watch_integration(self, tmp_path):
        """测试文件监控集成"""
        execution_log = []

        def mock_executor(flow_id, variables):
            execution_log.append({"flow_id": flow_id, "vars": variables})
            return {"status": "completed"}

        scheduler = FlowScheduler(flow_executor=mock_executor)
        manager = EventManager(scheduler=scheduler)

        schedule = Schedule(
            id="file-watch-integration",
            name="文件监控集成测试",
            flow_id="test-flow",
            trigger_type=TriggerType.FILE_WATCH,
            watch_path=str(tmp_path),
            watch_pattern="*.txt",
            watch_events=[FileWatchEvent.CREATED],
            initial_variables={"processor": "data-pipeline"},
        )
        scheduler.add_schedule(schedule)
        manager.start_file_watch(schedule)

        # 模拟文件创建事件
        event = FileChangeEvent(
            path=str(tmp_path / "data.txt"),
            event_type=FileWatchEvent.CREATED,
        )
        manager._handle_file_event(schedule, event)

        assert len(execution_log) == 1
        assert execution_log[0]["vars"]["event_type"] == "created"
        assert execution_log[0]["vars"]["processor"] == "data-pipeline"

        manager.stop_all()


# ============= 注册表完整性测试 =============

class TestSchedulerRegistry:
    """调度系统模块完整性测试"""

    def test_imports(self):
        """测试所有模块可以正确导入"""
        from rpa_engine.scheduler import FlowScheduler, EventManager, FileWatcher
        from rpa_engine.scheduler.scheduler import CronExpression

        assert FlowScheduler is not None
        assert EventManager is not None
        assert FileWatcher is not None
        assert CronExpression is not None

    def test_schedule_model(self):
        """测试Schedule模型"""
        schedule = Schedule(
            id="model-test",
            name="模型测试",
            flow_id="flow-1",
            trigger_type=TriggerType.CRON,
            cron_expression="0 9 * * *",
        )
        data = schedule.model_dump()
        assert data["id"] == "model-test"
        assert data["trigger_type"] == "cron"
        assert data["status"] == "active"

    def test_execution_history_model(self):
        """测试ExecutionHistory模型"""
        history = ExecutionHistory(
            id="hist-1",
            schedule_id="sched-1",
            flow_id="flow-1",
            trigger_type=TriggerType.MANUAL,
            status=ExecutionStatus.COMPLETED,
        )
        data = history.model_dump()
        assert data["id"] == "hist-1"
        assert data["status"] == "completed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

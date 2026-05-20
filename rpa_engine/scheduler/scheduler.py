"""
RPA自动化工具 - 流程调度引擎

支持的触发方式:
- Cron表达式: 类似Linux cron的定时任务
- 固定间隔: 每隔N秒执行一次
- 单次定时: 在指定时间执行一次
- Webhook: 通过HTTP请求触发
- 文件监控: 文件变化时触发
- 手动: 手动触发执行
"""

import uuid
import threading
import time
import re
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

import pytz

from ..models.schemas import (
    ExecutionHistory,
    ExecutionStatus,
    Flow,
    Schedule,
    ScheduleStatus,
    TriggerType,
)


class CronExpression:
    """Cron表达式解析器
    
    支持标准cron格式: 分 时 日 月 周
    - *: 任意值
    - */N: 每隔N个单位
    - N: 精确值
    - N,M: 列表
    - N-M: 范围
    """

    FIELD_RANGES = {
        "minute": (0, 59),
        "hour": (0, 23),
        "day": (1, 31),
        "month": (1, 12),
        "weekday": (0, 6),  # 0=周日
    }

    def __init__(self, expression: str):
        self.expression = expression.strip()
        self.fields = self._parse()

    def _parse(self) -> Dict[str, set]:
        """解析cron表达式"""
        parts = self.expression.split()
        if len(parts) != 5:
            raise ValueError(
                f"无效的cron表达式: '{self.expression}' - 需要5个字段 (分 时 日 月 周)"
            )

        field_names = ["minute", "hour", "day", "month", "weekday"]
        fields = {}

        for name, value_str in zip(field_names, parts):
            fields[name] = self._parse_field(name, value_str)

        return fields

    def _parse_field(self, field_name: str, value_str: str) -> set:
        """解析单个cron字段"""
        min_val, max_val = self.FIELD_RANGES[field_name]
        results = set()

        # 处理逗号分隔的多个值
        for part in value_str.split(","):
            part = part.strip()

            if part == "*":
                results.update(range(min_val, max_val + 1))
            elif part.startswith("*/"):
                step = int(part[2:])
                if step <= 0:
                    raise ValueError(f"无效的步长: {part}")
                results.update(range(min_val, max_val + 1, step))
            elif "-" in part:
                # 范围
                start, end = part.split("-", 1)
                start, end = int(start), int(end)
                if start < min_val or end > max_val or start > end:
                    raise ValueError(f"范围超出限制 [{min_val}-{max_val}]: {part}")
                results.update(range(start, end + 1))
            else:
                # 精确值
                val = int(part)
                if val < min_val or val > max_val:
                    raise ValueError(f"值超出限制 [{min_val}-{max_val}]: {val}")
                results.add(val)

        return results

    def matches(self, dt: datetime) -> bool:
        """检查给定时间是否匹配cron表达式"""
        return (
            dt.minute in self.fields["minute"]
            and dt.hour in self.fields["hour"]
            and dt.day in self.fields["day"]
            and dt.month in self.fields["month"]
            and dt.weekday() in self._convert_weekday(self.fields["weekday"])
        )

    def _convert_weekday(self, cron_weekdays: set) -> set:
        """将cron星期(0=周日)转换为Python weekday(0=周一)"""
        result = set()
        for d in cron_weekdays:
            if d == 0:
                result.add(6)  # 周日
            else:
                result.add(d - 1)
        return result

    def next_run_time(self, after: datetime) -> datetime:
        """计算下次运行时间"""
        # 简化实现：从after开始每分钟检查
        candidate = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
        
        # 最多检查2年的分钟数
        max_iterations = 366 * 24 * 60
        for _ in range(max_iterations):
            if self.matches(candidate):
                return candidate
            candidate += timedelta(minutes=1)

        raise ValueError(f"无法找到匹配的时间: {self.expression}")


class FlowScheduler:
    """流程调度器

    管理所有调度任务的生命周期，负责触发流程执行。
    """

    def __init__(self, flow_executor: Callable = None):
        """
        Args:
            flow_executor: 流程执行函数，签名: (flow_id, variables) -> ExecutionResult
        """
        self._schedules: Dict[str, Schedule] = {}
        self._history: List[ExecutionHistory] = []
        self._flow_executor = flow_executor
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._cron_expressions: Dict[str, CronExpression] = {}
        self._callbacks: Dict[str, List[Callable]] = defaultdict(list)

    def set_flow_executor(self, executor: Callable):
        """设置流程执行器"""
        self._flow_executor = executor

    # ============= 调度任务管理 =============

    def add_schedule(self, schedule: Schedule) -> Schedule:
        """添加调度任务"""
        with self._lock:
            # 验证配置
            self._validate_schedule(schedule)

            # 设置初始状态
            if schedule.status == ScheduleStatus.ACTIVE:
                schedule.next_run_at = self._calculate_next_run(schedule)

            # 生成webhook token
            if schedule.trigger_type == TriggerType.WEBHOOK and not schedule.webhook_token:
                schedule.webhook_token = str(uuid.uuid4())

            self._schedules[schedule.id] = schedule

            # 解析cron表达式
            if schedule.cron_expression:
                self._cron_expressions[schedule.id] = CronExpression(schedule.cron_expression)

            # 触发回调
            self._fire_event("schedule_added", schedule)

            return schedule

    def update_schedule(self, schedule_id: str, updates: Dict[str, Any]) -> Schedule:
        """更新调度任务"""
        with self._lock:
            schedule = self._schedules.get(schedule_id)
            if not schedule:
                raise ValueError(f"调度任务不存在: {schedule_id}")

            # 应用更新
            for key, value in updates.items():
                if value is not None and hasattr(schedule, key):
                    setattr(schedule, key, value)

            # 重新解析cron
            if schedule.cron_expression:
                self._cron_expressions[schedule_id] = CronExpression(schedule.cron_expression)

            # 重新计算下次运行时间
            if schedule.status == ScheduleStatus.ACTIVE:
                schedule.next_run_at = self._calculate_next_run(schedule)

            return schedule

    def remove_schedule(self, schedule_id: str) -> bool:
        """删除调度任务"""
        with self._lock:
            if schedule_id in self._schedules:
                del self._schedules[schedule_id]
                self._cron_expressions.pop(schedule_id, None)
                return True
            return False

    def get_schedule(self, schedule_id: str) -> Optional[Schedule]:
        """获取调度任务"""
        return self._schedules.get(schedule_id)

    def list_schedules(self, status: Optional[ScheduleStatus] = None) -> List[Schedule]:
        """列出调度任务"""
        schedules = list(self._schedules.values())
        if status:
            schedules = [s for s in schedules if s.status == status]
        return schedules

    def pause_schedule(self, schedule_id: str) -> Schedule:
        """暂停调度任务"""
        return self.update_schedule(schedule_id, {
            "status": ScheduleStatus.PAUSED,
            "next_run_at": None
        })

    def resume_schedule(self, schedule_id: str) -> Schedule:
        """恢复调度任务"""
        schedule = self.get_schedule(schedule_id)
        if not schedule:
            raise ValueError(f"调度任务不存在: {schedule_id}")

        updates = {"status": ScheduleStatus.ACTIVE}
        updates["next_run_at"] = self._calculate_next_run(schedule)
        return self.update_schedule(schedule_id, updates)

    # ============= 手动触发 =============

    def trigger_schedule(self, schedule_id: str, variables: Dict[str, Any] = None) -> ExecutionHistory:
        """手动触发调度任务执行"""
        schedule = self.get_schedule(schedule_id)
        if not schedule:
            raise ValueError(f"调度任务不存在: {schedule_id}")

        return self._execute_schedule(
            schedule,
            trigger_type=TriggerType.MANUAL,
            trigger_info="手动触发",
            extra_variables=variables
        )

    # ============= Webhook触发 =============

    def trigger_webhook(self, token: str, payload: Dict[str, Any] = None,
                        secret: str = None) -> ExecutionHistory:
        """通过Webhook触发执行"""
        # 查找匹配的调度任务
        schedule = None
        for s in self._schedules.values():
            if (s.trigger_type == TriggerType.WEBHOOK
                    and s.webhook_token == token
                    and s.status == ScheduleStatus.ACTIVE):
                schedule = s
                break

        if not schedule:
            raise ValueError(f"无效的Webhook令牌: {token}")

        # 验证密钥
        if schedule.webhook_secret and schedule.webhook_secret != secret:
            raise ValueError("Webhook密钥验证失败")

        # 合并变量
        variables = dict(schedule.initial_variables)
        if payload:
            variables["webhook_payload"] = payload

        return self._execute_schedule(
            schedule,
            trigger_type=TriggerType.WEBHOOK,
            trigger_info=f"Webhook触发 (token={token[:8]}...)",
            extra_variables=variables
        )

    # ============= 事件回调 =============

    def on(self, event: str, callback: Callable):
        """注册事件回调"""
        self._callbacks[event].append(callback)

    def _fire_event(self, event: str, *args, **kwargs):
        """触发事件回调"""
        for callback in self._callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"事件回调执行失败 ({event}): {e}")

    # ============= 调度循环 =============

    def start(self, check_interval: float = 10.0):
        """启动调度器（非阻塞）"""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._scheduler_loop,
            args=(check_interval,),
            daemon=True,
            name="rpa-scheduler"
        )
        self._thread.start()
        self._fire_event("scheduler_started")

    def stop(self):
        """停止调度器"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=30)
            self._thread = None
        self._fire_event("scheduler_stopped")

    def is_running(self) -> bool:
        """检查调度器是否运行中"""
        return self._running

    def _scheduler_loop(self, check_interval: float):
        """调度主循环"""
        while self._running:
            try:
                now = datetime.now()
                self._check_and_run_schedules(now)
            except Exception as e:
                print(f"调度循环异常: {e}")

            time.sleep(check_interval)

    def _check_and_run_schedules(self, now: datetime):
        """检查并执行到期的调度任务"""
        with self._lock:
            for schedule in list(self._schedules.values()):
                if schedule.status != ScheduleStatus.ACTIVE:
                    continue

                if schedule.trigger_type in (TriggerType.WEBHOOK, TriggerType.FILE_WATCH, TriggerType.MANUAL):
                    continue

                if schedule.next_run_at and now >= schedule.next_run_at:
                    # 在线程中执行，不阻塞调度循环
                    threading.Thread(
                        target=self._execute_schedule,
                        args=(schedule, schedule.trigger_type, f"定时触发 ({schedule.trigger_type.value})"),
                        daemon=True
                    ).start()

                    # 更新调度信息
                    schedule.last_run_at = now
                    schedule.run_count += 1

                    # 计算下次运行时间
                    if schedule.trigger_type == TriggerType.ONCE:
                        schedule.status = ScheduleStatus.COMPLETED
                        schedule.next_run_at = None
                    else:
                        schedule.next_run_at = self._calculate_next_run(schedule)

    def _execute_schedule(self, schedule: Schedule, trigger_type: TriggerType,
                          trigger_info: str = "", extra_variables: Dict[str, Any] = None) -> ExecutionHistory:
        """执行调度任务"""
        history_id = str(uuid.uuid4())
        variables = dict(schedule.initial_variables)
        if extra_variables:
            variables.update(extra_variables)

        history = ExecutionHistory(
            id=history_id,
            schedule_id=schedule.id,
            flow_id=schedule.flow_id,
            trigger_type=trigger_type,
            status=ExecutionStatus.RUNNING,
            started_at=datetime.now(),
            trigger_info=trigger_info,
        )

        # 重试逻辑
        max_attempts = 1 + schedule.max_retries
        for attempt in range(max_attempts):
            history.retry_count = attempt

            try:
                if self._flow_executor:
                    result = self._flow_executor(schedule.flow_id, variables)
                    history.execution_id = getattr(result, "execution_id", None)
                    history.status = ExecutionStatus.COMPLETED
                    schedule.success_count += 1
                    break
                else:
                    raise RuntimeError("未设置流程执行器")

            except Exception as e:
                history.error = str(e)
                if attempt < max_attempts - 1:
                    history.retry_count = attempt + 1
                    time.sleep(schedule.retry_delay_seconds)
                else:
                    history.status = ExecutionStatus.FAILED
                    schedule.fail_count += 1

        history.completed_at = datetime.now()
        if history.started_at:
            delta = history.completed_at - history.started_at
            history.duration_ms = int(delta.total_seconds() * 1000)

        # 保存历史记录
        self._history.append(history)

        # 触发回调
        self._fire_event("execution_completed", history)

        return history

    # ============= 历史记录 =============

    def get_history(self, schedule_id: str = None, limit: int = 100) -> List[ExecutionHistory]:
        """获取执行历史"""
        records = self._history
        if schedule_id:
            records = [h for h in records if h.schedule_id == schedule_id]
        return records[-limit:]

    def clear_history(self, schedule_id: str = None):
        """清空执行历史"""
        if schedule_id:
            self._history = [h for h in self._history if h.schedule_id != schedule_id]
        else:
            self._history.clear()

    # ============= 内部方法 =============

    def _validate_schedule(self, schedule: Schedule):
        """验证调度任务配置"""
        if schedule.trigger_type == TriggerType.CRON:
            if not schedule.cron_expression:
                raise ValueError("Cron触发器必须设置cron_expression")
            # 验证表达式格式
            CronExpression(schedule.cron_expression)

        elif schedule.trigger_type == TriggerType.INTERVAL:
            if not schedule.interval_seconds or schedule.interval_seconds <= 0:
                raise ValueError("间隔触发器必须设置大于0的interval_seconds")

        elif schedule.trigger_type == TriggerType.ONCE:
            if not schedule.run_at:
                raise ValueError("单次触发器必须设置run_at时间")

        elif schedule.trigger_type == TriggerType.WEBHOOK:
            if not schedule.webhook_token:
                schedule.webhook_token = str(uuid.uuid4())

        elif schedule.trigger_type == TriggerType.FILE_WATCH:
            if not schedule.watch_path:
                raise ValueError("文件监控触发器必须设置watch_path")

    def _calculate_next_run(self, schedule: Schedule) -> Optional[datetime]:
        """计算下次运行时间"""
        now = datetime.now()

        if schedule.trigger_type == TriggerType.CRON:
            if schedule.cron_expression:
                cron = self._cron_expressions.get(schedule.id)
                if not cron:
                    cron = CronExpression(schedule.cron_expression)
                    self._cron_expressions[schedule.id] = cron
                try:
                    return cron.next_run_time(now)
                except ValueError:
                    return None

        elif schedule.trigger_type == TriggerType.INTERVAL:
            if schedule.interval_seconds:
                return now + timedelta(seconds=schedule.interval_seconds)

        elif schedule.trigger_type == TriggerType.ONCE:
            if schedule.run_at and schedule.run_at > now:
                return schedule.run_at

        return None

    # ============= 统计 =============

    def get_statistics(self) -> Dict[str, Any]:
        """获取调度器统计信息"""
        total_schedules = len(self._schedules)
        active_count = sum(1 for s in self._schedules.values() if s.status == ScheduleStatus.ACTIVE)
        paused_count = sum(1 for s in self._schedules.values() if s.status == ScheduleStatus.PAUSED)
        completed_count = sum(1 for s in self._schedules.values() if s.status == ScheduleStatus.COMPLETED)

        return {
            "total_schedules": total_schedules,
            "active": active_count,
            "paused": paused_count,
            "completed": completed_count,
            "total_executions": len(self._history),
            "is_running": self._running,
        }

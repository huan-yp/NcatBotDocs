"""
common/05_scheduled_tasks — 定时任务（跨平台）

演示功能:
  - TimeTaskMixin: add_scheduled_task / remove_scheduled_task
  - 多种时间格式: "30s"（秒）、"HH:MM"（每日）、一次性
  - conditions 条件执行
  - @registrar.on_command() 跨平台命令

本示例不依赖任何平台。
使用方式:
  "启动心跳"       → 每 30 秒打印心跳日志
  "停止心跳"       → 停止心跳任务
  "任务列表"       → 查看当前活跃的定时任务
  "添加提醒 10"    → 10 秒后发送一次性提醒
  "开关任务"       → 切换定时任务启用状态
"""

from ncatbot.core import registrar
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("ScheduledTasks")


class ScheduledTasksPlugin(NcatBotPlugin):
    name = "scheduled_tasks"
    version = "1.0.0"
    author = "NcatBot"
    description = "定时任务演示（跨平台）"

    async def on_load(self):
        self._enabled = True

        self.add_scheduled_task(
            "conditional_tick",
            "60s",
            conditions=[lambda: self._enabled],
        )

        LOG.info("ScheduledTasks 插件已加载")

    @registrar.on_command("启动心跳")
    async def on_start_heartbeat(self, event):
        """启动心跳定时任务（每 30 秒）"""
        success = self.add_scheduled_task("heartbeat", "30s")
        if success:
            await event.reply("💓 心跳任务已启动（每 30 秒）")
        else:
            await event.reply("心跳任务已存在或启动失败")

    @registrar.on_command("停止心跳")
    async def on_stop_heartbeat(self, event):
        """停止心跳定时任务"""
        self.remove_scheduled_task("heartbeat")
        await event.reply("💔 心跳任务已停止")

    @registrar.on_command("添加提醒")
    async def on_add_reminder(self, event, seconds: int = 0):
        """添加一次性提醒"""
        if seconds <= 0:
            await event.reply("请输入秒数，例如: 添加提醒 10")
            return

        task_name = f"reminder_{seconds}s"
        success = self.add_scheduled_task(task_name, seconds, max_runs=1)
        if success:
            await event.reply(f"⏰ 将在 {seconds} 秒后提醒你")
        else:
            await event.reply("添加提醒失败")

    @registrar.on_command("开关任务")
    async def on_toggle(self, event):
        """切换定时任务启用状态"""
        self._enabled = not self._enabled
        state = "启用" if self._enabled else "禁用"
        await event.reply(f"定时任务已{state} {'✅' if self._enabled else '❌'}")

    @registrar.on_command("任务列表")
    async def on_list_tasks(self, event):
        """查看当前定时任务列表"""
        tasks = self.list_scheduled_tasks()
        if not tasks:
            await event.reply("当前没有活跃的定时任务")
            return

        lines = ["📋 定时任务列表:"]
        for name in tasks:
            status = self.get_task_status(name)
            if status:
                lines.append(f"  {name}: 运行 {status.get('run_count', 0)} 次")
            else:
                lines.append(f"  {name}")

        await event.reply("\n".join(lines))

    async def heartbeat(self):
        """心跳回调"""
        LOG.info("💓 心跳")

    async def conditional_tick(self):
        """条件任务回调"""
        LOG.info("⏱️ 条件定时任务触发")

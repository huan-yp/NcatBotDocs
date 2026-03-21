"""
bilibili/06_dynamic — Bilibili 动态页多 UP 主合并监听

演示功能:
  - self.api.bilibili.add_dynamic_page_watch(): 动态页监听（多 UP 主合并轮询）
  - self.api.bilibili.remove_dynamic_page_watch(): 移除动态页监听
  - registrar.bilibili.on_dynamic_new(): 新动态事件处理
  - BiliDynamicEvent: 动态事件属性读取

使用方式: 将本文件夹复制到 plugins/ 目录，启动 Bot。
修改 on_load 中的 UID 列表，替换为要监听的 UP 主 UID。
每当订阅的 UP 主发布新动态时，触发 on_new_dynamic 打印日志。

说明:
  - add_dynamic_page_watch 内部会自动关注目标 UP 主（已关注则跳过）
  - 动态页接口一次拉取覆盖所有订阅用户，比逐个轮询效率更高
  - 不检测动态删除，只检测新动态

参考文档: docs/guide/api_usage/bilibili/4_source_query.md
"""

from ncatbot.core import registrar
from ncatbot.event.bilibili import BiliDynamicEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("BiliDynamic")

# 要监听的 UP 主 UID 列表，替换为实际 UID
WATCH_UIDS = [
    621240130,   # 示例 UID 1
    1802011210,  # 示例 UID 2
]


class BiliDynamicPlugin(NcatBotPlugin):
    name = "dynamic_bilibili"
    version = "1.0.0"
    author = "NcatBot"
    description = "Bilibili 动态页多 UP 主合并监听"

    async def on_load(self):
        """启动时批量添加动态页监听"""
        for uid in WATCH_UIDS:
            await self.api.bilibili.add_dynamic_page_watch(uid)
            LOG.info("已添加动态页监听: uid=%d", uid)
        LOG.info("BiliDynamic 插件已加载，共监听 %d 个 UP 主", len(WATCH_UIDS))

    async def on_unload(self):
        """退出时移除监听"""
        for uid in WATCH_UIDS:
            await self.api.bilibili.remove_dynamic_page_watch(uid)

    @registrar.bilibili.on_dynamic_new()
    async def on_new_dynamic(self, event: BiliDynamicEvent):
        """收到新动态时触发"""
        LOG.info(
            "[新动态] UP主=%s (uid=%s) 类型=%s 内容=%s",
            event.user_id,
            event.user_id,
            event.dynamic_type,
            (event.text or "")[:80],
        )

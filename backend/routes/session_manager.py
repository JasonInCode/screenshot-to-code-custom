import asyncio
import time
from typing import Any, Dict, Optional

from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError


class GenerationSession:
    """保存一次代码生成的会话状态，支持 WebSocket 断线重连"""

    def __init__(self, session_id: str, params: Dict[str, Any]):
        self.session_id = session_id
        self.params = params
        self.websocket: Optional[Any] = None
        self.is_connected: bool = False
        self.send_lock = asyncio.Lock()

        # 每个 variant 的累积代码和状态
        self.variant_codes: Dict[int, str] = {}
        self.variant_statuses: Dict[int, str] = {}
        self.variant_errors: Dict[int, str] = {}
        self.variant_count: int = 0
        self.variant_models: list = []

        # 会话完成信号
        self._done_event = asyncio.Event()

        # 用于清理过期会话
        self.created_at: float = time.time()

    def set_websocket(self, ws: Any) -> None:
        """设置当前 WebSocket 连接（重连时调用）"""
        self.websocket = ws
        self.is_connected = True

    def is_done(self) -> bool:
        return self._done_event.is_set()

    def mark_done(self) -> None:
        """标记生成完成（幂等）"""
        self._done_event.set()

    async def wait_until_done(self) -> None:
        """阻塞等待生成完成"""
        await self._done_event.wait()

    async def send(self, msg_type: str, value, variant_index: int,
                   data=None, event_id=None) -> None:
        """通过当前 WebSocket 发送消息，连接断开时静默跳过"""
        if not self.is_connected:
            return
        async with self.send_lock:
            if not self.is_connected or self.websocket is None:
                return
            try:
                payload: Dict[str, Any] = {
                    "type": msg_type,
                    "variantIndex": variant_index,
                }
                if value is not None:
                    payload["value"] = value
                if data is not None:
                    payload["data"] = data
                if event_id is not None:
                    payload["eventId"] = event_id
                await self.websocket.send_json(payload)
            except (ConnectionClosedOK, ConnectionClosedError):
                print(f"🔌 WebSocket 连接已断开 (session={self.session_id[:8]})")
                self.is_connected = False

    def update_state(self, msg_type: str, value, variant_index: int) -> None:
        """根据发送的消息类型更新会话状态（用于重连时重放）"""
        if msg_type == "chunk":
            if value:
                self.variant_codes[variant_index] = (
                    self.variant_codes.get(variant_index, "") + value
                )
        elif msg_type == "setCode":
            self.variant_codes[variant_index] = value or ""
        elif msg_type == "variantComplete":
            self.variant_statuses[variant_index] = "complete"
        elif msg_type == "variantError":
            self.variant_statuses[variant_index] = "error"
            self.variant_errors[variant_index] = value or ""
        elif msg_type == "variantCount":
            self.variant_count = int(value or 0)
        elif msg_type == "variantModels" and value:
            self.variant_models = value if isinstance(value, list) else []


class SessionManager:
    """管理所有活跃的生成会话"""

    SESSION_TTL_SECONDS = 1800  # 30 分钟过期

    def __init__(self):
        self._sessions: Dict[str, GenerationSession] = {}

    def create_session(self, session_id: str,
                       params: Dict[str, Any]) -> GenerationSession:
        """创建新会话"""
        self._cleanup_expired()
        session = GenerationSession(session_id, params)
        self._sessions[session_id] = session
        print(f"📝 创建会话: {session_id[:8]}...")
        return session

    def get_session(self, session_id: str) -> Optional[GenerationSession]:
        """获取已有会话，不存在或已过期返回 None"""
        session = self._sessions.get(session_id)
        if session is None:
            return None
        # 检查是否过期
        if time.time() - session.created_at > self.SESSION_TTL_SECONDS:
            print(f"⏰ 会话已过期: {session_id[:8]}...")
            del self._sessions[session_id]
            return None
        return session

    def remove_session(self, session_id: str) -> None:
        """移除会话"""
        session = self._sessions.pop(session_id, None)
        if session:
            session.mark_done()

    def _cleanup_expired(self) -> None:
        """清理过期会话"""
        now = time.time()
        expired = [
            sid for sid, s in self._sessions.items()
            if now - s.created_at > self.SESSION_TTL_SECONDS
        ]
        for sid in expired:
            print(f"🗑️ 清理过期会话: {sid[:8]}...")
            self._sessions[sid].mark_done()
            del self._sessions[sid]


# 全局会话管理器单例
session_manager = SessionManager()

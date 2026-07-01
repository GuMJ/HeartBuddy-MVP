"""JSON Lines 日志工具 — 所有 trace 事件持久化写入日志文件"""

import json
import os
from typing import Optional
from pathlib import Path
from backend.config import settings


class JsonLinesLogger:
    """线程安全的 JSON Lines 日志写入器"""

    def __init__(self, log_path: Optional[str] = None):
        self.log_path = Path(log_path or settings.log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, event_type: str, session_id: str, **data) -> None:
        """追加一行 JSON 到日志文件"""
        log_entry = {
            "type": event_type,
            "session_id": session_id,
            "data": data,
        }

        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except OSError:
            # 静默失败，不阻塞主流程
            pass

    def read_last(self, n: int = 100) -> list[dict]:
        """读取最近 N 行日志（调试用）"""
        if not self.log_path.exists():
            return []

        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                # 简单实现：读取整个文件取最后 N 行
                lines = f.readlines()
                result = []
                for line in lines[-n:]:
                    try:
                        result.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
                return result
        except OSError:
            return []


# 模块级单例
logger = JsonLinesLogger()

from __future__ import annotations

from typing import Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from jgmd.logging import Color
    from .consts import LogType


class LogEntry:
    def __init__(
        self,
        lambdaToLog: Callable[[], str],
        logType: "LogType",
        color: Optional["Color"] = None,
    ):
        self.lambdaToLog = lambdaToLog
        self.logType = logType
        self.color = color

from __future__ import annotations

from typing import Optional, List, Callable, TYPE_CHECKING
from .logEntry import LogEntry
from .consts import LogType

if TYPE_CHECKING:
    from jgmd.logging import FreeTextLogger
    from jgmd.logging import Color


class LazyLogBuffer:
    def __init__(self):
        self.entries: List[LogEntry] = []

    def lazyLogDebug(
        self, lambdaToLog: Callable[[], str], color: Optional["Color"] = None
    ):
        self.entries.append(LogEntry(lambdaToLog, LogType.DEBUG, color))

    def lazyLogInfo(
        self, lambdaToLog: Callable[[], str], color: Optional["Color"] = None
    ):
        self.entries.append(LogEntry(lambdaToLog, LogType.INFO, color))

    def lazyLogWarning(
        self, lambdaToLog: Callable[[], str], color: Optional["Color"] = None
    ):
        self.entries.append(LogEntry(lambdaToLog, LogType.WARNING, color))

    def lazyLogError(
        self, lambdaToLog: Callable[[], str], color: Optional["Color"] = None
    ):
        self.entries.append(LogEntry(lambdaToLog, LogType.ERROR, color))

    def lazyLogSuccessful(
        self, lambdaToLog: Callable[[], str], color: Optional["Color"] = None
    ):
        self.entries.append(LogEntry(lambdaToLog, LogType.SUCCESS, color))

    def logAll(self, logger: "FreeTextLogger"):
        for entry in self.entries:
            if entry.logType == LogType.DEBUG:
                logger.logDebug(entry.lambdaToLog, entry.color)
            elif entry.logType == LogType.INFO:
                logger.logInfo(entry.lambdaToLog, entry.color)
            elif entry.logType == LogType.WARNING:
                logger.logWarning(entry.lambdaToLog, entry.color)
            elif entry.logType == LogType.ERROR:
                logger.logError(entry.lambdaToLog, entry.color)
            elif entry.logType == LogType.SUCCESS:
                logger.logSuccessful(entry.lambdaToLog, entry.color)

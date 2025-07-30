from __future__ import annotations

from typing import Optional, List, Callable, TYPE_CHECKING
from .logEntry import LogEntry
from .consts import LogType

if TYPE_CHECKING:
    from jgmd.logging import FreeTextLogger
    from jgmd.logging import Color

"""
If syncLogger is passed in the constructor, all logging will be done synchronously, not lazily.
This is useful for debugging purposes, as it allows you to see the logs when they are logged. 
For example, if you are logging an f-string with a variable, lazy logging means the f-string is not evaluated immediately.
Therefore, the value of the variable in the f-string may change before the log is actually written, 
leading to confusing results and making debugging difficult. 

In this situation, you can pass in a syncLogger to the constructor,
and all logging will be done synchronously, allowing you to see the logs as they are written with the values 
of the variables at the time the logging function was called.

Incidentally, if you DO run into the problem described above, you can easily fix it with "default argument binding". For example:

lazyLogInfo(lambda: f"Starting reconciliation process for {repoName}...")

can be changed to:

lazyLogInfo(lambda repoName=repoName: f"Starting reconciliation process for {repoName}...")

and the value of repoName will be captured at the time the lambda is created, not when it is called.
"""


class LazyLogBuffer:
    def __init__(self, syncLogger: Optional["FreeTextLogger"] = None):
        self.entries: List[LogEntry] = []
        self.syncLogger = (
            syncLogger  # allows for easy synchronous logging for debug purposes
        )

    def lazyLogDebug(
        self, lambdaToLog: Callable[[], str], color: Optional["Color"] = None
    ):
        if self.syncLogger:
            self.syncLogger.logDebug(lambdaToLog, color)
            return
        self.entries.append(LogEntry(lambdaToLog, LogType.DEBUG, color))

    def lazyLogInfo(
        self, lambdaToLog: Callable[[], str], color: Optional["Color"] = None
    ):
        if self.syncLogger:
            self.syncLogger.logInfo(lambdaToLog, color)
            return
        self.entries.append(LogEntry(lambdaToLog, LogType.INFO, color))

    def lazyLogWarning(
        self, lambdaToLog: Callable[[], str], color: Optional["Color"] = None
    ):
        if self.syncLogger:
            self.syncLogger.logWarning(lambdaToLog, color)
            return
        self.entries.append(LogEntry(lambdaToLog, LogType.WARNING, color))

    def lazyLogError(
        self, lambdaToLog: Callable[[], str], color: Optional["Color"] = None
    ):
        if self.syncLogger:
            self.syncLogger.logError(lambdaToLog, color)
            return
        self.entries.append(LogEntry(lambdaToLog, LogType.ERROR, color))

    def lazyLogSuccessful(
        self, lambdaToLog: Callable[[], str], color: Optional["Color"] = None
    ):
        if self.syncLogger:
            self.syncLogger.logSuccessful(lambdaToLog, color)
            return
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
        self.clear()

    def clear(self):
        """Clear the log buffer."""
        self.entries.clear()

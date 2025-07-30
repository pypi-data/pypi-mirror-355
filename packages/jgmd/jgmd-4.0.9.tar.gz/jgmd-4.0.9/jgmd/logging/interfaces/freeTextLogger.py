from typing import Callable
from ..loggingConsts import LogLevel, Color
from .logger import Logger


class FreeTextLogger(Logger):
    def __init__(
        self,
        logDirectory: str,
        fileName: str,
        logLevel: LogLevel,
        printToConsole: bool = True,
    ):
        super().__init__(logDirectory, fileName, logLevel, printToConsole)
        self.printToConsole: bool = printToConsole

    def _log(self, s: str, color: Color = ""):
        if self.printToConsole:
            print(f"{color}{s}{Color.ENDC.value}")
        with open(self.filePath, "a") as file:
            file.write(s + "\n")

    def logDebug(self, getStrToLog: Callable[[], str], color: Color = None):
        if self.logLevel == LogLevel.DEBUG:
            s = getStrToLog()
            color = color or Color.PINK
            self._log(s, color.value)

    def logInfo(self, getStrToLog: Callable[[], str], color: Color = None):
        if self.logLevel == LogLevel.DEBUG or self.logLevel == LogLevel.INFO:
            s = getStrToLog()
            color = color or Color.CYAN
            self._log(s, color.value)

    def logWarning(self, getStrToLog: Callable[[], str], color: Color = None):
        if (
            self.logLevel == LogLevel.DEBUG
            or self.logLevel == LogLevel.INFO
            or self.logLevel == LogLevel.WARNING
        ):
            s = getStrToLog()
            color = color or Color.YELLOW
            self._log(s, color.value)

    def logError(self, getStrToLog: Callable[[], str], color: Color = None):
        s = getStrToLog()
        color = color or Color.RED
        self._log(s, color.value)

    def logSuccessful(self, getStrToLog: Callable[[], str], color: Color = None):
        s = getStrToLog()
        color = color or Color.GREEN
        self._log(s, color.value)

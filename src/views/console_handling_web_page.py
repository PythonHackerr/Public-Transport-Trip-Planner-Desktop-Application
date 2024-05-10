from PySide6.QtCore import Signal
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWidgets import QMessageBox


class ConsoleHandlingWebPage(QWebEnginePage):
    """
    Shows QT message boxes on javascript alerts and confirms. Sends console_message_recieved signal with
    console data dict.
    """
    console_message_recieved = Signal(dict)

    def javaScriptConsoleMessage(self, level, msg, line, sourceID):
        self.console_message_recieved.emit(msg)

    def javaScriptPrompt(self, securityOrigin, msg: str, defaultValue: str):
        pass

    def javaScriptAlert(self, securityOrigin, msg: str) -> None:
        QMessageBox.warning(None, "Web alert", msg)

    def javaScriptConfirm(self, securityOrigin, msg: str) -> bool:
        resp = QMessageBox.question(None, "Web confirm", msg)
        return resp == QMessageBox.StandardButton.Yes

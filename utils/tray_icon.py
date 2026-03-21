from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QAction


def quit_app():
    QApplication.quit()


class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        super().__init__(icon, parent)
        self.parent_window = parent

        menu = QMenu()
        show_action = QAction("Показать главное окно", self)
        show_action.triggered.connect(self.show_window)
        menu.addAction(show_action)

        hide_action = QAction("Скрыть окно", self)
        hide_action.triggered.connect(self.hide_window)
        menu.addAction(hide_action)

        menu.addSeparator()
        quit_action = QAction("Выход", self)
        quit_action.triggered.connect(quit_app)
        menu.addAction(quit_action)

        self.setContextMenu(menu)
        self.activated.connect(self.on_tray_icon_activated)

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.parent_window and self.parent_window.isVisible():
                self.parent_window.hide()
            else:
                self.show_window()

    def show_window(self):
        if self.parent_window:
            self.parent_window.show()
            self.parent_window.activateWindow()

    def hide_window(self):
        if self.parent_window:
            self.parent_window.hide()


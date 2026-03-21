from PyQt6.QtCore import QObject, pyqtSignal

class AppSignals(QObject):
    """
    Глобальные сигналы приложения для уведомления об изменениях данных.
    """
    employee_changed = pyqtSignal()
    department_changed = pyqtSignal()
    skzi_changed = pyqtSignal()
    destruction_changed = pyqtSignal()
    training_changed = pyqtSignal()
    control_changed = pyqtSignal()
    audit_changed = pyqtSignal()

# Единственный экземпляр для всего приложения
app_signals = AppSignals()
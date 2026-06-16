import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFileDialog
)


class BackupDialog(QDialog):
    def __init__(self, mode='backup', parent=None):
        super().__init__(parent)
        self.mode = mode  # 'backup' или 'restore'
        self.setWindowTitle(
            "Резервное копирование" if mode == 'backup'
            else "Восстановление из резервной копии"
        )
        self.setMinimumWidth(450)
        layout = QVBoxLayout(self)

        if mode == 'backup':
            layout.addWidget(QLabel("Выберите путь для сохранения резервной копии:"))
            self.path_edit = QLineEdit()
            btn_browse = QPushButton("Обзор...")
            btn_browse.clicked.connect(self.browse_save)
            path_layout = QHBoxLayout()
            path_layout.addWidget(self.path_edit)
            path_layout.addWidget(btn_browse)
            layout.addLayout(path_layout)

            # Поле пароля оставлено для совместимости,
            # но помечено как «не реализовано»
            pwd_label = QLabel(
                "Пароль для шифрования: <i>(не реализовано — поле игнорируется)</i>"
            )
            pwd_label.setStyleSheet("color: gray; font-size: 11px;")
            layout.addWidget(pwd_label)
            self.password_edit = QLineEdit()
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.password_edit.setEnabled(False)
            self.password_edit.setPlaceholderText("Шифрование будет добавлено в следующей версии")
            layout.addWidget(self.password_edit)

        else:
            layout.addWidget(QLabel("Выберите файл резервной копии для восстановления:"))
            self.path_edit = QLineEdit()
            btn_browse = QPushButton("Обзор...")
            btn_browse.clicked.connect(self.browse_open)
            path_layout = QHBoxLayout()
            path_layout.addWidget(self.path_edit)
            path_layout.addWidget(btn_browse)
            layout.addLayout(path_layout)

            pwd_label = QLabel(
                "Пароль: <i>(не реализовано — поле игнорируется)</i>"
            )
            pwd_label.setStyleSheet("color: gray; font-size: 11px;")
            layout.addWidget(pwd_label)
            self.password_edit = QLineEdit()
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.password_edit.setEnabled(False)
            layout.addWidget(self.password_edit)

            warn = QLabel(
                "⚠️  Внимание! Восстановление перезапишет текущую базу данных.\n"
                "Приложение будет закрыто для применения изменений."
            )
            warn.setStyleSheet("color: #c0392b; font-weight: bold;")
            warn.setWordWrap(True)
            layout.addWidget(warn)

        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("Выполнить")
        self.ok_btn.setObjectName("primaryButton")
        self.ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def browse_save(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить резервную копию", "backup.zip", "ZIP archives (*.zip)"
        )
        if path:
            self.path_edit.setText(path)

    def browse_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите файл резервной копии", "", "ZIP archives (*.zip)"
        )
        if path:
            self.path_edit.setText(path)

    def get_data(self):
        return {
            'path': self.path_edit.text().strip(),
            'password': None  # шифрование не реализовано — всегда None
        }
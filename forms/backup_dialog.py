import os
from PyQt6.QtWidgets import *
from PyQt6.QtCore import QTimer

class BackupDialog(QDialog):
    def __init__(self, mode='backup', parent=None):
        super().__init__(parent)
        self.mode = mode  # 'backup' или 'restore'
        self.setWindowTitle("Резервное копирование" if mode == 'backup' else "Восстановление из резервной копии")
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

            layout.addWidget(QLabel("Пароль для шифрования (необязательно):"))
            self.password_edit = QLineEdit()
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
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

            layout.addWidget(QLabel("Пароль (если был установлен):"))
            self.password_edit = QLineEdit()
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addWidget(self.password_edit)

            layout.addWidget(QLabel("Внимание! Восстановление перезапишет текущую базу данных. Приложение будет закрыто."))

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
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить резервную копию", "backup.zip", "ZIP archives (*.zip)")
        if path:
            self.path_edit.setText(path)

    def browse_open(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите файл резервной копии", "", "ZIP archives (*.zip)")
        if path:
            self.path_edit.setText(path)

    def get_data(self):
        return {
            'path': self.path_edit.text().strip(),
            'password': self.password_edit.text()
        }
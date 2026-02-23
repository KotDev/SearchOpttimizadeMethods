from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import sys


class LabBaseWidget(QWidget):
    """Базовый класс для всех лабораторных работ"""

    def __init__(self, lab_number, lab_name):
        super().__init__()
        self.lab_number = lab_number
        self.lab_name = lab_name
        self.setup_ui()

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Основной layout
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        # Заголовок лабораторной работы
        title = QLabel(f"Лабораторная работа {self.lab_number}: {self.lab_name}")
        title.setStyleSheet("""
            font-size: 13px;
            font-weight: bold;
            color: #2c3e50;
            padding: 8px;
            background-color: #ecf0f1;
            border-radius: 4px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setWordWrap(True)
        layout.addWidget(title)

        # Описание задачи
        desc_label = QLabel("Описание задачи:")
        desc_label.setStyleSheet("font-weight: bold; color: #34495e; font-size: 12px;")
        layout.addWidget(desc_label)

        self.description = QTextEdit()
        self.description.setReadOnly(True)
        self.description.setMaximumHeight(70)
        self.description.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 6px;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.description)

        # Контейнер для полей ввода с прокруткой
        input_label = QLabel("Параметры:")
        input_label.setStyleSheet("font-weight: bold; color: #34495e; font-size: 12px; margin-top: 5px;")
        layout.addWidget(input_label)

        self.input_scroll = QScrollArea()
        self.input_scroll.setWidgetResizable(True)
        self.input_scroll.setMinimumHeight(200)
        self.input_scroll.setMaximumHeight(300)
        # Сбрасываем возможную темную тему у области прокрутки
        self.input_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
            }
        """)
        # Явно делаем viewport светлым
        self.input_scroll.viewport().setStyleSheet("background-color: white;")

        self.inputs_container = QWidget()
        self.inputs_container.setObjectName("InputsContainer")
        self.inputs_layout = QVBoxLayout(self.inputs_container)
        self.inputs_layout.setSpacing(6)
        self.inputs_layout.setContentsMargins(8, 8, 8, 8)
        self.inputs_layout.addStretch()

        # Явно задаем светлый фон для области ввода,
        # чтобы не зависеть от системной темной темы
        self.inputs_container.setStyleSheet("""
            QWidget#InputsContainer {
                background-color: white;
            }
        """)

        self.input_scroll.setWidget(self.inputs_container)
        layout.addWidget(self.input_scroll)

        # Кнопка расчета
        self.btn_calculate = QPushButton("Выполнить расчет")
        self.btn_calculate.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 4px;
                font-size: 13px;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c6ea4;
            }
        """)
        layout.addWidget(self.btn_calculate)

        # Контейнер для результатов с прокруткой
        results_label = QLabel("Результаты:")
        results_label.setStyleSheet("font-weight: bold; color: #34495e; font-size: 12px; margin-top: 5px;")
        layout.addWidget(results_label)

        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.setMinimumHeight(150)
        self.results_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: #f8f9fa;
            }
        """)
        # Viewport тоже принудительно делаем светлым
        self.results_scroll.viewport().setStyleSheet("background-color: #f8f9fa;")

        self.results_container = QWidget()
        self.results_container.setObjectName("ResultsContainer")
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setSpacing(6)
        self.results_layout.setContentsMargins(8, 8, 8, 8)
        self.results_layout.addStretch()

        # Светлый фон для области результатов
        self.results_container.setStyleSheet("""
            QWidget#ResultsContainer {
                background-color: #f8f9fa;
            }
        """)

        self.results_scroll.setWidget(self.results_container)
        layout.addWidget(self.results_scroll)

    def set_description(self, text):
        """Устанавливает текст описания"""
        self.description.setText(text)

    def add_input_widget(self, widget):
        """Добавляет виджет в контейнер ввода перед stretch"""
        self.inputs_layout.insertWidget(self.inputs_layout.count() - 1, widget)

    def add_input_field(self, label_text, widget_class, **kwargs):
        """Добавляет поле ввода с меткой"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        label = QLabel(label_text)
        label.setMinimumWidth(130)
        label.setWordWrap(True)
        label.setStyleSheet("color: #2c3e50; font-size: 11px;")
        layout.addWidget(label)

        widget = widget_class()
        widget.setStyleSheet("""
            QSpinBox, QDoubleSpinBox, QComboBox {
                padding: 4px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
                min-height: 22px;
                font-size: 11px;
            }
        """)

        if 'value' in kwargs:
            if hasattr(widget, 'setValue'):
                widget.setValue(kwargs['value'])
        if 'range' in kwargs:
            if hasattr(widget, 'setRange'):
                widget.setRange(*kwargs['range'])
        if 'items' in kwargs:
            if hasattr(widget, 'addItems'):
                widget.addItems(kwargs['items'])

        layout.addWidget(widget)
        self.add_input_widget(container)

        return widget

    def clear_results(self):
        """Очищает контейнер с результатами"""
        while self.results_layout.count() > 1:
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        QApplication.processEvents()

    def add_result_text(self, text):
        """Добавляет текстовый результат"""
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setMaximumHeight(180)
        text_edit.setText(text)
        text_edit.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 6px;
                font-family: Consolas, Monaco, monospace;
                font-size: 11px;
            }
        """)
        self.results_layout.insertWidget(self.results_layout.count() - 1, text_edit)

    def add_result_label(self, text, style="normal"):
        """Добавляет метку с результатом"""
        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setMinimumHeight(35)

        if style == "success":
            label.setStyleSheet("""
                QLabel {
                    color: #27ae60; 
                    font-weight: bold; 
                    font-size: 13px;
                    padding: 8px;
                    background-color: #e8f5e9;
                    border: 1px solid #a5d6a7;
                    border-radius: 4px;
                }
            """)
        elif style == "error":
            label.setStyleSheet("""
                QLabel {
                    color: #e74c3c; 
                    font-weight: bold;
                    padding: 8px;
                    background-color: #fde9e9;
                    border: 1px solid #f5c6cb;
                    border-radius: 4px;
                }
            """)
        elif style == "warning":
            label.setStyleSheet("""
                QLabel {
                    color: #f39c12; 
                    font-weight: bold;
                    padding: 8px;
                    background-color: #fff3e0;
                    border: 1px solid #ffe0b2;
                    border-radius: 4px;
                }
            """)
        else:
            label.setStyleSheet("""
                QLabel {
                    color: #2c3e50;
                    padding: 8px;
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                }
            """)

        self.results_layout.insertWidget(self.results_layout.count() - 1, label)
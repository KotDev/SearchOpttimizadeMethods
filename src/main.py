import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import vtk
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from src.labs.lab1.lab1 import Lab1Widget
from src.labs.lab2.lab2 import Lab2Widget


class VTKWidget(QVTKRenderWindowInteractor):
    """Кастомный VTK виджет с осями координат"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 500)

        # Создаем рендерер
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0.95, 0.95, 0.95)
        self.renderer.SetBackground2(0.85, 0.85, 0.9)
        self.renderer.GradientBackgroundOn()

        # Создаем окно рендера
        self.render_window = self.GetRenderWindow()
        self.render_window.AddRenderer(self.renderer)
        self.render_window.SetSize(800, 600)

        # Включаем антиалиасинг
        self.render_window.SetMultiSamples(8)

        # Включаем глубину
        self.render_window.SetAlphaBitPlanes(1)

        # Создаем интерактор
        self.interactor = self.render_window.GetInteractor()

        # Создаем кастомный стиль интерактора с обновлением clipping planes
        style = vtk.vtkInteractorStyleTrackballCamera()

        # Переопределяем обработчики событий для обновления clipping planes
        style.AddObserver("InteractionEvent", self.on_interaction_event)

        self.interactor.SetInteractorStyle(style)

        # Список базовых акторов
        self.base_actors = []

        # Создаем оси координат
        self.create_axes()

        # Создаем сетку
        self.create_grid()

        # Настраиваем камеру с широкими clipping planes
        camera = self.renderer.GetActiveCamera()
        camera.SetPosition(10, 10, 10)
        camera.SetFocalPoint(0, 0, 0)
        camera.SetViewUp(0, 0, 1)

        # Очень широкие clipping planes
        camera.SetClippingRange(0.001, 10000)

        self.renderer.ResetCamera()

        # Инициализируем интерактор
        self.interactor.Initialize()

        self.render_window.Render()

    def on_interaction_event(self, obj, event):
        """Обработчик событий взаимодействия (вращение, масштабирование)"""
        # Обновляем clipping planes при каждом взаимодействии
        self.renderer.ResetCameraClippingRange()
        self.render_window.Render()

    def create_axes(self):
        """Создает оси координат"""
        # Ось X (красная)
        # Создаем линию для оси X (более надежно чем стрелка)
        line_x = vtk.vtkLineSource()
        line_x.SetPoint1(-15, 0, 0)
        line_x.SetPoint2(15, 0, 0)

        line_mapper_x = vtk.vtkPolyDataMapper()
        line_mapper_x.SetInputConnection(line_x.GetOutputPort())

        line_actor_x = vtk.vtkActor()
        line_actor_x.SetMapper(line_mapper_x)
        line_actor_x.GetProperty().SetColor(1, 0, 0)
        line_actor_x.GetProperty().SetLineWidth(2)

        # Стрелка на конце оси X
        arrow_x = vtk.vtkArrowSource()
        arrow_x.SetTipLength(0.3)
        arrow_x.SetTipRadius(0.1)
        arrow_x.SetShaftRadius(0.02)

        transform_x = vtk.vtkTransform()
        transform_x.Translate(15, 0, 0)
        transform_x.RotateZ(-90)
        transform_x.Scale(1.5, 1, 1)

        transform_filter_x = vtk.vtkTransformPolyDataFilter()
        transform_filter_x.SetTransform(transform_x)
        transform_filter_x.SetInputConnection(arrow_x.GetOutputPort())

        arrow_mapper_x = vtk.vtkPolyDataMapper()
        arrow_mapper_x.SetInputConnection(transform_filter_x.GetOutputPort())

        arrow_actor_x = vtk.vtkActor()
        arrow_actor_x.SetMapper(arrow_mapper_x)
        arrow_actor_x.GetProperty().SetColor(1, 0, 0)

        # Ось Y (зеленая)
        line_y = vtk.vtkLineSource()
        line_y.SetPoint1(0, -15, 0)
        line_y.SetPoint2(0, 15, 0)

        line_mapper_y = vtk.vtkPolyDataMapper()
        line_mapper_y.SetInputConnection(line_y.GetOutputPort())

        line_actor_y = vtk.vtkActor()
        line_actor_y.SetMapper(line_mapper_y)
        line_actor_y.GetProperty().SetColor(0, 1, 0)
        line_actor_y.GetProperty().SetLineWidth(2)

        arrow_y = vtk.vtkArrowSource()
        arrow_y.SetTipLength(0.3)
        arrow_y.SetTipRadius(0.1)
        arrow_y.SetShaftRadius(0.02)

        transform_y = vtk.vtkTransform()
        transform_y.Translate(0, 15, 0)
        transform_y.Scale(1.5, 1, 1)

        transform_filter_y = vtk.vtkTransformPolyDataFilter()
        transform_filter_y.SetTransform(transform_y)
        transform_filter_y.SetInputConnection(arrow_y.GetOutputPort())

        arrow_mapper_y = vtk.vtkPolyDataMapper()
        arrow_mapper_y.SetInputConnection(transform_filter_y.GetOutputPort())

        arrow_actor_y = vtk.vtkActor()
        arrow_actor_y.SetMapper(arrow_mapper_y)
        arrow_actor_y.GetProperty().SetColor(0, 1, 0)

        # Ось Z (синяя)
        line_z = vtk.vtkLineSource()
        line_z.SetPoint1(0, 0, -15)
        line_z.SetPoint2(0, 0, 15)

        line_mapper_z = vtk.vtkPolyDataMapper()
        line_mapper_z.SetInputConnection(line_z.GetOutputPort())

        line_actor_z = vtk.vtkActor()
        line_actor_z.SetMapper(line_mapper_z)
        line_actor_z.GetProperty().SetColor(0, 0, 1)
        line_actor_z.GetProperty().SetLineWidth(2)

        arrow_z = vtk.vtkArrowSource()
        arrow_z.SetTipLength(0.3)
        arrow_z.SetTipRadius(0.1)
        arrow_z.SetShaftRadius(0.02)

        transform_z = vtk.vtkTransform()
        transform_z.Translate(0, 0, 15)
        transform_z.RotateY(90)
        transform_z.Scale(1.5, 1, 1)

        transform_filter_z = vtk.vtkTransformPolyDataFilter()
        transform_filter_z.SetTransform(transform_z)
        transform_filter_z.SetInputConnection(arrow_z.GetOutputPort())

        arrow_mapper_z = vtk.vtkPolyDataMapper()
        arrow_mapper_z.SetInputConnection(transform_filter_z.GetOutputPort())

        arrow_actor_z = vtk.vtkActor()
        arrow_actor_z.SetMapper(arrow_mapper_z)
        arrow_actor_z.GetProperty().SetColor(0, 0, 1)

        # Добавляем все элементы
        self.renderer.AddActor(line_actor_x)
        self.renderer.AddActor(arrow_actor_x)
        self.renderer.AddActor(line_actor_y)
        self.renderer.AddActor(arrow_actor_y)
        self.renderer.AddActor(line_actor_z)
        self.renderer.AddActor(arrow_actor_z)

        self.base_actors.extend([line_actor_x, arrow_actor_x, line_actor_y,
                                 arrow_actor_y, line_actor_z, arrow_actor_z])

        # Подписи осей
        self.create_axis_labels()

    def create_axis_labels(self):
        """Создает подписи для осей"""
        # Надпись X
        text_x = vtk.vtkVectorText()
        text_x.SetText("X")

        mapper_x = vtk.vtkPolyDataMapper()
        mapper_x.SetInputConnection(text_x.GetOutputPort())

        actor_x = vtk.vtkActor()
        actor_x.SetMapper(mapper_x)
        actor_x.SetScale(0.5, 0.5, 0.5)
        actor_x.SetPosition(16, 0, 0)
        actor_x.GetProperty().SetColor(1, 0, 0)

        # Надпись Y
        text_y = vtk.vtkVectorText()
        text_y.SetText("Y")

        mapper_y = vtk.vtkPolyDataMapper()
        mapper_y.SetInputConnection(text_y.GetOutputPort())

        actor_y = vtk.vtkActor()
        actor_y.SetMapper(mapper_y)
        actor_y.SetScale(0.5, 0.5, 0.5)
        actor_y.SetPosition(0, 16, 0)
        actor_y.GetProperty().SetColor(0, 1, 0)

        # Надпись Z
        text_z = vtk.vtkVectorText()
        text_z.SetText("Z")

        mapper_z = vtk.vtkPolyDataMapper()
        mapper_z.SetInputConnection(text_z.GetOutputPort())

        actor_z = vtk.vtkActor()
        actor_z.SetMapper(mapper_z)
        actor_z.SetScale(0.5, 0.5, 0.5)
        actor_z.SetPosition(0, 0, 16)
        actor_z.GetProperty().SetColor(0, 0, 1)

        self.renderer.AddActor(actor_x)
        self.renderer.AddActor(actor_y)
        self.renderer.AddActor(actor_z)

        self.base_actors.extend([actor_x, actor_y, actor_z])

    def create_grid(self):
        """Создает координатную сетку"""
        # Сетка в плоскости XY - с широкими границами
        grid_source = vtk.vtkPlaneSource()
        grid_source.SetOrigin(-15, -15, 0)
        grid_source.SetPoint1(15, -15, 0)
        grid_source.SetPoint2(-15, 15, 0)
        grid_source.SetXResolution(30)
        grid_source.SetYResolution(30)

        grid_mapper = vtk.vtkPolyDataMapper()
        grid_mapper.SetInputConnection(grid_source.GetOutputPort())

        grid_actor = vtk.vtkActor()
        grid_actor.SetMapper(grid_mapper)
        grid_actor.GetProperty().SetColor(0.7, 0.7, 0.7)
        grid_actor.GetProperty().SetOpacity(0.2)
        grid_actor.GetProperty().SetRepresentationToWireframe()
        grid_actor.GetProperty().SetLineWidth(1)

        # Сетка в плоскости XZ
        grid_source_xz = vtk.vtkPlaneSource()
        grid_source_xz.SetOrigin(-15, 0, -15)
        grid_source_xz.SetPoint1(15, 0, -15)
        grid_source_xz.SetPoint2(-15, 0, 15)
        grid_source_xz.SetXResolution(30)
        grid_source_xz.SetYResolution(30)

        transform_xz = vtk.vtkTransform()
        transform_xz.RotateX(90)

        transform_filter_xz = vtk.vtkTransformPolyDataFilter()
        transform_filter_xz.SetTransform(transform_xz)
        transform_filter_xz.SetInputConnection(grid_source_xz.GetOutputPort())

        grid_mapper_xz = vtk.vtkPolyDataMapper()
        grid_mapper_xz.SetInputConnection(transform_filter_xz.GetOutputPort())

        grid_actor_xz = vtk.vtkActor()
        grid_actor_xz.SetMapper(grid_mapper_xz)
        grid_actor_xz.GetProperty().SetColor(0.7, 0.7, 0.8)
        grid_actor_xz.GetProperty().SetOpacity(0.15)
        grid_actor_xz.GetProperty().SetRepresentationToWireframe()

        # Сетка в плоскости YZ
        grid_source_yz = vtk.vtkPlaneSource()
        grid_source_yz.SetOrigin(0, -15, -15)
        grid_source_yz.SetPoint1(0, 15, -15)
        grid_source_yz.SetPoint2(0, -15, 15)
        grid_source_yz.SetXResolution(30)
        grid_source_yz.SetYResolution(30)

        transform_yz = vtk.vtkTransform()
        transform_yz.RotateY(-90)

        transform_filter_yz = vtk.vtkTransformPolyDataFilter()
        transform_filter_yz.SetTransform(transform_yz)
        transform_filter_yz.SetInputConnection(grid_source_yz.GetOutputPort())

        grid_mapper_yz = vtk.vtkPolyDataMapper()
        grid_mapper_yz.SetInputConnection(transform_filter_yz.GetOutputPort())

        grid_actor_yz = vtk.vtkActor()
        grid_actor_yz.SetMapper(grid_mapper_yz)
        grid_actor_yz.GetProperty().SetColor(0.7, 0.8, 0.7)
        grid_actor_yz.GetProperty().SetOpacity(0.15)
        grid_actor_yz.GetProperty().SetRepresentationToWireframe()

        self.renderer.AddActor(grid_actor)
        self.renderer.AddActor(grid_actor_xz)
        self.renderer.AddActor(grid_actor_yz)

        self.base_actors.extend([grid_actor, grid_actor_xz, grid_actor_yz])

    def clear_scene(self):
        """Очищает все объекты кроме осей и сетки"""
        actors = self.renderer.GetActors()
        actors.InitTraversal()

        actors_to_remove = []
        for i in range(actors.GetNumberOfItems()):
            actor = actors.GetNextItem()
            if actor not in self.base_actors:
                actors_to_remove.append(actor)

        for actor in actors_to_remove:
            self.renderer.RemoveActor(actor)

        # Обновляем clipping range
        self.renderer.ResetCameraClippingRange()
        self.render_window.Render()

    def add_actor(self, actor):
        """Добавляет актор в сцену"""
        self.renderer.AddActor(actor)

        # Обновляем clipping range
        self.renderer.ResetCameraClippingRange()
        self.render_window.Render()

    def reset_camera(self):
        """Сбрасывает камеру в начальное положение"""
        camera = self.renderer.GetActiveCamera()
        camera.SetPosition(10, 10, 10)
        camera.SetFocalPoint(0, 0, 0)
        camera.SetViewUp(0, 0, 1)
        camera.SetClippingRange(0.001, 10000)

        self.renderer.ResetCamera()
        self.renderer.ResetCameraClippingRange()
        self.render_window.Render()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Лабораторный комплекс")
        self.setGeometry(100, 50, 1400, 900)

        # Центральный стиль
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f7fa;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 5px;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                padding: 6px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }
        """)

        self.current_lab = None
        self.lab_widgets = {}
        self.splitter = None

        self.setup_ui()
        self.setup_labs()

    def setup_ui(self):
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        # Основной горизонтальный layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # ===== ЛЕВАЯ ЧАСТЬ: 3D ВИЗУАЛИЗАЦИЯ =====
        left_container = QWidget()
        left_container.setMinimumWidth(600)
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Заголовок с иконкой
        title_label = QLabel("3D ВИЗУАЛИЗАЦИЯ РЕЗУЛЬТАТОВ")
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px;
            background-color: #ecf0f1;
            border-radius: 5px;
            margin-bottom: 5px;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(title_label)

        # VTK виджет с рамкой
        vtk_frame = QFrame()
        vtk_frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        vtk_frame.setLineWidth(2)
        vtk_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-color: #3498db;
                border-radius: 4px;
            }
        """)

        vtk_layout = QVBoxLayout(vtk_frame)
        vtk_layout.setContentsMargins(1, 1, 1, 1)

        self.vtk_widget = VTKWidget()
        vtk_layout.addWidget(self.vtk_widget)

        left_layout.addWidget(vtk_frame, 1)

        # Панель управления графиком
        controls_panel = QWidget()
        controls_layout = QHBoxLayout(controls_panel)
        controls_layout.setContentsMargins(0, 5, 0, 0)

        # Кнопка сброса камеры
        self.btn_reset = QPushButton("🔄 Сбросить вид")
        self.btn_reset.setToolTip("Вернуть камеру в исходное положение")
        self.btn_reset.clicked.connect(self.vtk_widget.reset_camera)
        self.btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)

        # Кнопка очистки сцены
        self.btn_clear = QPushButton("🗑️ Очистить")
        self.btn_clear.setToolTip("Удалить все построенные объекты")
        self.btn_clear.clicked.connect(self.vtk_widget.clear_scene)
        self.btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)

        # Информация о состоянии
        self.status_label = QLabel("Готов к работе")
        self.status_label.setStyleSheet("""
            padding: 8px 12px;
            background-color: #ecf0f1;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            font-size: 12px;
            color: #7f8c8d;
        """)

        controls_layout.addWidget(self.btn_reset)
        controls_layout.addWidget(self.btn_clear)
        controls_layout.addStretch()
        controls_layout.addWidget(self.status_label)

        left_layout.addWidget(controls_panel)

        # ===== ПРАВАЯ ЧАСТЬ: ПАНЕЛЬ УПРАВЛЕНИЯ =====
        right_container = QWidget()
        right_container.setMinimumWidth(350)
        right_container.setMaximumWidth(450)
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Заголовок панели
        panel_title = QLabel("ПАНЕЛЬ УПРАВЛЕНИЯ")
        panel_title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px;
            background-color: #ecf0f1;
            border-radius: 5px;
            margin-bottom: 5px;
        """)
        panel_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(panel_title)

        # Выбор лабораторной работы
        lab_group = QGroupBox("Выбор лабораторной работы")
        lab_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        lab_layout = QVBoxLayout(lab_group)

        self.lab_selector = QComboBox()
        self.lab_selector.setStyleSheet("""
            QComboBox {
                padding: 8px;
                font-size: 13px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }
        """)
        self.lab_selector.currentIndexChanged.connect(self.change_lab)

        lab_layout.addWidget(QLabel("Выберите лабораторную работу:"))
        lab_layout.addWidget(self.lab_selector)
        right_layout.addWidget(lab_group)

        # Контейнер для виджета лабораторной
        self.lab_container = QStackedWidget()
        self.lab_container.setStyleSheet("""
            QStackedWidget {
                border: 1px solid #3498db;
                border-radius: 5px;
                background-color: white;
                margin-top: 5px;
            }
        """)
        right_layout.addWidget(self.lab_container, 1)

        # Информационная панель
        info_group = QGroupBox("Информация")
        info_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        info_layout = QVBoxLayout(info_group)

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(100)
        self.info_text.setStyleSheet("""
            QTextEdit {
                font-size: 12px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: #f8f9fa;
                padding: 5px;
            }
        """)
        self.info_text.setText("Выберите лабораторную работу для начала работы.")

        info_layout.addWidget(self.info_text)
        right_layout.addWidget(info_group)

        # Создаем splitter и добавляем обе части
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(left_container)
        self.splitter.addWidget(right_container)
        self.splitter.setSizes([900, 400])
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #bdc3c7;
                width: 3px;
            }
            QSplitter::handle:hover {
                background-color: #3498db;
            }
        """)

        main_layout.addWidget(self.splitter)

        # Добавляем стили для текста
        self.setStyleSheet(self.styleSheet() + """
            QLabel, QGroupBox, QRadioButton, QCheckBox, QComboBox, QSpinBox, QDoubleSpinBox {
                color: #2c3e50;
            }
            QTextEdit, QLineEdit {
                color: #2c3e50;
                background-color: white;
            }
            QPushButton {
                color: white;
            }
            QMenuBar {
                color: white;
            }
            QMenu {
                color: #2c3e50;
            }
        """)

        # Создаем меню
        self.create_menu()

    def resizeEvent(self, event):
        """Обработчик изменения размера окна"""
        super().resizeEvent(event)

        if hasattr(self, 'splitter') and self.splitter:
            width = self.width()
            if width < 1000:
                # Для маленьких экранов делаем соотношение 55/45
                self.splitter.setSizes([int(width * 0.55), int(width * 0.45)])
            else:
                # Для больших экранов фиксированные размеры
                self.splitter.setSizes([900, 400])

    def create_menu(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #2c3e50;
                color: white;
                font-weight: bold;
            }
            QMenuBar::item:selected {
                background-color: #3498db;
            }
            QMenu {
                background-color: white;
                border: 1px solid #bdc3c7;
            }
            QMenu::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)

        # Меню Файл
        file_menu = menubar.addMenu("📁 Файл")

        export_action = QAction("💾 Экспорт графика...", self)
        export_action.setShortcut("Ctrl+E")
        file_menu.addAction(export_action)

        screenshot_action = QAction("📷 Сделать скриншот", self)
        screenshot_action.setShortcut("Ctrl+P")
        file_menu.addAction(screenshot_action)

        file_menu.addSeparator()

        exit_action = QAction("🚪 Выход", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Меню Вид
        view_menu = menubar.addMenu("👁️ Вид")

        fullscreen_action = QAction("🖥️ Полный экран", self, checkable=True)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)

        view_menu.addSeparator()

        axes_action = QAction("📏 Показать/скрыть оси", self, checkable=True, checked=True)
        axes_action.triggered.connect(self.toggle_axes)
        view_menu.addAction(axes_action)

        grid_action = QAction("🔲 Показать/скрыть сетку", self, checkable=True, checked=True)
        grid_action.triggered.connect(self.toggle_grid)
        view_menu.addAction(grid_action)

        # Меню Справка
        help_menu = menubar.addMenu("❓ Справка")

        help_action = QAction("📚 Руководство", self)
        help_menu.addAction(help_action)

        about_action = QAction("ℹ️ О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_labs(self):
        """Настраивает список лабораторных работ"""
        # Импортируем здесь, чтобы избежать циклических импортов
        from src.lab_base_widget import LabBaseWidget

        # Добавляем названия в комбобокс
        self.lab_selector.addItems([
            "Лаб 1: Градиентные методы оптимизации",
            "Лаб 2: Квадратичное программирование",
            "Лаб 3: Векторное поле",
            "Лаб 4: Изоповерхности",
            "Лаб 5: Анимация"
        ])

        # Создаем виджеты для лабораторных
        lab_widgets_list = []

        # Лабораторная 1 - градиентные методы
        lab1 = Lab1Widget()
        lab1.vtk_widget = self.vtk_widget
        lab_widgets_list.append(lab1)

        # Лабораторная 2 - методы прямого поиска
        lab2 = Lab2Widget()
        lab2.vtk_widget = self.vtk_widget
        lab_widgets_list.append(lab2)

        # Остальные - заглушки
        for i in range(3, 6):
            lab_widget = LabBaseWidget(i, f"Лабораторная {i}")
            lab_widget.set_description("Здесь будет описание лабораторной работы.\n\n"
                                       "Добавьте поля ввода и логику расчета в соответствующем классе.")
            lab_widget.vtk_widget = self.vtk_widget
            lab_widgets_list.append(lab_widget)

        # Добавляем виджеты в stacked widget
        for widget in lab_widgets_list:
            self.lab_container.addWidget(widget)

        # Сохраняем словарь для быстрого доступа
        for i, widget in enumerate(lab_widgets_list):
            self.lab_widgets[i] = widget

        # Устанавливаем первую лабораторную по умолчанию
        self.change_lab(0)

    def change_lab(self, index):
        """Переключает между лабораторными работами"""
        if 0 <= index < self.lab_container.count():
            self.lab_container.setCurrentIndex(index)
            self.current_lab = index

            # Обновляем информацию
            lab_number = index + 1
            if index == 0:
                self.info_text.setText(
                    f"Активная лабораторная работа: №{lab_number} - Градиентные методы оптимизации\n"
                    f"Исследование методов: градиентный спуск, наискорейший спуск, "
                    f"покоординатный спуск, метод Ньютона-Рафсона.\n"
                    f"Выберите функцию и параметры, нажмите 'Выполнить расчет'."
                )
            elif index == 1:
                self.info_text.setText(
                    f"Активная лабораторная работа: №{lab_number} - Квадратичное программирование\n"
                    f"Метод искусственных переменных. min 0.5 x'Qx + c'x при Ax ≤ b, x ≥ 0.\n"
                    f"Выберите задачу и нажмите 'Выполнить расчет'."
                )
            else:
                self.info_text.setText(
                    f"Активная лабораторная работа: №{lab_number}\n"
                    f"Для начала работы заполните параметры и нажмите 'Выполнить расчет'.\n"
                    f"Вы можете вращать график с помощью мыши."
                )
            self.status_label.setText(f"Выбрана лабораторная работа №{lab_number}")

    def toggle_fullscreen(self, checked):
        if checked:
            self.showFullScreen()
        else:
            self.showNormal()

    def toggle_axes(self, checked):
        pass

    def toggle_grid(self, checked):
        pass

    def show_about(self):
        QMessageBox.about(self, "О программе",
                          "<h2>3D Лабораторный комплекс</h2>"
                          "<p>Версия 1.0.0</p>"
                          "<p>Программа для визуализации результатов лабораторных работ</p>"
                          "<p>Использует PyQt6 и VTK для 3D графики</p>"
                          "<hr>"
                          "<p>© 2024 Все права защищены</p>")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
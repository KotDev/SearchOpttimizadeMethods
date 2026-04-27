import numpy as np
import vtk
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from src.lab_base_widget import LabBaseWidget
from .bees_algorithm import BeesAlgorithm
from .bees_algorithm_worker import BeesAlgorithmWorker
from src.test_functions.test_func_fabric import TestFunctionFactory


class Lab5Widget(LabBaseWidget):
    def __init__(self):
        super().__init__(5, "Алгоритм пчелиного роя (Bees Algorithm)")
        self.history = []
        self.pop_actor = None
        self.surface_actor = None
        self.best_actor = None
        
        # Коэффициенты для нормализации Z
        self.z_min = 0
        self.z_range = 1.0
        self.current_function = None
        
        # Для сохранения камеры
        self.camera_position = None
        self.camera_focal_point = None
        self.bees_worker = None
        
        self.setup_custom_ui()

    def setup_custom_ui(self):
        # 1. Описание
        self.set_description(
            "Глобальная оптимизация Алгоритмом Пчелиного Роя (Bees Algorithm).\n"
            "Алгоритм имитирует поведение пчелиной колонии при поиске источников нектара.\n"
            "Пчелы-разведчики находят перспективные участки, рабочие пчелы исследуют их.\n"
            "Элитные участки получают больше рабочих пчел. Радиус поиска динамически уменьшается."
        )

        # 2. Выбор функции
        self.functions = TestFunctionFactory.create_all(dim=2)
        func_names = [f.name for f in self.functions]
        self.func_combo = self.add_input_field("Функция:", QComboBox, items=func_names)

        # 3. Параметры алгоритма
        param_group = QGroupBox("Параметры пчелиного роя")
        param_layout = QGridLayout()
        param_group.setLayout(param_layout)
        
        # Базовые параметры
        self.scouts_input = self.add_input_field("Пчел-разведчиков:", QSpinBox, value=16, range=(5, 100))
        self.elite_sites_input = self.add_input_field("Элитных участков:", QSpinBox, value=2, range=(1, 20))
        self.best_sites_input = self.add_input_field("Перспективных участков:", QSpinBox, value=3, range=(1, 20))
        self.elite_bees_input = self.add_input_field("Пчел на элитном участке:", QSpinBox, value=7, range=(1, 30))
        self.best_bees_input = self.add_input_field("Пчел на перспективном участке:", QSpinBox, value=4, range=(1, 30))
        
        # Радиус и итерации
        self.radius_input = self.add_input_field(
            "Начальный радиус:", QDoubleSpinBox, value=0.2, range=(0.05, 1.0), step=0.05,
            tooltip="Радиус области поиска вокруг перспективных участков"
        )
        self.radius_reduction_input = self.add_input_field(
            "Коэффициент уменьшения радиуса:", QDoubleSpinBox, value=0.8, range=(0.5, 0.95), step=0.05,
            tooltip="Как быстро уменьшается радиус поиска (меньше = быстрее)"
        )
        self.gens_input = self.add_input_field("Макс. итераций:", QSpinBox, value=500, range=(10, 1000))
        self.stagnation_input = self.add_input_field(
            "Лимит стагнации:", QSpinBox, value=20, range=(5, 100),
            tooltip="Остановка, если нет улучшения за N итераций"
        )
        
        self.inputs_layout.addWidget(param_group)
        
        # 4. Режим визуализации
        viz_group = QGroupBox("Визуализация")
        viz_layout = QHBoxLayout()
        viz_group.setLayout(viz_layout)
        
        self.real_time_checkbox = QCheckBox("Реальное время (симуляция)")
        self.real_time_checkbox.setToolTip("Показывает процесс оптимизации пошагово")
        self.real_time_checkbox.stateChanged.connect(self.toggle_real_time_mode)
        
        self.speed_label = QLabel("Скорость (мс):")
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(20, 500)
        self.speed_slider.setValue(100)
        self.speed_slider.setEnabled(False)
        self.speed_slider.setToolTip("Задержка между кадрами (мс) - меньше = быстрее")
        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        
        self.speed_value_label = QLabel("100")
        self.speed_value_label.setFixedWidth(35)
        
        viz_layout.addWidget(self.real_time_checkbox)
        viz_layout.addWidget(self.speed_label)
        viz_layout.addWidget(self.speed_slider)
        viz_layout.addWidget(self.speed_value_label)
        
        self.inputs_layout.addWidget(viz_group)
        
        # 5. Слайдер итераций
        label_slider = QLabel("Просмотр эволюции (итерации):")
        self.inputs_layout.addWidget(label_slider)
        self.iter_slider = QSlider(Qt.Orientation.Horizontal)
        self.iter_slider.setEnabled(False)
        self.iter_slider.valueChanged.connect(self.update_iteration)
        self.inputs_layout.addWidget(self.iter_slider)
        
        # 6. Информационная метка
        self.info_label = QLabel()
        self.info_label.setStyleSheet("color: #2c3e50; font-size: 10pt; margin-top: 10px;")
        self.inputs_layout.addWidget(self.info_label)
        
        # 7. Кнопка сброса камеры
        camera_layout = QHBoxLayout()
        
        self.reset_camera_btn = QPushButton("🎥 Сбросить камеру")
        self.reset_camera_btn.setToolTip("Вернуть камеру в исходное положение")
        self.reset_camera_btn.clicked.connect(self.reset_camera)
        
        camera_layout.addWidget(self.reset_camera_btn)
        self.inputs_layout.addLayout(camera_layout)
        
        # Привязываем кнопку расчета
        self.btn_calculate.clicked.connect(self.calculate_bees)

    def on_speed_changed(self, value):
        """Обновление отображения скорости"""
        self.speed_value_label.setText(str(value))

    def toggle_real_time_mode(self, state):
        """Включение/выключение режима реального времени"""
        enabled = (state == Qt.CheckState.Checked.value)
        self.speed_slider.setEnabled(enabled)
        self.speed_label.setEnabled(enabled)
        self.speed_value_label.setEnabled(enabled)

    def calculate_bees(self):
        # Останавливаем текущую симуляцию если есть
        self.stop_simulation()
        
        # 1. Подготовка функции
        self.current_function = self.functions[self.func_combo.currentIndex()]
        bounds = self.current_function.bounds

        # 2. Создание алгоритма
        self.bees_algorithm = BeesAlgorithm(
            func=self.current_function,
            bounds=bounds,
            n_scouts=self.scouts_input.value(),
            n_elite_sites=self.elite_sites_input.value(),
            n_best_sites=self.best_sites_input.value(),
            n_elite_bees=self.elite_bees_input.value(),
            n_best_bees=self.best_bees_input.value(),
            patch_radius=self.radius_input.value(),
            radius_reduction=self.radius_reduction_input.value(),
            max_iterations=self.gens_input.value(),
            stagnation_limit=self.stagnation_input.value(),
            verbose=True
        )
        
        # 3. Визуализация поверхности
        self.vtk_widget.clear_scene()
        self.plot_normalized_surface(bounds)
        
        # 4. Выбор режима работы
        if self.real_time_checkbox.isChecked():
            self.start_real_time_simulation()
        else:
            self.run_batch_optimization()

    def run_batch_optimization(self):
        """Запуск оптимизации без пошаговой визуализации"""
        # Запускаем алгоритм
        best_position, best_value, history = self.bees_algorithm.solve(real_time_callback=None)
        
        self.history = history
        
        # Отрисовка финальной позиции
        self.plot_best_point(best_position, best_value)
        
        # Вывод результатов
        self.display_results(best_position, best_value)
        
        # Настройка слайдера
        self.iter_slider.setEnabled(True)
        self.iter_slider.setRange(0, len(self.history) - 1)
        self.iter_slider.setValue(len(self.history) - 1)
        self.update_iteration(self.iter_slider.value())

    def start_real_time_simulation(self):
        """Запуск симуляции в реальном времени"""
        self.is_simulating = True
        self.history = []
        
        # Отключаем элементы управления
        self.btn_calculate.setEnabled(False)
        self.func_combo.setEnabled(False)
        self.real_time_checkbox.setEnabled(False)

        self.bees_worker = BeesAlgorithmWorker(
            self.bees_algorithm,
            max_iterations=self.gens_input.value(),
            delay_ms=self.speed_slider.value(),
        )
        self.bees_worker.iteration_update.connect(self.on_worker_iteration)
        self.bees_worker.finished_signal.connect(self.on_worker_finished)
        self.bees_worker.start()

    def stop_simulation(self):
        """Остановка симуляции"""
        self.is_simulating = False
        if self.bees_worker is not None:
            self.bees_worker.stop()
            self.bees_worker.wait(2000)
            self.bees_worker = None
        self.btn_calculate.setEnabled(True)
        self.func_combo.setEnabled(True)
        self.real_time_checkbox.setEnabled(True)

    def on_worker_iteration(self, iteration, positions, best_pos, best_val):
        """Обновление GUI из рабочего потока"""
        if not self.is_simulating:
            return

        self.current_iteration = iteration
        self.history.append(np.array(positions))

        self.iter_slider.blockSignals(True)
        self.iter_slider.setEnabled(True)
        self.iter_slider.setRange(0, len(self.history) - 1)
        self.iter_slider.setValue(iteration)
        self.iter_slider.blockSignals(False)

        self.update_iteration(iteration)
        self.plot_best_point(best_pos, best_val)
        self.info_label.setText(
            f"🐝 Итерация {iteration} | Лучшее значение: {best_val:.10f} | Пчел: {len(positions)}"
        )

    def on_worker_finished(self, best_position, best_value, history):
        """Завершение симуляции в реальном времени"""
        self.history = history

        if self.history:
            self.iter_slider.setEnabled(True)
            self.iter_slider.setRange(0, len(self.history) - 1)
            self.iter_slider.setValue(len(self.history) - 1)

        if best_position is not None:
            self.plot_best_point(best_position, best_value)
            self.display_results(best_position, best_value)

        self.btn_calculate.setEnabled(True)
        self.func_combo.setEnabled(True)
        self.real_time_checkbox.setEnabled(True)
        self.is_simulating = False

        if self.bees_worker is not None:
            self.bees_worker.wait(1000)
            self.bees_worker = None

        self.info_label.setText("✅ Симуляция завершена!")

    def plot_normalized_surface(self, bounds):
        """Отрисовка поверхности функции с нормализацией высоты"""
        res = 60
        x = np.linspace(bounds[0, 0], bounds[0, 1], res)
        y = np.linspace(bounds[1, 0], bounds[1, 1], res)
        X, Y = np.meshgrid(x, y)
        Z = np.array([[self.current_function([xi, yi]) for xi in x] for yi in y])

        self.z_min = Z.min()
        real_range = Z.max() - self.z_min
        self.z_range = real_range if real_range > 1e-10 else 1.0

        Z_norm = 10 * (Z - self.z_min) / self.z_range

        points = vtk.vtkPoints()
        for i in range(res):
            for j in range(res):
                points.InsertNextPoint(X[i, j], Y[i, j], Z_norm[i, j])

        grid = vtk.vtkStructuredGrid()
        grid.SetDimensions(res, res, 1)
        grid.SetPoints(points)

        surf = vtk.vtkDataSetSurfaceFilter()
        surf.SetInputData(grid)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(surf.GetOutputPort())
        
        self.surface_actor = vtk.vtkActor()
        self.surface_actor.SetMapper(mapper)
        self.surface_actor.GetProperty().SetColor(0.3, 0.6, 0.9)
        self.surface_actor.GetProperty().SetOpacity(0.6)
        
        self.vtk_widget.add_actor(self.surface_actor)
        
        # Устанавливаем камеру только при первом отображении поверхности
        if self.camera_position is None:
            self.vtk_widget.reset_camera()
            # Сохраняем начальную позицию камеры
            camera = self.vtk_widget.renderer.GetActiveCamera()
            self.camera_position = camera.GetPosition()
            self.camera_focal_point = camera.GetFocalPoint()
        else:
            # Восстанавливаем позицию камеры
            camera = self.vtk_widget.renderer.GetActiveCamera()
            camera.SetPosition(self.camera_position)
            camera.SetFocalPoint(self.camera_focal_point)
            camera.SetViewUp(0, 0, 1)
            self.vtk_widget.render_window.Render()

    def update_iteration(self, idx):
        """Обновление отображения пчел на выбранной итерации"""
        if not self.history or idx >= len(self.history):
            return

        # Удаляем старый актор
        if self.pop_actor:
            self.vtk_widget.renderer.RemoveActor(self.pop_actor)

        # Создаем точки для текущего поколения (пчелы)
        pts = vtk.vtkPoints()
        positions = self.history[idx]
        
        for p in positions:
            z_real = self.current_function(p)
            z_norm = 10 * (z_real - self.z_min) / self.z_range
            pts.InsertNextPoint(p[0], p[1], z_norm + 0.1)

        pd = vtk.vtkPolyData()
        pd.SetPoints(pts)

        # Используем сферы для отображения пчел
        spheres = vtk.vtkSphereSource()
        spheres.SetRadius(0.08)

        glyph = vtk.vtkGlyph3D()
        glyph.SetSourceConnection(spheres.GetOutputPort())
        glyph.SetInputData(pd)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(glyph.GetOutputPort())

        self.pop_actor = vtk.vtkActor()
        self.pop_actor.SetMapper(mapper)
        self.pop_actor.GetProperty().SetColor(1.0, 0.8, 0.2)  # Золотисто-желтые пчелы
        
        self.vtk_widget.add_actor(self.pop_actor)
        
        self.vtk_widget.render_window.Render()

    def plot_best_point(self, point, val):
        """Рисует сферу в точке найденного минимума (источник нектара)"""
        if point is None:
            return
            
        # Удаляем старый актор если есть
        if self.best_actor:
            self.vtk_widget.renderer.RemoveActor(self.best_actor)
            
        z_norm = 10 * (val - self.z_min) / self.z_range
        sphere = vtk.vtkSphereSource()
        sphere.SetCenter(point[0], point[1], z_norm + 0.3)
        sphere.SetRadius(0.2)
        
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(sphere.GetOutputPort())
        
        self.best_actor = vtk.vtkActor()
        self.best_actor.SetMapper(mapper)
        self.best_actor.GetProperty().SetColor(1.0, 0.5, 0.0)  # Оранжевый - цвет нектара
        self.best_actor.GetProperty().SetAmbient(0.3)
        self.best_actor.GetProperty().SetDiffuse(0.7)
        
        self.vtk_widget.add_actor(self.best_actor)
        
        self.vtk_widget.render_window.Render()

    def reset_camera(self):
        """Сброс камеры в исходное положение"""
        if self.vtk_widget:
            self.vtk_widget.reset_camera()
            # Сохраняем новую позицию камеры
            camera = self.vtk_widget.renderer.GetActiveCamera()
            self.camera_position = camera.GetPosition()
            self.camera_focal_point = camera.GetFocalPoint()
            self.vtk_widget.render_window.Render()
            self.info_label.setText("🎥 Камера сброшена")

    def display_results(self, best_position, best_value):
        """Отображение результатов оптимизации"""
        self.clear_results()
        
        # Расчет общего числа пчел
        total_bees = (self.elite_sites_input.value() * self.elite_bees_input.value() +
                     self.best_sites_input.value() * self.best_bees_input.value() +
                     self.scouts_input.value())
        
        res_text = f"""
            <div style='color: #2c3e50;'>
                <b>🐝 Результаты оптимизации пчелиным роем (Bees Algorithm):</b><br>
                <hr>
                <b>🍯 Найденный источник нектара (минимум):</b><br>
                X: {best_position[0]:.8f}<br>
                Y: {best_position[1]:.8f}<br><br>
                <b>📊 Значение функции:</b><br>
                f(x, y) = <b style='color: #e74c3c;'>{best_value:.12f}</b><br><br>
                <b>🐝 Параметры колонии:</b><br>
                • Пчел-разведчиков: {self.scouts_input.value()}<br>
                • Элитных участков: {self.elite_sites_input.value()} (по {self.elite_bees_input.value()} пчел)<br>
                • Перспективных участков: {self.best_sites_input.value()} (по {self.best_bees_input.value()} пчел)<br>
                • Всего пчел в рое: {total_bees}<br>
                • Начальный радиус: {self.radius_input.value()}<br>
                • Коэффициент уменьшения: {self.radius_reduction_input.value()}<br>
                • Лимит стагнации: {self.stagnation_input.value()} итераций
            </div>
        """
        self.add_result_text(res_text)
        
        # Обновляем информационную метку
        self.info_label.setText(f"🍯 Лучшее значение: {best_value:.12f}")
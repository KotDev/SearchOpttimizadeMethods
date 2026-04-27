import numpy as np
import vtk
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import *

from src.lab_base_widget import LabBaseWidget
from src.test_functions.test_func_fabric import TestFunctionFactory
from .hybrid_pso_bees import HybridPSOBeesAlgorithm
from .hybrid_pso_bees_worker import HybridPSOBeesWorker


class Lab8Widget(LabBaseWidget):
    def __init__(self):
        super().__init__(8, "Гибридный алгоритм оптимизации (PSO + Bees)")
        self.history = []
        self.phase_history = []
        self.pop_actor = None
        self.surface_actor = None
        self.best_actor = None

        self.z_min = 0
        self.z_range = 1.0
        self.current_function = None

        self.camera_position = None
        self.camera_focal_point = None
        self.hybrid_worker = None

        self.setup_custom_ui()

    def setup_custom_ui(self):
        self.set_description(
            "Гибридный алгоритм сочетает глобальный поиск роем частиц и локальное уточнение пчелиным роем.\n"
            "Сначала PSO быстро находит перспективные области, затем Bees Algorithm детально исследует их.\n"
            "Поддерживается пакетный и realtime-режим визуализации."
        )

        self.functions = TestFunctionFactory.create_all(dim=2)
        func_names = [f.name for f in self.functions]
        self.func_combo = self.add_input_field("Функция:", QComboBox, items=func_names)

        pso_group = QGroupBox("Фаза 1: PSO")
        pso_layout = QGridLayout()
        pso_group.setLayout(pso_layout)
        self.pso_pop_input = self.add_input_field("Размер роя:", QSpinBox, value=30, range=(10, 200))
        self.pso_iters_input = self.add_input_field("Итераций PSO:", QSpinBox, value=40, range=(5, 300))
        self.inertia_input = self.add_input_field("Инерция (ω):", QDoubleSpinBox, value=0.9, range=(0.1, 1.0), step=0.05)
        self.cognitive_input = self.add_input_field("Когнитивный (c1):", QDoubleSpinBox, value=2.05, range=(0.5, 4.0), step=0.05)
        self.social_input = self.add_input_field("Социальный (c2):", QDoubleSpinBox, value=2.05, range=(0.5, 4.0), step=0.05)
        self.inputs_layout.addWidget(pso_group)

        bees_group = QGroupBox("Фаза 2: Bees")
        bees_layout = QGridLayout()
        bees_group.setLayout(bees_layout)
        self.scouts_input = self.add_input_field("Пчел-разведчиков:", QSpinBox, value=16, range=(5, 100))
        self.elite_sites_input = self.add_input_field("Элитных участков:", QSpinBox, value=2, range=(1, 20))
        self.best_sites_input = self.add_input_field("Перспективных участков:", QSpinBox, value=3, range=(1, 20))
        self.elite_bees_input = self.add_input_field("Пчел на элитном:", QSpinBox, value=7, range=(1, 30))
        self.best_bees_input = self.add_input_field("Пчел на перспективном:", QSpinBox, value=4, range=(1, 30))
        self.radius_input = self.add_input_field("Начальный радиус:", QDoubleSpinBox, value=0.2, range=(0.05, 1.0), step=0.05)
        self.radius_reduction_input = self.add_input_field("Уменьшение радиуса:", QDoubleSpinBox, value=0.8, range=(0.5, 0.95), step=0.05)
        self.stagnation_input = self.add_input_field("Лимит стагнации:", QSpinBox, value=20, range=(5, 100))
        self.inputs_layout.addWidget(bees_group)

        viz_group = QGroupBox("Визуализация")
        viz_layout = QHBoxLayout()
        viz_group.setLayout(viz_layout)
        self.real_time_checkbox = QCheckBox("Реальное время (симуляция)")
        self.real_time_checkbox.stateChanged.connect(self.toggle_real_time_mode)
        self.speed_label = QLabel("Скорость (мс):")
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(20, 500)
        self.speed_slider.setValue(100)
        self.speed_slider.setEnabled(False)
        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        self.speed_value_label = QLabel("100")
        self.speed_value_label.setFixedWidth(35)

        viz_layout.addWidget(self.real_time_checkbox)
        viz_layout.addWidget(self.speed_label)
        viz_layout.addWidget(self.speed_slider)
        viz_layout.addWidget(self.speed_value_label)
        self.inputs_layout.addWidget(viz_group)

        self.inputs_layout.addWidget(QLabel("Просмотр эволюции (итерации):"))
        self.iter_slider = QSlider(Qt.Orientation.Horizontal)
        self.iter_slider.setEnabled(False)
        self.iter_slider.valueChanged.connect(self.update_iteration)
        self.inputs_layout.addWidget(self.iter_slider)

        self.info_label = QLabel()
        self.info_label.setStyleSheet("color: #2c3e50; font-size: 10pt; margin-top: 10px;")
        self.inputs_layout.addWidget(self.info_label)

        self.reset_camera_btn = QPushButton("Сбросить камеру")
        self.reset_camera_btn.clicked.connect(self.reset_camera)
        self.inputs_layout.addWidget(self.reset_camera_btn)

        self.btn_calculate.clicked.connect(self.calculate_hybrid)

    def on_speed_changed(self, value):
        self.speed_value_label.setText(str(value))

    def toggle_real_time_mode(self, state):
        enabled = (state == Qt.CheckState.Checked.value)
        self.speed_slider.setEnabled(enabled)
        self.speed_label.setEnabled(enabled)
        self.speed_value_label.setEnabled(enabled)

    def calculate_hybrid(self):
        self.stop_simulation()

        self.current_function = self.functions[self.func_combo.currentIndex()]
        bounds = self.current_function.bounds
        self.hybrid_algorithm = HybridPSOBeesAlgorithm(
            func=self.current_function,
            bounds=bounds,
            pso_population=self.pso_pop_input.value(),
            pso_iterations=self.pso_iters_input.value(),
            inertia_weight=self.inertia_input.value(),
            cognitive_weight=self.cognitive_input.value(),
            social_weight=self.social_input.value(),
            n_scouts=self.scouts_input.value(),
            n_elite_sites=self.elite_sites_input.value(),
            n_best_sites=self.best_sites_input.value(),
            n_elite_bees=self.elite_bees_input.value(),
            n_best_bees=self.best_bees_input.value(),
            patch_radius=self.radius_input.value(),
            radius_reduction=self.radius_reduction_input.value(),
            stagnation_limit=self.stagnation_input.value(),
            verbose=True,
        )

        self.vtk_widget.clear_scene()
        self.plot_normalized_surface(bounds)

        if self.real_time_checkbox.isChecked():
            self.start_real_time_simulation()
        else:
            self.run_batch_optimization()

    def run_batch_optimization(self):
        best_position, best_value, history, phase_history = self.hybrid_algorithm.solve(real_time_callback=None)
        self.history = history
        self.phase_history = phase_history
        self.plot_best_point(best_position, best_value)
        self.display_results(best_position, best_value)
        self.iter_slider.setEnabled(True)
        self.iter_slider.setRange(0, len(self.history) - 1)
        self.iter_slider.setValue(len(self.history) - 1)
        self.update_iteration(self.iter_slider.value())

    def start_real_time_simulation(self):
        self.is_simulating = True
        self.history = []
        self.phase_history = []
        self.btn_calculate.setEnabled(False)
        self.func_combo.setEnabled(False)
        self.real_time_checkbox.setEnabled(False)

        self.hybrid_worker = HybridPSOBeesWorker(self.hybrid_algorithm, delay_ms=self.speed_slider.value())
        self.hybrid_worker.iteration_update.connect(self.on_worker_iteration)
        self.hybrid_worker.finished_signal.connect(self.on_worker_finished)
        self.hybrid_worker.start()

    def stop_simulation(self):
        self.is_simulating = False
        if self.hybrid_worker is not None:
            self.hybrid_worker.stop()
            self.hybrid_worker.wait(2000)
            self.hybrid_worker = None
        self.btn_calculate.setEnabled(True)
        self.func_combo.setEnabled(True)
        if hasattr(self, "real_time_checkbox"):
            self.real_time_checkbox.setEnabled(True)

    def on_worker_iteration(self, iteration, phase, positions, best_pos, best_val):
        if not self.is_simulating:
            return

        self.history.append(np.array(positions))
        self.phase_history.append(phase)
        self.iter_slider.blockSignals(True)
        self.iter_slider.setEnabled(True)
        self.iter_slider.setRange(0, len(self.history) - 1)
        self.iter_slider.setValue(iteration)
        self.iter_slider.blockSignals(False)
        self.update_iteration(iteration)
        self.plot_best_point(best_pos, best_val)
        self.info_label.setText(
            f"Гибрид | Фаза: {phase} | Итерация {iteration} | Лучшее: {best_val:.10f} | Агентов: {len(positions)}"
        )

    def on_worker_finished(self, best_position, best_value, history, phase_history):
        self.history = history
        self.phase_history = phase_history
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

        if self.hybrid_worker is not None:
            self.hybrid_worker.wait(1000)
            self.hybrid_worker = None

        self.info_label.setText("✅ Гибридная симуляция завершена!")

    def plot_normalized_surface(self, bounds):
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
        self.surface_actor.GetProperty().SetColor(0.4, 0.65, 0.95)
        self.surface_actor.GetProperty().SetOpacity(0.6)
        self.vtk_widget.add_actor(self.surface_actor)

        if self.camera_position is None:
            self.vtk_widget.reset_camera()
            camera = self.vtk_widget.renderer.GetActiveCamera()
            self.camera_position = camera.GetPosition()
            self.camera_focal_point = camera.GetFocalPoint()
        else:
            camera = self.vtk_widget.renderer.GetActiveCamera()
            camera.SetPosition(self.camera_position)
            camera.SetFocalPoint(self.camera_focal_point)
            camera.SetViewUp(0, 0, 1)
            self.vtk_widget.render_window.Render()

    def update_iteration(self, idx):
        if not self.history or idx >= len(self.history):
            return

        if self.pop_actor:
            self.vtk_widget.renderer.RemoveActor(self.pop_actor)

        positions = self.history[idx]
        phase = self.phase_history[idx] if idx < len(self.phase_history) else "PSO"

        pts = vtk.vtkPoints()
        for p in positions:
            z_real = self.current_function(p)
            z_norm = 10 * (z_real - self.z_min) / self.z_range
            pts.InsertNextPoint(p[0], p[1], z_norm + 0.1)

        pd = vtk.vtkPolyData()
        pd.SetPoints(pts)

        spheres = vtk.vtkSphereSource()
        spheres.SetRadius(0.08)
        glyph = vtk.vtkGlyph3D()
        glyph.SetSourceConnection(spheres.GetOutputPort())
        glyph.SetInputData(pd)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(glyph.GetOutputPort())

        self.pop_actor = vtk.vtkActor()
        self.pop_actor.SetMapper(mapper)
        if phase == "PSO":
            self.pop_actor.GetProperty().SetColor(0.9, 0.1, 0.1)
        else:
            self.pop_actor.GetProperty().SetColor(1.0, 0.8, 0.2)

        self.vtk_widget.add_actor(self.pop_actor)
        self.vtk_widget.render_window.Render()

    def plot_best_point(self, point, val):
        if point is None:
            return

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
        self.best_actor.GetProperty().SetColor(0.1, 0.8, 0.1)
        self.best_actor.GetProperty().SetAmbient(0.3)
        self.best_actor.GetProperty().SetDiffuse(0.7)
        self.vtk_widget.add_actor(self.best_actor)
        self.vtk_widget.render_window.Render()

    def reset_camera(self):
        if self.vtk_widget:
            self.vtk_widget.reset_camera()
            camera = self.vtk_widget.renderer.GetActiveCamera()
            self.camera_position = camera.GetPosition()
            self.camera_focal_point = camera.GetFocalPoint()
            self.vtk_widget.render_window.Render()
            self.info_label.setText("Камера сброшена")

    def display_results(self, best_position, best_value):
        self.clear_results()
        res_text = f"""
            <div style='color: #2c3e50;'>
                <b>Результаты гибридной оптимизации PSO + Bees:</b><br>
                <hr>
                <b>Найденный минимум:</b><br>
                X: {best_position[0]:.8f}<br>
                Y: {best_position[1]:.8f}<br><br>
                <b>Значение функции:</b><br>
                f(x, y) = <b style='color: #e74c3c;'>{best_value:.12f}</b><br><br>
                <b>Параметры PSO:</b><br>
                • Размер роя: {self.pso_pop_input.value()}<br>
                • Итераций PSO: {self.pso_iters_input.value()}<br>
                • Инерция: {self.inertia_input.value()}<br>
                • c1: {self.cognitive_input.value()}<br>
                • c2: {self.social_input.value()}<br><br>
                <b>Параметры Bees:</b><br>
                • Пчел-разведчиков: {self.scouts_input.value()}<br>
                • Элитных участков: {self.elite_sites_input.value()}<br>
                • Перспективных участков: {self.best_sites_input.value()}<br>
                • Радиус поиска: {self.radius_input.value()}<br>
                • Уменьшение радиуса: {self.radius_reduction_input.value()}
            </div>
        """
        self.add_result_text(res_text)
        self.info_label.setText(f"Лучшее значение: {best_value:.12f}")

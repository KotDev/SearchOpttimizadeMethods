import numpy as np
import vtk
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import *

from src.lab_base_widget import LabBaseWidget
from src.test_functions.test_func_fabric import TestFunctionFactory
from .bacterial_optimization import BacterialForagingOptimization
from .bacterial_optimization_worker import BacterialOptimizationWorker


class Lab7Widget(LabBaseWidget):
    def __init__(self):
        super().__init__(7, "Бактериальная оптимизация (BFO)")
        self.history = []
        self.pop_actor = None
        self.surface_actor = None
        self.best_actor = None

        self.z_min = 0
        self.z_range = 1.0
        self.current_function = None

        self.camera_position = None
        self.camera_focal_point = None
        self.bacterial_worker = None

        self.setup_custom_ui()

    def setup_custom_ui(self):
        self.set_description(
            "Глобальная оптимизация бактериальным поиском.\n"
            "Бактерии выполняют tumbling/swimming, затем размножаются и частично рассеиваются.\n"
            "Алгоритм хорошо подходит для многомодальных функций."
        )

        self.functions = TestFunctionFactory.create_all(dim=2)
        func_names = [f.name for f in self.functions]
        self.func_combo = self.add_input_field("Функция:", QComboBox, items=func_names)

        self.bacteria_input = self.add_input_field("Число бактерий:", QSpinBox, value=20, range=(6, 120))
        self.chemotaxis_input = self.add_input_field("Шагов chemotaxis:", QSpinBox, value=12, range=(1, 50))
        self.swim_input = self.add_input_field("Длина swim:", QSpinBox, value=4, range=(1, 20))
        self.reproduction_input = self.add_input_field("Шагов размножения:", QSpinBox, value=6, range=(1, 30))
        self.elimination_input = self.add_input_field("Шагов рассеивания:", QSpinBox, value=2, range=(1, 20))
        self.step_size_input = self.add_input_field(
            "Размер шага:", QDoubleSpinBox, value=0.12, range=(0.01, 0.5), step=0.01
        )
        self.elimination_prob_input = self.add_input_field(
            "Вероятность рассеивания:", QDoubleSpinBox, value=0.2, range=(0.01, 0.8), step=0.01
        )
        self.gens_input = self.add_input_field("Макс. итераций:", QSpinBox, value=144, range=(10, 1000))
        self.stagnation_input = self.add_input_field("Лимит стагнации:", QSpinBox, value=30, range=(5, 200))

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

        self.btn_calculate.clicked.connect(self.calculate_bacterial)

    def on_speed_changed(self, value):
        self.speed_value_label.setText(str(value))

    def toggle_real_time_mode(self, state):
        enabled = (state == Qt.CheckState.Checked.value)
        self.speed_slider.setEnabled(enabled)
        self.speed_label.setEnabled(enabled)
        self.speed_value_label.setEnabled(enabled)

    def calculate_bacterial(self):
        self.stop_simulation()

        self.current_function = self.functions[self.func_combo.currentIndex()]
        bounds = self.current_function.bounds

        self.bacterial_algorithm = BacterialForagingOptimization(
            func=self.current_function,
            bounds=bounds,
            n_bacteria=self.bacteria_input.value(),
            chemotaxis_steps=self.chemotaxis_input.value(),
            swim_length=self.swim_input.value(),
            reproduction_steps=self.reproduction_input.value(),
            elimination_steps=self.elimination_input.value(),
            step_size=self.step_size_input.value(),
            elimination_probability=self.elimination_prob_input.value(),
            max_iterations=self.gens_input.value(),
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
        best_position, best_value, history = self.bacterial_algorithm.solve(real_time_callback=None)
        self.history = history
        self.plot_best_point(best_position, best_value)
        self.display_results(best_position, best_value)
        self.iter_slider.setEnabled(True)
        self.iter_slider.setRange(0, len(self.history) - 1)
        self.iter_slider.setValue(len(self.history) - 1)
        self.update_iteration(self.iter_slider.value())

    def start_real_time_simulation(self):
        self.is_simulating = True
        self.history = []
        self.btn_calculate.setEnabled(False)
        self.func_combo.setEnabled(False)
        self.real_time_checkbox.setEnabled(False)

        self.bacterial_worker = BacterialOptimizationWorker(
            self.bacterial_algorithm, delay_ms=self.speed_slider.value()
        )
        self.bacterial_worker.iteration_update.connect(self.on_worker_iteration)
        self.bacterial_worker.finished_signal.connect(self.on_worker_finished)
        self.bacterial_worker.start()

    def stop_simulation(self):
        self.is_simulating = False
        if self.bacterial_worker is not None:
            self.bacterial_worker.stop()
            self.bacterial_worker.wait(2000)
            self.bacterial_worker = None
        self.btn_calculate.setEnabled(True)
        self.func_combo.setEnabled(True)
        if hasattr(self, "real_time_checkbox"):
            self.real_time_checkbox.setEnabled(True)

    def on_worker_iteration(self, iteration, positions, best_pos, best_val):
        if not self.is_simulating:
            return

        self.history.append(np.array(positions))
        self.iter_slider.blockSignals(True)
        self.iter_slider.setEnabled(True)
        self.iter_slider.setRange(0, len(self.history) - 1)
        self.iter_slider.setValue(iteration)
        self.iter_slider.blockSignals(False)
        self.update_iteration(iteration)
        self.plot_best_point(best_pos, best_val)
        self.info_label.setText(
            f"BFO | Итерация {iteration} | Лучшее: {best_val:.10f} | Бактерий: {len(positions)}"
        )

    def on_worker_finished(self, best_position, best_value, history):
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

        if self.bacterial_worker is not None:
            self.bacterial_worker.wait(1000)
            self.bacterial_worker = None

        self.info_label.setText("✅ Симуляция завершена!")

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
        self.surface_actor.GetProperty().SetColor(0.5, 0.75, 0.9)
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

        pts = vtk.vtkPoints()
        positions = self.history[idx]
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
        self.pop_actor.GetProperty().SetColor(0.7, 0.2, 0.2)
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
        self.best_actor.GetProperty().SetColor(0.8, 0.1, 0.1)
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
                <b>Результаты бактериальной оптимизации:</b><br>
                <hr>
                <b>Найденный минимум:</b><br>
                X: {best_position[0]:.8f}<br>
                Y: {best_position[1]:.8f}<br><br>
                <b>Значение функции:</b><br>
                f(x, y) = <b style='color: #e74c3c;'>{best_value:.12f}</b><br><br>
                <b>Параметры BFO:</b><br>
                • Бактерий: {self.bacteria_input.value()}<br>
                • Chemotaxis: {self.chemotaxis_input.value()}<br>
                • Swim: {self.swim_input.value()}<br>
                • Размножение: {self.reproduction_input.value()}<br>
                • Рассеивание: {self.elimination_input.value()}<br>
                • Размер шага: {self.step_size_input.value()}<br>
                • Вероятность рассеивания: {self.elimination_prob_input.value()}
            </div>
        """
        self.add_result_text(res_text)
        self.info_label.setText(f"Лучшее значение: {best_value:.12f}")

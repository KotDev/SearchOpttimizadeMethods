import numpy as np
import vtk
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from src.lab_base_widget import LabBaseWidget
from .pso import ParticleSwarmOptimization
from src.test_functions.test_func_fabric import TestFunctionFactory


class Lab4Widget(LabBaseWidget):
    def __init__(self):
        super().__init__(4, "Алгоритм роя частиц")
        self.history = []
        self.pop_actor = None
        self.surface_actor = None
        self.best_actor = None
        self.global_best_actor = None  # Для отображения глобального лучшего решения
        
        # Коэффициенты для нормализации Z
        self.z_min = 0
        self.z_range = 1.0
        self.current_function = None
        
        self.setup_custom_ui()

    def setup_custom_ui(self):
        # 1. Описание
        self.set_description(
            "Глобальная оптимизация Алгоритмом Роя Частиц (PSO).\n"
            "Алгоритм имитирует поведение роя (стаи птиц, косяка рыб).\n"
            "Каждая частица запоминает свою лучшую позицию и учитывает глобальную лучшую позицию роя.\n"
            "Используется нормализация высоты для стабильного отображения."
        )

        # 2. Выбор функции
        self.functions = TestFunctionFactory.create_all(dim=2)
        func_names = [f.name for f in self.functions]
        self.func_combo = self.add_input_field("Функция:", QComboBox, items=func_names)

        # 3. Параметры PSO
        self.pop_size_input = self.add_input_field("Размер роя:", QSpinBox, value=50, range=(10, 300))
        self.gens_input = self.add_input_field("Итераций:", QSpinBox, value=50, range=(1, 500))
        
        # Коэффициенты алгоритма
        self.inertia_input = self.add_input_field(
            "Инерция (ω):", QDoubleSpinBox, value=0.9, range=(0.1, 1.0), step=0.05,
            tooltip="Коэффициент инерции. Влияет на сохранение текущей скорости. Уменьшается динамически."
        )
        self.cognitive_input = self.add_input_field(
            "Когнитивный (c1):", QDoubleSpinBox, value=2.05, range=(0.5, 4.0), step=0.05,
            tooltip="Влияние личного лучшего решения частицы (постальгия)"
        )
        self.social_input = self.add_input_field(
            "Социальный (c2):", QDoubleSpinBox, value=2.05, range=(0.5, 4.0), step=0.05,
            tooltip="Влияние глобального лучшего решения роя"
        )
        
        # 4. Слайдер итераций
        label_slider = QLabel("Просмотр эволюции (итерации):")
        self.inputs_layout.addWidget(label_slider)
        self.iter_slider = QSlider(Qt.Orientation.Horizontal)
        self.iter_slider.setEnabled(False)
        self.iter_slider.valueChanged.connect(self.update_iteration)
        self.inputs_layout.addWidget(self.iter_slider)
        
        # 5. Дополнительная информация
        self.info_label = QLabel()
        self.info_label.setStyleSheet("color: #2c3e50; font-size: 10pt; margin-top: 10px;")
        self.inputs_layout.addWidget(self.info_label)

        # Привязываем кнопку расчета
        self.btn_calculate.clicked.connect(self.calculate_pso)

    def calculate_pso(self):
        # 1. Подготовка функции
        self.current_function = self.functions[self.func_combo.currentIndex()]
        bounds = self.current_function.bounds

        # 2. Запуск алгоритма роя частиц
        pso = ParticleSwarmOptimization(
            func=self.current_function,
            bounds=bounds,
            pop_size=self.pop_size_input.value(),
            inertia_weight=self.inertia_input.value(),
            cognitive_weight=self.cognitive_input.value(),
            social_weight=self.social_input.value()
        )
        
        generations = self.gens_input.value()
        pso.solve(generations=generations, verbose=True)
        
        self.history = pso.history
        best_position, best_value = pso.get_best_solution()

        # 3. Визуализация поверхности (нормализованная)
        self.vtk_widget.clear_scene()
        self.plot_normalized_surface(bounds)

        # 4. Вывод текстового результата
        self.clear_results()
        
        # Дополнительная информация о коэффициентах
        phi = self.cognitive_input.value() + self.social_input.value()
        chi_info = ""
        if phi > 4:
            chi = 2 / abs(2 - phi - np.sqrt(phi**2 - 4*phi))
            chi_info = f"<br>Коэффициент сжатия χ = {chi:.4f} (φ = {phi:.2f} > 4)"
        else:
            chi_info = f"<br>φ = {phi:.2f} ≤ 4, сжатие не применяется"
        
        res_text = f"""
            <div style='color: #2c3e50;'>
                <b>Результаты оптимизации PSO (Алгоритм роя частиц):</b><br>
                <hr>
                <b>Найденный минимум:</b><br>
                X: {best_position[0]:.8f}<br>
                Y: {best_position[1]:.8f}<br><br>
                <b>Значение функции:</b><br>
                f(x, y) = <b style='color: #e74c3c;'>{best_value:.12f}</b><br><br>
                <b>Параметры алгоритма:</b><br>
                Размер роя: {self.pop_size_input.value()}<br>
                Инерция (ω): {self.inertia_input.value()} → уменьшается до 0.4<br>
                Когнитивный (c1): {self.cognitive_input.value()}<br>
                Социальный (c2): {self.social_input.value()}{chi_info}
            </div>
        """
        self.add_result_text(res_text)
        
        # Обновляем информационную метку
        self.info_label.setText(f"🎯 Лучшее значение: {best_value:.12f}")

        # 5. Отрисовка точки на графике
        self.plot_best_point(best_position, best_value)
        self.plot_global_best_trajectory()

        # 6. Настройка слайдера
        self.iter_slider.setEnabled(True)
        self.iter_slider.setRange(0, len(self.history) - 1)
        self.iter_slider.setValue(len(self.history) - 1)
        self.update_iteration(self.iter_slider.value())

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
        self.vtk_widget.reset_camera()

    def update_iteration(self, idx):
        """Обновление отображения частиц на выбранной итерации"""
        if not self.history or idx >= len(self.history):
            return

        # Удаляем старый актор частиц
        if self.pop_actor:
            self.vtk_widget.renderer.RemoveActor(self.pop_actor)

        # Создаем точки для текущего поколения
        pts = vtk.vtkPoints()
        positions = self.history[idx]
        
        for p in positions:
            z_real = self.current_function(p)
            z_norm = 10 * (z_real - self.z_min) / self.z_range
            pts.InsertNextPoint(p[0], p[1], z_norm + 0.1)

        pd = vtk.vtkPolyData()
        pd.SetPoints(pts)

        spheres = vtk.vtkSphereSource()
        spheres.SetRadius(0.12)

        glyph = vtk.vtkGlyph3D()
        glyph.SetSourceConnection(spheres.GetOutputPort())
        glyph.SetInputData(pd)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(glyph.GetOutputPort())

        self.pop_actor = vtk.vtkActor()
        self.pop_actor.SetMapper(mapper)
        self.pop_actor.GetProperty().SetColor(1, 0, 0)  # Красные частицы
        
        self.vtk_widget.add_actor(self.pop_actor)
        
        # Обновляем информационную метку
        self.info_label.setText(f"📊 Итерация {idx}/{len(self.history)-1} | Частиц: {len(positions)}")
        
        self.vtk_widget.render_window.Render()

    def plot_best_point(self, point, val):
        """Рисует золотую сферу в точке найденного минимума"""
        # Удаляем старый актор если есть
        if self.best_actor:
            self.vtk_widget.renderer.RemoveActor(self.best_actor)
            
        z_norm = 10 * (val - self.z_min) / self.z_range
        sphere = vtk.vtkSphereSource()
        sphere.SetCenter(point[0], point[1], z_norm + 0.3)
        sphere.SetRadius(0.25)
        
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(sphere.GetOutputPort())
        
        self.best_actor = vtk.vtkActor()
        self.best_actor.SetMapper(mapper)
        self.best_actor.GetProperty().SetColor(1.0, 0.8, 0.0)  # Золотой
        self.best_actor.GetProperty().SetAmbient(0.3)
        self.best_actor.GetProperty().SetDiffuse(0.7)
        
        self.vtk_widget.add_actor(self.best_actor)
        
    def plot_global_best_trajectory(self):
        """Рисует траекторию глобального лучшего решения (опционально)"""
        # Здесь можно добавить отображение траектории лучшей частицы
        # Для этого нужно модифицировать PSO для сохранения истории лучших позиций
        pass
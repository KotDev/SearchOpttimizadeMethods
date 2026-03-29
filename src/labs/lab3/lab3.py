import numpy as np
import vtk
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from src.lab_base_widget import LabBaseWidget
from .ga import GeneticAlgorithm
from src.test_functions.test_func_fabric import TestFunctionFactory

class Lab3Widget(LabBaseWidget):
    def __init__(self):
        super().__init__(3, "Генетический алгоритм")
        self.history = []
        self.pop_actor = None
        self.surface_actor = None
        self.best_actor = None
        
        # Коэффициенты для нормализации Z
        self.z_min = 0
        self.z_range = 1.0
        self.current_function = None
        
        self.setup_custom_ui()

    def setup_custom_ui(self):
        # 1. Описание
        self.set_description("Глобальная оптимизация Генетическим Алгоритмом.\n"
                             "Используется нормализация высоты для стабильного отображения.")

        # 2. Выбор функции
        self.functions = TestFunctionFactory.create_all(dim=2)
        func_names = [f.name for f in self.functions]
        # Используем ваш метод add_input_field
        self.func_combo = self.add_input_field("Функция:", QComboBox, items=func_names)

        # 3. Параметры ГА (используем add_input_field, как в вашем рабочем коде)
        self.pop_size_input = self.add_input_field("Популяция:", QSpinBox, value=50, range=(10, 300))
        self.gens_input = self.add_input_field("Поколений:", QSpinBox, value=50, range=(1, 500))
        self.mut_rate_input = self.add_input_field("Мутация:", QDoubleSpinBox, value=0.1, range=(0, 1))
        
        # 4. Слайдер итераций
        label_slider = QLabel("Просмотр эволюции (поколения):")
        self.inputs_layout.addWidget(label_slider)
        self.iter_slider = QSlider(Qt.Orientation.Horizontal)
        self.iter_slider.setEnabled(False)
        self.iter_slider.valueChanged.connect(self.update_iteration)
        self.inputs_layout.addWidget(self.iter_slider)

        # Привязываем кнопку расчета (в базе она обычно self.btn_calculate)
        self.btn_calculate.clicked.connect(self.calculate_ga)

    def calculate_ga(self):
        # 1. Подготовка функции
        self.current_function = self.functions[self.func_combo.currentIndex()]
        bounds = self.current_function.bounds

        # 2. Запуск алгоритма
        ga = GeneticAlgorithm(
            func=self.current_function,
            bounds=bounds,
            pop_size=self.pop_size_input.value(),
            mut_rate=self.mut_rate_input.value()
        )
        ga.solve(generations=self.gens_input.value())
        self.history = ga.history

        # 3. Визуализация поверхности (нормализованная)
        self.vtk_widget.clear_scene()
        self.plot_normalized_surface(bounds)

        # 4. Поиск лучшей точки (Минимума)
        last_pop = self.history[-1]
        fitness = np.array([self.current_function(p) for p in last_pop])
        best_idx = np.argmin(fitness)
        best_point = last_pop[best_idx]
        best_value = fitness[best_idx]

        # 5. Вывод текстового результата
        self.clear_results()
        res_text = f"""
            <div style='color: #2c3e50;'>
                <b>Результаты оптимизации ГА:</b><br>
                <hr>
                <b>Точка минимума:</b><br>
                X: {best_point[0]:.6f}<br>
                Y: {best_point[1]:.6f}<br><br>
                <b>Значение функции:</b><br>
                f(x, y) = <b>{best_value:.10f}</b>
            </div>
        """
        self.add_result_text(res_text)

        # 6. Отрисовка точки на графике
        self.plot_best_point(best_point, best_value)

        # 7. Настройка слайдера
        self.iter_slider.setEnabled(True)
        self.iter_slider.setRange(0, len(self.history) - 1)
        self.iter_slider.setValue(len(self.history) - 1) # Сразу к последнему
        self.update_iteration(self.iter_slider.value())

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
        self.surface_actor.GetProperty().SetColor(0.3, 0.6, 0.9)
        self.surface_actor.GetProperty().SetOpacity(0.6)
        
        self.vtk_widget.add_actor(self.surface_actor)
        self.vtk_widget.reset_camera()

    def update_iteration(self, idx):
        if not self.history or idx >= len(self.history): return

        if self.pop_actor:
            self.vtk_widget.renderer.RemoveActor(self.pop_actor)

        pts = vtk.vtkPoints()
        for p in self.history[idx]:
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
        self.pop_actor.GetProperty().SetColor(1, 0, 0)
        
        self.vtk_widget.add_actor(self.pop_actor)
        self.vtk_widget.render_window.Render()

    def plot_best_point(self, point, val):
        """Рисует золотую сферу в точке минимума"""
        z_norm = 10 * (val - self.z_min) / self.z_range
        sphere = vtk.vtkSphereSource()
        sphere.SetCenter(point[0], point[1], z_norm + 0.3)
        sphere.SetRadius(0.25)
        
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(sphere.GetOutputPort())
        
        self.best_actor = vtk.vtkActor()
        self.best_actor.SetMapper(mapper)
        self.best_actor.GetProperty().SetColor(1.0, 0.8, 0.0) # Gold
        
        self.vtk_widget.add_actor(self.best_actor)
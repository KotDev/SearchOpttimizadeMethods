import numpy as np
from src.lab_base_widget import LabBaseWidget
from src.labs.lab1.methods_factory import MethodFactory
from src.test_functions.test_func_fabric import (
    TestFunctionFactory,
)
from PyQt6.QtWidgets import *
import vtk
from vtkmodules.util import numpy_support
import sys
import numpy as np
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import vtk
from vtkmodules.util import numpy_support


class Lab1Widget(LabBaseWidget):
    """Лабораторная работа №1: Градиентные методы оптимизации"""

    def __init__(self):
        super().__init__(1, "Градиентные методы оптимизации")
        self.current_function = None
        self.current_method = None
        self.trajectory_actor = None
        self.surface_actor = None
        self.contour_actor = None
        self.min_point_actor = None
        self.start_point_actor = None
        self.setup_custom_ui()

    def setup_custom_ui(self):
        """Настройка интерфейса для лабы 1"""
        self.set_description(
            "Исследование градиентных методов оптимизации:\n"
            "• Градиентный спуск с постоянным шагом\n"
            "• Наискорейший спуск\n"
            "• Покоординатный спуск\n"
            "• Метод Ньютона-Рафсона\n\n"
            "Визуализация поверхности, линий уровня и траектории поиска минимума."
        )

        # Получаем все тестовые функции
        self.functions = TestFunctionFactory.create_all(dim=2)
        function_names = [f.name for f in self.functions]

        # Выбор функции
        self.func_combo = self.add_input_field(
            "Тестовая функция:",
            QComboBox,
            items=function_names
        )
        self.func_combo.currentTextChanged.connect(self.on_function_changed)

        # Метод оптимизации
        self.method_combo = self.add_input_field(
            "Метод оптимизации:",
            QComboBox,
            items=[
                "Градиентный спуск (постоянный шаг)",
                "Наискорейший спуск",
                "Покоординатный спуск",
                "Ньютон-Рафсон"
            ]
        )

        # Параметры метода
        self.step_size = self.add_input_field(
            "Шаг (для град. спуска):",
            QDoubleSpinBox,
            value=0.01,
            range=(0.0001, 1.0)
        )

        self.damping = self.add_input_field(
            "Демпфирование (Ньютон):",
            QDoubleSpinBox,
            value=1.0,
            range=(0.1, 2.0)
        )

        # Начальная точка
        self.start_x = self.add_input_field(
            "Начальная X₀:",
            QDoubleSpinBox,
            value=0.5,
            range=(-5, 5)
        )

        self.start_y = self.add_input_field(
            "Начальная Y₀:",
            QDoubleSpinBox,
            value=1.0,
            range=(-5, 5)
        )

        # Параметры останова
        self.max_iter = self.add_input_field(
            "Макс. итераций:",
            QSpinBox,
            value=100,
            range=(10, 1000)
        )

        self.epsilon = self.add_input_field(
            "Точность ε:",
            QDoubleSpinBox,
            value=0.01,
            range=(0.0001, 0.1)
        )

        # Параметры визуализации
        self.resolution = self.add_input_field(
            "Разрешение сетки:",
            QSpinBox,
            value=50,
            range=(20, 200)
        )

        # Параметры отображения
        options_container = QWidget()
        options_layout = QHBoxLayout(options_container)

        self.show_surface = QCheckBox("Показать поверхность")
        self.show_surface.setChecked(True)
        options_layout.addWidget(self.show_surface)

        self.show_contours = QCheckBox("Показать линии уровня")
        self.show_contours.setChecked(True)
        options_layout.addWidget(self.show_contours)

        self.show_trajectory = QCheckBox("Показать траекторию")
        self.show_trajectory.setChecked(True)
        options_layout.addWidget(self.show_trajectory)

        self.show_minimum = QCheckBox("Показать минимум")
        self.show_minimum.setChecked(True)
        options_layout.addWidget(self.show_minimum)

        self.inputs_layout.addWidget(options_container)

        # Кнопка сброса вида
        self.btn_reset_view = QPushButton("Сбросить вид")
        self.btn_reset_view.clicked.connect(self.reset_view)
        self.inputs_layout.addWidget(self.btn_reset_view)

        # Подключаем кнопку расчета
        self.btn_calculate.clicked.connect(self.calculate)

        # Устанавливаем начальные диапазоны
        self.on_function_changed(self.func_combo.currentText())

    def on_function_changed(self, func_name):
        """Обработчик изменения функции"""
        for f in self.functions:
            if f.name == func_name:
                self.current_function = f
                break

        if self.current_function:
            bounds = self.current_function.bounds
            self.start_x.setRange(bounds[0, 0], bounds[0, 1])
            self.start_y.setRange(bounds[1, 0], bounds[1, 1])

            # Устанавливаем начальную точку в зависимости от функции
            if "Розенброка" in func_name:
                self.start_x.setValue(0.5)
                self.start_y.setValue(1.0)
            elif "Химмельблау" in func_name:
                self.start_x.setValue(0.0)
                self.start_y.setValue(0.0)
            elif "Растригина" in func_name:
                self.start_x.setValue(1.0)
                self.start_y.setValue(1.0)
            elif "Аклея" in func_name:
                self.start_x.setValue(1.0)
                self.start_y.setValue(1.0)
            else:
                self.start_x.setValue(1.0)
                self.start_y.setValue(1.0)

    def calculate(self):
        """Основной метод расчета"""
        try:
            print("=" * 50)
            print("Starting calculation...")

            # Очищаем предыдущие результаты
            self.clear_results()
            print("Cleared previous results")

            if hasattr(self, 'vtk_widget') and self.vtk_widget:
                print("Clearing VTK scene")
                self.vtk_widget.clear_scene()
            else:
                print("WARNING: vtk_widget not available")
                self.add_result_label("Ошибка: VTK виджет не инициализирован", "error")
                return

            # Получаем выбранную функцию
            func_name = self.func_combo.currentText()
            print(f"Selected function: {func_name}")

            # Преобразуем название функции в ключ для фабрики
            func_key = self.get_function_key(func_name)
            print(f"Function key: {func_key}")

            # Создаем функцию через фабрику
            self.current_function = TestFunctionFactory.create(func_key, dim=2)
            print(f"Created function: {self.current_function.name}")

            # Получаем границы функции
            bounds = self.current_function.bounds
            print(f"Function bounds: {bounds}")

            # Определяем оптимальный диапазон для визуализации в зависимости от функции
            x_min, x_max = bounds[0, 0], bounds[0, 1]
            y_min, y_max = bounds[1, 0], bounds[1, 1]

            # Для некоторых функций дополнительно сужаем область,
            # чтобы поверхность была компактной и лучше попадала в кадр
            if "Розенброка" in func_name:
                x_min, x_max = -2.0, 2.0
                y_min, y_max = -1.0, 3.0
                print(f"Using Rosenbrock-specific bounds: [{x_min}, {x_max}] x [{y_min}, {y_max}]")
            elif "Химмельблау" in func_name:
                x_min, x_max = -4.0, 4.0
                y_min, y_max = -4.0, 4.0
                print(f"Using Himmelblau-specific bounds: [{x_min}, {x_max}] x [{y_min}, {y_max}]")

            # Для функций с огромными диапазонами (Швефель, Гриванк) ограничиваем
            if "Швефеля" in func_name:
                # Для Швефеля показываем центральную часть
                x_min, x_max = -500, 500
                y_min, y_max = -500, 500
                print(f"Using Schwefel-specific bounds: [{x_min}, {x_max}] x [{y_min}, {y_max}]")
            elif "Гриванка" in func_name:
                # Для Гриванка тоже ограничиваем
                x_min, x_max = -50, 50
                y_min, y_max = -50, 50
                print(f"Using Griewank-specific bounds: [{x_min}, {x_max}] x [{y_min}, {y_max}]")

            # Создаем сетку для визуализации
            resolution = self.resolution.value()
            x = np.linspace(x_min, x_max, resolution)
            y = np.linspace(y_min, y_max, resolution)
            X, Y = np.meshgrid(x, y)
            print(f"Grid created: X shape {X.shape}, Y shape {Y.shape}")

            # Вычисляем значения функции
            Z = np.zeros_like(X)
            for i in range(X.shape[0]):
                for j in range(X.shape[1]):
                    Z[i, j] = self.current_function([X[i, j], Y[i, j]])

            print(f"Original Z: min={Z.min():.4f}, max={Z.max():.4f}")

            # НОРМАЛИЗУЕМ Z для визуализации
            # Все функции будут приведены к диапазону [0, 10] по оси Z,
            # чтобы поверхность и траектория всегда были над плоскостью Z=0
            z_min, z_max = Z.min(), Z.max()
            z_range = z_max - z_min

            if z_range > 1e-10:
                # Нормализация к диапазону [0, 10]
                Z_normalized = 10 * (Z - z_min) / z_range
            else:
                Z_normalized = np.zeros_like(Z)

            print(f"Normalized Z: min={Z_normalized.min():.4f}, max={Z_normalized.max():.4f}")

            # Визуализируем поверхность с нормализованными значениями
            if self.show_surface.isChecked():
                print("Plotting surface...")
                self.plot_surface(X, Y, Z_normalized, Z)  # Передаем и оригинальные Z для цвета

            # Визуализируем линии уровня (тоже с нормализацией)
            if self.show_contours.isChecked():
                print("Plotting contours...")
                self.plot_contours(X, Y, Z_normalized)

            # Начальная точка
            x0 = [self.start_x.value(), self.start_y.value()]
            print(f"Start point: {x0}")

            # Показываем начальную точку (используем ту же нормализацию, что и для поверхности)
            self.plot_start_point(x0, z_min, z_range)

            # Создаем метод оптимизации
            method_name = self.method_combo.currentText()
            print(f"Selected method: {method_name}")

            method_params = {
                'step_size': self.step_size.value(),
                'damping': self.damping.value()
            }
            self.current_method = MethodFactory.create(method_name, **method_params)

            # Запускаем метод оптимизации
            print("Starting optimization...")
            x_opt, trajectory, iterations = self.current_method.minimize(
                self.current_function,
                x0,
                max_iter=self.max_iter.value(),
                epsilon=self.epsilon.value()
            )
            print(f"Optimization finished: {iterations} iterations, result: {x_opt}")

            # Визуализируем траекторию
            if self.show_trajectory.isChecked() and len(trajectory) > 0:
                print(f"Plotting trajectory with {len(trajectory)} points")
                self.plot_trajectory(trajectory, Z_normalized, X, Y, Z)

            # Показываем точку минимума
            if self.show_minimum.isChecked() and self.current_function.optimal_point is not None:
                print(f"Plotting minimum point: {self.current_function.optimal_point}")
                # Находим нормализованное значение для точки минимума
                min_point = self.current_function.optimal_point
                min_val = self.current_function(min_point)
                min_val_norm = 10 * (min_val - z_min) / z_range if z_range > 1e-10 else 0
                self.plot_minimum_point(min_point, min_val_norm)

            # После построения всех объектов можно сбросить камеру в базовое положение
            # (оси + сетка заданы в VTKWidget, и камера там подобрана под них)
            if hasattr(self, 'vtk_widget') and self.vtk_widget:
                self.vtk_widget.reset_camera()

            # Принудительно обновляем рендер
            if hasattr(self, 'vtk_widget') and self.vtk_widget:
                self.vtk_widget.render_window.Render()
                print("Render forced")

            # Получаем информацию о сходимости
            conv_info = self.current_method.get_convergence_info()

            # Выводим результаты
            f_opt = self.current_function(x_opt)

            # ВЫЗЫВАЕМ show_results для отображения результатов
            self.show_results(
                func_name,
                method_name,
                x_opt,
                iterations,
                f_opt,
                self.current_function.optimal_point,
                self.current_function.optimal_value,
                conv_info
            )

            # Обновляем статус
            if hasattr(self, 'parent') and self.parent() and hasattr(self.parent(), 'status_label'):
                self.parent().status_label.setText(
                    f"Расчет выполнен: {func_name}, метод: {method_name}, итераций: {iterations}"
                )

            print("Calculation completed successfully")
            print("=" * 50)

            # Показываем сообщение об успехе
            self.add_result_label("✓ Расчет успешно выполнен!", "success")

        except Exception as e:
            print(f"ERROR in calculate: {str(e)}")
            import traceback
            traceback.print_exc()
            self.add_result_label(f"Ошибка при расчете: {str(e)}", "error")

    def get_function_key(self, display_name):
        """Преобразует отображаемое имя в ключ для фабрики"""
        mapping = {
            "Функция Розенброка (dim=2)": "rosenbrock",
            "Функция Растригина (dim=2)": "rastrigin",
            "Функция Аклея (dim=2)": "ackley",
            "Сферическая функция (dim=2)": "spherical",
            "Функция Гриванка (dim=2)": "griewank",
            "Функция Швефеля (dim=2)": "schwefel",
            "Функция Химмельблау": "himmelblau"
        }
        return mapping.get(display_name, "rosenbrock")

    def plot_surface(self, X, Y, Z_norm, Z_original=None):
        """Строит 3D поверхность функции с нормализованными значениями"""
        # Создаем точки поверхности
        points = vtk.vtkPoints()
        grid = vtk.vtkStructuredGrid()
        grid.SetDimensions(X.shape[0], X.shape[1], 1)

        # Добавляем точки (используем нормализованные Z)
        for i in range(X.shape[0]):
            for j in range(X.shape[1]):
                points.InsertNextPoint(X[i, j], Y[i, j], Z_norm[i, j])

        grid.SetPoints(points)

        # Создаем цветовую карту на основе оригинальных значений (если есть)
        colors = vtk.vtkUnsignedCharArray()
        colors.SetNumberOfComponents(3)
        colors.SetName("Colors")

        if Z_original is not None:
            # Используем оригинальные значения для цвета
            z_min, z_max = Z_original.min(), Z_original.max()
            if z_max - z_min > 1e-10:
                Z_norm_color = (Z_original - z_min) / (z_max - z_min)
            else:
                Z_norm_color = np.zeros_like(Z_original)
        else:
            # Используем нормализованные значения для цвета
            z_min, z_max = Z_norm.min(), Z_norm.max()
            if z_max - z_min > 1e-10:
                Z_norm_color = (Z_norm - z_min) / (z_max - z_min)
            else:
                Z_norm_color = np.zeros_like(Z_norm)

        # Цветовая схема
        for i in range(X.shape[0]):
            for j in range(X.shape[1]):
                val = Z_norm_color[i, j]
                if val < 0.33:
                    r = 0
                    g = int(255 * val * 3)
                    b = 255
                elif val < 0.66:
                    r = int(255 * (val - 0.33) * 3)
                    g = 255
                    b = int(255 * (1 - (val - 0.33) * 3))
                else:
                    r = 255
                    g = int(255 * (1 - (val - 0.66) * 3))
                    b = 0
                colors.InsertNextTuple3(r, g, b)

        grid.GetPointData().SetScalars(colors)

        # Создаем геометрию поверхности (используем SurfaceFilter вместо GeometryFilter)
        surface_filter = vtk.vtkDataSetSurfaceFilter()
        surface_filter.SetInputData(grid)

        # Создаем mapper
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(surface_filter.GetOutputPort())
        mapper.ScalarVisibilityOn()
        mapper.SetScalarModeToUsePointData()

        # Создаем actor
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

        # Добавляем на сцену
        self.vtk_widget.add_actor(actor)
        self.surface_actor = actor

        # Обновляем только плоскости отсечения, положение камеры не трогаем
        self.vtk_widget.renderer.ResetCameraClippingRange()
        self.vtk_widget.render_window.Render()

    def adjust_camera_for_function(self, X, Y, Z_norm):
        """Оставлено для совместимости, камера настраивается в самом VTKWidget"""
        # Ничего не делаем здесь, чтобы не ломать базовые настройки камеры
        pass

    def plot_contours(self, X, Y, Z, num_contours=20):
        """Строит линии уровня"""
        # Создаем равномерную сетку
        grid = vtk.vtkImageData()
        grid.SetDimensions(X.shape[0], X.shape[1], 1)
        grid.SetSpacing(
            (X[0, -1] - X[0, 0]) / (X.shape[0] - 1),
            (Y[-1, 0] - Y[0, 0]) / (Y.shape[0] - 1),
            1
        )
        grid.SetOrigin(X[0, 0], Y[0, 0], 0)

        # Добавляем значения
        z_flat = Z.flatten()
        z_array = numpy_support.numpy_to_vtk(z_flat, deep=True, array_type=vtk.VTK_DOUBLE)
        z_array.SetName("values")
        grid.GetPointData().AddArray(z_array)

        # Создаем контуры
        contour = vtk.vtkContourFilter()
        contour.SetInputData(grid)
        contour.SetInputArrayToProcess(0, 0, 0, 0, "values")

        # Генерируем значения контуров
        z_min, z_max = Z.min(), Z.max()
        contour.GenerateValues(num_contours, z_min, z_max)

        # Создаем mapper
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(contour.GetOutputPort())
        mapper.ScalarVisibilityOff()

        # Создаем actor
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0.3, 0.3, 0.3)
        actor.GetProperty().SetLineWidth(1)
        actor.GetProperty().SetOpacity(0.5)

        self.vtk_widget.add_actor(actor)
        self.contour_actor = actor

    def plot_trajectory(self, trajectory, Z_norm, X, Y, Z_original):
        """Строит траекторию поиска минимума с нормализованными значениями"""
        if len(trajectory) < 2:
            return

        # Фильтруем NaN значения
        valid_points = []
        for point in trajectory:
            if not np.any(np.isnan(point)):
                valid_points.append(point)

        if len(valid_points) < 2:
            print("No valid points in trajectory")
            return

        # Нормализуем значения Z для точек траектории в тот же диапазон [0, 10],
        # что и поверхность
        z_min, z_max = Z_original.min(), Z_original.max()
        z_range = z_max - z_min

        # Создаем точки траектории с нормализованными Z
        points = vtk.vtkPoints()
        for point in valid_points:
            # Находим ближайшую точку на сетке для интерполяции
            z_orig = self.current_function(point)
            if z_range > 1e-10:
                z_norm = 10 * (z_orig - z_min) / z_range
            else:
                z_norm = 0
            points.InsertNextPoint(point[0], point[1], z_norm)

        # Создаем линию
        line = vtk.vtkPolyLine()
        line.GetPointIds().SetNumberOfIds(len(valid_points))
        for i in range(len(valid_points)):
            line.GetPointIds().SetId(i, i)

        # Создаем ячейку линии
        lines = vtk.vtkCellArray()
        lines.InsertNextCell(line)

        # Создаем полидату для линии
        line_polydata = vtk.vtkPolyData()
        line_polydata.SetPoints(points)
        line_polydata.SetLines(lines)

        # Создаем mapper для линии
        line_mapper = vtk.vtkPolyDataMapper()
        line_mapper.SetInputData(line_polydata)

        # Создаем actor для линии
        line_actor = vtk.vtkActor()
        line_actor.SetMapper(line_mapper)
        line_actor.GetProperty().SetColor(1, 0, 0)  # Красный
        line_actor.GetProperty().SetLineWidth(3)

        self.vtk_widget.add_actor(line_actor)

        # Создаем точки для маркеров (сферы)
        for i, point in enumerate(valid_points):
            if np.any(np.isnan(point)):
                continue

            z_orig = self.current_function(point)
            if z_range > 1e-10:
                z_norm = 10 * (z_orig - z_min) / z_range
            else:
                z_norm = 0

            sphere = vtk.vtkSphereSource()
            sphere.SetCenter(point[0], point[1], z_norm)

            if i == 0:
                sphere.SetRadius(0.15)  # Начальная точка
                color = (0, 1, 0)  # Зеленый
            elif i == len(valid_points) - 1:
                sphere.SetRadius(0.2)  # Конечная точка
                color = (1, 0, 0)  # Красный
            else:
                sphere.SetRadius(0.08)  # Промежуточные точки
                color = (0, 0, 1)  # Синий

            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(sphere.GetOutputPort())

            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(*color)
            actor.GetProperty().SetSpecular(0.3)
            actor.GetProperty().SetSpecularPower(20)

            self.vtk_widget.add_actor(actor)

        self.trajectory_actor = line_actor

    def plot_start_point(self, point, z_min, z_range):
        """Отмечает начальную точку с нормализованным Z (в диапазоне [0, 10])"""
        z_orig = self.current_function(point)

        if z_range > 1e-10:
            z_norm = 10 * (z_orig - z_min) / z_range
        else:
            z_norm = 0

        sphere = vtk.vtkSphereSource()
        sphere.SetCenter(point[0], point[1], z_norm)
        sphere.SetRadius(0.2)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(sphere.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0, 1, 0)  # Зеленый
        actor.GetProperty().SetSpecular(0.5)
        actor.GetProperty().SetSpecularPower(30)

        self.vtk_widget.add_actor(actor)
        self.start_point_actor = actor

    def plot_minimum_point(self, point, z_norm):
        """Отмечает точку минимума с нормализованным Z"""
        sphere = vtk.vtkSphereSource()
        sphere.SetCenter(point[0], point[1], z_norm)
        sphere.SetRadius(0.25)
        sphere.SetThetaResolution(20)
        sphere.SetPhiResolution(20)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(sphere.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(1, 1, 0)  # Желтый
        actor.GetProperty().SetSpecular(0.6)
        actor.GetProperty().SetSpecularPower(40)

        self.vtk_widget.add_actor(actor)
        self.min_point_actor = actor



    def show_results(self, func_name, method_name, x_opt, iterations,
                     f_opt, exact_min, exact_val, conv_info):
        """Отображает результаты расчета"""

        # Очищаем предыдущие результаты
        self.clear_results()

        # Основная информация
        info_text = f"""
        <b>Функция:</b> {func_name}<br>
        <b>Метод:</b> {method_name}<br>
        <b>Начальная точка:</b> ({self.start_x.value():.3f}, {self.start_y.value():.3f})<br>
        <b>Найденная точка:</b> ({x_opt[0]:.6f}, {x_opt[1]:.6f})<br>
        <b>Значение функции:</b> {f_opt:.6f}<br>
        <b>Количество итераций:</b> {iterations}<br>
        <b>Норма градиента:</b> {conv_info['final_grad_norm']:.6f}
        """

        self.add_result_text(info_text)

        if exact_min is not None:
            # Информация о точном решении
            exact_text = f"""
        <b>Точное решение:</b><br>
        <b>Точка минимума:</b> ({exact_min[0]:.6f}, {exact_min[1]:.6f})<br>
        <b>Значение в минимуме:</b> {exact_val:.6f}<br>
        <b>Погрешность:</b> {np.linalg.norm(x_opt - exact_min):.6f}
        """
            self.add_result_text(exact_text)

        # Информация о сходимости
        conv_text = f"""
        <b>Сходимость:</b><br>
        <b>Начальное значение:</b> {conv_info['f_values'][0]:.6f}<br>
        <b>Конечное значение:</b> {conv_info['f_values'][-1]:.6f}<br>
        <b>Уменьшение:</b> {conv_info['f_values'][0] - conv_info['f_values'][-1]:.6f}
        """
        self.add_result_text(conv_text)

    def reset_view(self):
        """Сбрасывает вид камеры"""
        if hasattr(self, 'vtk_widget'):
            self.vtk_widget.reset_camera()
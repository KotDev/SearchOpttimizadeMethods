import numpy as np
from src.lab_base_widget import LabBaseWidget
from src.labs.lab2.qp_problem import QuadraticProblem, QPProblemFactory
from src.labs.lab2.artificial_variables_solver import ArtificialVariablesSolver
from PyQt6.QtWidgets import *
import vtk
from vtkmodules.util import numpy_support


class Lab2Widget(LabBaseWidget):
    """Лабораторная работа №2: Квадратичное программирование (метод искусственных переменных)"""

    def __init__(self):
        super().__init__(2, "Квадратичное программирование")
        self.current_problem: QuadraticProblem | None = None
        self.trajectory_actor = None
        self.surface_actor = None
        self.contour_actor = None
        self.min_point_actor = None
        self.feasible_actor = None
        self.setup_custom_ui()

    def setup_custom_ui(self):
        """Настройка интерфейса для лабы 2"""
        self.set_description(
            "Квадратичное программирование — метод искусственных переменных:\n"
            "• Минимизация f(x) = 0.5 x'Qx + c'x при линейных ограничениях Ax ≤ b, x ≥ 0\n"
            "• Двухэтапный симплекс: этап 1 — искусственные переменные\n"
            "• Этап 2 — перебор вершин допустимой области\n\n"
            "Визуализация поверхности, линий уровня, допустимой области и решения."
        )

        self.problems = QPProblemFactory.create_all()
        problem_names = [p.name for p in self.problems]

        self.problem_combo = self.add_input_field(
            "Задача КП:",
            QComboBox,
            items=problem_names
        )
        self.problem_combo.currentTextChanged.connect(self.on_problem_changed)

        self.resolution = self.add_input_field(
            "Разрешение сетки:",
            QSpinBox,
            value=50,
            range=(20, 200)
        )

        options_container = QWidget()
        options_layout = QHBoxLayout(options_container)

        self.show_surface = QCheckBox("Показать поверхность")
        self.show_surface.setChecked(True)
        options_layout.addWidget(self.show_surface)

        self.show_contours = QCheckBox("Показать линии уровня")
        self.show_contours.setChecked(True)
        options_layout.addWidget(self.show_contours)

        self.show_trajectory = QCheckBox("Показать вершины")
        self.show_trajectory.setChecked(True)
        options_layout.addWidget(self.show_trajectory)

        self.show_minimum = QCheckBox("Показать минимум")
        self.show_minimum.setChecked(True)
        options_layout.addWidget(self.show_minimum)

        self.show_feasible = QCheckBox("Показать допустимую область")
        self.show_feasible.setChecked(True)
        options_layout.addWidget(self.show_feasible)

        self.inputs_layout.addWidget(options_container)

        self.btn_reset_view = QPushButton("Сбросить вид")
        self.btn_reset_view.clicked.connect(self.reset_view)
        self.inputs_layout.addWidget(self.btn_reset_view)

        self.btn_calculate.clicked.connect(self.calculate)
        self.on_problem_changed(self.problem_combo.currentText())

    def on_problem_changed(self, problem_name: str):
        """Обработчик изменения задачи"""
        for p in self.problems:
            if p.name == problem_name:
                self.current_problem = p
                break

    def calculate(self):
        """Основной метод расчета"""
        try:
            self.clear_results()
            if hasattr(self, 'vtk_widget') and self.vtk_widget:
                self.vtk_widget.clear_scene()
            else:
                self.add_result_label("Ошибка: VTK виджет не инициализирован", "error")
                return

            problem_name = self.problem_combo.currentText()
            for p in self.problems:
                if p.name == problem_name:
                    self.current_problem = p
                    break

            if self.current_problem is None:
                self.add_result_label("Ошибка: задача не выбрана", "error")
                return

            problem = self.current_problem
            bounds = problem.bounds

            x_min, x_max = bounds[0, 0], bounds[0, 1]
            y_min, y_max = bounds[1, 0], bounds[1, 1]

            resolution = self.resolution.value()
            x = np.linspace(x_min, x_max, resolution)
            y = np.linspace(y_min, y_max, resolution)
            X, Y = np.meshgrid(x, y)
            Z = np.zeros_like(X)
            for i in range(X.shape[0]):
                for j in range(X.shape[1]):
                    pt = np.array([X[i, j], Y[i, j]])
                    Z[i, j] = problem.f(pt) if problem.is_feasible(pt) else np.nan

            z_valid = Z[~np.isnan(Z)]
            z_min = z_valid.min() if len(z_valid) > 0 else 0
            z_max = z_valid.max() if len(z_valid) > 0 else 1
            z_range = z_max - z_min if z_max > z_min else 1
            Z_plot = np.where(np.isnan(Z), z_max + 1, Z)
            Z_normalized = 10 * (Z_plot - z_min) / z_range
            Z_normalized = np.where(np.isnan(Z), 0, Z_normalized)

            if self.show_surface.isChecked():
                self.plot_surface(X, Y, Z_normalized, Z)

            if self.show_contours.isChecked():
                self.plot_contours(X, Y, Z_normalized)

            if self.show_feasible.isChecked():
                self.plot_feasible_region(problem, z_min, z_range)

            solver = ArtificialVariablesSolver()
            x_opt, trajectory, iterations = solver.solve(problem)

            if self.show_trajectory.isChecked() and len(trajectory) > 0:
                self.plot_trajectory(trajectory, problem, z_min, z_range)

            if self.show_minimum.isChecked():
                f_opt = problem.f(x_opt)
                min_val_norm = 10 * (f_opt - z_min) / z_range if z_range > 1e-10 else 0
                self.plot_minimum_point(x_opt, min_val_norm)

            if hasattr(self, 'vtk_widget') and self.vtk_widget:
                self.vtk_widget.reset_camera()
                self.vtk_widget.render_window.Render()

            conv_info = solver.get_convergence_info()
            f_opt = problem.f(x_opt)

            self.show_results(
                problem_name,
                "Метод искусственных переменных",
                x_opt,
                iterations,
                f_opt,
                problem.optimal_point,
                problem.optimal_value,
                conv_info
            )

            if hasattr(self, 'parent') and self.parent() and hasattr(self.parent(), 'status_label'):
                self.parent().status_label.setText(
                    f"Расчет выполнен: {problem_name}, итераций: {iterations}"
                )

            self.add_result_label("✓ Расчет успешно выполнен!", "success")

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.add_result_label(f"Ошибка при расчете: {str(e)}", "error")

    def plot_surface(self, X, Y, Z_norm, Z_original=None):
        """Строит 3D поверхность"""
        points = vtk.vtkPoints()
        grid = vtk.vtkStructuredGrid()
        grid.SetDimensions(X.shape[0], X.shape[1], 1)

        for i in range(X.shape[0]):
            for j in range(X.shape[1]):
                points.InsertNextPoint(X[i, j], Y[i, j], Z_norm[i, j])

        grid.SetPoints(points)

        colors = vtk.vtkUnsignedCharArray()
        colors.SetNumberOfComponents(3)
        colors.SetName("Colors")

        Z_use = np.nan_to_num(Z_original, nan=0) if Z_original is not None else Z_norm
        z_min, z_max = Z_use.min(), Z_use.max()
        Z_norm_color = (Z_use - z_min) / (z_max - z_min + 1e-10)

        for i in range(X.shape[0]):
            for j in range(X.shape[1]):
                val = Z_norm_color[i, j]
                if val < 0.33:
                    r, g, b = 0, int(255 * val * 3), 255
                elif val < 0.66:
                    r, g, b = int(255 * (val - 0.33) * 3), 255, int(255 * (1 - (val - 0.33) * 3))
                else:
                    r, g, b = 255, int(255 * (1 - (val - 0.66) * 3)), 0
                colors.InsertNextTuple3(r, g, b)

        grid.GetPointData().SetScalars(colors)

        surface_filter = vtk.vtkDataSetSurfaceFilter()
        surface_filter.SetInputData(grid)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(surface_filter.GetOutputPort())
        mapper.ScalarVisibilityOn()
        mapper.SetScalarModeToUsePointData()

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        self.vtk_widget.add_actor(actor)
        self.surface_actor = actor
        self.vtk_widget.renderer.ResetCameraClippingRange()
        self.vtk_widget.render_window.Render()

    def plot_contours(self, X, Y, Z, num_contours=20):
        """Строит линии уровня"""
        Z_clean = np.nan_to_num(Z, nan=Z.max() + 1)
        grid = vtk.vtkImageData()
        grid.SetDimensions(X.shape[0], X.shape[1], 1)
        grid.SetSpacing(
            (X[0, -1] - X[0, 0]) / max(X.shape[0] - 1, 1),
            (Y[-1, 0] - Y[0, 0]) / max(Y.shape[0] - 1, 1),
            1
        )
        grid.SetOrigin(X[0, 0], Y[0, 0], 0)

        z_flat = Z_clean.flatten()
        z_array = numpy_support.numpy_to_vtk(z_flat, deep=True, array_type=vtk.VTK_DOUBLE)
        z_array.SetName("values")
        grid.GetPointData().AddArray(z_array)

        contour = vtk.vtkContourFilter()
        contour.SetInputData(grid)
        contour.SetInputArrayToProcess(0, 0, 0, 0, "values")
        z_min, z_max = Z_clean.min(), Z_clean.max()
        contour.GenerateValues(num_contours, z_min, z_max)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(contour.GetOutputPort())
        mapper.ScalarVisibilityOff()

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0.3, 0.3, 0.3)
        actor.GetProperty().SetLineWidth(1)
        actor.GetProperty().SetOpacity(0.5)

        self.vtk_widget.add_actor(actor)
        self.contour_actor = actor

    def plot_feasible_region(self, problem: QuadraticProblem, z_min: float, z_range: float):
        """Отображает допустимую область (полигон на плоскости z=0)"""
        vertices = self._get_feasible_vertices(problem)
        if len(vertices) < 3:
            return

        # Сортируем вершины по углу для выпуклого полигона
        center = np.mean(vertices, axis=0)
        angles = np.arctan2(
            np.array([v[1] - center[1] for v in vertices]),
            np.array([v[0] - center[0] for v in vertices])
        )
        order = np.argsort(angles)
        vertices = [vertices[i] for i in order]

        points = vtk.vtkPoints()
        for v in vertices:
            points.InsertNextPoint(v[0], v[1], 0)

        poly = vtk.vtkPolygon()
        poly.GetPointIds().SetNumberOfIds(len(vertices))
        for i in range(len(vertices)):
            poly.GetPointIds().SetId(i, i)

        cells = vtk.vtkCellArray()
        cells.InsertNextCell(poly)

        polydata = vtk.vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetPolys(cells)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(polydata)

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0.8, 0.9, 1.0)
        actor.GetProperty().SetOpacity(0.3)

        self.vtk_widget.add_actor(actor)
        self.feasible_actor = actor

    def _get_feasible_vertices(self, problem: QuadraticProblem):
        """Вершины допустимой области"""
        A, b = problem.A, problem.b
        n = 2
        A_full = np.vstack([A, -np.eye(n)])
        b_full = np.hstack([b, np.zeros(n)])
        vertices = []
        for i in range(len(A_full)):
            for j in range(i + 1, len(A_full)):
                try:
                    sol = np.linalg.solve(np.vstack([A_full[i], A_full[j]]), np.array([b_full[i], b_full[j]]))
                    if np.all(sol >= -1e-9) and np.all(A_full @ sol <= b_full + 1e-9):
                        if not any(np.allclose(sol, u) for u in vertices):
                            vertices.append(sol)
                except np.linalg.LinAlgError:
                    pass
        return vertices

    def plot_trajectory(self, trajectory, problem: QuadraticProblem, z_min: float, z_range: float):
        """Строит вершины (траекторию)"""
        valid_points = [np.asarray(p).ravel() for p in trajectory if p is not None and len(p) >= 2]
        valid_points = [p for p in valid_points if not np.any(np.isnan(p)) and problem.is_feasible(p)]
        if len(valid_points) < 1:
            return

        for i, point in enumerate(valid_points):
            z_orig = problem.f(point)
            z_norm = 10 * (z_orig - z_min) / z_range if z_range > 1e-10 else 0

            sphere = vtk.vtkSphereSource()
            sphere.SetCenter(point[0], point[1], z_norm)
            sphere.SetRadius(0.15)
            color = (0, 0, 1)  # синий — вершины

            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(sphere.GetOutputPort())
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(*color)
            actor.GetProperty().SetSpecular(0.3)
            actor.GetProperty().SetSpecularPower(20)
            self.vtk_widget.add_actor(actor)

        self.trajectory_actor = actor

    def plot_minimum_point(self, point, z_norm):
        """Отмечает точку минимума"""
        sphere = vtk.vtkSphereSource()
        sphere.SetCenter(point[0], point[1], z_norm)
        sphere.SetRadius(0.25)
        sphere.SetThetaResolution(20)
        sphere.SetPhiResolution(20)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(sphere.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(1, 1, 0)
        actor.GetProperty().SetSpecular(0.6)
        actor.GetProperty().SetSpecularPower(40)
        self.vtk_widget.add_actor(actor)
        self.min_point_actor = actor

    def show_results(self, problem_name, method_name, x_opt, iterations,
                     f_opt, exact_min, exact_val, conv_info):
        """Отображает результаты"""
        self.clear_results()

        info_text = f"""
        <b>Задача:</b> {problem_name}<br>
        <b>Метод:</b> {method_name}<br>
        <b>Найденная точка:</b> ({x_opt[0]:.6f}, {x_opt[1]:.6f})<br>
        <b>Значение функции:</b> {f_opt:.6f}<br>
        <b>Количество итераций:</b> {iterations}
        """

        self.add_result_text(info_text)

        if exact_min is not None:
            exact_val_disp = exact_val if exact_val is not None else self.current_problem.f(exact_min)
            exact_text = f"""
        <b>Точное решение:</b><br>
        <b>Точка минимума:</b> ({exact_min[0]:.6f}, {exact_min[1]:.6f})<br>
        <b>Значение в минимуме:</b> {exact_val_disp:.6f}<br>
        <b>Погрешность:</b> {np.linalg.norm(x_opt - exact_min):.6f}
        """
            self.add_result_text(exact_text)

        f_vals = conv_info.get('f_values', [])
        if len(f_vals) >= 2:
            conv_text = f"""
        <b>Сходимость:</b><br>
        <b>Начальное значение:</b> {f_vals[0]:.6f}<br>
        <b>Конечное значение:</b> {f_vals[-1]:.6f}<br>
        <b>Уменьшение:</b> {f_vals[0] - f_vals[-1]:.6f}
        """
            self.add_result_text(conv_text)

            # ИСПРАВЛЕНИЕ: обрабатываем массив, а не словарь
        if hasattr(self.current_problem, 'check_kkt_conditions'):
            try:
                lambda_vals = self.current_problem.check_kkt_conditions(x_opt)
                print(f"Получены множители Лагранжа: {lambda_vals}")
                
                if len(lambda_vals) > 0:
                    # Формируем строку с множителями
                    lambda_str = ", ".join([f"λ{i} = {l:.4f}" for i, l in enumerate(lambda_vals)])
                    
                    # Проверяем условие λ ≥ 0 (для задачи минимизации)
                    kkt_satisfied = np.all(lambda_vals >= -1e-6)
                    kkt_status = "✓ ВЫПОЛНЕНЫ" if kkt_satisfied else "✗ НАРУШЕНЫ"
                    
                    kkt_text = f"""
                    <b>Проверка условий Куна-Таккера:</b><br>
                    <b>Множители Лагранжа (активные ограничения):</b> {lambda_str}<br>
                    <b>Статус:</b> {kkt_status}<br>
                    <b>Пояснение:</b> {'Все λ ≥ 0 → условия ККТ выполнены' if kkt_satisfied else 'λ < 0 → условия ККТ нарушены'}
                    """
                    
                    # Добавляем информацию об активных ограничениях
                    residuals = self.current_problem.A @ x_opt - self.current_problem.b
                    active_indices = np.where(np.abs(residuals) < 1e-6)[0]
                    if len(active_indices) > 0:
                        active_str = ", ".join([f"g{i}(x)=0" for i in active_indices])
                        kkt_text += f"<br><b>Активные ограничения:</b> {active_str}"
                    
                    self.add_result_text(kkt_text)
                else:
                    # Если нет активных ограничений
                    grad_f = self.current_problem.Q @ x_opt + self.current_problem.c
                    stationarity = np.linalg.norm(grad_f) < 1e-6
                    
                    kkt_text = f"""
                    <b>Проверка условий Куна-Таккера:</b><br>
                    <b>Активные ограничения:</b> отсутствуют<br>
                    <b>Стационарность (||∇f(x)||):</b> {np.linalg.norm(grad_f):.6f}<br>
                    <b>Статус:</b> {'✓ ВЫПОЛНЕНЫ' if stationarity else '✗ НЕ ВЫПОЛНЕНЫ (градиент не равен 0)'}
                    """
                    self.add_result_text(kkt_text)
                    
            except Exception as e:
                print(f"Ошибка при проверке ККТ: {e}")
                import traceback
                traceback.print_exc()

    def reset_view(self):
        """Сбрасывает вид камеры"""
        if hasattr(self, 'vtk_widget'):
            self.vtk_widget.reset_camera()

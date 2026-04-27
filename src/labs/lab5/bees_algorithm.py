import numpy as np
from typing import Callable, List, Tuple, Optional


class BeesAlgorithm:
    """
    Алгоритм пчелиного роя (Bees Algorithm) для глобальной оптимизации.
    
    Реализует классический B-алгоритм с элитными и перспективными участками.
    """
    
    def __init__(
        self,
        func: Callable,
        bounds: np.ndarray,
        n_scouts: int = 16,           # Число пчел-разведчиков
        n_elite_sites: int = 2,        # Число элитных участков
        n_best_sites: int = 3,         # Число перспективных участков
        n_elite_bees: int = 7,         # Число пчел на элитном участке
        n_best_bees: int = 4,          # Число пчел на перспективном участке
        patch_radius: float = 0.2,     # Начальный радиус участка
        radius_reduction: float = 0.8, # Коэффициент уменьшения радиуса
        max_iterations: int = 500,
        stagnation_limit: int = 20,    # Лимит стагнации
        verbose: bool = False
    ):
        """
        Инициализация алгоритма пчелиного роя.
        
        Параметры:
        -----------
        func : callable
            Целевая функция (для минимизации)
        bounds : array_like
            Границы поиска [[min1, max1], [min2, max2], ...]
        n_scouts : int
            Количество пчел-разведчиков
        n_elite_sites : int
            Количество элитных участков
        n_best_sites : int
            Количество перспективных участков
        n_elite_bees : int
            Количество рабочих пчел на элитном участке
        n_best_bees : int
            Количество рабочих пчел на перспективном участке
        patch_radius : float
            Начальный радиус участка
        radius_reduction : float
            Коэффициент уменьшения радиуса (для улучшенного алгоритма)
        max_iterations : int
            Максимальное количество итераций
        stagnation_limit : int
            Количество итераций без улучшения для остановки
        verbose : bool
            Выводить ли прогресс
        """
        self.func = func
        self.bounds = np.array(bounds)
        self.dimension = len(bounds)
        
        # Параметры алгоритма
        self.n_scouts = n_scouts
        self.n_elite_sites = n_elite_sites
        self.n_best_sites = n_best_sites
        self.n_elite_bees = n_elite_bees
        self.n_best_bees = n_best_bees
        self.patch_radius = patch_radius
        self.initial_radius = patch_radius
        self.radius_reduction = radius_reduction
        self.max_iterations = max_iterations
        self.stagnation_limit = stagnation_limit
        self.verbose = verbose
        
        # История для визуализации
        self.history = []           # Позиции всех пчел по итерациям
        self.best_history = []      # История лучших значений
        self.best_positions_history = []  # История лучших позиций
        
        # Лучшее найденное решение
        self.best_position = None
        self.best_value = float('inf')
        
    def _random_position(self) -> np.ndarray:
        """Генерирует случайную позицию в границах"""
        return np.random.uniform(
            self.bounds[:, 0], 
            self.bounds[:, 1], 
            size=self.dimension
        )
    
    def _random_in_patch(self, center: np.ndarray, radius: float) -> np.ndarray:
        """Генерирует случайную позицию в окрестности центра"""
        position = center + np.random.uniform(-radius, radius, size=self.dimension)
        return np.clip(position, self.bounds[:, 0], self.bounds[:, 1])
    
    def _evaluate(self, position: np.ndarray) -> float:
        """Вычисляет значение функции в точке"""
        return self.func(position)
    
    def solve(self, real_time_callback: Optional[Callable] = None) -> Tuple[np.ndarray, float, List]:
        """
        Запуск алгоритма оптимизации.
        
        Параметры:
        -----------
        real_time_callback : callable, optional
            Функция обратного вызова для визуализации в реальном времени.
            Принимает (iteration, swarm_positions, best_position, best_value)
            
        Возвращает:
        ------------
        best_position : np.ndarray
            Лучшая найденная позиция
        best_value : float
            Значение функции в лучшей точке
        history : list
            История всех позиций пчел
        """
        self.history = []
        self.best_history = []
        self.best_positions_history = []
        
        # Текущий радиус участков
        current_radius = self.patch_radius
        
        # Счетчик стагнации
        stagnation_counter = 0
        last_best_value = float('inf')
        
        # Инициализация: случайные позиции пчел-разведчиков
        scout_positions = [self._random_position() for _ in range(self.n_scouts)]
        scout_values = [self._evaluate(pos) for pos in scout_positions]
        
        # Обновление лучшего решения
        for pos, val in zip(scout_positions, scout_values):
            if val < self.best_value:
                self.best_value = val
                self.best_position = pos.copy()
        
        # Основной цикл алгоритма
        for iteration in range(self.max_iterations):
            # Сохраняем историю для визуализации
            all_positions = scout_positions.copy()
            self.history.append(np.array(all_positions))
            self.best_history.append(self.best_value)
            self.best_positions_history.append(self.best_position.copy() if self.best_position is not None else None)
            
            # Вызов callback для реального времени
            if real_time_callback is not None:
                real_time_callback(iteration, all_positions, self.best_position, self.best_value)
            
            if self.verbose and iteration % 10 == 0:
                print(f"Итерация {iteration}: лучшее значение = {self.best_value:.10f}, радиус = {current_radius:.4f}")
            
            # Шаг 1: Сортировка участков по качеству
            sites = list(zip(scout_positions, scout_values))
            sites.sort(key=lambda x: x[1])  # Сортировка по возрастанию (лучшие первые)
            
            # Шаг 2: Выделение элитных и перспективных участков
            elite_sites = sites[:self.n_elite_sites]
            best_sites = sites[self.n_elite_sites:self.n_elite_sites + self.n_best_sites]
            
            # Шаг 3: Отправка рабочих пчел на участки
            new_scout_positions = []
            new_scout_values = []
            
            # Обработка элитных участков
            for site_pos, site_val in elite_sites:
                # Отправляем n_elite_bees пчел в окрестность
                for _ in range(self.n_elite_bees):
                    bee_pos = self._random_in_patch(site_pos, current_radius)
                    bee_val = self._evaluate(bee_pos)
                    new_scout_positions.append(bee_pos)
                    new_scout_values.append(bee_val)
                    
                    # Обновляем лучшее решение
                    if bee_val < self.best_value:
                        self.best_value = bee_val
                        self.best_position = bee_pos.copy()
                
                # Сохраняем сам участок
                new_scout_positions.append(site_pos)
                new_scout_values.append(site_val)
            
            # Обработка перспективных участков
            for site_pos, site_val in best_sites:
                for _ in range(self.n_best_bees):
                    bee_pos = self._random_in_patch(site_pos, current_radius)
                    bee_val = self._evaluate(bee_pos)
                    new_scout_positions.append(bee_pos)
                    new_scout_values.append(bee_val)
                    
                    if bee_val < self.best_value:
                        self.best_value = bee_val
                        self.best_position = bee_pos.copy()
                
                new_scout_positions.append(site_pos)
                new_scout_values.append(site_val)
            
            # Шаг 4: Добавление новых случайных разведчиков (глобальный поиск)
            remaining_scouts = self.n_scouts - len(new_scout_positions)
            for _ in range(remaining_scouts):
                random_pos = self._random_position()
                random_val = self._evaluate(random_pos)
                new_scout_positions.append(random_pos)
                new_scout_values.append(random_val)
                
                if random_val < self.best_value:
                    self.best_value = random_val
                    self.best_position = random_pos.copy()
            
            # Обновляем позиции разведчиков для следующей итерации
            scout_positions = new_scout_positions
            scout_values = new_scout_values
            
            # Шаг 5: Уменьшение радиуса (для улучшенного алгоритма)
            # Уменьшаем радиус только если нашли улучшение
            if self.best_value < last_best_value:
                current_radius *= self.radius_reduction
                stagnation_counter = 0
                last_best_value = self.best_value
            else:
                stagnation_counter += 1
            
            # Шаг 6: Проверка условия остановки (стагнация)
            if stagnation_counter >= self.stagnation_limit:
                if self.verbose:
                    print(f"Остановка на итерации {iteration}: стагнация в течение {stagnation_limit} итераций")
                break
        
        # Сохраняем финальное поколение
        self.history.append(np.array(scout_positions))
        self.best_history.append(self.best_value)
        self.best_positions_history.append(self.best_position.copy() if self.best_position is not None else None)
        
        if self.verbose:
            print(f"\nОптимизация завершена!")
            print(f"Лучшее значение: {self.best_value:.12f}")
            print(f"Лучшая позиция: {self.best_position}")
        
        return self.best_position, self.best_value, self.history
    
    def get_best_solution(self) -> Tuple[np.ndarray, float]:
        """Возвращает лучшее найденное решение"""
        return self.best_position, self.best_value
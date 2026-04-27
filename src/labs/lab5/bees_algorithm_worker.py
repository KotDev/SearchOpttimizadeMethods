import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal
from .bees_algorithm import BeesAlgorithm


class BeesAlgorithmWorker(QThread):
    """Рабочий поток для выполнения алгоритма пчелиного роя"""
    
    # Сигналы для обновления GUI
    iteration_update = pyqtSignal(int, np.ndarray, np.ndarray, float)  # (iteration, positions, best_pos, best_val)
    finished_signal = pyqtSignal(np.ndarray, float, list)  # (best_position, best_value, history)
    progress_update = pyqtSignal(int, float)  # (iteration, best_value)
    
    def __init__(self, bees_algorithm, max_iterations, delay_ms=50):
        super().__init__()
        self.bees_algorithm = bees_algorithm
        self.max_iterations = max_iterations
        self.delay_ms = delay_ms
        self.is_paused = False
        self.is_stopped = False
        self._mutex = None
        
    def run(self):
        """Запуск алгоритма с возможностью паузы и остановки"""
        self.is_paused = False
        self.is_stopped = False
        
        # Инициализация
        self.bees_algorithm.history = []
        self.bees_algorithm.best_history = []
        self.bees_algorithm.best_positions_history = []
        
        # Создаем начальный рой
        scout_positions = [self.bees_algorithm._random_position() 
                          for _ in range(self.bees_algorithm.n_scouts)]
        scout_values = [self.bees_algorithm._evaluate(pos) for pos in scout_positions]
        
        # Обновление лучшего решения
        best_value = float('inf')
        best_position = None
        for pos, val in zip(scout_positions, scout_values):
            if val < best_value:
                best_value = val
                best_position = pos.copy()
        
        self.bees_algorithm.best_global_value = best_value
        self.bees_algorithm.best_global_position = best_position
        
        # Сохраняем начальное поколение
        self.bees_algorithm.history.append(np.array(scout_positions))
        self.bees_algorithm.best_history.append(best_value)
        self.bees_algorithm.best_positions_history.append(best_position.copy() if best_position is not None else None)
        
        # Отправляем начальное состояние
        self.iteration_update.emit(0, np.array(scout_positions), 
                                   best_position if best_position is not None else np.array([0, 0]), 
                                   best_value)
        
        # Текущий радиус
        current_radius = self.bees_algorithm.patch_radius
        
        # Счетчик стагнации
        stagnation_counter = 0
        last_best_value = best_value
        
        # Основной цикл
        for iteration in range(1, self.max_iterations + 1):
            # Проверка на остановку
            if self.is_stopped:
                break
                
            # Проверка на паузу
            while self.is_paused and not self.is_stopped:
                self.msleep(100)
            
            # Сортировка участков
            sites = list(zip(scout_positions, scout_values))
            sites.sort(key=lambda x: x[1])
            
            # Выделение элитных и перспективных участков
            elite_sites = sites[:self.bees_algorithm.n_elite_sites]
            best_sites = sites[self.bees_algorithm.n_elite_sites:
                              self.bees_algorithm.n_elite_sites + self.bees_algorithm.n_best_sites]
            
            # Отправка рабочих пчел
            new_scout_positions = []
            new_scout_values = []
            
            # Элитные участки
            for site_pos, site_val in elite_sites:
                for _ in range(self.bees_algorithm.n_elite_bees):
                    bee_pos = self.bees_algorithm._random_in_patch(site_pos, current_radius)
                    bee_val = self.bees_algorithm._evaluate(bee_pos)
                    new_scout_positions.append(bee_pos)
                    new_scout_values.append(bee_val)
                    
                    if bee_val < best_value:
                        best_value = bee_val
                        best_position = bee_pos.copy()
                
                new_scout_positions.append(site_pos)
                new_scout_values.append(site_val)
            
            # Перспективные участки
            for site_pos, site_val in best_sites:
                for _ in range(self.bees_algorithm.n_best_bees):
                    bee_pos = self.bees_algorithm._random_in_patch(site_pos, current_radius)
                    bee_val = self.bees_algorithm._evaluate(bee_pos)
                    new_scout_positions.append(bee_pos)
                    new_scout_values.append(bee_val)
                    
                    if bee_val < best_value:
                        best_value = bee_val
                        best_position = bee_pos.copy()
                
                new_scout_positions.append(site_pos)
                new_scout_values.append(site_val)
            
            # Добавление новых разведчиков
            remaining_scouts = self.bees_algorithm.n_scouts - len(new_scout_positions)
            for _ in range(remaining_scouts):
                random_pos = self.bees_algorithm._random_position()
                random_val = self.bees_algorithm._evaluate(random_pos)
                new_scout_positions.append(random_pos)
                new_scout_values.append(random_val)
                
                if random_val < best_value:
                    best_value = random_val
                    best_position = random_pos.copy()
            
            # Обновление
            scout_positions = new_scout_positions
            scout_values = new_scout_values
            
            # Обновление лучшего глобального решения
            self.bees_algorithm.best_global_value = best_value
            self.bees_algorithm.best_global_position = best_position.copy() if best_position is not None else None
            
            # Сохранение истории
            self.bees_algorithm.history.append(np.array(scout_positions))
            self.bees_algorithm.best_history.append(best_value)
            self.bees_algorithm.best_positions_history.append(best_position.copy() if best_position is not None else None)
            
            # Отправка сигнала обновления
            self.iteration_update.emit(iteration, np.array(scout_positions),
                                       best_position if best_position is not None else np.array([0, 0]),
                                       best_value)
            self.progress_update.emit(iteration, best_value)
            
            # Обновление радиуса
            if best_value < last_best_value:
                current_radius *= self.bees_algorithm.radius_reduction
                stagnation_counter = 0
                last_best_value = best_value
            else:
                stagnation_counter += 1
            
            # Проверка стагнации
            if stagnation_counter >= self.bees_algorithm.stagnation_limit:
                break
            
            # Задержка для визуализации
            self.msleep(self.delay_ms)
        
        # Отправка сигнала о завершении
        self.finished_signal.emit(best_position, best_value, self.bees_algorithm.history)
    
    def pause(self):
        """Пауза"""
        self.is_paused = True
    
    def resume(self):
        """Продолжить"""
        self.is_paused = False
    
    def stop(self):
        """Остановка"""
        self.is_stopped = True
        self.is_paused = False
import numpy as np


class Particle:
    """Класс, описывающий одну частицу"""
    def __init__(self, bounds, func):
        self.bounds = bounds
        self.func = func
        self.dimension = len(bounds)
        
        # Случайная начальная позиция
        self.position = np.random.uniform(
            bounds[:, 0], bounds[:, 1], size=self.dimension
        )
        
        # Случайная начальная скорость (в пределах 10% от диапазона)
        scale = (bounds[:, 1] - bounds[:, 0]) * 0.1
        self.velocity = np.random.uniform(-scale, scale, size=self.dimension)
        
        # Лучшая позиция частицы
        self.best_position = self.position.copy()
        self.best_value = self.func(self.position)
        
    def update_best(self):
        """Обновляет лучшую позицию частицы"""
        current_value = self.func(self.position)
        if current_value < self.best_value:
            self.best_value = current_value
            self.best_position = self.position.copy()
            return True
        return False


class ParticleSwarmOptimization:
    """
    Алгоритм роя частиц (Particle Swarm Optimization)
    
    Реализует канонический вариант алгоритма с коэффициентом сжатия χ (chi)
    """
    
    def __init__(self, func, bounds, pop_size=50, 
                 inertia_weight=0.9, cognitive_weight=2.05, social_weight=2.05):
        """
        Инициализация алгоритма роя частиц
        
        Параметры:
        -----------
        func : callable
            Целевая функция для минимизации
        bounds : array_like
            Границы поиска для каждой размерности [[min1, max1], [min2, max2], ...]
        pop_size : int
            Размер роя (количество частиц)
        inertia_weight : float
            Коэффициент инерции (ω) - влияет на сохранение текущей скорости
            Обычно уменьшается от 0.9 до 0.4 в процессе итераций
        cognitive_weight : float
            Когнитивный коэффициент (c1) - влияние личного лучшего решения
        social_weight : float
            Социальный коэффициент (c2) - влияние глобального лучшего решения
        """
        self.func = func
        self.bounds = np.array(bounds)
        self.pop_size = pop_size
        self.inertia_weight = inertia_weight
        self.cognitive_weight = cognitive_weight
        self.social_weight = social_weight
        
        # Вычисляем коэффициент сжатия для канонического варианта
        # χ = 2 / |2 - φ - sqrt(φ^2 - 4φ)|, где φ = c1 + c2, φ > 4
        phi = cognitive_weight + social_weight
        if phi > 4:
            self.chi = 2 / abs(2 - phi - np.sqrt(phi**2 - 4*phi))
        else:
            self.chi = 1.0  # Если φ <= 4, сжатие не применяется
            
        self.history = []  # Список поколений (каждое поколение - массив точек)
        self.best_global_position = None
        self.best_global_value = float('inf')
        self.best_history = []  # История лучших значений
        
    def _update_velocity(self, particle, iteration, max_iterations):
        """
        Обновление скорости частицы по формуле:
        v(t+1) = ω * v(t) + c1 * r1 * (p_best - x) + c2 * r2 * (g_best - x)
        
        С использованием динамического коэффициента инерции (линейное уменьшение)
        """
        # Динамический коэффициент инерции (уменьшается от начального до 0.4)
        inertia = self.inertia_weight * (1 - iteration / max_iterations) + 0.4 * (iteration / max_iterations)
        
        # Случайные коэффициенты
        r1 = np.random.random(particle.dimension)
        r2 = np.random.random(particle.dimension)
        
        # Когнитивная и социальная компоненты
        cognitive = self.cognitive_weight * r1 * (particle.best_position - particle.position)
        social = self.social_weight * r2 * (self.best_global_position - particle.position)
        
        # Новая скорость с коэффициентом сжатия
        new_velocity = self.chi * (inertia * particle.velocity + cognitive + social)
        
        return new_velocity
    
    def _update_position(self, particle, new_velocity):
        """Обновление позиции частицы и применение границ"""
        particle.position = particle.position + new_velocity
        
        # Обрезка по границам
        particle.position = np.clip(
            particle.position, 
            self.bounds[:, 0], 
            self.bounds[:, 1]
        )
        
        # Ограничение скорости (опционально, для стабильности)
        max_velocity = (self.bounds[:, 1] - self.bounds[:, 0]) * 0.2
        new_velocity = np.clip(new_velocity, -max_velocity, max_velocity)
        particle.velocity = new_velocity
        
    def solve(self, generations=50, verbose=False):
        """
        Запуск алгоритма оптимизации
        
        Параметры:
        -----------
        generations : int
            Количество итераций (поколений)
        verbose : bool
            Выводить ли прогресс
            
        Возвращает:
        ------------
        history : list
            История позиций всех частиц по поколениям
        """
        self.history = []
        self.best_history = []
        
        # Инициализация роя частиц
        swarm = [Particle(self.bounds, self.func) for _ in range(self.pop_size)]
        
        # Поиск глобального лучшего решения
        for particle in swarm:
            if particle.best_value < self.best_global_value:
                self.best_global_value = particle.best_value
                self.best_global_position = particle.best_position.copy()
        
        # Основной цикл алгоритма
        for generation in range(generations):
            # Сохраняем текущее облако частиц для визуализации
            self.history.append(np.array([p.position.copy() for p in swarm]))
            self.best_history.append(self.best_global_value)
            
            if verbose and generation % 10 == 0:
                print(f"Поколение {generation}: лучшее значение = {self.best_global_value:.10f}")
            
            # Обновление каждой частицы
            for particle in swarm:
                # Обновление скорости
                new_velocity = self._update_velocity(particle, generation, generations)
                
                # Обновление позиции
                self._update_position(particle, new_velocity)
                
                # Обновление личного лучшего решения
                particle.update_best()
                
                # Обновление глобального лучшего решения
                if particle.best_value < self.best_global_value:
                    self.best_global_value = particle.best_value
                    self.best_global_position = particle.best_position.copy()
        
        # Сохраняем финальное поколение
        self.history.append(np.array([p.position.copy() for p in swarm]))
        self.best_history.append(self.best_global_value)
        
        if verbose:
            print(f"\nОптимизация завершена!")
            print(f"Лучшее значение: {self.best_global_value:.10f}")
            print(f"Лучшая позиция: {self.best_global_position}")
        
        return self.history
    
    def get_best_solution(self):
        """Возвращает лучшее найденное решение"""
        return self.best_global_position, self.best_global_value
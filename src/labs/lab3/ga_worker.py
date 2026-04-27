import time

import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal


class GeneticAlgorithmWorker(QThread):
    """Рабочий поток для выполнения генетического алгоритма"""

    generation_update = pyqtSignal(int, np.ndarray, np.ndarray, float)
    finished_signal = pyqtSignal(np.ndarray, float, list)

    def __init__(self, algorithm, generations, delay_ms=50):
        super().__init__()
        self.algorithm = algorithm
        self.generations = generations
        self.delay_ms = delay_ms
        self.is_stopped = False

    def run(self):
        def callback(generation, population, best_point, best_value):
            if self.is_stopped:
                return False

            self.generation_update.emit(generation, population, best_point, best_value)
            time.sleep(self.delay_ms / 1000.0)
            return not self.is_stopped

        _, best_value, best_point, history = self.algorithm.solve(
            generations=self.generations,
            generation_callback=callback,
        )

        if not self.is_stopped:
            self.finished_signal.emit(best_point, best_value, history)

    def stop(self):
        """Остановка воркера"""
        self.is_stopped = True

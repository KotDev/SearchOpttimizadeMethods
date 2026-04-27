import time

import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal


class PSOWorker(QThread):
    """Рабочий поток для выполнения PSO"""

    iteration_update = pyqtSignal(int, np.ndarray, np.ndarray, float)
    finished_signal = pyqtSignal(np.ndarray, float, list)

    def __init__(self, algorithm, generations, delay_ms=50):
        super().__init__()
        self.algorithm = algorithm
        self.generations = generations
        self.delay_ms = delay_ms
        self.is_stopped = False

    def run(self):
        def callback(iteration, positions, best_point, best_value):
            if self.is_stopped:
                return False

            self.iteration_update.emit(iteration, positions, best_point, best_value)
            time.sleep(self.delay_ms / 1000.0)
            return not self.is_stopped

        history = self.algorithm.solve(
            generations=self.generations,
            verbose=True,
            generation_callback=callback,
        )

        if not self.is_stopped:
            best_point, best_value = self.algorithm.get_best_solution()
            self.finished_signal.emit(best_point, best_value, history)

    def stop(self):
        """Остановка воркера"""
        self.is_stopped = True

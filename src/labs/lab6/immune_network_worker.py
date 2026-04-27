import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal


class ImmuneNetworkWorker(QThread):
    """Рабочий поток для иммунной сети"""

    iteration_update = pyqtSignal(int, np.ndarray, np.ndarray, float)
    finished_signal = pyqtSignal(np.ndarray, float, list)

    def __init__(self, immune_algorithm, delay_ms=50):
        super().__init__()
        self.immune_algorithm = immune_algorithm
        self.delay_ms = delay_ms
        self.is_stopped = False

    def run(self):
        def callback(iteration, positions, best_pos, best_val):
            if self.is_stopped:
                return False

            self.iteration_update.emit(iteration, np.array(positions), np.array(best_pos), float(best_val))
            self.msleep(self.delay_ms)
            return not self.is_stopped

        best_position, best_value, history = self.immune_algorithm.solve(real_time_callback=callback)

        if not self.is_stopped:
            self.finished_signal.emit(np.array(best_position), float(best_value), history)

    def stop(self):
        self.is_stopped = True

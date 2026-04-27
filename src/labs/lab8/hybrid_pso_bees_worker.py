import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal


class HybridPSOBeesWorker(QThread):
    """Рабочий поток для гибридного алгоритма PSO + Bees"""

    iteration_update = pyqtSignal(int, str, np.ndarray, np.ndarray, float)
    finished_signal = pyqtSignal(np.ndarray, float, list, list)

    def __init__(self, hybrid_algorithm, delay_ms=50):
        super().__init__()
        self.hybrid_algorithm = hybrid_algorithm
        self.delay_ms = delay_ms
        self.is_stopped = False

    def run(self):
        def callback(iteration, phase, positions, best_pos, best_val):
            if self.is_stopped:
                return False

            best_array = np.array(best_pos) if best_pos is not None else np.array([0.0, 0.0])
            self.iteration_update.emit(iteration, phase, np.array(positions), best_array, float(best_val))
            self.msleep(self.delay_ms)
            return not self.is_stopped

        best_position, best_value, history, phase_history = self.hybrid_algorithm.solve(
            real_time_callback=callback
        )

        if not self.is_stopped:
            self.finished_signal.emit(np.array(best_position), float(best_value), history, phase_history)

    def stop(self):
        self.is_stopped = True

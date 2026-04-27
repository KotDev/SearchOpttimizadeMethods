import numpy as np
from typing import Callable, List, Optional, Tuple


class HybridPSOBeesAlgorithm:
    """
    Гибридный алгоритм оптимизации: PSO + Bees Algorithm.

    На первой фазе выполняется глобальный поиск роем частиц,
    на второй фазе лучшие найденные области уточняются пчелиным роем.
    """

    def __init__(
        self,
        func: Callable,
        bounds: np.ndarray,
        pso_population: int = 30,
        pso_iterations: int = 40,
        inertia_weight: float = 0.9,
        cognitive_weight: float = 2.05,
        social_weight: float = 2.05,
        n_scouts: int = 16,
        n_elite_sites: int = 2,
        n_best_sites: int = 3,
        n_elite_bees: int = 7,
        n_best_bees: int = 4,
        patch_radius: float = 0.2,
        radius_reduction: float = 0.8,
        stagnation_limit: int = 20,
        verbose: bool = False,
    ):
        self.func = func
        self.bounds = np.array(bounds, dtype=float)
        self.dimension = len(bounds)

        self.pso_population = pso_population
        self.pso_iterations = pso_iterations
        self.inertia_weight = inertia_weight
        self.cognitive_weight = cognitive_weight
        self.social_weight = social_weight

        phi = cognitive_weight + social_weight
        if phi > 4:
            self.chi = 2 / abs(2 - phi - np.sqrt(phi**2 - 4 * phi))
        else:
            self.chi = 1.0

        self.n_scouts = n_scouts
        self.n_elite_sites = n_elite_sites
        self.n_best_sites = n_best_sites
        self.n_elite_bees = n_elite_bees
        self.n_best_bees = n_best_bees
        self.patch_radius = patch_radius
        self.radius_reduction = radius_reduction
        self.stagnation_limit = stagnation_limit
        self.verbose = verbose

        self.history: List[np.ndarray] = []
        self.phase_history: List[str] = []
        self.best_history: List[float] = []
        self.best_positions_history: List[np.ndarray] = []

        self.best_position = None
        self.best_value = float("inf")

    def _random_position(self) -> np.ndarray:
        return np.random.uniform(self.bounds[:, 0], self.bounds[:, 1], size=self.dimension)

    def _evaluate(self, position: np.ndarray) -> float:
        return float(self.func(position))

    def _random_in_patch(self, center: np.ndarray, radius: float) -> np.ndarray:
        position = center + np.random.uniform(-radius, radius, size=self.dimension)
        return np.clip(position, self.bounds[:, 0], self.bounds[:, 1])

    def _record_state(
        self,
        iteration: int,
        phase: str,
        positions: np.ndarray,
        callback: Optional[Callable],
    ) -> bool:
        self.history.append(positions.copy())
        self.phase_history.append(phase)
        self.best_history.append(self.best_value)
        self.best_positions_history.append(self.best_position.copy() if self.best_position is not None else None)

        if callback is not None:
            should_continue = callback(iteration, phase, positions.copy(), self.best_position, self.best_value)
            if should_continue is False:
                return False
        return True

    def solve(
        self,
        real_time_callback: Optional[Callable] = None,
    ) -> Tuple[np.ndarray, float, List[np.ndarray], List[str]]:
        self.history = []
        self.phase_history = []
        self.best_history = []
        self.best_positions_history = []
        self.best_position = None
        self.best_value = float("inf")

        iteration = 0

        # ===== Phase 1: PSO =====
        scale = (self.bounds[:, 1] - self.bounds[:, 0]) * 0.1
        swarm_positions = [
            np.random.uniform(self.bounds[:, 0], self.bounds[:, 1], size=self.dimension)
            for _ in range(self.pso_population)
        ]
        swarm_velocities = [
            np.random.uniform(-scale, scale, size=self.dimension)
            for _ in range(self.pso_population)
        ]
        personal_best_positions = [pos.copy() for pos in swarm_positions]
        personal_best_values = [self._evaluate(pos) for pos in swarm_positions]

        for pos, val in zip(personal_best_positions, personal_best_values):
            if val < self.best_value:
                self.best_value = val
                self.best_position = pos.copy()

        for generation in range(self.pso_iterations):
            positions_array = np.array([p.copy() for p in swarm_positions])
            if not self._record_state(iteration, "PSO", positions_array, real_time_callback):
                return self.best_position, self.best_value, self.history, self.phase_history

            if self.verbose and generation % 10 == 0:
                print(f"PSO итерация {generation}: лучшее значение = {self.best_value:.10f}")

            inertia = self.inertia_weight * (1 - generation / max(self.pso_iterations, 1)) + 0.4 * (
                generation / max(self.pso_iterations, 1)
            )

            for i in range(self.pso_population):
                r1 = np.random.random(self.dimension)
                r2 = np.random.random(self.dimension)
                cognitive = self.cognitive_weight * r1 * (personal_best_positions[i] - swarm_positions[i])
                social = self.social_weight * r2 * (self.best_position - swarm_positions[i])
                new_velocity = self.chi * (inertia * swarm_velocities[i] + cognitive + social)

                max_velocity = (self.bounds[:, 1] - self.bounds[:, 0]) * 0.2
                new_velocity = np.clip(new_velocity, -max_velocity, max_velocity)

                swarm_velocities[i] = new_velocity
                swarm_positions[i] = np.clip(
                    swarm_positions[i] + new_velocity,
                    self.bounds[:, 0],
                    self.bounds[:, 1],
                )

                value = self._evaluate(swarm_positions[i])
                if value < personal_best_values[i]:
                    personal_best_values[i] = value
                    personal_best_positions[i] = swarm_positions[i].copy()

                if value < self.best_value:
                    self.best_value = value
                    self.best_position = swarm_positions[i].copy()

            iteration += 1

        # ===== Phase 2: Bees =====
        final_pso_positions = np.array([p.copy() for p in swarm_positions])
        final_values = np.array([self._evaluate(p) for p in final_pso_positions])
        order = np.argsort(final_values)

        scout_positions = [final_pso_positions[i].copy() for i in order[: min(self.n_scouts, len(order))]]
        while len(scout_positions) < self.n_scouts:
            scout_positions.append(self._random_position())
        scout_values = [self._evaluate(pos) for pos in scout_positions]

        current_radius = self.patch_radius
        stagnation_counter = 0
        last_best_value = self.best_value

        max_bees_iterations = max(self.pso_iterations, 1)
        for local_iteration in range(max_bees_iterations):
            positions_array = np.array(scout_positions)
            if not self._record_state(iteration, "BEES", positions_array, real_time_callback):
                return self.best_position, self.best_value, self.history, self.phase_history

            if self.verbose and local_iteration % 10 == 0:
                print(
                    f"Bees итерация {local_iteration}: лучшее значение = "
                    f"{self.best_value:.10f}, радиус = {current_radius:.4f}"
                )

            sites = list(zip(scout_positions, scout_values))
            sites.sort(key=lambda x: x[1])
            elite_sites = sites[: self.n_elite_sites]
            best_sites = sites[self.n_elite_sites : self.n_elite_sites + self.n_best_sites]

            new_scout_positions = []
            new_scout_values = []

            for site_pos, site_val in elite_sites:
                for _ in range(self.n_elite_bees):
                    bee_pos = self._random_in_patch(site_pos, current_radius)
                    bee_val = self._evaluate(bee_pos)
                    new_scout_positions.append(bee_pos)
                    new_scout_values.append(bee_val)

                    if bee_val < self.best_value:
                        self.best_value = bee_val
                        self.best_position = bee_pos.copy()

                new_scout_positions.append(site_pos.copy())
                new_scout_values.append(site_val)

            for site_pos, site_val in best_sites:
                for _ in range(self.n_best_bees):
                    bee_pos = self._random_in_patch(site_pos, current_radius)
                    bee_val = self._evaluate(bee_pos)
                    new_scout_positions.append(bee_pos)
                    new_scout_values.append(bee_val)

                    if bee_val < self.best_value:
                        self.best_value = bee_val
                        self.best_position = bee_pos.copy()

                new_scout_positions.append(site_pos.copy())
                new_scout_values.append(site_val)

            remaining_scouts = self.n_scouts - len(new_scout_positions)
            for _ in range(max(remaining_scouts, 0)):
                random_pos = self._random_position()
                random_val = self._evaluate(random_pos)
                new_scout_positions.append(random_pos)
                new_scout_values.append(random_val)

                if random_val < self.best_value:
                    self.best_value = random_val
                    self.best_position = random_pos.copy()

            scout_positions = new_scout_positions[: self.n_scouts]
            scout_values = new_scout_values[: self.n_scouts]

            if self.best_value < last_best_value:
                current_radius *= self.radius_reduction
                stagnation_counter = 0
                last_best_value = self.best_value
            else:
                stagnation_counter += 1

            iteration += 1
            if stagnation_counter >= self.stagnation_limit:
                break

        final_positions = np.array(scout_positions)
        self.history.append(final_positions.copy())
        self.phase_history.append("BEES")
        self.best_history.append(self.best_value)
        self.best_positions_history.append(self.best_position.copy() if self.best_position is not None else None)

        if self.verbose:
            print("\nГибридная оптимизация завершена!")
            print(f"Лучшее значение: {self.best_value:.12f}")
            print(f"Лучшая позиция: {self.best_position}")

        return self.best_position, self.best_value, self.history, self.phase_history

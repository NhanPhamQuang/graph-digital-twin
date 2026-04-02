# Application risk
# === Risk Layer ===

import numpy as np


# --- Individual Risks ---

def congestion_risk(density, jam_density=0.2):
    r = density / jam_density
    return min(r, 1.0)


def spillback_risk(queue, lane_length=50):
    r = queue / lane_length
    return min(r, 1.0)


def instability_risk(speed_history):
    """
    speed_history: list of recent speeds (window)
    """
    if len(speed_history) < 2:
        return 0

    std = np.std(speed_history)
    mean = np.mean(speed_history) + 1e-5

    return min(std / mean, 1.0)


# --- Risk Manager ---

class RiskManager:
    def __init__(self, window_size=5):
        self.window_size = window_size
        self.speed_buffer = {}  # lane → list of speeds

    def _update_speed_buffer(self, lane, speed):
        if lane not in self.speed_buffer:
            self.speed_buffer[lane] = []

        self.speed_buffer[lane].append(speed)

        if len(self.speed_buffer[lane]) > self.window_size:
            self.speed_buffer[lane].pop(0)

    def compute(self, state):
        risks = {}

        for lane in state.density:

            speed = state.speed[lane]
            self._update_speed_buffer(lane, speed)

            Rc = congestion_risk(state.density[lane])
            Ri = instability_risk(self.speed_buffer[lane])
            Rs = spillback_risk(state.queue[lane])

            risks[lane] = {
                "congestion": Rc,
                "instability": Ri,
                "spillback": Rs,
                "total": (Rc + Ri + Rs) / 3   # simple aggregation
            }

        return risks
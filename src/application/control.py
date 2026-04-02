# Application control
# === Control Layer ===

import traci


# --- Phase Policy (chọn hướng ưu tiên) ---
class PhasePolicy:
    def select_lane(self, lanes, risks):
        """
        chọn lane có pressure cao nhất
        """
        best_lane = None
        best_pressure = -1

        for lane in lanes:
            Rc = risks[lane]["congestion"]
            Rs = risks[lane]["spillback"]

            # 🔥 max-pressure (lite version)
            pressure = Rc + Rs

            if pressure > best_pressure:
                best_pressure = pressure
                best_lane = lane

        return best_lane, best_pressure


# --- Timing Policy (tính thời gian đèn xanh) ---
class TimingPolicy:
    def __init__(self, min_green=20, max_green=45, target_congestion=0.8):
        self.min_green = min_green
        self.max_green = max_green
        self.target_congestion = target_congestion

    def compute_green_time(self, pressure):
        pressure = min(pressure, 1.0)

        green_time = self.min_green + pressure * (self.max_green - self.min_green)

        # 🔥 anti-overflow boost
        if pressure > self.target_congestion:
            green_time *= 1.5

        return int(green_time)


# --- Signal Controller ---
class SignalController:
    def __init__(self):
        self.phase_policy = PhasePolicy()
        self.timing_policy = TimingPolicy()

        self.last_switch = {}
        self.min_switch_interval = 10  # seconds

    def decide(self, state, risks):
        actions = {}

        # ===== group lane theo traffic light =====
        tl_groups = {}

        for lane in risks:
            try:
                tl = traci.lane.getTrafficLightID(lane)
                if not tl:
                    continue

                tl_groups.setdefault(tl, []).append(lane)
            except:
                continue

        # ===== xử lý từng traffic light =====
        for tl, lanes in tl_groups.items():

            # --- phase selection ---
            best_lane, pressure = self.phase_policy.select_lane(lanes, risks)

            # --- timing ---
            green_time = self.timing_policy.compute_green_time(pressure)

            actions[tl] = {
                "lane": best_lane,
                "pressure": pressure,
                "green_time": green_time
            }

        return actions

    def apply(self, actions):
        sim_time = traci.simulation.getTime()

        for tl, action in actions.items():
            try:
                green_time = action["green_time"]

                # ===== tránh switch quá nhanh =====
                last = self.last_switch.get(tl, -999)
                if sim_time - last < self.min_switch_interval:
                    continue

                current_phase = traci.trafficlight.getPhase(tl)
                next_phase = (current_phase + 1) % traci.trafficlight.getPhaseNumber(tl)

                traci.trafficlight.setPhase(tl, next_phase)
                traci.trafficlight.setPhaseDuration(tl, green_time)

                self.last_switch[tl] = sim_time

                # DEBUG
                print(
                    f"🚦 TL {tl} | phase {current_phase}->{next_phase} | "
                    f"pressure={action['pressure']:.2f} | green={green_time}"
                )

            except Exception:
                continue
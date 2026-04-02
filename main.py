from src.physical.environment import SumoEnv
from src.twin.digital_twin import TrafficState
from src.twin.digital_twin import StateSync
from src.application.risks import RiskManager
from src.application.control import SignalController

def main():
    print("🚀 Starting Digital Twin System...")

    # ===== INIT =====
    env = SumoEnv("config/simulation.sumocfg")
    state = TrafficState()
    sync = StateSync()
    risk_manager = RiskManager()
    controller = SignalController()

    # ===== START SIMULATION =====
    env.start()
    print("✅ SUMO started")

    total_steps = 2000

    for step in range(total_steps):
        env.step()

        # ===== SYNC (Physical → Twin) =====
        density, speed, queue = sync.sync()
        state.update(density, speed, queue)

        # ===== BASIC DEBUG =====
        # if step % 20 == 0:
        #     print(f"\n🧠 Step {step}")
        #     print(f"   lanes detected: {len(state.density)}")

        # ===== RISK COMPUTATION =====
        risks = risk_manager.compute(state)

        # ===== ADVANCED DEBUG =====
        if step % 10 == 0 and len(risks) > 0:
            print(f"\n🧠 Step {step}")
            # worst congestion lane
            worst_lane = max(risks, key=lambda k: risks[k]["congestion"])

            avg_congestion = sum(r["congestion"] for r in risks.values()) / len(risks)
            avg_spillback = sum(r["spillback"] for r in risks.values()) / len(risks)

            # print(f"   🔴 worst lane: {worst_lane}")
            print(f"      congestion: {risks[worst_lane]['congestion']:.2f}")
            # print(f"      spillback: {risks[worst_lane]['spillback']:.2f}")
            print(f"🔥 Avg congestion: {avg_congestion:.2f}")
            # print(f"🚗 Avg spillback: {avg_spillback:.2f}")

        # ===== CONTROL (Application → Physical) =====
        actions = controller.decide(state, risks)
        controller.apply(actions)

    # ===== END =====
    env.close()
    print("🛑 Simulation ended")


if __name__ == "__main__":
    main()

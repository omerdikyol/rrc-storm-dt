"""
Phase 3: Digital Twin Controller with EMA prediction and ACB.
No calibration loop yet. Logs state mirroring error E over time.
"""

import os
import sys
import simpy
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from config import SIM_TIME, RANDOM_SEED
from gnb_core import TrafficGenerator, GNBQueue, DigitalTwinController


def logger(env, gnb, dt, records, interval=5.0):
    while True:
        yield env.timeout(interval)
        E = abs(gnb.q_real - dt.q_virtual)
        records.append({
            "time": env.now,
            "q_real": gnb.q_real,
            "q_virtual": round(dt.q_virtual, 2),
            "total": gnb.total,
            "dropped": gnb.dropped,
            "served": gnb.served,
            "drop_rate": round(gnb.drop_rate, 4),
            "ema_t": round(dt.ema_t, 4),
            "p_acb": round(dt.p_acb, 4),
            "E": round(E, 2),
        })


def run_phase3(sim_time=SIM_TIME):
    print(f"\n=== Phase 3: Digital Twin Controller ({sim_time}s) ===")
    env = simpy.Environment()
    rng = np.random.default_rng(RANDOM_SEED)
    records = []

    gnb = GNBQueue(env, rng)
    tgen = TrafficGenerator(env, gnb, rng)
    dt = DigitalTwinController(env, gnb, calibrate=False)

    env.process(tgen.run())
    env.process(dt.run())
    env.process(logger(env, gnb, dt, records))
    env.run(until=sim_time)

    df = pd.DataFrame(records)
    os.makedirs("output", exist_ok=True)
    df.to_csv("output/phase3_dt.csv", index=False)

    p_success = gnb.served / max(gnb.total, 1)
    p_drop = gnb.dropped / max(gnb.total, 1)
    E_mean = df["E"].mean() if len(df) > 0 else 0.0
    print(f"Phase 3 complete.")
    print(f"  Total={gnb.total}, Dropped={gnb.dropped}, Served={gnb.served}")
    print(f"  P_success={p_success:.3f}, P_drop={p_drop:.3f}, E_mean={E_mean:.2f}")
    print(f"  CSV saved to output/phase3_dt.csv")
    return df


if __name__ == "__main__":
    os.chdir(os.path.join(os.path.dirname(__file__), ".."))
    run_phase3()

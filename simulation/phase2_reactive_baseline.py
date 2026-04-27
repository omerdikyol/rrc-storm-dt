"""
Phase 2: Reactive threshold controller baseline.
If Q_real > 0.8*K → set drop_rate=0.5; else drop_rate=0.
Establishes comparison baseline for Phase 4.
"""

import os
import sys
import simpy
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from config import SIM_TIME, RANDOM_SEED
from gnb_core import TrafficGenerator, GNBQueue, ReactiveController


def logger(env, gnb, records, interval=5.0):
    while True:
        yield env.timeout(interval)
        records.append({
            "time": env.now,
            "q_real": gnb.q_real,
            "total": gnb.total,
            "dropped": gnb.dropped,
            "served": gnb.served,
            "drop_rate": gnb.drop_rate,
        })


def run_phase2(sim_time=SIM_TIME):
    print(f"\n=== Phase 2: Reactive Baseline ({sim_time}s) ===")
    env = simpy.Environment()
    rng = np.random.default_rng(RANDOM_SEED)
    records = []

    gnb = GNBQueue(env, rng)
    tgen = TrafficGenerator(env, gnb, rng)
    ctrl = ReactiveController(env, gnb)

    env.process(tgen.run())
    env.process(ctrl.run())
    env.process(logger(env, gnb, records))
    env.run(until=sim_time)

    df = pd.DataFrame(records)
    os.makedirs("output", exist_ok=True)
    df.to_csv("output/phase2_baseline.csv", index=False)

    p_success = gnb.served / max(gnb.total, 1)
    p_drop = gnb.dropped / max(gnb.total, 1)
    print(f"Phase 2 complete.")
    print(f"  Total={gnb.total}, Dropped={gnb.dropped}, Served={gnb.served}")
    print(f"  P_success={p_success:.3f}, P_drop={p_drop:.3f}")
    print(f"  CSV saved to output/phase2_baseline.csv")
    return df


if __name__ == "__main__":
    os.chdir(os.path.join(os.path.dirname(__file__), ".."))
    run_phase2()

"""
Phase 1: 2-state MMPP Traffic Generator + bare M/c/K gNB queue.
No mitigation. Run 100s to verify burst fills buffer.
"""

import os
import sys
import simpy
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from config import SIM_TIME_TEST, RANDOM_SEED
from gnb_core import TrafficGenerator, GNBQueue


def logger(env, gnb, records, interval=5.0):
    while True:
        yield env.timeout(interval)
        records.append({
            "time": env.now,
            "q_real": gnb.q_real,
            "total": gnb.total,
            "dropped": gnb.dropped,
            "served": gnb.served,
        })
        print(f"  t={env.now:6.1f}s | Q_real={gnb.q_real:4d} | "
              f"total={gnb.total:6d} | dropped={gnb.dropped:6d} | served={gnb.served:6d}")


def run_phase1(sim_time=SIM_TIME_TEST):
    print(f"\n=== Phase 1: MMPP Traffic + Bare M/c/K Queue ({sim_time}s) ===")
    env = simpy.Environment()
    rng = np.random.default_rng(RANDOM_SEED)
    records = []

    gnb = GNBQueue(env, rng)
    tgen = TrafficGenerator(env, gnb, rng)

    env.process(tgen.run())
    env.process(logger(env, gnb, records))
    env.run(until=sim_time)

    df = pd.DataFrame(records)
    os.makedirs("output", exist_ok=True)
    df.to_csv("output/phase1_queue.csv", index=False)
    print(f"\nPhase 1 complete. Rows logged: {len(df)}. CSV saved to output/phase1_queue.csv")
    print(f"Final: total={gnb.total}, dropped={gnb.dropped}, served={gnb.served}")
    print(f"Drop rate: {gnb.dropped/max(gnb.total,1)*100:.1f}%")
    return df


if __name__ == "__main__":
    os.chdir(os.path.join(os.path.dirname(__file__), ".."))
    run_phase1()

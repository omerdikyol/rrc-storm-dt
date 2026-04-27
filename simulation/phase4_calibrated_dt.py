"""
Phase 4: Calibrated Digital Twin + side-by-side comparison with Phase 2 baseline.
Calibration loop: if E > epsilon, increase alpha; else decay alpha.
Outputs matplotlib figures comparing queue stability and success rate.
"""

import os
import sys
import simpy
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from config import (
    K, SIM_TIME, RANDOM_SEED,
    REACTIVE_THRESHOLD, OMEGA_1, OMEGA_2,
    EPSILON,
)
from gnb_core import (
    TrafficGenerator, GNBQueue,
    ReactiveController, DigitalTwinController,
)


# ---------------------------------------------------------------------------
# Loggers
# ---------------------------------------------------------------------------

def logger_reactive(env, gnb, records, interval=5.0):
    while True:
        yield env.timeout(interval)
        records.append({
            "time": env.now,
            "q_real": gnb.q_real,
            "total": gnb.total,
            "dropped": gnb.dropped,
            "served": gnb.served,
            "drop_rate": gnb.drop_rate,
            "E": 0.0,
        })


def logger_dt(env, gnb, dt, records, interval=5.0):
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
            "alpha": round(dt.ema_alpha, 4),
        })


# ---------------------------------------------------------------------------
# Runners
# ---------------------------------------------------------------------------

def run_phase2_baseline(sim_time=SIM_TIME):
    env = simpy.Environment()
    rng = np.random.default_rng(RANDOM_SEED)
    records = []

    gnb = GNBQueue(env, rng)
    tgen = TrafficGenerator(env, gnb, rng)
    ctrl = ReactiveController(env, gnb)

    env.process(tgen.run())
    env.process(ctrl.run())
    env.process(logger_reactive(env, gnb, records))
    env.run(until=sim_time)

    return pd.DataFrame(records), gnb


def run_phase3_uncalibrated(sim_time=SIM_TIME):
    env = simpy.Environment()
    rng = np.random.default_rng(RANDOM_SEED)
    records = []

    gnb = GNBQueue(env, rng)
    tgen = TrafficGenerator(env, gnb, rng)
    dt = DigitalTwinController(env, gnb, calibrate=False)

    env.process(tgen.run())
    env.process(dt.run())
    env.process(logger_dt(env, gnb, dt, records))
    env.run(until=sim_time)

    return pd.DataFrame(records), gnb


def run_phase4_calibrated(sim_time=SIM_TIME):
    env = simpy.Environment()
    rng = np.random.default_rng(RANDOM_SEED)
    records = []

    gnb = GNBQueue(env, rng)
    tgen = TrafficGenerator(env, gnb, rng)
    dt = DigitalTwinController(env, gnb, calibrate=True)

    env.process(tgen.run())
    env.process(dt.run())
    env.process(logger_dt(env, gnb, dt, records))
    env.run(until=sim_time)

    return pd.DataFrame(records), gnb


# ---------------------------------------------------------------------------
# Objective function
# ---------------------------------------------------------------------------

def compute_objective(gnb, df, e_col="E", omega1=OMEGA_1, omega2=OMEGA_2):
    P_success = gnb.served / max(gnb.total, 1)
    E_mean_norm = (df[e_col].mean() / K) if e_col in df.columns else 0.0
    P_drop = gnb.dropped / max(gnb.total, 1)
    return P_success - omega1 * E_mean_norm - omega2 * P_drop


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------

def plot_queue_stability(df2, df3, df4, out_path):
    fig, ax = plt.subplots(figsize=(13, 5))
    ax.plot(df2["time"], df2["q_real"], color="#e06c75",
            linewidth=1.2, alpha=0.85, label="Reactive Baseline")
    ax.plot(df3["time"], df3["q_real"], color="#e5c07b",
            linewidth=1.0, alpha=0.75, label="DT (No Calibration)")
    ax.plot(df4["time"], df4["q_real"], color="#61afef",
            linewidth=1.4, label="Calibrated DT")
    ax.axhline(K, color="#be5046", linestyle="--", linewidth=0.9,
               alpha=0.7, label=f"Buffer Limit K={K}")
    ax.axhline(REACTIVE_THRESHOLD, color="#d19a66", linestyle="--",
               linewidth=0.9, alpha=0.7,
               label=f"Reactive Threshold={int(REACTIVE_THRESHOLD)}")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Queue Length Q_real")
    ax.set_title("Queue Stability: 3-Way Comparison")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_success_rate(df2, df3, df4, out_path):
    for df in [df2, df3, df4]:
        df["success_rate"] = df["served"] / df["total"].replace(0, np.nan)

    fig, ax = plt.subplots(figsize=(13, 5))
    ax.plot(df2["time"], df2["success_rate"], color="#e06c75",
            linewidth=1.2, alpha=0.85, label="Reactive Baseline")
    ax.plot(df3["time"], df3["success_rate"], color="#e5c07b",
            linewidth=1.0, alpha=0.75, label="DT (No Calibration)")
    ax.plot(df4["time"], df4["success_rate"], color="#61afef",
            linewidth=1.4, label="Calibrated DT")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("P_success (served / total)")
    ax.set_title("Cumulative Connection Success Rate: 3-Way Comparison")
    ax.set_ylim(0, 1)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_mirroring_error(df3, df4, out_path):
    fig, ax = plt.subplots(figsize=(13, 4))
    ax.plot(df3["time"], df3["E"], color="#e5c07b",
            linewidth=1.0, alpha=0.8, label="DT (No Calibration)")
    ax.plot(df4["time"], df4["E"], color="#61afef",
            linewidth=1.2, label="Calibrated DT")
    ax.axhline(EPSILON, color="#be5046", linestyle="--", linewidth=0.9,
               alpha=0.8, label=f"Calibration Threshold ε={EPSILON}")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("E = |Q_real − Q_virtual|")
    ax.set_title("State Mirroring Error: Calibration Reduces Model Drift")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_ema_alpha(df4, out_path):
    from config import EMA_ALPHA_INIT
    fig, ax = plt.subplots(figsize=(13, 4))
    ax.plot(df4["time"], df4["alpha"], color="#98c379",
            linewidth=1.0, label="EMA α (adaptive)")
    ax.axhline(EMA_ALPHA_INIT, color="#abb2bf", linestyle="--",
               linewidth=0.8, label=f"Initial α={EMA_ALPHA_INIT}")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("EMA α")
    ax.set_title("Calibration Loop: EMA α Adaptation Over Time")
    ax.set_ylim(0, 1.05)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    os.chdir(os.path.join(os.path.dirname(__file__), ".."))
    os.makedirs("output/figures", exist_ok=True)

    print("=== Running Phase 2: Reactive Baseline ===")
    df2, gnb2 = run_phase2_baseline(sim_time=SIM_TIME)
    df2.to_csv("output/phase2_baseline.csv", index=False)

    print("=== Running Phase 3: DT (No Calibration) ===")
    df3, gnb3 = run_phase3_uncalibrated(sim_time=SIM_TIME)
    df3.to_csv("output/phase3_dt.csv", index=False)

    print("=== Running Phase 4: Calibrated Digital Twin ===")
    df4, gnb4 = run_phase4_calibrated(sim_time=SIM_TIME)
    df4.to_csv("output/phase4_comparison.csv", index=False)

    obj2 = compute_objective(gnb2, df2)
    obj3 = compute_objective(gnb3, df3)
    obj4 = compute_objective(gnb4, df4)

    print("\n=== Objective Function: max(P_success - ω₁·E/K - ω₂·P_drop) ===")
    print(f"  Phase 2 Reactive:            {obj2:+.4f}")
    print(f"  Phase 3 DT (no calib):       {obj3:+.4f}")
    print(f"  Phase 4 Calibrated DT:       {obj4:+.4f}")
    print(f"  Calibration vs No-Calib DT:  {obj4 - obj3:+.4f}")

    print("\n=== Key Metrics (3-Way) ===")
    print(f"  {'Label':20s}  P_success  P_drop  E_mean   E/K")
    print(f"  {'-'*60}")
    for label, gnb, df in [
        ("Reactive Baseline", gnb2, df2),
        ("DT (No Calibration)", gnb3, df3),
        ("Calibrated DT", gnb4, df4),
    ]:
        ps = gnb.served / max(gnb.total, 1)
        pd_ = gnb.dropped / max(gnb.total, 1)
        em = df["E"].mean()
        em_norm = em / K
        print(f"  {label:20s}  {ps:.4f}     {pd_:.4f}  {em:7.2f}  {em_norm:.4f}")

    plot_queue_stability(df2, df3, df4, "output/figures/phase4_queue_stability.png")
    plot_success_rate(df2, df3, df4, "output/figures/phase4_success_rate.png")
    plot_mirroring_error(df3, df4, "output/figures/phase4_mirroring_error.png")
    plot_ema_alpha(df4, "output/figures/phase4_ema_alpha.png")
    print("\nFigures saved to output/figures/")

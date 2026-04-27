"""
Phase 5: Academic Evaluation Layer.

Adds three empirical rigor improvements over Phase 4:
  1. Delay CDF — per-request queueing delay logged and plotted (P50/P90/P99).
  2. Multi-seed CI — 10 seeds, 95% confidence bands on all time-series figures.
  3. Epsilon sensitivity — sweep epsilon in {5,10,20,40,80}, export CSV table.
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
    K, EPSILON, SIM_TIME,
    OMEGA_1, OMEGA_2,
)
from gnb_core import TrafficGenerator, GNBQueue, ReactiveController, DigitalTwinController

SEEDS = [42, 7, 13, 99, 137, 256, 314, 512, 999, 2024]
EPSILON_SWEEP = [5, 10, 20, 40, 80]
LOG_INTERVAL = 5.0     # seconds between logger samples
METHODS = ["reactive", "uncalibrated", "calibrated"]

METHOD_STYLE = {
    "reactive":     {"color": "#e06c75", "label": "Reactive Baseline",     "lw": 1.2, "alpha": 0.85},
    "uncalibrated": {"color": "#e5c07b", "label": "DT (No Calibration)",   "lw": 1.0, "alpha": 0.75},
    "calibrated":   {"color": "#61afef", "label": "Calibrated DT",         "lw": 1.5, "alpha": 1.0},
}


# ---------------------------------------------------------------------------
# Single-seed runner — returns (DataFrame, GNBQueue)
# ---------------------------------------------------------------------------

def _logger(env, gnb, ctrl, records):
    """Generic per-tick logger. ctrl may be ReactiveController or DigitalTwinController."""
    while True:
        yield env.timeout(LOG_INTERVAL)
        row = {
            "time":      env.now,
            "q_real":    gnb.q_real,
            "total":     gnb.total,
            "dropped":   gnb.dropped,
            "served":    gnb.served,
            "drop_rate": gnb.drop_rate,
        }
        if isinstance(ctrl, DigitalTwinController):
            row["E"]        = abs(gnb.q_real - ctrl.q_virtual)
            row["q_virtual"] = ctrl.q_virtual
            row["p_acb"]    = ctrl.p_acb
            row["ema_t"]    = ctrl.ema_t
            row["alpha"]    = ctrl.ema_alpha
        else:
            row["E"]        = 0.0
        records.append(row)


def run_one_seed(method: str, seed: int,
                 epsilon: float = EPSILON,
                 sim_time: float = SIM_TIME):
    env = simpy.Environment()
    rng = np.random.default_rng(seed)
    records: list[dict] = []

    gnb = GNBQueue(env, rng)
    tgen = TrafficGenerator(env, gnb, rng)

    if method == "reactive":
        ctrl = ReactiveController(env, gnb)
    elif method == "uncalibrated":
        ctrl = DigitalTwinController(env, gnb, epsilon=epsilon, calibrate=False)
    else:  # calibrated
        ctrl = DigitalTwinController(env, gnb, epsilon=epsilon, calibrate=True)

    env.process(tgen.run())
    env.process(ctrl.run())
    env.process(_logger(env, gnb, ctrl, records))
    env.run(until=sim_time)

    df = pd.DataFrame(records)
    df["success_rate"] = df["served"] / df["total"].replace(0, np.nan)
    return df, gnb


# ---------------------------------------------------------------------------
# CI computation
# ---------------------------------------------------------------------------

def compute_ci(arrays: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Given list of equal-length 1-D arrays, return (mean, lower_95, upper_95)."""
    mat = np.vstack(arrays)           # shape (N_seeds, T)
    mean = mat.mean(axis=0)
    se   = mat.std(axis=0, ddof=1) / np.sqrt(len(arrays))
    return mean, mean - 1.96 * se, mean + 1.96 * se


# ---------------------------------------------------------------------------
# Multi-seed runner
# ---------------------------------------------------------------------------

def run_multi_seed(seeds=SEEDS, sim_time=SIM_TIME, epsilon=EPSILON):
    """Run all 3 methods over all seeds. Returns nested dict of DataFrames and delay logs."""
    results = {m: {"dfs": [], "delays": []} for m in METHODS}

    for i, seed in enumerate(seeds):
        print(f"  Seed {seed} ({i+1}/{len(seeds)}) ...", end=" ", flush=True)
        for method in METHODS:
            df, gnb = run_one_seed(method, seed, epsilon=epsilon, sim_time=sim_time)
            results[method]["dfs"].append(df)
            results[method]["delays"].append(np.array(gnb.delay_log, dtype=float))
        print("done")

    return results


# ---------------------------------------------------------------------------
# Epsilon sensitivity sweep
# ---------------------------------------------------------------------------

def run_epsilon_sweep(epsilons=EPSILON_SWEEP, seed=42, sim_time=SIM_TIME):
    rows = []
    for eps in epsilons:
        print(f"  ε={eps} ...", end=" ", flush=True)
        df, gnb = run_one_seed("calibrated", seed=seed, epsilon=eps, sim_time=sim_time)
        ps    = gnb.served  / max(gnb.total, 1)
        pd_   = gnb.dropped / max(gnb.total, 1)
        e_mean = df["E"].mean()
        e_norm = e_mean / K
        obj   = ps - OMEGA_1 * e_norm - OMEGA_2 * pd_
        delays = np.array(gnb.delay_log)
        rows.append({
            "epsilon":     eps,
            "P_success":   round(ps, 4),
            "P_drop":      round(pd_, 4),
            "E_mean":      round(e_mean, 3),
            "E_mean_norm": round(e_norm, 4),
            "objective":   round(obj, 4),
            "delay_P50_s": round(float(np.percentile(delays, 50)) if len(delays) else 0, 3),
            "delay_P90_s": round(float(np.percentile(delays, 90)) if len(delays) else 0, 3),
            "delay_P99_s": round(float(np.percentile(delays, 99)) if len(delays) else 0, 3),
        })
        print("done")
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def _ci_plot(ax, times, mean, lo, hi, style: dict):
    ax.fill_between(times, lo, hi, color=style["color"], alpha=0.18, linewidth=0)
    ax.plot(times, mean, color=style["color"], linewidth=style["lw"],
            alpha=style["alpha"], label=style["label"])


def plot_q_real_ci(results: dict, out_path: str):
    fig, ax = plt.subplots(figsize=(13, 5))
    for method in METHODS:
        dfs = results[method]["dfs"]
        times = dfs[0]["time"].values
        arrays = [df["q_real"].values.astype(float) for df in dfs]
        mean, lo, hi = compute_ci(arrays)
        _ci_plot(ax, times, mean, lo, hi, METHOD_STYLE[method])
    ax.axhline(K, color="#be5046", linestyle="--", linewidth=0.9,
               alpha=0.7, label=f"Buffer K={K}")
    ax.axhline(REACTIVE_THRESHOLD, color="#d19a66", linestyle="--",
               linewidth=0.9, alpha=0.7,
               label=f"Reactive Threshold={int(REACTIVE_THRESHOLD)}")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Queue Length Q_real")
    ax.set_title(f"Queue Stability — Mean ± 95% CI  (N={len(SEEDS)} seeds)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"  Saved: {out_path}")


def plot_success_ci(results: dict, out_path: str):
    fig, ax = plt.subplots(figsize=(13, 5))
    for method in METHODS:
        dfs = results[method]["dfs"]
        times = dfs[0]["time"].values
        arrays = [df["success_rate"].fillna(0).values.astype(float) for df in dfs]
        mean, lo, hi = compute_ci(arrays)
        lo = np.clip(lo, 0, 1)
        hi = np.clip(hi, 0, 1)
        _ci_plot(ax, times, mean, lo, hi, METHOD_STYLE[method])
    ax.set_ylim(0, 1)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("P_success (served / total)")
    ax.set_title(f"Connection Success Rate — Mean ± 95% CI  (N={len(SEEDS)} seeds)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"  Saved: {out_path}")


def plot_E_ci(results: dict, out_path: str):
    fig, ax = plt.subplots(figsize=(13, 5))
    for method in ["uncalibrated", "calibrated"]:
        dfs = results[method]["dfs"]
        times = dfs[0]["time"].values
        arrays = [df["E"].values.astype(float) for df in dfs]
        mean, lo, hi = compute_ci(arrays)
        lo = np.clip(lo, 0, None)
        _ci_plot(ax, times, mean, lo, hi, METHOD_STYLE[method])
    ax.axhline(EPSILON, color="#be5046", linestyle="--", linewidth=0.9,
               alpha=0.8, label=f"ε={EPSILON}")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("E = |Q_real − Q_virtual|")
    ax.set_title(f"State Mirroring Error — Mean ± 95% CI  (N={len(SEEDS)} seeds)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"  Saved: {out_path}")


def plot_delay_cdf(results: dict, out_path: str):
    fig, ax = plt.subplots(figsize=(11, 5))
    percentile_marks = [50, 90, 99]

    for method in METHODS:
        style = METHOD_STYLE[method]
        # Pool delay logs from all seeds for a richer empirical CDF
        all_delays = np.concatenate(results[method]["delays"])
        if len(all_delays) == 0:
            continue
        sorted_d = np.sort(all_delays)
        cdf = np.arange(1, len(sorted_d) + 1) / len(sorted_d)

        # Cap x-axis at 99th percentile to suppress extreme outliers
        cap = float(np.percentile(sorted_d, 99.5))
        mask = sorted_d <= cap
        ax.plot(sorted_d[mask], cdf[mask], color=style["color"],
                linewidth=style["lw"], alpha=style["alpha"], label=style["label"])

        # Annotate P50 / P90 / P99
        for pct in percentile_marks:
            val = float(np.percentile(sorted_d, pct))
            cdf_val = pct / 100.0
            ax.plot(val, cdf_val, "o", color=style["color"],
                    markersize=4, alpha=0.8)

    # Reference lines for percentile marks
    for pct in percentile_marks:
        ax.axhline(pct / 100.0, color="#5c6370", linestyle=":", linewidth=0.7, alpha=0.6)

    ax.set_xlabel("Queueing Delay (s)")
    ax.set_ylabel("CDF")
    ax.set_title(f"CDF of Per-Request Queueing Delay  (all seeds pooled, N={len(SEEDS)})")
    ax.legend()
    ax.grid(True, alpha=0.2)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"  Saved: {out_path}")


def plot_epsilon_sensitivity(df_eps: pd.DataFrame, out_path: str):
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), sharey=False)

    axes[0].plot(df_eps["epsilon"], df_eps["P_success"], "o-", color="#61afef", linewidth=1.5)
    axes[0].set_xlabel("ε (calibration threshold)")
    axes[0].set_ylabel("P_success")
    axes[0].set_title("P_success vs ε")

    axes[1].plot(df_eps["epsilon"], df_eps["E_mean"], "o-", color="#e5c07b", linewidth=1.5)
    axes[1].set_xlabel("ε (calibration threshold)")
    axes[1].set_ylabel("E_mean (queue units)")
    axes[1].set_title("State Mirroring Error vs ε")

    axes[2].plot(df_eps["epsilon"], df_eps["objective"], "o-", color="#98c379", linewidth=1.5)
    axes[2].set_xlabel("ε (calibration threshold)")
    axes[2].set_ylabel("Objective Score")
    axes[2].set_title("Objective Score vs ε")

    for ax in axes:
        ax.grid(True, alpha=0.25)
    fig.suptitle("Epsilon Sensitivity Analysis (Calibrated DT, seed=42)", fontsize=11)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"  Saved: {out_path}")


# ---------------------------------------------------------------------------
# Aggregate summary stats across seeds
# ---------------------------------------------------------------------------

def print_summary_table(results: dict):
    print(f"\n{'Method':22s}  P_success±CI       P_drop±CI          E_mean±CI")
    print("─" * 80)
    for method in METHODS:
        dfs = results[method]["dfs"]
        ps_vals  = [gnb_df["served"].iloc[-1] / max(gnb_df["total"].iloc[-1], 1)
                    for gnb_df in dfs]
        pd_vals  = [gnb_df["dropped"].iloc[-1] / max(gnb_df["total"].iloc[-1], 1)
                    for gnb_df in dfs]
        em_vals  = [gnb_df["E"].mean() for gnb_df in dfs]

        def fmt(vals):
            m = np.mean(vals)
            ci = 1.96 * np.std(vals, ddof=1) / np.sqrt(len(vals))
            return f"{m:.4f} ± {ci:.4f}"

        label = METHOD_STYLE[method]["label"]
        print(f"  {label:20s}  {fmt(ps_vals)}  {fmt(pd_vals)}  {fmt(em_vals)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    os.chdir(os.path.join(os.path.dirname(__file__), ".."))
    os.makedirs("output/figures", exist_ok=True)

    # ── 1. Multi-seed runs ────────────────────────────────────────────────
    print(f"\n=== Multi-Seed Evaluation  (N={len(SEEDS)} seeds × 3 methods × {SIM_TIME}s) ===")
    results = run_multi_seed(seeds=SEEDS, sim_time=SIM_TIME)

    print_summary_table(results)

    print("\n── Generating CI figures ──")
    plot_q_real_ci(results,   "output/figures/phase5_q_real_ci.png")
    plot_success_ci(results,  "output/figures/phase5_success_ci.png")
    plot_E_ci(results,        "output/figures/phase5_E_ci.png")
    plot_delay_cdf(results,   "output/figures/phase5_delay_cdf.png")

    # ── 2. Epsilon sensitivity sweep ──────────────────────────────────────
    print(f"\n=== Epsilon Sensitivity Sweep  ε ∈ {EPSILON_SWEEP} (seed=42) ===")
    df_eps = run_epsilon_sweep(epsilons=EPSILON_SWEEP, seed=42, sim_time=SIM_TIME)
    df_eps.to_csv("output/sensitivity_epsilon.csv", index=False)
    print("\n── Epsilon sweep results ──")
    print(df_eps.to_string(index=False))
    plot_epsilon_sensitivity(df_eps, "output/figures/phase5_epsilon_sensitivity.png")

    print("\n=== Phase 5 complete. All outputs in output/ and output/figures/ ===")

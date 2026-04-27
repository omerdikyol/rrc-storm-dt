# Evaluation Scenarios and Metrics

## 1. Simulation Scenarios
The simulation must run two distinct scenarios for direct comparison:
* **Baseline (Reactive):** Standard threshold-based ACB. (e.g., if $Q_{real} > 0.8K$, set $p_{acb} = 0.5$).
* **Proposed (Proactive Calibrated DT):** The Digital Twin runs the unified pipeline to calculate $p_{acb}$ dynamically.

## 2. Data Collection
Log the following metrics at every control interval ($\Delta$):
* Timestamp ($t$).
* Current traffic state (Normal/Burst).
* $Q_{real}$ and $Q_{virtual}$.
* State Mirroring Error ($E$).
* Applied $p_{acb}$.
* Cumulative legitimate UE successes.
* Cumulative legitimate UE drops.

## 3. Required Output Plots (For IEEE Paper)
* **Queue Stability:** Time-series plot showing $Q_{real}$ vs. Time for both scenarios against the capacity limit $K$.
* **Model Fidelity:** Time-series plot of $Q_{real}$ vs. $Q_{virtual}$ showing the effectiveness of the calibration loop.
* **Success Probability:** Bar chart comparing total access success probability of legitimate UEs between the Baseline and Proposed scenarios.
* **Delay:** CDF (Cumulative Distribution Function) of connection setup delays.
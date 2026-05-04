# Unified Pipeline: Prediction, Calibration, and Control

The Digital Twin operates as a continuous, unified pipeline executing at defined interval steps ($t$).

## Phase 1: Observation & Prediction
1.  Read current physical queue length ($Q_{real}$) from the simulation.
2.  Observe the incoming arrival rate ($\lambda_{current}$).
3.  Forecast the future arrival rate $\lambda(t+\Delta)$ using an Exponential Moving Average (EMA).

## Phase 2: Control Decision
1.  Using $Q_{real}$ and the EMA-predicted arrival rate, calculate the stochastic Access Class Barring probability ($p_{acb}$) required to keep the physical queue below capacity $K$.
2.  Apply $p_{acb}$ to the gNB simulation as the proactive request barring rate.
3.  Update the DT virtual queue ($Q_{virtual}$) using the post-barring admitted arrival estimate.

## Phase 3: Continuous Calibration Loop
1.  Calculate State Mirroring Error: $E = |Q_{real} - Q_{virtual}|$.
2.  **Calibration Trigger:** If $E > \epsilon$ (tolerance threshold), increase the EMA weight ($\alpha$) to prioritize recent observations.
3.  If $E \leq \epsilon$, slowly decrease $\alpha$ to preserve normal-traffic smoothing stability.

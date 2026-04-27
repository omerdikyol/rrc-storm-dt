# Unified Pipeline: Prediction, Calibration, and Control

The Digital Twin operates as a continuous, unified pipeline executing at defined interval steps ($t$).

## Phase 1: Observation & Prediction
1.  Read current physical queue length ($Q_{real}$) from the simulation.
2.  Observe the incoming arrival rate ($\lambda_{current}$).
3.  Forecast the future arrival rate $\lambda(t+\Delta)$ using an Exponential Moving Average (EMA).

## Phase 2: Continuous Calibration Loop
1.  Calculate expected virtual queue length ($Q_{virtual}$) based on the DT's internal model.
2.  Calculate State Mirroring Error: $E = |Q_{real} - Q_{virtual}|$.
3.  **Calibration Trigger:** If $E > \epsilon$ (tolerance threshold), update the EMA weight ($\alpha$) and internal service rate assumptions to resynchronize the DT with physical reality.

## Phase 3: Control Decision
1.  Using the calibrated $\lambda(t+\Delta)$, calculate the expected future queue length.
2.  If expected queue exceeds capacity $K$, calculate the exact stochastic Access Class Barring probability ($p_{acb}$) required to stabilize the queue.
3.  Apply $p_{acb}$ to the gNB simulation to drop incoming requests proactively.
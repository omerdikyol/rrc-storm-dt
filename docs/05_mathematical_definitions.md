# Mathematical Definitions

## 1. MMPP Traffic Generation
The attacker traffic follows a 2-state Continuous-Time Markov Chain (CTMC):
* $S_0$ (Normal State): Generates legitimate RRC requests at rate $\lambda_{legit}$.
* $S_1$ (Burst State): Generates adversarial RRC requests at rate $\lambda_{attack}$.
* Transition Probabilities: Defined by a generator matrix $Q$, dictating the duration spent in each state.

## 2. Arrival Rate Forecasting
The Digital Twin predicts the future arrival rate using an Exponential Moving Average (EMA):
$$EMA_t = \alpha \cdot \lambda_{current} + (1 - \alpha) \cdot EMA_{t-1}$$
* $\lambda_{current}$: The actual observed arrival rate at time $t$.
* $\alpha$: The prediction weight (smoothing factor), bounded between $[0, 1]$.

## 3. Continuous Calibration Loop
The DT calculates the state mirroring error:
$$E = |Q_{real} - Q_{virtual}|$$
* If $E > \epsilon$ (the tolerance threshold), the DT assumes model drift.
* [cite_start]Calibration Action: Autonomously adjust $\alpha$ (e.g., increase $\alpha$ to prioritize recent observations) to force $Q_{virtual}$ to converge with $Q_{real}$[cite: 9, 10].

## 4. Access Class Barring ($p_{acb}$) Calculation
To prevent the physical queue ($Q_{real}$) from exceeding capacity ($K$) in the next time step ($\Delta$), the required dropping probability is:
$$p_{acb} = \max\left(0, 1 - \frac{K - Q_{real}}{EMA_t \cdot \Delta}\right)$$
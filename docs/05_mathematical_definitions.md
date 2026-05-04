# Mathematical Definitions

## 1. MMPP Traffic Generation
The aggregate RRC request traffic follows a 2-state Continuous-Time Markov Chain (CTMC):
* $S_0$ (Normal State): Generates aggregate RRC requests at rate $\lambda_{low}$.
* $S_1$ (Burst State): Generates aggregate RRC requests at rate $\lambda_{high}$.
* Transition rates are defined by the CTMC generator matrix $Q$, with $\alpha_{mmpp}$ for $S_0 \rightarrow S_1$ and $\beta_{mmpp}$ for $S_1 \rightarrow S_0$.

## 2. Arrival Rate Forecasting
The Digital Twin predicts the future arrival rate using an Exponential Moving Average (EMA):
$$EMA_t = \alpha \cdot \lambda_{current} + (1 - \alpha) \cdot EMA_{t-1}$$
* $\lambda_{current}$: The actual observed arrival rate at time $t$.
* $\alpha$: The prediction weight (smoothing factor), bounded between $[0, 1]$.

## 3. Access Class Barring ($p_{acb}$) Calculation
To prevent the physical queue ($Q_{real}$) from exceeding capacity ($K$) in the next time step ($\Delta$), the required dropping probability is:
$$p_{acb} = \max\left(0, \min\left(1, 1 - \frac{K - Q_{real}}{\max(EMA_t \cdot \Delta, 10^{-9})}\right)\right)$$

## 4. Virtual Queue Update
After applying $p_{acb}$, the DT updates its virtual queue using the post-barring admitted arrival estimate:
$$Q_{virtual}(t+\Delta)=\mathrm{clip}\left(Q_{virtual}(t)+EMA_t(1-p_{acb})\Delta-c\Delta,\ 0,\ K\right)$$

## 5. Continuous Calibration Loop
The DT calculates the state mirroring error:
$$E = |Q_{real} - Q_{virtual}|$$
* If $E > \epsilon$ (the tolerance threshold), the DT assumes model drift.
* Calibration Action: increase $\alpha$ to prioritize recent observations when $E > \epsilon$; otherwise decay $\alpha$ slowly to preserve smoothing stability.

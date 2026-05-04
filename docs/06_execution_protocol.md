# Autonomous Execution Protocol

You have full autonomous control to read files, write code, execute scripts, and search the web. Execute the project in the following strict phases. 

**Mandatory Research Step:** Before writing code for any phase, you MUST search the internet to:
1. Validate the mathematical formulas (e.g., MMPP properties, EMA stability in queuing).
2. Locate and review standard open-source Python/SimPy implementations to accelerate development and ensure best practices.

## Phase 1: Traffic & Baseline Queue
* **Action:** Research standard open-source $MMPP/M/c/K$ queue implementations in Python.
* **Implement:** Write a `simpy` script containing the 2-state MMPP Traffic Generator and the physical gNB queue. Do not add the Digital Twin.
* **Test:** Run a 100-second simulation. Execute the script and verify the queue fills under burst traffic. Log the output.

## Phase 2: Reactive Baseline
* **Implement:** Add a standard reactive controller (if $Q_{real} > 0.8K$, drop 50% of traffic). 
* **Test:** Execute the simulation and log connection success rates and drops. This establishes the baseline performance.

## Phase 3: Digital Twin Integration
* **Action:** Research academic literature on applying Exponential Moving Averages (EMA) to network traffic forecasting, and document whether any cited source actually supports the selected $\alpha$ value. If not, treat $\alpha_0$ as an empirical simulation parameter.
* **Implement:** Build the `DigitalTwinController` running in parallel. Implement EMA forecasting and the $p_{acb}$ formula from Document 05.
* **Test:** Execute the simulation. Log the state mirroring error ($E$) over time.

## Phase 4: Calibration Loop & Evaluation
* **Implement:** Add the continuous calibration loop (if $E > \epsilon$, adjust $\alpha$).
* **Evaluate:** Run both the Phase 2 Baseline and the Phase 4 Calibrated DT side-by-side. 
* **Output:** Generate and save `matplotlib` graphs comparing Queue Stability and Connection Success Rates.

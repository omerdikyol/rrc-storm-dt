# Implementation Specifications

## 1. Environment & Libraries
* Python 3.10+
* `simpy`: Discrete-event simulation engine.
* `numpy` / `scipy`: Statistical distributions and math.
* `pandas` / `matplotlib`: Data logging and visualization.

## 2. Core Class Architecture
* **`TrafficGenerator`:** Implements the 2-state MMPP. Uses a continuous-time Markov chain to switch between 'Normal' ($\lambda_{low}$) and 'Burst' ($\lambda_{high}$) states. Generates connection request events.
* **`gNB_Queue`:** Represents the physical network. Implements the $M/c/K$ queue logic. Tracks $Q_{real}$, total requests, dropped requests, and successful connections.
* **`DigitalTwinController`:** Runs in parallel. Contains the unified pipeline (Prediction -> Calibration -> Control). Reads $Q_{real}$, calculates $p_{acb}$, and updates the `gNB_Queue` barring rate.

## 3. Simulation Parameters (Initial Tuning)
* Simulation time: 1000 seconds.
* $c$ (Preambles): 54.
* $K$ (Buffer limit): 200.
* $\lambda_{low}$: 10 requests/sec.
* $\lambda_{high}$: 500 requests/sec.
* $\epsilon$ (Calibration tolerance): 10.
* Control interval ($\Delta$): 1 second.

## 4. Open-Source Integration
* Prioritize leveraging existing, legally permissible open-source Python code for standard queueing models ($M/M/c$) and mathematical functions.
* When adapting open-source code for the MMPP generator or EMA forecaster, ensure the variables are renamed and structured to align strictly with the mathematical definitions in this project.
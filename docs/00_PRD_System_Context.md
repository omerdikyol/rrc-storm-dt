# Product Requirements Document (PRD)
## Project Title
Predictive Digital Twin with Continuous Calibration for 5G RRC Signaling Storm Mitigation.

## 1. Core Objectives
* Simulate a 5G gNodeB (gNB) Random Access Channel (RACH) under an RRC signaling storm.
* Mitigate the storm using a proactive Digital Twin featuring a continuous calibration loop.
* Prove that maintaining state mirroring fidelity prevents the model drift seen in standard predictive controllers.

## 2. System Architecture
* **Traffic Model:** $MMPP/M/c/K$ (Markov-Modulated Poisson Process) queue to capture burst dynamics.
* **Digital Twin:** Autonomously calibrates prediction weights based on mirroring error before calculating and applying optimal stochastic Access Class Barring probability ($p_{acb}$).

## 3. Implementation Constraints & Allowances
* **Language:** Python 3.10+
* **Core Library:** `simpy` (strict requirement: no complex network stacks like ns-3 or OAI).
* **Code Style:** Procedural or lightweight Object-Oriented. Keep logic explicit. Do not over-engineer with abstract base classes.
* **Open Source Utilization:** It is explicitly permitted to reference, adapt, and integrate open-source mathematical formulas, queueing theory implementations, and SimPy examples, provided they are academically and legally clear for use. Existing open-source snippets for MMPP or EMA generation should be utilized to accelerate development.
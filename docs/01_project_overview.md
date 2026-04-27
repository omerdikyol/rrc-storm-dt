# Project Overview: Predictive DT for 5G RRC Storm Mitigation

## 1. Project Objective
Develop a Python-based discrete-event simulation (using SimPy) of a 5G gNodeB (gNB) Random Access Channel (RACH) under an RRC signaling storm. Mitigate the storm using a Predictive Digital Twin (DT) equipped with a continuous calibration loop.

## 2. Technical Challenge
Adversarial 5G RRC signaling storms use highly correlated, bursty traffic to exhaust gNB baseband resources. Standard reactive Access Class Barring (ACB) fails due to control-loop latency. Predictive controllers suffer from model drift when attack patterns change abruptly.

## 3. Mathematical Model
* **Queueing System:** $MMPP/M/c/K$ (Markov-Modulated Poisson Process).
    * $MMPP$: Represents the correlated burst dynamics of a botnet (Normal vs. Attack states).
    * $c$: Total available RACH preambles (servers).
    * $K$: Maximum RRC connection buffer capacity.
* **Objective Function:** $\max \left( P_{success} - \omega_1 \cdot E - \omega_2 \cdot P_{drop} \right)$
    * $P_{success}$: Legitimate connection success rate.
    * $E$: State mirroring error between physical queue and DT queue.
    * $P_{drop}$: Packet drop rate.

## 4. Expected Output
A simulation script outputting comparative CSV data and time-series plots demonstrating the superiority of the Calibrated Predictive DT over a standard reactive threshold mechanism.
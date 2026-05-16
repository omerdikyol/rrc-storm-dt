# Predictive Digital Twin for 5G RRC Storm Mitigation

Course project for BLG 632E (Next Generation Wireless Networks).

Python/SimPy simulation project for modeling and mitigating 5G RRC signaling storms using a calibrated predictive Digital Twin (DT).

## Overview

This repository implements a phased simulation pipeline:

1. Traffic and queue baseline (`MMPP/M/c/K` without mitigation)
2. Reactive baseline controller (threshold-based ACB)
3. Predictive DT controller (EMA-based forecasting)
4. Calibrated predictive DT (adaptive EMA via mirroring error)
5. Academic evaluation layer (multi-seed CI, delay CDF, epsilon sweep)

Primary objective:

$$
\max\left(P_{success} - \omega_1 \cdot E - \omega_2 \cdot P_{drop}\right)
$$

Where:

- $P_{success}$ is successful connection ratio
- $E = |Q_{real} - Q_{virtual}|$ is DT mirroring error
- $P_{drop}$ is dropped request ratio

## Experiment Goal

The experiment evaluates whether a calibrated predictive Digital Twin can reduce queue instability and packet drops during bursty/adversarial RRC signaling conditions, compared with:

- no mitigation
- a standard reactive threshold policy
- an uncalibrated predictive DT

The core research question is: can continuous calibration improve robustness when traffic dynamics shift and model drift appears?

## Methodology

The simulation models gNB random access behavior as an MMPP-driven queueing system and applies control in increasing sophistication across phases.

1. Model bursty arrivals with a 2-state MMPP (normal and burst states).
2. Simulate gNB queue/service under finite capacity constraints.
3. Apply reactive ACB (threshold policy) as baseline control.
4. Apply predictive ACB via DT with EMA-based arrival forecasting.
5. Add adaptive calibration loop using mirroring error trigger $E > \epsilon$.

The calibrated controller increases EMA responsiveness when drift is high, and relaxes it when mirroring is stable.

## Experiment Protocol

The end-to-end protocol follows five executable phases:

1. Phase 1 establishes unmitigated congestion behavior.
2. Phase 2 builds reactive baseline metrics.
3. Phase 3 introduces predictive DT without calibration.
4. Phase 4 compares reactive, uncalibrated DT, and calibrated DT.
5. Phase 5 adds academic rigor with multi-seed confidence intervals, delay CDF analysis, and epsilon sensitivity.

Primary evaluation dimensions:

- connection success rate
- drop rate
- queue stability and overflow tendency
- DT mirroring error $E$
- objective score trend under parameter sweeps

## Repository Structure

- `simulation/`: runnable simulation phases and shared core modules
- `docs/`: project design, math, and execution specifications
- `output/`: generated CSV outputs and figures
- `paper/`: IEEE manuscript sources
- `presentation/`: presentation assets

## Requirements

- Python 3.10+
- Packages listed in `requirements.txt`

Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Quick Start

Run from repository root:

```bash
python simulation/phase1_traffic_queue.py
python simulation/phase2_reactive_baseline.py
python simulation/phase3_digital_twin.py
python simulation/phase4_calibrated_dt.py
python simulation/phase5_academic_eval.py
```

Each script sets its own working directory to the project root internally, so these commands can be run from anywhere as long as the relative script path is valid.

## Phase Outputs

- Phase 1: `output/phase1_queue.csv`
- Phase 2: `output/phase2_baseline.csv`
- Phase 3: `output/phase3_dt.csv`
- Phase 4: `output/phase4_comparison.csv` and figures under `output/figures/`
- Phase 5: `output/sensitivity_epsilon.csv` and CI/CDF/sensitivity figures under `output/figures/`

Common figure files include:

- `output/figures/phase4_queue_stability.png`
- `output/figures/phase4_success_rate.png`
- `output/figures/phase4_mirroring_error.png`
- `output/figures/phase4_ema_alpha.png`
- `output/figures/phase5_q_real_ci.png`
- `output/figures/phase5_success_ci.png`
- `output/figures/phase5_E_ci.png`
- `output/figures/phase5_delay_cdf.png`
- `output/figures/phase5_epsilon_sensitivity.png`

## Core Simulation Defaults

From `simulation/config.py`:

- `SIM_TIME = 1000` seconds (`SIM_TIME_TEST = 100` for Phase 1)
- Queue model: `c = 54`, `K = 200`
- MMPP rates: `lambda_low = 10`, `lambda_high = 500`
- Calibration threshold: `epsilon = 10.0`

Adjust these values in `simulation/config.py` for custom experiments.

## Documentation Map

- `docs/00_PRD_System_Context.md`
- `docs/01_project_overview.md`
- `docs/02_unified_pipeline.md`
- `docs/03_implementation_spec.md`
- `docs/04_evaluation_and_metrics.md`
- `docs/05_mathematical_definitions.md`
- `docs/06_execution_protocol.md`

## Paper and Presentation Workflow

This repository is organized to support both implementation and final course deliverables.

- `paper/` contains IEEE-format manuscript sources and versions used for reporting the method and results.
- `presentation/` contains slide source and compiled presentation files for the oral defense.

Recommended workflow:

1. Run Phase 4 and Phase 5 experiments to generate final CSVs/figures.
2. Use `output/` artifacts directly in the Results and Discussion sections of the paper.
3. Reuse the same figures/metrics in the presentation to keep narrative consistency between written and oral deliverables.

## Notes

- The project is simulation-first and intended for reproducible academic evaluation.
- `phase5_academic_eval.py` is the most complete experiment entry point when you need confidence intervals and sensitivity analysis.
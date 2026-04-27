"""
Shared simulation primitives for all phases.

All parameters sourced from config.py — this module is the single
authoritative definition of TrafficGenerator, GNBQueue,
ReactiveController, and DigitalTwinController.
"""

import simpy
import numpy as np

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from config import (
    C, K, LAMBDA_LOW, LAMBDA_HIGH,
    ALPHA_MMPP, BETA_MMPP,
    DELTA, EPSILON,
    EMA_ALPHA_INIT, EMA_ALPHA_MIN, EMA_ALPHA_MAX,
    EMA_ALPHA_INCREASE, EMA_ALPHA_DECREASE,
    REACTIVE_THRESHOLD, REACTIVE_DROP_RATE,
)


class TrafficGenerator:
    """2-state MMPP traffic source.

    CTMC generator matrix Q = [[-α, α], [β, -β]].
    Sojourn in state i ~ Exp(|Q[i,i]|); arrivals within sojourn ~ Poisson(λ_i).
    Implemented via sojourn-time sampling — exact for CTMC, no matrix exponential needed.
    """

    def __init__(self, env, gnb, rng):
        self.env = env
        self.gnb = gnb
        self.rng = rng
        self.state = 0  # 0 = Normal, 1 = Burst

    def _lambda(self):
        return LAMBDA_LOW if self.state == 0 else LAMBDA_HIGH

    def run(self):
        while True:
            rate = ALPHA_MMPP if self.state == 0 else BETA_MMPP
            sojourn = self.rng.exponential(1.0 / rate)
            state_end = self.env.now + sojourn
            lam = self._lambda()

            while self.env.now < state_end:
                ia = self.rng.exponential(1.0 / lam)
                if self.env.now + ia > state_end:
                    yield self.env.timeout(state_end - self.env.now)
                    break
                yield self.env.timeout(ia)
                self.env.process(self.gnb.submit_request(self.env.now))

            self.state ^= 1


class GNBQueue:
    """Physical gNB RACH as M/c/K finite-capacity queue.

    c preamble channels (servers), buffer limit K.
    drop_rate [0,1] set externally by whichever controller is active.
    delay_log records per-request queueing delay for CDF analysis.
    """

    def __init__(self, env, rng):
        self.env = env
        self.rng = rng
        self.resource = simpy.Resource(env, capacity=C)

        self.total = 0
        self.dropped = 0
        self.served = 0
        self.arrivals_in_window = 0
        self.drop_rate = 0.0

        self.delay_log: list[float] = []

    @property
    def q_real(self):
        return self.resource.count + len(self.resource.queue)

    def reset_window_counter(self):
        self.arrivals_in_window = 0

    def submit_request(self, arrival_time):
        self.total += 1
        self.arrivals_in_window += 1

        if self.q_real >= K:
            self.dropped += 1
            return

        if self.rng.random() < self.drop_rate:
            self.dropped += 1
            return

        with self.resource.request() as req:
            yield req
            queue_delay = self.env.now - arrival_time
            self.delay_log.append(queue_delay)
            yield self.env.timeout(self.rng.exponential(1.0))
            self.served += 1


class ReactiveController:
    """Threshold-based ACB: if Q_real > 0.8K apply 50% drop rate."""

    def __init__(self, env, gnb):
        self.env = env
        self.gnb = gnb

    def run(self):
        while True:
            yield self.env.timeout(DELTA)
            self.gnb.drop_rate = (
                REACTIVE_DROP_RATE if self.gnb.q_real > REACTIVE_THRESHOLD else 0.0
            )


class DigitalTwinController:
    """Predictive DT with EMA forecasting and ACB control.

    calibrate=True  → Phase 4 behaviour: α adjusted when E > epsilon.
    calibrate=False → Phase 3 behaviour: α fixed at EMA_ALPHA_INIT.
    """

    def __init__(self, env, gnb, epsilon=EPSILON, calibrate=True):
        self.env = env
        self.gnb = gnb
        self.epsilon = epsilon
        self.calibrate = calibrate

        self.ema_alpha = EMA_ALPHA_INIT
        self.ema_t = LAMBDA_LOW   # warm-start at normal-state rate
        self.q_virtual = 0.0
        self.p_acb = 0.0

    def _update_alpha(self, E):
        if not self.calibrate:
            return
        if E > self.epsilon:
            self.ema_alpha = min(EMA_ALPHA_MAX, self.ema_alpha + EMA_ALPHA_INCREASE)
        else:
            self.ema_alpha = max(EMA_ALPHA_MIN, self.ema_alpha - EMA_ALPHA_DECREASE)

    def run(self):
        while True:
            yield self.env.timeout(DELTA)

            lam_cur = self.gnb.arrivals_in_window / DELTA
            self.gnb.reset_window_counter()

            self.ema_t = self.ema_alpha * lam_cur + (1.0 - self.ema_alpha) * self.ema_t

            denom = max(self.ema_t * DELTA, 1e-9)
            self.p_acb = max(0.0, min(1.0, 1.0 - (K - self.gnb.q_real) / denom))
            self.gnb.drop_rate = self.p_acb

            eff_arrivals = self.ema_t * (1.0 - self.p_acb)
            self.q_virtual = max(0.0, min(K,
                self.q_virtual + eff_arrivals * DELTA - C * DELTA))

            E = abs(self.gnb.q_real - self.q_virtual)
            self._update_alpha(E)

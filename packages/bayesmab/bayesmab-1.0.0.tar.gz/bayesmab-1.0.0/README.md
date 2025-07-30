# BayesMAB

Bayesian Multi-Armed Bandit with adaptive Thompson Sampling, suitable for A/B testing and real-time decision-making.

## Install

```bash
pip install bayesmab
```

## Usage Example
An example script is included in the examples/ directory.

You can run it with:
```bash
python examples/run_bernoulli_bandit.py
```
The example initializes a bandit with three arms, each simulating a different true conversion rate. It uses:

- Thompson Sampling to allocate "traffic" to each arm based on uncertainty

- Updates posterior beliefs as binary rewards are observed

- Tracks and visualizes:

    - Posterior distributions

    - Posterior mean estimates over time

    - Cumulative regret

    - Traffic allocation per arm

This simulates an A/B/n test where better-performing variants gradually receive more attention, showing how Bayesian bandits adaptively optimize decisions under uncertainty.

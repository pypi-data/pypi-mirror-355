import numpy as np
from collections import defaultdict
import matplotlib.pyplot as plt
from scipy.stats import beta

class BayesianBandit:
    def __init__(self, arms, true_rates=None):
        """
        Initialize the Bayesian MAB with a list of arm names.
        Each arm starts with a uniform prior: Beta(1, 1)
        """
        self.arms = arms
        self.alpha = defaultdict(lambda: 1)
        self.beta = defaultdict(lambda: 1)
        self.true_rates = true_rates  # used for regret calculation

        self.counts = defaultdict(int)
        self.regret_history = []
        self.traffic_history = {arm: [] for arm in arms}
        self.posterior_means = {arm: [] for arm in arms}

    def sample(self):
        samples = {
            arm: np.random.beta(self.alpha[arm], self.beta[arm])
            for arm in self.arms
        }
        best_arm = max(samples, key=samples.get)
        return best_arm, samples

    def update(self, arm, reward):
        if reward == 1:
            self.alpha[arm] += 1
        else:
            self.beta[arm] += 1

        self.counts[arm] += 1

        # Regret tracking (if ground truth is known)
        if self.true_rates:
            optimal_reward = max(self.true_rates.values())
            observed_reward = self.true_rates[arm]
            regret = optimal_reward - observed_reward
            self.regret_history.append(regret)

        # Traffic tracking
        for a in self.arms:
            self.traffic_history[a].append(self.counts[a])

        # Posterior mean tracking
        for a in self.arms:
            mean = self.alpha[a] / (self.alpha[a] + self.beta[a])
            self.posterior_means[a].append(mean)

    def get_posteriors(self):
        return {arm: (self.alpha[arm], self.beta[arm]) for arm in self.arms}

    def get_prob_best(self, num_simulations=10000):
        wins = {arm: 0 for arm in self.arms}
        for _ in range(num_simulations):
            sampled_thetas = {
                arm: np.random.beta(self.alpha[arm], self.beta[arm])
                for arm in self.arms
            }
            winner = max(sampled_thetas, key=sampled_thetas.get)
            wins[winner] += 1
        return {arm: wins[arm] / num_simulations for arm in self.arms}

    def plot_posteriors(self):
        x = np.linspace(0, 0.2, 1000)
        plt.figure(figsize=(10, 5))
        for arm in self.arms:
            a, b = self.alpha[arm], self.beta[arm]
            y = beta.pdf(x, a, b)
            plt.plot(x, y, label=f"{arm} (α={a}, β={b})")
        plt.title("Posterior Distributions")
        plt.xlabel("Conversion Rate")
        plt.ylabel("Density")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def plot_posterior_means(self):
        plt.figure(figsize=(10, 5))
        for arm in self.arms:
            plt.plot(self.posterior_means[arm], label=f"Arm {arm}")
        if self.true_rates:
            for arm, rate in self.true_rates.items():
                plt.axhline(rate, linestyle="--", alpha=0.3, label=f"{arm} true rate")
        plt.title("Posterior Mean Estimates Over Time")
        plt.xlabel("Rounds")
        plt.ylabel("Estimated Conversion Rate")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def plot_regret(self):
        if self.regret_history:
            cumulative_regret = np.cumsum(self.regret_history)
            plt.figure(figsize=(10, 5))
            plt.plot(cumulative_regret)
            plt.title("Cumulative Regret Over Time")
            plt.xlabel("Rounds")
            plt.ylabel("Cumulative Regret")
            plt.grid(True)
            plt.tight_layout()
            plt.show()
        else:
            print("regret_history not tracked. True Rates not specified.")

    def plot_traffic_allocation(self):
        plt.figure(figsize=(10, 5))
        for arm in self.arms:
            plt.plot(self.traffic_history[arm], label=f"Arm {arm}")
        plt.title("Traffic Allocation Over Time")
        plt.xlabel("Rounds")
        plt.ylabel("Cumulative Selections")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

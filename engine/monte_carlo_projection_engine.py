# engine/monte_carlo_projection_engine.py
# L18

import random


class MonteCarloProjectionEngine:

    def __init__(
        self,
        current_price,
        volatility=0.002,
        steps=30,
        simulations=200,
        bias=0
    ):
        """
        current_price : latest price
        volatility    : expected move per step
        steps         : projection steps
        simulations   : number of paths
        bias          : directional bias (-1 to +1)
        """

        self.current_price = current_price
        self.volatility = volatility
        self.steps = steps
        self.simulations = simulations
        self.bias = bias

    # =====================================================
    # SINGLE PATH SIMULATION
    # =====================================================

    def _simulate_path(self):

        price = self.current_price
        path = [price]

        for _ in range(self.steps):

            drift = self.bias * self.volatility
            shock = random.gauss(0, self.volatility)

            price = price * (1 + drift + shock)

            path.append(price)

        return path

    # =====================================================
    # GENERATE ALL SIMULATIONS
    # =====================================================

    def generate_paths(self):

        simulations = []

        for _ in range(self.simulations):
            simulations.append(self._simulate_path())

        return simulations

    # =====================================================
    # BUILD PROBABILITY CONE
    # =====================================================

    def build_probability_cone(self):

        paths = self.generate_paths()

        cone = []

        for step in range(self.steps + 1):

            prices = [path[step] for path in paths]

            prices.sort()

            lower = prices[int(len(prices) * 0.1)]
            median = prices[int(len(prices) * 0.5)]
            upper = prices[int(len(prices) * 0.9)]

            cone.append({
                "step": step,
                "lower": lower,
                "median": median,
                "upper": upper
            })

        return {
            "paths": paths,
            "cone": cone
        }
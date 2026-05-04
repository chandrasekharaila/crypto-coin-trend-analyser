# engine/liquidity_heatmap_engine.py
# L19

import numpy as np


class LiquidityHeatmapEngine:

    def __init__(
        self,
        df,
        zones,
        equal_liquidity,
        session_levels,
        imbalances,
        bins=60
    ):

        self.df = df
        self.zones = zones
        self.equal_liquidity = equal_liquidity
        self.session_levels = session_levels
        self.imbalances = imbalances
        self.bins = bins

    # =====================================================
    # COLLECT ALL LIQUIDITY LEVELS
    # =====================================================

    def _collect_levels(self):

        levels = []

        # Zones
        for zone in self.zones["resistance"][:3]:
            levels.append((zone["zone_low"], 2))
            levels.append((zone["zone_high"], 2))

        for zone in self.zones["support"][:3]:
            levels.append((zone["zone_low"], 2))
            levels.append((zone["zone_high"], 2))

        # Equal highs/lows
        for pool in self.equal_liquidity["buy_side"][:3]:
            if not pool["swept"]:
                levels.append((pool["mid_price"], 1.5))

        for pool in self.equal_liquidity["sell_side"][:3]:
            if not pool["swept"]:
                levels.append((pool["mid_price"], 1.5))

        # Session liquidity
        for level in self.session_levels.values():
            if not level["swept"]:
                levels.append((level["price"], 2))

        # Imbalances
        for imb in self.imbalances[:3]:
            if not imb["mitigated"]:
                mid = (imb["zone_low"] + imb["zone_high"]) / 2
                levels.append((mid, 1))

        return levels

    # =====================================================
    # BUILD HEATMAP
    # =====================================================

    def generate_heatmap(self):

        df = self.df.tail(200)

        price_min = df["low"].min()
        price_max = df["high"].max()

        bins = np.linspace(price_min, price_max, self.bins)

        heat = np.zeros(len(bins))

        levels = self._collect_levels()

        for price, weight in levels:

            idx = np.argmin(np.abs(bins - price))

            heat[idx] += weight

        return {
            "bins": bins,
            "heat": heat
        }
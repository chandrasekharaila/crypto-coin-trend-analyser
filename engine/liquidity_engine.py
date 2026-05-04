# engine/liquidity_engine.py
#L4
import numpy as np


class LiquidityEngine:
    def __init__(
        self,
        df,
        swings,
        timeframe,
        liquidity_multiplier=0.25,
        decay_factor=60,
    ):
        self.df = df
        self.swings = swings
        self.timeframe = timeframe
        self.liquidity_multiplier = liquidity_multiplier
        self.decay_factor = decay_factor

        self.atr_mean = self.df["atr"].mean()
        self.threshold = self.atr_mean * self.liquidity_multiplier

        self.buy_side_liquidity = []
        self.sell_side_liquidity = []

        self._build_liquidity_pools()
        self._apply_decay()
        self._detect_sweeps()
        self.imbalance_ratio = self._calculate_imbalance()

    # =====================================================
    # BUILD LIQUIDITY POOLS (SWING-BASED)
    # =====================================================

    def _build_liquidity_pools(self):
        highs = [s for s in self.swings if s["type"] == "high"]
        lows = [s for s in self.swings if s["type"] == "low"]

        self.buy_side_liquidity = self._cluster(highs, "buy")
        self.sell_side_liquidity = self._cluster(lows, "sell")

    def _cluster(self, swing_list, side):
        pools = []

        for swing in swing_list:
            price = swing["price"]
            timestamp = swing["timestamp"]

            matched = False

            for pool in pools:
                if abs(price - pool["mid_price"]) <= self.threshold:
                    pool["touches"] += 1
                    pool["last_touch"] = timestamp
                    pool["mid_price"] = (
                        pool["mid_price"] * (pool["touches"] - 1) + price
                    ) / pool["touches"]
                    matched = True
                    break

            if not matched:
                pools.append({
                    "side": side,
                    "mid_price": price,
                    "touches": 1,
                    "last_touch": timestamp,
                    "strength": 0.0,
                    "swept": False,
                })

        return pools

    # =====================================================
    # DECAY LOGIC
    # =====================================================

    def _apply_decay(self):
        total_bars = len(self.df)

        for pool in self.buy_side_liquidity + self.sell_side_liquidity:
            bars_since_touch = (
                total_bars - self.df.index.get_loc(pool["last_touch"])
            )

            recency_score = 1 / (1 + bars_since_touch / self.decay_factor)
            normalized_touches = pool["touches"] / max(1, pool["touches"])

            pool["strength"] = round(
                min(1.0, 0.6 * normalized_touches + 0.4 * recency_score),
                3,
            )

    # =====================================================
    # SWEEP DETECTION
    # =====================================================

    def _detect_sweeps(self):
        last_price = self.df["close"].iloc[-1]
        sweep_threshold = self.atr_mean * 0.5

        for pool in self.buy_side_liquidity:
            if last_price > pool["mid_price"] + sweep_threshold:
                pool["swept"] = True
                pool["strength"] *= 0.3  # Reduce strength after sweep

        for pool in self.sell_side_liquidity:
            if last_price < pool["mid_price"] - sweep_threshold:
                pool["swept"] = True
                pool["strength"] *= 0.3

    # =====================================================
    # LIQUIDITY IMBALANCE
    # =====================================================

    def _calculate_imbalance(self):
        total_buy = sum(p["strength"] for p in self.buy_side_liquidity)
        total_sell = sum(p["strength"] for p in self.sell_side_liquidity)

        if total_sell == 0:
            return float("inf")

        return round(total_buy / total_sell, 3)

    # =====================================================
    # PUBLIC OUTPUT
    # =====================================================

    def get_liquidity(self):
        return {
            "buy_side": sorted(
                self.buy_side_liquidity,
                key=lambda x: x["strength"],
                reverse=True,
            ),
            "sell_side": sorted(
                self.sell_side_liquidity,
                key=lambda x: x["strength"],
                reverse=True,
            ),
            "imbalance_ratio": self.imbalance_ratio,
        }
# engine/liquidity_imbalance_engine.py
#L6

class LiquidityImbalanceEngine:
    def __init__(self, equal_liquidity, session_liquidity):
        self.equal_liquidity = equal_liquidity
        self.session_liquidity = session_liquidity

        self.upside_strength = 0.0
        self.downside_strength = 0.0
        self.imbalance_ratio = 1.0
        self.bias = "Neutral"

        self._compute_strength()
        self._compute_bias()

    # =====================================================
    # STRENGTH CALCULATION
    # =====================================================

    def _compute_strength(self):

        # Equal Liquidity (L4)
        for pool in self.equal_liquidity["buy_side"]:
            if not pool["swept"]:
                self.upside_strength += pool["strength"] * 1.0

        for pool in self.equal_liquidity["sell_side"]:
            if not pool["swept"]:
                self.downside_strength += pool["strength"] * 1.0

        # Session Liquidity (L5)
        for level in self.session_liquidity.values():
            if level["swept"]:
                continue

            if level["type"] == "buy_liquidity":
                self.upside_strength += 1.2

            elif level["type"] == "sell_liquidity":
                self.downside_strength += 1.2

        if self.downside_strength == 0:
            self.imbalance_ratio = float("inf")
        else:
            self.imbalance_ratio = round(
                self.upside_strength / self.downside_strength, 3
            )

    # =====================================================
    # BIAS INTERPRETATION
    # =====================================================

    def _compute_bias(self):

        if self.imbalance_ratio > 1.2:
            self.bias = "Upside Liquidity Heavy"

        elif self.imbalance_ratio < 0.8:
            self.bias = "Downside Liquidity Heavy"

        else:
            self.bias = "Balanced"

    # =====================================================
    # PUBLIC
    # =====================================================

    def get_liquidity_bias(self):
        return {
            "upside_strength": round(self.upside_strength, 3),
            "downside_strength": round(self.downside_strength, 3),
            "imbalance_ratio": self.imbalance_ratio,
            "bias": self.bias,
        }
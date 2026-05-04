# engine/valuation_engine.py
#l2

class PremiumDiscountEngine:
    def __init__(self, df, swings):
        self.df = df
        self.swings = swings

        self.range_high = None
        self.range_low = None
        self.equilibrium = None
        self.current_position = "Neutral"

        self._compute_range()

    # =====================================================
    # RANGE COMPUTATION
    # =====================================================

    def _compute_range(self):

        highs = [s for s in self.swings if s["type"] == "high"]
        lows = [s for s in self.swings if s["type"] == "low"]

        if not highs or not lows:
            return

        last_high = highs[-1]["price"]
        last_low = lows[-1]["price"]

        self.range_high = max(last_high, last_low)
        self.range_low = min(last_high, last_low)

        self.equilibrium = (
            self.range_high + self.range_low
        ) / 2

        current_price = self.df["close"].iloc[-1]

        if current_price > self.equilibrium:
            self.current_position = "Premium"
        elif current_price < self.equilibrium:
            self.current_position = "Discount"
        else:
            self.current_position = "Equilibrium"

    # =====================================================
    # ZONE ALIGNMENT
    # =====================================================

    def classify_zone(self, zone):

        zone_mid = (zone["zone_low"] + zone["zone_high"]) / 2

        if zone_mid > self.equilibrium:
            return "Premium"
        elif zone_mid < self.equilibrium:
            return "Discount"
        else:
            return "Equilibrium"

    # =====================================================
    # PUBLIC
    # =====================================================

    def get_valuation(self):
        return {
            "range_high": self.range_high,
            "range_low": self.range_low,
            "equilibrium": self.equilibrium,
            "current_position": self.current_position,
        }
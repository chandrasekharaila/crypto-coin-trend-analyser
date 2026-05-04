# engine/smart_money_engine.py
# L20

import numpy as np


class SmartMoneyEngine:

    def __init__(self, df, equal_liquidity, imbalances):

        self.df = df
        self.equal_liquidity = equal_liquidity
        self.imbalances = imbalances

    # =====================================================
    # LIQUIDITY SWEEP DETECTION
    # =====================================================

    def _detect_liquidity_sweeps(self):

        sweeps = []

        recent = self.df.tail(20)

        high = recent["high"].max()
        low = recent["low"].min()

        # buy side sweeps
        for pool in self.equal_liquidity["buy_side"]:

            if pool["swept"]:
                sweeps.append({
                    "type": "buy_side_sweep",
                    "price": pool["mid_price"]
                })

        # sell side sweeps
        for pool in self.equal_liquidity["sell_side"]:

            if pool["swept"]:
                sweeps.append({
                    "type": "sell_side_sweep",
                    "price": pool["mid_price"]
                })

        return sweeps

    # =====================================================
    # DISPLACEMENT DETECTION
    # =====================================================

    def _detect_displacement(self):

        df = self.df.tail(30)

        bodies = abs(df["close"] - df["open"])

        avg_body = bodies.mean()

        last = bodies.iloc[-1]

        if last > avg_body * 2:

            direction = "bullish"

            if df["close"].iloc[-1] < df["open"].iloc[-1]:
                direction = "bearish"

            return {
                "displacement": True,
                "direction": direction,
                "strength": last / avg_body
            }

        return None

    # =====================================================
    # IMBALANCE CONFIRMATION
    # =====================================================

    def _imbalance_confirmation(self):

        for imb in self.imbalances:

            if not imb["mitigated"]:
                return True

        return False

    # =====================================================
    # SMART MONEY EVENT
    # =====================================================

    def detect_events(self):

        events = []

        sweeps = self._detect_liquidity_sweeps()

        displacement = self._detect_displacement()

        imbalance = self._imbalance_confirmation()

        if sweeps and displacement:

            for sweep in sweeps:

                strength = "medium"

                if displacement["strength"] > 3:
                    strength = "high"

                events.append({
                    "event": "smart_money_move",
                    "sweep_type": sweep["type"],
                    "price": sweep["price"],
                    "displacement": displacement["direction"],
                    "imbalance_present": imbalance,
                    "strength": strength
                })

        return {
            "events": events
        }
# engine/imbalance_engine.py
# L7
import numpy as np


class ImbalanceEngine:
    def __init__(self, df, atr_multiplier=0.5):
        self.df = df
        self.atr_multiplier = atr_multiplier

        self.atr_mean = self.df["atr"].mean()
        self.min_gap_size = self.atr_mean * self.atr_multiplier

        self.imbalances = []

        self._detect_imbalances()
        self._merge_overlaps()
        self._update_mitigation_status()
        self._score_imbalances()

    # =====================================================
    # DETECT FVG (3-CANDLE LOGIC)
    # =====================================================

    def _detect_imbalances(self):
        df = self.df

        for i in range(2, len(df)):
            c1 = df.iloc[i - 2]
            c2 = df.iloc[i - 1]
            c3 = df.iloc[i]

            # Bullish imbalance
            if c1["high"] < c3["low"]:
                gap_size = c3["low"] - c1["high"]

                if gap_size >= self.min_gap_size:
                    self.imbalances.append({
                        "type": "bullish",
                        "zone_low": c1["high"],
                        "zone_high": c3["low"],
                        "created_at": df.index[i],
                        "mitigated": False,
                        "fill_ratio": 0.0,
                        "strength": 0.0
                    })

            # Bearish imbalance
            if c1["low"] > c3["high"]:
                gap_size = c1["low"] - c3["high"]

                if gap_size >= self.min_gap_size:
                    self.imbalances.append({
                        "type": "bearish",
                        "zone_low": c3["high"],
                        "zone_high": c1["low"],
                        "created_at": df.index[i],
                        "mitigated": False,
                        "fill_ratio": 0.0,
                        "strength": 0.0
                    })

    # =====================================================
    # MERGE OVERLAPPING IMBALANCES
    # =====================================================

    def _merge_overlaps(self):
        self.imbalances.sort(key=lambda x: x["zone_low"])
        merged = []

        for imb in self.imbalances:
            if not merged:
                merged.append(imb)
            else:
                prev = merged[-1]

                if imb["zone_low"] <= prev["zone_high"]:
                    prev["zone_high"] = max(prev["zone_high"], imb["zone_high"])
                else:
                    merged.append(imb)

        self.imbalances = merged

    # =====================================================
    # MITIGATION & FILL TRACKING
    # =====================================================

    def _update_mitigation_status(self):
        last_price = self.df["close"].iloc[-1]

        for imb in self.imbalances:

            zone_range = imb["zone_high"] - imb["zone_low"]

            if imb["type"] == "bullish":
                if last_price <= imb["zone_low"]:
                    imb["mitigated"] = True
                    imb["fill_ratio"] = 1.0
                elif imb["zone_low"] < last_price < imb["zone_high"]:
                    imb["fill_ratio"] = (
                        (imb["zone_high"] - last_price) / zone_range
                    )

            elif imb["type"] == "bearish":
                if last_price >= imb["zone_high"]:
                    imb["mitigated"] = True
                    imb["fill_ratio"] = 1.0
                elif imb["zone_low"] < last_price < imb["zone_high"]:
                    imb["fill_ratio"] = (
                        (last_price - imb["zone_low"]) / zone_range
                    )

    # =====================================================
    # SCORING
    # =====================================================

    def _score_imbalances(self):
        if not self.imbalances:
            return

        max_size = max(
            imb["zone_high"] - imb["zone_low"]
            for imb in self.imbalances
        )

        for imb in self.imbalances:
            size = imb["zone_high"] - imb["zone_low"]
            size_score = size / max_size if max_size > 0 else 0

            freshness = 1 / (
                1 + (
                    len(self.df) - self.df.index.get_loc(imb["created_at"])
                ) / 100
            )

            fill_penalty = 1 - imb["fill_ratio"]

            strength = 0.5 * size_score + 0.3 * freshness + 0.2 * fill_penalty

            imb["strength"] = round(min(1.0, strength), 3)

        self.imbalances.sort(
            key=lambda x: x["strength"],
            reverse=True
        )

    # =====================================================
    # PUBLIC
    # =====================================================

    def get_imbalances(self):
        return self.imbalances
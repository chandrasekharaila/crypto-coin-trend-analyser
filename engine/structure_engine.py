#L1
import pandas as pd
import numpy as np
from dataclasses import dataclass


# =====================================================
# STRUCTURE STATE OBJECT
# =====================================================

@dataclass
class StructureState:
    trend: str
    bos: bool
    choch: bool
    structure_strength: float
    slope_score: float
    swing_count: int
    last_swing_high: float
    last_swing_low: float


# =====================================================
# MAIN STRUCTURE ENGINE
# =====================================================

class StructureEngine:
    def __init__(self, df, timeframe, atr_period=14, atr_multiplier=0.75):
        self.df = df.copy()
        self.timeframe = timeframe
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier

        self._calculate_atr()
        self._detect_swings()
        self.swings = self._extract_swings()
        self.state = self._classify_structure()

    # =====================================================
    # ATR
    # =====================================================

    def _calculate_atr(self):
        df = self.df
        df["prev_close"] = df["close"].shift(1)

        df["tr"] = np.maximum(
            df["high"] - df["low"],
            np.maximum(
                abs(df["high"] - df["prev_close"]),
                abs(df["low"] - df["prev_close"]),
            ),
        )

        df["atr"] = df["tr"].rolling(self.atr_period).mean()
        self.df = df

    # =====================================================
    # SWING DETECTION
    # =====================================================

    def _detect_swings(self):
        df = self.df

        df["swing_high"] = False
        df["swing_low"] = False

        last_swing_price = None
        last_swing_type = None

        for i in range(1, len(df) - 1):
            atr = df["atr"].iloc[i]
            if np.isnan(atr):
                continue

            min_distance = atr * self.atr_multiplier

            high = df["high"].iloc[i]
            low = df["low"].iloc[i]

            is_high = high > df["high"].iloc[i - 1] and high > df["high"].iloc[i + 1]
            is_low = low < df["low"].iloc[i - 1] and low < df["low"].iloc[i + 1]

            if is_high:
                if last_swing_type != "high":
                    if last_swing_price is None or abs(high - last_swing_price) >= min_distance:
                        df.at[df.index[i], "swing_high"] = True
                        last_swing_price = high
                        last_swing_type = "high"

            elif is_low:
                if last_swing_type != "low":
                    if last_swing_price is None or abs(low - last_swing_price) >= min_distance:
                        df.at[df.index[i], "swing_low"] = True
                        last_swing_price = low
                        last_swing_type = "low"

        self.df = df

    # =====================================================
    # SWING EXPORT
    # =====================================================

    def _extract_swings(self):
        swings = []

        for idx, row in self.df.iterrows():
            if row["swing_high"]:
                swings.append(
                    {"type": "high", "price": row["high"], "timestamp": idx}
                )
            if row["swing_low"]:
                swings.append(
                    {"type": "low", "price": row["low"], "timestamp": idx}
                )

        return swings

    # =====================================================
    # SLOPE INTELLIGENCE
    # =====================================================

    def _calculate_slope_score(self):
        window_map = {
            "1h": 48,
            "15m": 64,
            "5m": 96,
        }

        window = window_map.get(self.timeframe, 50)

        if len(self.df) < window:
            return 0.0

        closes = self.df["close"].tail(window).values
        x = np.arange(len(closes))

        slope = np.polyfit(x, closes, 1)[0]

        avg_atr = self.df["atr"].mean()
        if avg_atr == 0:
            return 0.0

        normalized = slope / avg_atr

        return round(min(1.0, abs(normalized) / 5), 3)

    # =====================================================
    # STRUCTURE CLASSIFICATION
    # =====================================================

    def _classify_structure(self):
        highs = [s for s in self.swings if s["type"] == "high"]
        lows = [s for s in self.swings if s["type"] == "low"]

        if len(highs) < 2 or len(lows) < 2:
            return StructureState(
                trend="Unknown",
                bos=False,
                choch=False,
                structure_strength=0.0,
                slope_score=0.0,
                swing_count=len(self.swings),
                last_swing_high=0.0,
                last_swing_low=0.0,
            )

        last_highs = highs[-2:]
        last_lows = lows[-2:]

        hh = last_highs[1]["price"] > last_highs[0]["price"]
        lh = last_highs[1]["price"] < last_highs[0]["price"]

        hl = last_lows[1]["price"] > last_lows[0]["price"]
        ll = last_lows[1]["price"] < last_lows[0]["price"]

        trend = "Range"
        if hh and hl:
            trend = "Bullish"
        elif lh and ll:
            trend = "Bearish"

        last_close = self.df["close"].iloc[-1]

        bos = False
        choch = False

        # BOS continuation
        if trend == "Bullish" and last_close > last_highs[1]["price"]:
            bos = True

        if trend == "Bearish" and last_close < last_lows[1]["price"]:
            bos = True

        # CHOCH reversal
        if trend == "Bullish" and last_close < last_lows[1]["price"]:
            choch = True

        if trend == "Bearish" and last_close > last_highs[1]["price"]:
            choch = True

        slope_score = self._calculate_slope_score()

        # Structure strength from impulse size
        impulse = abs(last_highs[1]["price"] - last_lows[1]["price"])
        avg_atr = self.df["atr"].mean()
        strength = 0 if avg_atr == 0 else min(1.0, (impulse / avg_atr) / 5)

        return StructureState(
            trend=trend,
            bos=bos,
            choch=choch,
            structure_strength=round(strength, 3),
            slope_score=slope_score,
            swing_count=len(self.swings),
            last_swing_high=last_highs[1]["price"],
            last_swing_low=last_lows[1]["price"],
        )

    # =====================================================
    # PUBLIC OUTPUT
    # =====================================================

    def get_summary(self):
        return self.state.__dict__

    def get_raw_features(self):
        return {
            "trend": self.state.trend,
            "bos": self.state.bos,
            "choch": self.state.choch,
            "structure_strength": self.state.structure_strength,
            "slope_score": self.state.slope_score,
            "swing_count": self.state.swing_count,
        }

    def get_swings(self):
        return self.swings
    
    def get_dataframe(self):
        return self.df
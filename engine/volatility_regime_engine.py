# engine/volatility_regime_engine.py
#L8
import numpy as np


class VolatilityRegimeEngine:
    def __init__(self, df, atr_period=14, bb_period=20):
        self.df = df.copy()
        self.atr_period = atr_period
        self.bb_period = bb_period

        self.regime = "Normal"
        self.atr_ratio = 1.0
        self.bb_width_ratio = 1.0

        self._compute_regime()

    # =====================================================
    # MAIN REGIME LOGIC
    # =====================================================

    def _compute_regime(self):

        df = self.df

        # ATR Regime
        atr_series = df["atr"]
        current_atr = atr_series.iloc[-1]
        atr_ma = atr_series.rolling(50).mean().iloc[-1]

        if atr_ma == 0 or np.isnan(atr_ma):
            return

        self.atr_ratio = current_atr / atr_ma

        # Bollinger Band Width
        close = df["close"]

        ma = close.rolling(self.bb_period).mean()
        std = close.rolling(self.bb_period).std()

        upper = ma + 2 * std
        lower = ma - 2 * std

        bb_width = (upper - lower) / ma

        current_width = bb_width.iloc[-1]
        width_ma = bb_width.rolling(50).mean().iloc[-1]

        if width_ma == 0 or np.isnan(width_ma):
            return

        self.bb_width_ratio = current_width / width_ma

        # Final Classification
        if self.atr_ratio < 0.8 and self.bb_width_ratio < 0.8:
            self.regime = "Compression"

        elif self.atr_ratio > 1.2 and self.bb_width_ratio > 1.2:
            self.regime = "Expansion"

        else:
            self.regime = "Normal"

    # =====================================================
    # PUBLIC
    # =====================================================

    def get_regime(self):
        return {
            "regime": self.regime,
            "atr_ratio": round(self.atr_ratio, 3),
            "bb_width_ratio": round(self.bb_width_ratio, 3),
        }
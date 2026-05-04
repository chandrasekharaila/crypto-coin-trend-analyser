# engine/reaction_engine.py
#L9
import numpy as np


class ReactionStrengthEngine:
    def __init__(self, df, lookahead=5):
        self.df = df
        self.lookahead = lookahead

    # =====================================================
    # MAIN REACTION ANALYSIS
    # =====================================================

    def analyze_reaction(self, level_price, level_type):
        """
        level_type: 'resistance' or 'support'
        """

        df = self.df
        atr = df["atr"].mean()

        reactions = []

        for i in range(len(df) - self.lookahead):

            high = df["high"].iloc[i]
            low = df["low"].iloc[i]
            close = df["close"].iloc[i]

            # Check touch
            if level_type == "resistance" and high >= level_price:
                reactions.append(
                    self._compute_reaction_metrics(i, "down")
                )

            if level_type == "support" and low <= level_price:
                reactions.append(
                    self._compute_reaction_metrics(i, "up")
                )

        if not reactions:
            return 0.0

        return round(np.mean(reactions), 3)

    # =====================================================
    # METRICS
    # =====================================================

    def _compute_reaction_metrics(self, index, direction):

        df = self.df

        candle = df.iloc[index]
        atr = df["atr"].mean()

        # Wick strength
        range_size = candle["high"] - candle["low"]
        if range_size == 0:
            wick_score = 0
        else:
            if direction == "down":
                wick_score = candle["upper_wick"] / range_size
            else:
                wick_score = candle["lower_wick"] / range_size

        # Displacement over next N candles
        future_close = df["close"].iloc[index + self.lookahead]
        current_close = candle["close"]

        move = abs(future_close - current_close)

        displacement_score = move / atr if atr > 0 else 0
        displacement_score = min(1.0, displacement_score / 3)

        # Volume spike
        volume_mean = df["volume"].rolling(20).mean().iloc[index]
        if volume_mean == 0:
            volume_score = 0
        else:
            volume_score = min(1.0, candle["volume"] / volume_mean / 3)

        # Follow-through direction check
        direction_correct = (
            (direction == "down" and future_close < current_close)
            or (direction == "up" and future_close > current_close)
        )

        follow_score = 1.0 if direction_correct else 0.0

        # Final weighted score
        score = (
            0.3 * wick_score +
            0.3 * displacement_score +
            0.2 * volume_score +
            0.2 * follow_score
        )

        return min(1.0, score)
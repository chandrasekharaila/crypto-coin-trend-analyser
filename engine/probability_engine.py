# engine/probability_engine.py
#L11
import numpy as np


class ProbabilityEngine:
    def __init__(
        self,
        confluence_result,
        liquidity_bias,
        structure_state,
        regime,
        imbalances,
    ):
        self.confluence = confluence_result
        self.liquidity_bias = liquidity_bias
        self.structure = structure_state
        self.regime = regime
        self.imbalances = imbalances

    # =====================================================
    # MAIN PROBABILITY CALCULATION
    # =====================================================

    def estimate(self):

        zone = self.confluence["zone"]
        confluence_score = self.confluence["confluence_score"] / 10

        pressure = confluence_score

        breakdown = {}

        # -------------------------------------------------
        # Liquidity Effect
        # -------------------------------------------------
        bias = self.liquidity_bias["bias"]

        liquidity_adjustment = 0

        if zone["type"] == "resistance":
            if bias == "Upside Liquidity Heavy":
                liquidity_adjustment -= 0.15
            elif bias == "Downside Liquidity Heavy":
                liquidity_adjustment += 0.15

        elif zone["type"] == "support":
            if bias == "Downside Liquidity Heavy":
                liquidity_adjustment -= 0.15
            elif bias == "Upside Liquidity Heavy":
                liquidity_adjustment += 0.15

        breakdown["liquidity_adjustment"] = liquidity_adjustment
        pressure += liquidity_adjustment

        # -------------------------------------------------
        # Volatility Effect
        # -------------------------------------------------
        volatility_adjustment = 0

        if self.regime["regime"] == "Compression":
            volatility_adjustment -= 0.1  # breakout more likely
        elif self.regime["regime"] == "Expansion":
            volatility_adjustment += 0.1  # rejection more likely

        breakdown["volatility_adjustment"] = volatility_adjustment
        pressure += volatility_adjustment

        # -------------------------------------------------
        # Slope Momentum Effect
        # -------------------------------------------------
        slope = self.structure.get("slope_score", 0)

        slope_adjustment = 0

        if zone["type"] == "resistance" and slope > 0.6:
            slope_adjustment -= 0.1

        if zone["type"] == "support" and slope > 0.6:
            slope_adjustment += 0.1

        breakdown["slope_adjustment"] = slope_adjustment
        pressure += slope_adjustment

        # -------------------------------------------------
        # Imbalance Pull Effect
        # -------------------------------------------------
        imbalance_adjustment = 0

        strong_imbalances = [
            imb for imb in self.imbalances
            if not imb["mitigated"] and imb["strength"] > 0.6
        ]

        if strong_imbalances:
            imbalance_adjustment += 0.1

        breakdown["imbalance_adjustment"] = imbalance_adjustment
        pressure += imbalance_adjustment

        # -------------------------------------------------
        # Logistic Probability
        # -------------------------------------------------
        x = (pressure - 0.5) * 5  # scaling factor
        reject_probability = 1 / (1 + np.exp(-x))
        breakout_probability = 1 - reject_probability

        reject_probability = round(reject_probability * 100, 2)
        breakout_probability = round(breakout_probability * 100, 2)

        # Confidence grading
        diff = abs(reject_probability - breakout_probability)

        if diff > 40:
            confidence = "High"
        elif diff > 20:
            confidence = "Moderate"
        else:
            confidence = "Low"

        return {
            "reject_probability": reject_probability,
            "breakout_probability": breakout_probability,
            "confidence": confidence,
            "breakdown": breakdown,
        }
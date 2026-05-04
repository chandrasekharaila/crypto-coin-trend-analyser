# engine/multi_timeframe_engine.py
# L16 — Multi-Timeframe Aggregation Layer


class MultiTimeframeAggregator:
    def __init__(self, tf_outputs):
        """
        tf_outputs = {
            "4h": {...},
            "1h": {...},
            "15m": {...},
            "5m": {...}
        }
        """
        self.tf_outputs = tf_outputs

        # Only used for probability blending
        self.weights = {
            "4h": 0.4,
            "1h": 0.3,
            "15m": 0.2,
            "5m": 0.1,
        }

    # =====================================================
    # GLOBAL TREND (Hierarchical)
    # =====================================================
    def _aggregate_trend(self):

        tf_4h = self.tf_outputs.get("4h")
        tf_1h = self.tf_outputs.get("1h")

        # Step 1 — Macro Authority (4H)
        if not tf_4h:
            return "Neutral"

        macro_trend = tf_4h["structure"]["trend"]

        # If 4H neutral → fallback to 1H
        if macro_trend == "Neutral" and tf_1h:
            return tf_1h["structure"]["trend"]

        # Step 2 — 1H Alignment Check
        if tf_1h:
            h1_trend = tf_1h["structure"]["trend"]

            # Aligned → continuation
            if h1_trend == macro_trend:
                return macro_trend

            # Opposite → pullback inside macro
            if h1_trend != macro_trend and h1_trend != "Neutral":
                return f"{macro_trend} (Pullback Phase)"

        # Default → macro trend dominates
        return macro_trend

    # =====================================================
    # GLOBAL LIQUIDITY BIAS (Hierarchical)
    # =====================================================
    def _aggregate_liquidity(self):

        tf_4h = self.tf_outputs.get("4h")
        tf_1h = self.tf_outputs.get("1h")

        if not tf_4h:
            return "Balanced"

        macro_bias = tf_4h["liquidity_bias"]["bias"]

        if tf_1h:
            h1_bias = tf_1h["liquidity_bias"]["bias"]

            # Aligned
            if h1_bias == macro_bias:
                return macro_bias

            # Conflict
            if h1_bias != macro_bias:
                return f"{macro_bias} (Short-Term Conflict)"

        return macro_bias

    # =====================================================
    # GLOBAL PROBABILITY (Weighted Blend)
    # =====================================================
    def _aggregate_probability(self):

        weighted_reject = 0
        total_weight = 0

        for tf, data in self.tf_outputs.items():

            weight = self.weights.get(tf, 0)

            prob = data.get("probability", {})
            reject_prob = prob.get("reject_probability")

            if reject_prob is not None:
                weighted_reject += reject_prob * weight
                total_weight += weight

        if total_weight == 0:
            return 50.0

        return round(weighted_reject / total_weight, 2)

    # =====================================================
    # GLOBAL PATH (Semi-Hierarchical)
    # =====================================================
    def _aggregate_path(self):

        tf_4h = self.tf_outputs.get("4h")
        tf_1h = self.tf_outputs.get("1h")

        # Prefer 4H path
        if tf_4h:
            return tf_4h["path"]["direction"]

        # Fallback to 1H
        if tf_1h:
            return tf_1h["path"]["direction"]

        return "Indecisive"

    # =====================================================
    # MAIN AGGREGATION
    # =====================================================
    def aggregate(self):

        global_trend = self._aggregate_trend()
        global_liquidity = self._aggregate_liquidity()
        global_reject_probability = self._aggregate_probability()
        global_path = self._aggregate_path()

        return {
            "global_trend": global_trend,
            "global_liquidity_bias": global_liquidity,
            "global_rejection_probability": global_reject_probability,
            "global_path": global_path,
        }
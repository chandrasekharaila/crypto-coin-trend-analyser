# engine/path_predictor_engine.py
#L12

class PathPredictorEngine:
    def __init__(
        self,
        liquidity_bias,
        session_levels,
        imbalances,
        structure_state,
        regime,
    ):
        self.liquidity_bias = liquidity_bias
        self.session_levels = session_levels
        self.imbalances = imbalances
        self.structure = structure_state
        self.regime = regime

    # =====================================================
    # MAIN PATH PREDICTION
    # =====================================================

    def predict(self):

        up_score = 0.0
        down_score = 0.0
        reasoning = {}

        # -------------------------------------------------
        # 1️⃣ Liquidity Imbalance
        # -------------------------------------------------
        ratio = self.liquidity_bias["imbalance_ratio"]

        if ratio > 1.2:
            up_score += 1.5
        elif ratio < 0.8:
            down_score += 1.5

        reasoning["liquidity_ratio"] = ratio

        # -------------------------------------------------
        # 2️⃣ Untouched Session Liquidity
        # -------------------------------------------------
        untouched_buy = 0
        untouched_sell = 0

        for level in self.session_levels.values():
            if level["swept"]:
                continue

            if level["type"] == "buy_liquidity":
                untouched_buy += 1
            elif level["type"] == "sell_liquidity":
                untouched_sell += 1

        up_score += untouched_buy * 0.5
        down_score += untouched_sell * 0.5

        reasoning["untouched_buy_levels"] = untouched_buy
        reasoning["untouched_sell_levels"] = untouched_sell

        # -------------------------------------------------
        # 3️⃣ Strong Imbalance Magnets
        # -------------------------------------------------
        for imb in self.imbalances:
            if imb["mitigated"] or imb["strength"] < 0.6:
                continue

            if imb["type"] == "bearish":
                up_score += 0.5
            elif imb["type"] == "bullish":
                down_score += 0.5

        # -------------------------------------------------
        # 4️⃣ Structure Bias
        # -------------------------------------------------
        if self.structure["trend"] == "Bullish":
            up_score += 1.0
        elif self.structure["trend"] == "Bearish":
            down_score += 1.0

        reasoning["trend"] = self.structure["trend"]

        # -------------------------------------------------
        # 5️⃣ Volatility Regime
        # -------------------------------------------------
        if self.regime["regime"] == "Compression":
            up_score += 0.5
            down_score += 0.5

        # -------------------------------------------------
        # Final Decision
        # -------------------------------------------------
        if up_score > down_score:
            direction = "Likely Upside Sweep First"
        elif down_score > up_score:
            direction = "Likely Downside Sweep First"
        else:
            direction = "Indecisive"

        diff = abs(up_score - down_score)

        if diff > 2:
            confidence = "High"
        elif diff > 1:
            confidence = "Moderate"
        else:
            confidence = "Low"

        return {
            "direction": direction,
            "up_score": round(up_score, 2),
            "down_score": round(down_score, 2),
            "confidence": confidence,
            "reasoning": reasoning,
        }
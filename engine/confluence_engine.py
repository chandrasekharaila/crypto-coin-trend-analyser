# engine/confluence_engine.py
#L2
import numpy as np


class ConfluenceEngine:
    def __init__(
        self,
        structure_state,
        liquidity_bias,
        imbalances,
        regime,
        valuation_state,
        reaction_score,
    ):
        self.structure_state = structure_state
        self.liquidity_bias = liquidity_bias
        self.imbalances = imbalances
        self.regime = regime
        self.valuation = valuation_state
        self.reaction_score = reaction_score

    # =====================================================
    # MAIN SCORING
    # =====================================================

    def score_zone(self, zone):

        breakdown = {}

        # -------------------------------------------------
        # 1️⃣ Structure Alignment
        # -------------------------------------------------
        if zone["type"] == "resistance":
            structure_score = 1.0 if self.structure_state["trend"] == "Bearish" else 0.3
        else:
            structure_score = 1.0 if self.structure_state["trend"] == "Bullish" else 0.3

        breakdown["structure"] = structure_score

        # -------------------------------------------------
        # 2️⃣ Liquidity Alignment
        # -------------------------------------------------
        bias = self.liquidity_bias["bias"]

        if zone["type"] == "resistance":
            liquidity_score = 1.0 if bias == "Upside Liquidity Heavy" else 0.4
        else:
            liquidity_score = 1.0 if bias == "Downside Liquidity Heavy" else 0.4

        breakdown["liquidity"] = liquidity_score

        # -------------------------------------------------
        # 3️⃣ Imbalance Confluence
        # -------------------------------------------------
        zone_mid = (zone["zone_low"] + zone["zone_high"]) / 2

        imbalance_score = 0.0

        for imb in self.imbalances:
            if imb["mitigated"]:
                continue

            if imb["zone_low"] <= zone_mid <= imb["zone_high"]:
                imbalance_score = max(imbalance_score, imb["strength"])

        breakdown["imbalance"] = imbalance_score

        # -------------------------------------------------
        # 4️⃣ Reaction Score
        # -------------------------------------------------
        breakdown["reaction"] = self.reaction_score

        # -------------------------------------------------
        # 5️⃣ Volatility Context
        # -------------------------------------------------
        if self.regime["regime"] == "Compression":
            volatility_score = 0.7
        elif self.regime["regime"] == "Expansion":
            volatility_score = 1.0
        else:
            volatility_score = 0.85

        breakdown["volatility"] = volatility_score

        # -------------------------------------------------
        # 6️⃣ Zone Base Strength
        # -------------------------------------------------
        zone_strength = zone.get("base_strength", 0.5)
        breakdown["zone_strength"] = zone_strength

        # -------------------------------------------------
        # 7️⃣ Valuation Alignment (NEW)
        # -------------------------------------------------
        valuation_position = self.valuation["current_position"]

        if zone["type"] == "resistance":
            if valuation_position == "Premium":
                valuation_score = 1.0
            elif valuation_position == "Equilibrium":
                valuation_score = 0.6
            else:  # Discount
                valuation_score = 0.3

        elif zone["type"] == "support":
            if valuation_position == "Discount":
                valuation_score = 1.0
            elif valuation_position == "Equilibrium":
                valuation_score = 0.6
            else:  # Premium
                valuation_score = 0.3

        breakdown["valuation"] = valuation_score

        # -------------------------------------------------
        # Final Weighted Score
        # -------------------------------------------------
        weights = {
            "structure": 0.22,
            "liquidity": 0.18,
            "imbalance": 0.14,
            "reaction": 0.13,
            "volatility": 0.08,
            "zone_strength": 0.12,
            "valuation": 0.13,
        }

        total = sum(
            breakdown[key] * weights[key]
            for key in breakdown
        )

        final_score = round(total * 10, 2)

        return {
            "zone": zone,
            "confluence_score": final_score,
            "breakdown": breakdown,
        }
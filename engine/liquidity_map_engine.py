# engine/liquidity_map_engine.py
# L13

import numpy as np


class LiquidityMapEngine:

    def __init__(
        self,
        df,
        equal_liquidity,
        session_levels,
        imbalances,
        path_prediction,
    ):

        self.df = df
        self.equal_liquidity = equal_liquidity
        self.session_levels = session_levels
        self.imbalances = imbalances
        self.path_prediction = path_prediction

        self.current_price = df["close"].iloc[-1]

    # =====================================================
    # MAIN MAP GENERATOR
    # =====================================================

    def generate_map(self):

        targets = []

        # -------------------------------------------------
        # Equal Liquidity Pools
        # -------------------------------------------------
        for pool in self.equal_liquidity["buy_side"]:

            if not pool["swept"]:

                targets.append(
                    self._build_target(
                        pool["mid_price"],
                        pool["strength"],
                        "buy_liquidity"
                    )
                )

        for pool in self.equal_liquidity["sell_side"]:

            if not pool["swept"]:

                targets.append(
                    self._build_target(
                        pool["mid_price"],
                        pool["strength"],
                        "sell_liquidity"
                    )
                )

        # -------------------------------------------------
        # Session Liquidity
        # -------------------------------------------------
        for name, level in self.session_levels.items():

            if not level["swept"]:

                targets.append(
                    self._build_target(
                        level["price"],
                        0.8,   # baseline session strength
                        level["type"]
                    )
                )

        # -------------------------------------------------
        # Strong Imbalances
        # -------------------------------------------------
        for imb in self.imbalances:

            if not imb["mitigated"] and imb["strength"] > 0.6:

                mid = (imb["zone_low"] + imb["zone_high"]) / 2

                targets.append(
                    self._build_target(
                        mid,
                        imb["strength"],
                        "imbalance"
                    )
                )

        # -------------------------------------------------
        # No targets fallback
        # -------------------------------------------------
        if not targets:

            return {
                "message": "No active liquidity targets detected."
            }

        # -------------------------------------------------
        # Rank Targets
        # -------------------------------------------------
        targets.sort(key=lambda x: x["priority_score"], reverse=True)

        primary = targets[0]
        secondary = targets[1] if len(targets) > 1 else None

        confidence = self._compute_confidence(primary)

        # -------------------------------------------------
        # Separate targets for Gravity Engine
        # -------------------------------------------------
        buy_targets = []
        sell_targets = []

        for t in targets:

            if t["price"] > self.current_price:
                buy_targets.append(t)

            elif t["price"] < self.current_price:
                sell_targets.append(t)

        # -------------------------------------------------
        # Return map
        # -------------------------------------------------
        return {

            "primary_target": primary,
            "secondary_target": secondary,

            "buy_targets": buy_targets[:5],
            "sell_targets": sell_targets[:5],

            "map_confidence": confidence,
            "total_targets_considered": len(targets),
        }

    # =====================================================
    # TARGET SCORING
    # =====================================================

    def _build_target(self, price, strength, target_type):

        distance = abs(price - self.current_price)

        distance_score = 1 / (1 + distance / self.current_price)

        alignment_bonus = 0

        if (
            "Upside" in self.path_prediction["direction"]
            and price > self.current_price
        ):
            alignment_bonus = 0.2

        if (
            "Downside" in self.path_prediction["direction"]
            and price < self.current_price
        ):
            alignment_bonus = 0.2

        priority_score = (
            0.5 * strength +
            0.3 * distance_score +
            alignment_bonus
        )

        return {

            "price": round(price, 2),
            "type": target_type,
            "strength": round(strength, 3),
            "priority_score": round(priority_score, 3),
        }

    # =====================================================
    # CONFIDENCE ESTIMATION
    # =====================================================

    def _compute_confidence(self, primary):

        score = primary["priority_score"]

        if score > 0.8:
            return "High"

        elif score > 0.6:
            return "Moderate"

        else:
            return "Low"
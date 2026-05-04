# engine/liquidity_gravity_engine.py
# L21

class LiquidityGravityEngine:

    def __init__(self, current_price, liquidity_map):

        self.current_price = current_price
        self.liquidity_map = liquidity_map

    # =====================================================
    # DISTANCE NORMALIZATION
    # =====================================================

    def _distance_weight(self, price):

        distance = abs(price - self.current_price)

        if distance == 0:
            return 1

        return 1 / distance

    # =====================================================
    # GRAVITY SCORE
    # =====================================================

    def _gravity_score(self, target):

        price = target["price"]

        # LiquidityMapEngine uses priority_score
        base_score = target.get("priority_score", 1)

        distance_factor = self._distance_weight(price)

        gravity = base_score * distance_factor

        return gravity

    # =====================================================
    # BUILD GRAVITY MAP
    # =====================================================

    def compute_gravity(self):

        gravity_levels = []

        # Buy targets
        for target in self.liquidity_map.get("buy_targets", []):

            gravity = self._gravity_score(target)

            gravity_levels.append({
                "type": "buy_liquidity",
                "price": target["price"],
                "gravity": gravity
            })

        # Sell targets
        for target in self.liquidity_map.get("sell_targets", []):

            gravity = self._gravity_score(target)

            gravity_levels.append({
                "type": "sell_liquidity",
                "price": target["price"],
                "gravity": gravity
            })

        if not gravity_levels:
            return None

        # Sort by strongest gravity
        gravity_levels.sort(key=lambda x: x["gravity"], reverse=True)

        strongest = gravity_levels[0]

        return {
            "strongest_pull": strongest,
            "all_levels": gravity_levels[:5]
        }
# engine/projection_engine.py
# L17

class ProjectionEngine:

    def __init__(
        self,
        current_price,
        path_prediction,
        liquidity_map,
        imbalances,
        probability,
        smart_money=None
    ):

        self.current_price = current_price
        self.path_prediction = path_prediction
        self.liquidity_map = liquidity_map
        self.imbalances = imbalances
        self.probability = probability
        self.smart_money = smart_money or {"events": []}

    # =====================================================
    # DISTANCE FILTER
    # =====================================================

    def _valid_price(self, price):

        if not price:
            return False

        distance = abs(price - self.current_price) / self.current_price

        return distance < 0.08

    # =====================================================
    # SMART MONEY BIAS
    # =====================================================

    def _smart_money_bias(self):

        for event in self.smart_money["events"]:

            if event["sweep_type"] == "buy_side_sweep" and event["displacement"] == "bearish":
                return "down"

            if event["sweep_type"] == "sell_side_sweep" and event["displacement"] == "bullish":
                return "up"

        return None

    # =====================================================
    # FIND NEAREST LIQUIDITY
    # =====================================================

    def _nearest_liquidity(self):

        liquidity_levels = []

        if "buy_targets" in self.liquidity_map:
            liquidity_levels += [t["price"] for t in self.liquidity_map["buy_targets"]]

        if "sell_targets" in self.liquidity_map:
            liquidity_levels += [t["price"] for t in self.liquidity_map["sell_targets"]]

        liquidity_levels = [p for p in liquidity_levels if self._valid_price(p)]

        if not liquidity_levels:
            return None

        liquidity_levels.sort(key=lambda x: abs(x - self.current_price))

        return liquidity_levels[0]

    # =====================================================
    # FIND IMBALANCE TARGET
    # =====================================================

    def _major_imbalance(self):

        if not self.imbalances:
            return None

        targets = []

        for imb in self.imbalances:

            if imb["mitigated"]:
                continue

            mid = (imb["zone_low"] + imb["zone_high"]) / 2

            if self._valid_price(mid):
                targets.append(mid)

        if not targets:
            return None

        targets.sort(key=lambda x: abs(x - self.current_price))

        return targets[0]

    # =====================================================
    # REACTION PRICE
    # =====================================================

    def _reaction_price(self, sweep_price):

        distance = abs(sweep_price - self.current_price)

        bounce = distance * 0.35

        if sweep_price < self.current_price:
            return sweep_price + bounce
        else:
            return sweep_price - bounce

    # =====================================================
    # PRIMARY SCENARIO
    # =====================================================

    def _primary_scenario(self):

        sweep = self._nearest_liquidity()
        target = self._major_imbalance()

        smart_bias = self._smart_money_bias()

        if not sweep:
            sweep = self.current_price * 0.997

        reaction = self._reaction_price(sweep)

        # SMART MONEY OVERRIDE
        if smart_bias == "down":
            target = self.current_price * 0.985

        elif smart_bias == "up":
            target = self.current_price * 1.015

        elif not target:

            if sweep < self.current_price:
                target = sweep * 0.985
            else:
                target = sweep * 1.015

        path = [
            {
                "type": "liquidity_sweep",
                "price": round(sweep, 2),
            },
            {
                "type": "reaction",
                "price": round(reaction, 2),
            },
            {
                "type": "expansion_target",
                "price": round(target, 2),
            },
        ]

        return {
            "probability": round(self.probability["reject_probability"], 2),
            "path": path,
        }

    # =====================================================
    # ALTERNATE SCENARIO
    # =====================================================

    def _alternate_scenario(self):

        direction = self.path_prediction["direction"]

        if "Downside" in direction:
            alt_target = self.current_price * 1.015
        else:
            alt_target = self.current_price * 0.985

        reaction = (self.current_price + alt_target) / 2

        path = [
            {
                "type": "fake_move",
                "price": round(reaction, 2),
            },
            {
                "type": "alternate_target",
                "price": round(alt_target, 2),
            },
        ]

        return {
            "probability": round(1 - self.probability["reject_probability"], 2),
            "path": path,
        }

    # =====================================================
    # GENERATE PROJECTION
    # =====================================================

    def generate_projection(self):

        primary = self._primary_scenario()
        alternate = self._alternate_scenario()

        return {
            "primary_scenario": primary,
            "alternate_scenario": alternate,
        }
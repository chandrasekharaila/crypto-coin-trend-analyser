# engine/visualization_engine.py
# L15

import matplotlib.pyplot as plt


class VisualizationEngine:

    def __init__(
        self,
        df,
        zones,
        equal_liquidity,
        session_levels,
        imbalances,
        liquidity_map,
        projection=None,
        monte_carlo=None,
        heatmap=None,
        smart_money=None,
        title="Chart",
    ):

        self.df = df
        self.zones = zones
        self.equal_liquidity = equal_liquidity
        self.session_levels = session_levels
        self.imbalances = imbalances
        self.liquidity_map = liquidity_map
        self.projection = projection
        self.monte_carlo = monte_carlo
        self.heatmap = heatmap
        self.smart_money = smart_money
        self.title = title

    # =====================================================
    # MAIN PLOT FUNCTION
    # =====================================================

    def plot(self):

        df = self.df.tail(200)

        fig, ax = plt.subplots(figsize=(14, 8))

        # -------------------------------------------------
        # Past Price
        # -------------------------------------------------
        ax.plot(
            df.index,
            df["close"],
            color="blue",
            linewidth=2,
            label="Past Price"
        )

        # -------------------------------------------------
        # Liquidity Heatmap
        # -------------------------------------------------
        self._plot_heatmap(ax)

        # -------------------------------------------------
        # Zones
        # -------------------------------------------------
        for zone in self.zones["resistance"][:2]:
            ax.axhspan(zone["zone_low"], zone["zone_high"], alpha=0.15)

        for zone in self.zones["support"][:2]:
            ax.axhspan(zone["zone_low"], zone["zone_high"], alpha=0.15)

        # -------------------------------------------------
        # Equal Liquidity
        # -------------------------------------------------
        for pool in self.equal_liquidity["buy_side"][:2]:
            if not pool["swept"]:
                ax.axhline(pool["mid_price"], alpha=0.4)

        for pool in self.equal_liquidity["sell_side"][:2]:
            if not pool["swept"]:
                ax.axhline(pool["mid_price"], alpha=0.4)

        # -------------------------------------------------
        # Session Liquidity
        # -------------------------------------------------
        for level in self.session_levels.values():
            if not level["swept"]:
                ax.axhline(level["price"], linestyle="--", alpha=0.4)

        # -------------------------------------------------
        # Imbalances
        # -------------------------------------------------
        for imb in self.imbalances[:2]:
            if not imb["mitigated"]:
                ax.axhspan(
                    imb["zone_low"],
                    imb["zone_high"],
                    alpha=0.1
                )

        # -------------------------------------------------
        # Primary Target
        # -------------------------------------------------
        primary = self.liquidity_map.get("primary_target")

        if primary:
            ax.axhline(
                primary["price"],
                linewidth=2,
                color="purple",
                label="Primary Target"
            )

        # -------------------------------------------------
        # Projection Paths
        # -------------------------------------------------
        self._plot_projection(ax)

        # -------------------------------------------------
        # Monte Carlo Cone
        # -------------------------------------------------
        self._plot_probability_cone(ax)

        # -------------------------------------------------
        # Smart Money Markers
        # -------------------------------------------------
        self._plot_smart_money(ax)

        # -------------------------------------------------
        # Formatting
        # -------------------------------------------------
        ax.set_title(self.title)

        plt.xticks(rotation=45)
        ax.legend()
        plt.tight_layout()
        plt.show()

    # =====================================================
    # PROJECTION VISUALIZATION
    # =====================================================

    def _plot_projection(self, ax):

        if not self.projection:
            return

        df = self.df.tail(200)

        current_price = df["close"].iloc[-1]
        last_time = df.index[-1]
        step = df.index[-1] - df.index[-2]

        primary = self.projection["primary_scenario"]["path"]

        x = last_time
        y = current_price

        for i, step_data in enumerate(primary):

            target = step_data["price"]
            next_time = last_time + step * (i + 6)

            ax.plot(
                [x, next_time],
                [y, target],
                linestyle="--",
                linewidth=2,
                color="green",
                label="Primary Projection" if i == 0 else ""
            )

            x = next_time
            y = target

        alternate = self.projection.get("alternate_scenario")

        if alternate:

            x = last_time
            y = current_price

            for i, step_data in enumerate(alternate["path"]):

                target = step_data["price"]
                next_time = last_time + step * (i + 3)

                ax.plot(
                    [x, next_time],
                    [y, target],
                    linestyle="--",
                    linewidth=2,
                    color="orange",
                    label="Alternate Projection" if i == 0 else ""
                )

                x = next_time
                y = target

    # =====================================================
    # MONTE CARLO PROBABILITY CONE
    # =====================================================

    def _plot_probability_cone(self, ax):

        if not self.monte_carlo:
            return

        df = self.df.tail(200)

        last_time = df.index[-1]
        step_time = df.index[-1] - df.index[-2]

        cone = self.monte_carlo["cone"]

        x = []
        lower = []
        upper = []
        median = []

        for c in cone:

            x.append(last_time + step_time * c["step"])
            lower.append(c["lower"])
            upper.append(c["upper"])
            median.append(c["median"])

        ax.fill_between(
            x,
            lower,
            upper,
            alpha=0.15,
            color="grey",
            label="Probability Cone"
        )

        ax.plot(
            x,
            median,
            linestyle=":",
            linewidth=2,
            color="black",
            label="Median Projection"
        )

    # =====================================================
    # LIQUIDITY HEATMAP
    # =====================================================

    def _plot_heatmap(self, ax):

        if not self.heatmap:
            return

        bins = self.heatmap["bins"]
        heat = self.heatmap["heat"]

        max_heat = max(heat) if max(heat) > 0 else 1

        for price, intensity in zip(bins, heat):

            alpha = intensity / max_heat

            ax.axhspan(
                price - 5,
                price + 5,
                alpha=alpha * 0.6,
                color="darkred"
            )

    # =====================================================
    # SMART MONEY EVENTS
    # =====================================================

    def _plot_smart_money(self, ax):

        if not self.smart_money:
            return

        events = self.smart_money.get("events", [])

        if not events:
            return

        x = self.df.index[-1]

        for event in events:

            price = event["price"]

            if event["displacement"] == "bearish":

                ax.scatter(
                    x,
                    price,
                    color="red",
                    s=100,
                    marker="v",
                    label="Smart Money Sell"
                )

            else:

                ax.scatter(
                    x,
                    price,
                    color="green",
                    s=100,
                    marker="^",
                    label="Smart Money Buy"
                )
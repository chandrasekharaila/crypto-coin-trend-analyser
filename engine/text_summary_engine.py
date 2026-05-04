# L14
# engine/text_summary_engine.py


class TextSummaryEngine:
    def __init__(
        self,
        timeframe,
        structure,
        liquidity_bias,
        regime,
        probability,
        path_prediction,
        liquidity_map,
        gravity=None
    ):
        self.timeframe = timeframe
        self.structure = structure
        self.liquidity_bias = liquidity_bias
        self.regime = regime
        self.probability = probability
        self.path_prediction = path_prediction
        self.liquidity_map = liquidity_map
        self.gravity = gravity

    # =====================================================
    # MAIN SUMMARY
    # =====================================================

    def generate_summary(self):

        lines = []

        lines.append("=" * 70)
        lines.append(f"{self.timeframe.upper()} MARKET INTELLIGENCE REPORT")
        lines.append("=" * 70)

        # -------------------------------------------------
        # Structure
        # -------------------------------------------------
        lines.append("\nSTRUCTURAL CONTEXT:")
        lines.append(f"- Trend: {self.structure['trend']}")
        lines.append(f"- Structure Strength: {self.structure['structure_strength']}")
        lines.append(f"- Slope Score: {self.structure['slope_score']}")

        # -------------------------------------------------
        # Liquidity
        # -------------------------------------------------
        lines.append("\nLIQUIDITY CONTEXT:")
        lines.append(f"- Upside Strength: {self.liquidity_bias['upside_strength']}")
        lines.append(f"- Downside Strength: {self.liquidity_bias['downside_strength']}")
        lines.append(f"- Imbalance Ratio: {self.liquidity_bias['imbalance_ratio']}")
        lines.append(f"- Bias: {self.liquidity_bias['bias']}")

        # -------------------------------------------------
        # Volatility
        # -------------------------------------------------
        lines.append("\nVOLATILITY STATE:")
        lines.append(f"- Regime: {self.regime['regime']}")
        lines.append(f"- ATR Ratio: {self.regime['atr_ratio']}")
        lines.append(f"- BB Width Ratio: {self.regime['bb_width_ratio']}")

        # -------------------------------------------------
        # Probability
        # -------------------------------------------------
        lines.append("\nZONE PROBABILITY ESTIMATE:")
        lines.append(f"- Rejection Probability: {self.probability['reject_probability']}%")
        lines.append(f"- Breakout Probability: {self.probability['breakout_probability']}%")
        lines.append(f"- Confidence: {self.probability['confidence']}")

        # -------------------------------------------------
        # Path
        # -------------------------------------------------
        lines.append("\nLIKELY LIQUIDITY PATH:")
        lines.append(f"- Direction: {self.path_prediction['direction']}")
        lines.append(f"- Confidence: {self.path_prediction['confidence']}")

        # -------------------------------------------------
        # Liquidity Map
        # -------------------------------------------------
        lines.append("\nTODAY'S LIQUIDITY MAP:")

        primary = self.liquidity_map.get("primary_target")
        secondary = self.liquidity_map.get("secondary_target")

        if primary:
            lines.append(
                f"- Primary Target: {primary['price']} "
                f"({primary['type']}) "
                f"[Score: {primary['priority_score']}]"
            )

        if secondary:
            lines.append(
                f"- Secondary Target: {secondary['price']} "
                f"({secondary['type']}) "
                f"[Score: {secondary['priority_score']}]"
            )

        lines.append(f"- Map Confidence: {self.liquidity_map.get('map_confidence')}")

        # -------------------------------------------------
        # Liquidity Gravity (L21)
        # -------------------------------------------------
        if self.gravity:

            strongest = self.gravity.get("strongest_pull")

            if strongest:

                lines.append("\nLIQUIDITY GRAVITY:")

                lines.append(
                    f"- Strongest Pull Level: {strongest['price']} ({strongest['type']})"
                )

                lines.append(
                    f"- Gravity Strength: {round(strongest['gravity'], 6)}"
                )

        # -------------------------------------------------
        # Final Bias
        # -------------------------------------------------
        lines.append("\nFINAL CONTEXTUAL BIAS:")

        if self.path_prediction["direction"] == "Likely Upside Sweep First":
            bias_statement = "Market likely seeks liquidity above before any major reversal."

        elif self.path_prediction["direction"] == "Likely Downside Sweep First":
            bias_statement = "Market likely seeks liquidity below before continuation."

        else:
            bias_statement = "Liquidity distribution is balanced; reactive environment expected."

        lines.append(f"- {bias_statement}")

        lines.append("=" * 70)

        return "\n".join(lines)
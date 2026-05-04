import datetime

from engine.data_engine import DataEngine
from engine.structure_engine import StructureEngine
from engine.zone_engine import ZoneEngine
from engine.liquidity_engine import LiquidityEngine
from engine.session_liquidity_engine import SessionLiquidityEngine
from engine.liquidity_imbalance_engine import LiquidityImbalanceEngine
from engine.imbalance_engine import ImbalanceEngine
from engine.volatility_regime_engine import VolatilityRegimeEngine
from engine.reaction_engine import ReactionStrengthEngine
from engine.confluence_engine import ConfluenceEngine
from engine.probability_engine import ProbabilityEngine
from engine.path_predictor_engine import PathPredictorEngine
from engine.liquidity_map_engine import LiquidityMapEngine
from engine.text_summary_engine import TextSummaryEngine
from engine.visualization_engine import VisualizationEngine
from engine.valuation_engine import PremiumDiscountEngine
from engine.multi_timeframe_engine import MultiTimeframeAggregator
from engine.projection_engine import ProjectionEngine
from engine.monte_carlo_projection_engine import MonteCarloProjectionEngine
from engine.liquidity_heatmap_engine import LiquidityHeatmapEngine
from engine.smart_money_engine import SmartMoneyEngine
from engine.liquidity_gravity_engine import LiquidityGravityEngine


# =========================================================
# PER TIMEFRAME PIPELINE
# =========================================================
def run_timeframe_pipeline(tf, df):

    print(f"\n{'=' * 60}")
    print(f"{tf.upper()} ANALYSIS")
    print(f"{'=' * 60}")

    # -------------------------------------------------
    # L1 Structure
    # -------------------------------------------------
    structure_engine = StructureEngine(df, timeframe=tf)
    enriched_df = structure_engine.get_dataframe()
    swings = structure_engine.get_swings()
    structure_state = structure_engine.get_summary()

    print("\nSTRUCTURE")
    print(structure_state)

    # -------------------------------------------------
    # L2 Valuation
    # -------------------------------------------------
    valuation_engine = PremiumDiscountEngine(enriched_df, swings)
    valuation = valuation_engine.get_valuation()

    print("\nVALUATION")
    print(valuation)

    # -------------------------------------------------
    # L3 Zones
    # -------------------------------------------------
    zone_engine = ZoneEngine(enriched_df, swings, timeframe=tf)
    zones = zone_engine.get_zones()

    # -------------------------------------------------
    # L4 Equal Liquidity
    # -------------------------------------------------
    liquidity_engine = LiquidityEngine(enriched_df, swings, timeframe=tf)
    equal_liquidity = liquidity_engine.get_liquidity()

    # -------------------------------------------------
    # L5 Session Liquidity
    # -------------------------------------------------
    session_engine = SessionLiquidityEngine(enriched_df)
    session_levels = session_engine.get_session_liquidity()

    # -------------------------------------------------
    # L6 Liquidity Imbalance
    # -------------------------------------------------
    liquidity_imbalance_engine = LiquidityImbalanceEngine(
        equal_liquidity,
        session_levels
    )

    imbalance = liquidity_imbalance_engine.get_liquidity_bias()

    print("\nLIQUIDITY BIAS")
    print(imbalance)

    # -------------------------------------------------
    # L7 Imbalances
    # -------------------------------------------------
    imbalance_engine = ImbalanceEngine(enriched_df)
    imbalances = imbalance_engine.get_imbalances()

    # -------------------------------------------------
    # L20 Smart Money
    # -------------------------------------------------
    sm_engine = SmartMoneyEngine(
        df=enriched_df,
        equal_liquidity=equal_liquidity,
        imbalances=imbalances
    )

    smart_money = sm_engine.detect_events()

    print("\nSMART MONEY EVENTS")
    print(smart_money)

    # -------------------------------------------------
    # L19 Heatmap
    # -------------------------------------------------
    heatmap_engine = LiquidityHeatmapEngine(
        df=enriched_df,
        zones=zones,
        equal_liquidity=equal_liquidity,
        session_levels=session_levels,
        imbalances=imbalances
    )

    heatmap = heatmap_engine.generate_heatmap()

    # -------------------------------------------------
    # L8 Volatility
    # -------------------------------------------------
    regime_engine = VolatilityRegimeEngine(enriched_df)
    regime = regime_engine.get_regime()

    print("\nVOLATILITY")
    print(regime)

    # -------------------------------------------------
    # L9 Reaction
    # -------------------------------------------------
    reaction_engine = ReactionStrengthEngine(enriched_df)

    if not zones["resistance"]:
        return None

    top_zone = zones["resistance"][0]

    reaction_score = reaction_engine.analyze_reaction(
        level_price=(top_zone["zone_low"] + top_zone["zone_high"]) / 2,
        level_type="resistance"
    )

    print("\nREACTION SCORE:", reaction_score)

    # -------------------------------------------------
    # L10 Confluence
    # -------------------------------------------------
    confluence_engine = ConfluenceEngine(
        structure_state=structure_state,
        liquidity_bias=imbalance,
        imbalances=imbalances,
        regime=regime,
        valuation_state=valuation,
        reaction_score=reaction_score,
    )

    result = confluence_engine.score_zone(top_zone)

    print("\nCONFLUENCE")
    print(result)

    # -------------------------------------------------
    # L11 Probability
    # -------------------------------------------------
    prob_engine = ProbabilityEngine(
        confluence_result=result,
        liquidity_bias=imbalance,
        structure_state=structure_state,
        regime=regime,
        imbalances=imbalances
    )

    prob = prob_engine.estimate()

    print("\nPROBABILITY")
    print(prob)

    # -------------------------------------------------
    # L12 Path Prediction
    # -------------------------------------------------
    path_engine = PathPredictorEngine(
        liquidity_bias=imbalance,
        session_levels=session_levels,
        imbalances=imbalances,
        structure_state=structure_state,
        regime=regime,
    )

    path = path_engine.predict()

    print("\nPATH PREDICTION")
    print(path)

    # -------------------------------------------------
    # L13 Liquidity Map
    # -------------------------------------------------
    map_engine = LiquidityMapEngine(
        df=enriched_df,
        equal_liquidity=equal_liquidity,
        session_levels=session_levels,
        imbalances=imbalances,
        path_prediction=path,
    )

    liquidity_map = map_engine.generate_map()

    print("\nLIQUIDITY MAP")
    print(liquidity_map)

    # -------------------------------------------------
    # L21 Liquidity Gravity
    # -------------------------------------------------
    gravity_engine = LiquidityGravityEngine(
        current_price=enriched_df["close"].iloc[-1],
        liquidity_map=liquidity_map
    )

    gravity = gravity_engine.compute_gravity()

    print("\nLIQUIDITY GRAVITY")
    print(gravity)

    # -------------------------------------------------
    # L17 Projection
    # -------------------------------------------------
    current_price = enriched_df["close"].iloc[-1]

    projection_engine = ProjectionEngine(
        current_price=current_price,
        path_prediction=path,
        liquidity_map=liquidity_map,
        imbalances=imbalances,
        probability=prob,
        smart_money=smart_money
    )

    projection = projection_engine.generate_projection()

    # -------------------------------------------------
    # L18 Monte Carlo
    # -------------------------------------------------
    bias = 0

    if "Upside" in path["direction"]:
        bias = 0.3
    elif "Downside" in path["direction"]:
        bias = -0.3

    mc_engine = MonteCarloProjectionEngine(
        current_price=current_price,
        volatility=0.002,
        steps=30,
        simulations=200,
        bias=bias
    )

    monte_carlo = mc_engine.build_probability_cone()

    # -------------------------------------------------
    # L14 Text Report
    # -------------------------------------------------
    summary_engine = TextSummaryEngine(
        timeframe=tf,
        structure=structure_state,
        liquidity_bias=imbalance,
        regime=regime,
        probability=prob,
        path_prediction=path,
        liquidity_map=liquidity_map,
        gravity=gravity
    )

    report = summary_engine.generate_summary()

    print("\n")
    print(report)

    # -------------------------------------------------
    # L15 Visualization
    # -------------------------------------------------
    viz = VisualizationEngine(
        df=enriched_df,
        zones=zones,
        equal_liquidity=equal_liquidity,
        session_levels=session_levels,
        imbalances=imbalances,
        liquidity_map=liquidity_map,
        projection=projection,
        monte_carlo=monte_carlo,
        heatmap=heatmap,
        title=f"{tf.upper()} BTC Structural Intelligence"
    )

    viz.plot()

    return {
        "structure": structure_state,
        "liquidity_bias": imbalance,
        "regime": regime,
        "probability": prob,
        "path": path,
        "valuation": valuation,
        "liquidity_map": liquidity_map,
        "gravity": gravity
    }


# =========================================================
# MAIN EXECUTION
# =========================================================
if __name__ == "__main__":

    data_engine = DataEngine()
    multi_tf_data = data_engine.get_all_timeframes()

    tf_outputs = {}
    full_report_text = []

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"btc_intelligence_report_{timestamp}.txt"

    for timeframe, dataframe in multi_tf_data.items():

        output = run_timeframe_pipeline(timeframe, dataframe)

        if output:

            tf_outputs[timeframe] = output

            summary_engine = TextSummaryEngine(
                timeframe=timeframe,
                structure=output["structure"],
                liquidity_bias=output["liquidity_bias"],
                regime=output["regime"],
                probability=output["probability"],
                path_prediction=output["path"],
                liquidity_map=output["liquidity_map"],
                gravity=output["gravity"]
            )

            full_report_text.append(summary_engine.generate_summary())

    # -------------------------------------------------
    # L16 Multi Timeframe Aggregation
    # -------------------------------------------------
    mtf_engine = MultiTimeframeAggregator(tf_outputs)
    global_view = mtf_engine.aggregate()

    global_section = "\n" + "=" * 70 + "\n"
    global_section += "GLOBAL MULTI-TIMEFRAME VIEW\n"
    global_section += "=" * 70 + "\n"
    global_section += str(global_view) + "\n"

    print(global_section)

    full_report_text.append(global_section)

    # -------------------------------------------------
    # Save Report
    # -------------------------------------------------
    with open(filename, "w") as f:
        f.write("\n\n".join(full_report_text))

    print(f"\nReport successfully saved to: {filename}")
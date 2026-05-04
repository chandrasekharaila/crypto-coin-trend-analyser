# engine/zone_engine.py
#L3
import numpy as np


class ZoneEngine:
    def __init__(self, df, swings, timeframe, zone_multiplier=0.5):
        self.df = df
        self.swings = swings
        self.timeframe = timeframe
        self.zone_multiplier = zone_multiplier

        self.atr_mean = self.df["atr"].mean()
        self.zone_width = self.atr_mean * self.zone_multiplier

        self.support_zones = []
        self.resistance_zones = []

        self._build_zones()
        self._merge_overlaps()
        self._compute_zone_strength()

    # =====================================================
    # BUILD INITIAL ZONES
    # =====================================================

    def _build_zones(self):
        highs = [s for s in self.swings if s["type"] == "high"]
        lows = [s for s in self.swings if s["type"] == "low"]

        self.resistance_zones = self._cluster_zones(highs, "resistance")
        self.support_zones = self._cluster_zones(lows, "support")

    def _cluster_zones(self, swing_list, zone_type):
        zones = []

        for swing in swing_list:
            price = swing["price"]
            timestamp = swing["timestamp"]

            matched = False

            for zone in zones:
                if zone["zone_low"] <= price <= zone["zone_high"]:
                    zone["touches"] += 1
                    zone["zone_low"] = min(zone["zone_low"], price - self.zone_width / 2)
                    zone["zone_high"] = max(zone["zone_high"], price + self.zone_width / 2)
                    zone["last_touch"] = timestamp
                    matched = True
                    break

            if not matched:
                zones.append({
                    "type": zone_type,
                    "zone_low": price - self.zone_width / 2,
                    "zone_high": price + self.zone_width / 2,
                    "touches": 1,
                    "timeframe": self.timeframe,
                    "last_touch": timestamp,
                })

        return zones

    # =====================================================
    # MERGE OVERLAPPING ZONES
    # =====================================================

    def _merge_overlaps(self):
        def merge(zones):
            zones = sorted(zones, key=lambda x: x["zone_low"])
            merged = []

            for zone in zones:
                if not merged:
                    merged.append(zone)
                else:
                    prev = merged[-1]
                    if zone["zone_low"] <= prev["zone_high"]:
                        prev["zone_high"] = max(prev["zone_high"], zone["zone_high"])
                        prev["zone_low"] = min(prev["zone_low"], zone["zone_low"])
                        prev["touches"] += zone["touches"]
                        prev["last_touch"] = max(prev["last_touch"], zone["last_touch"])
                    else:
                        merged.append(zone)

            return merged

        self.resistance_zones = merge(self.resistance_zones)
        self.support_zones = merge(self.support_zones)

    # =====================================================
    # STRENGTH COMPUTATION
    # =====================================================

    def _compute_zone_strength(self):
        all_zones = self.resistance_zones + self.support_zones

        if not all_zones:
            return

        max_touches = max(z["touches"] for z in all_zones)

        current_index = self.df.index[-1]

        for zone in all_zones:
            normalized_touches = zone["touches"] / max_touches

            bars_since_touch = (
                len(self.df) - self.df.index.get_loc(zone["last_touch"])
            )

            recency_score = 1 / (1 + bars_since_touch / 50)

            base_strength = 0.6 * normalized_touches + 0.4 * recency_score

            zone["recency_score"] = round(recency_score, 3)
            zone["base_strength"] = round(min(1.0, base_strength), 3)

        # Sort strongest first
        self.resistance_zones.sort(key=lambda x: x["base_strength"], reverse=True)
        self.support_zones.sort(key=lambda x: x["base_strength"], reverse=True)

    # =====================================================
    # PUBLIC
    # =====================================================

    def get_zones(self):
        return {
            "support": self.support_zones,
            "resistance": self.resistance_zones,
        }
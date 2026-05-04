# engine/session_liquidity_engine.py
#L5
import pandas as pd


class SessionLiquidityEngine:
    def __init__(self, df):
        self.df = df.copy()

        self.session_levels = {}

        self._build_previous_day_levels()
        self._build_intraday_sessions()
        self._detect_sweeps()

    # =====================================================
    # PREVIOUS DAY HIGH / LOW
    # =====================================================

    def _build_previous_day_levels(self):
        df = self.df.copy()

        df["date"] = df.index.date

        grouped = df.groupby("date")

        daily = grouped.agg({
            "high": "max",
            "low": "min"
        })

        if len(daily) < 2:
            return

        prev_day = daily.iloc[-2]

        self.session_levels["PDH"] = {
            "price": float(prev_day["high"]),
            "type": "buy_liquidity",
            "swept": False
        }

        self.session_levels["PDL"] = {
            "price": float(prev_day["low"]),
            "type": "sell_liquidity",
            "swept": False
        }

    # =====================================================
    # INTRADAY SESSION LEVELS (UTC)
    # =====================================================

    def _build_intraday_sessions(self):
        df = self.df.copy()

        today = df.index[-1].date()
        today_df = df[df.index.date == today]

        if today_df.empty:
            return

        sessions = {
            "Asia": (0, 8),
            "London": (8, 16),
            "US": (16, 24),
        }

        for name, (start, end) in sessions.items():
            session_df = today_df[
                (today_df.index.hour >= start) &
                (today_df.index.hour < end)
            ]

            if session_df.empty:
                continue

            self.session_levels[f"{name}_High"] = {
                "price": float(session_df["high"].max()),
                "type": "buy_liquidity",
                "swept": False
            }

            self.session_levels[f"{name}_Low"] = {
                "price": float(session_df["low"].min()),
                "type": "sell_liquidity",
                "swept": False
            }

    # =====================================================
    # SWEEP DETECTION
    # =====================================================

    def _detect_sweeps(self):
        last_price = self.df["close"].iloc[-1]

        for level in self.session_levels.values():
            if level["type"] == "buy_liquidity" and last_price > level["price"]:
                level["swept"] = True

            if level["type"] == "sell_liquidity" and last_price < level["price"]:
                level["swept"] = True

    # =====================================================
    # PUBLIC
    # =====================================================

    def get_session_liquidity(self):
        return self.session_levels
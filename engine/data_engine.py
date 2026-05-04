#L0
import os
import ccxt
import pandas as pd
from datetime import datetime, timezone
from config.settings import (
    SYMBOL,
    EXCHANGE,
    TIMEFRAMES,
    DATA_DIRECTORY,
    INITIAL_FETCH_LIMIT,
    UPDATE_FETCH_LIMIT,
)


class DataEngine:
    def __init__(self):
        self.symbol = SYMBOL
        self.exchange_name = EXCHANGE
        self.timeframes = TIMEFRAMES
        self.data_dir = DATA_DIRECTORY

        os.makedirs(self.data_dir, exist_ok=True)

        self.exchange = getattr(ccxt, self.exchange_name)(
            {
                "enableRateLimit": True,
                "options": {
                    "defaultType": "future"  # Binance USDT perpetual
                },
            }
        )

    # =====================================================
    # PUBLIC METHODS
    # =====================================================

    def get_all_timeframes(self):
        data = {}
        for tf in self.timeframes:
            df = self._load_or_update_timeframe(tf)
            data[tf] = df
            print(f"{self.symbol} {tf} loaded: {len(df)} candles")

        print("All timeframes synchronized.\n")
        return data

    def get_timeframe(self, timeframe):
        if timeframe not in self.timeframes:
            raise ValueError(f"{timeframe} not configured in TIMEFRAMES")
        return self._load_or_update_timeframe(timeframe)

    # =====================================================
    # CORE LOGIC
    # =====================================================

    def _load_or_update_timeframe(self, timeframe):
        filepath = self._get_filepath(timeframe)

        if os.path.exists(filepath):
            df = pd.read_parquet(filepath)
            df.index = pd.to_datetime(df.index, utc=True)
            df = self._update_data(df, timeframe)
        else:
            df = self._fetch_full_history(timeframe)

        df = self._clean_dataframe(df)
        df.to_parquet(filepath)

        return df

    def _fetch_full_history(self, timeframe):
        print(f"Fetching full history for {timeframe}...")

        raw = self.exchange.fetch_ohlcv(
            self.symbol,
            timeframe=timeframe,
            limit=INITIAL_FETCH_LIMIT,
        )

        df = self._build_dataframe(raw)
        return df

    def _update_data(self, existing_df, timeframe):
        if existing_df.empty:
            return self._fetch_full_history(timeframe)

        last_timestamp = int(existing_df.index[-1].timestamp() * 1000)

        print(f"Updating {timeframe} from {existing_df.index[-1]}")

        raw = self.exchange.fetch_ohlcv(
            self.symbol,
            timeframe=timeframe,
            since=last_timestamp,
            limit=UPDATE_FETCH_LIMIT,
        )

        if not raw:
            return existing_df

        new_df = self._build_dataframe(raw)

        combined = pd.concat([existing_df, new_df])
        combined = combined[~combined.index.duplicated(keep="last")]

        return combined

    # =====================================================
    # DATA PROCESSING
    # =====================================================

    def _build_dataframe(self, raw_ohlcv):
        df = pd.DataFrame(
            raw_ohlcv,
            columns=["timestamp", "open", "high", "low", "close", "volume"],
        )

        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        df.set_index("timestamp", inplace=True)

        df = df.astype(float)

        df = self._add_derived_features(df)

        return df

    def _add_derived_features(self, df):
        df["range"] = df["high"] - df["low"]
        df["body_size"] = (df["close"] - df["open"]).abs()
        df["upper_wick"] = df["high"] - df[["open", "close"]].max(axis=1)
        df["lower_wick"] = df[["open", "close"]].min(axis=1) - df["low"]
        return df

    def _clean_dataframe(self, df):
        df = df.sort_index()

        # Drop forming candle (avoid lookahead bias)
        if len(df) > 1:
            df = df.iloc[:-1]

        df = df[~df.index.duplicated(keep="last")]

        return df

    # =====================================================
    # UTILITIES
    # =====================================================

    def _get_filepath(self, timeframe):
        safe_symbol = self.symbol.replace("/", "")
        return os.path.join(self.data_dir, f"{safe_symbol}_{timeframe}.parquet")
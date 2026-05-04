# 📊 Structural Intelligence Engine

A multi-layer market analysis engine that combines structure, liquidity, and probabilistic modeling to generate high-quality trading insights across multiple timeframes.

## 🔍 Analysis Layers

- **L1 – Structure**: Identifies market trend and swing points  
- **L2 – Valuation**: Determines premium and discount zones  
- **L3 – Zones**: Detects supply and demand areas  
- **L4 – Liquidity**: Finds equal highs/lows (liquidity pools)  
- **L5 – Session Liquidity**: Tracks session-based liquidity levels  
- **L6 – Liquidity Bias**: Determines directional bias from liquidity  
- **L7 – Imbalances**: Detects inefficiencies (fair value gaps)  
- **L8 – Volatility**: Classifies current market regime  
- **L9 – Reaction**: Measures price response strength at key levels  
- **L10 – Confluence**: Combines multiple signals into a score  
- **L11 – Probability**: Estimates likelihood of outcomes  
- **L12 – Path Prediction**: Predicts expected price movement  
- **L13 – Liquidity Map**: Maps key liquidity zones  
- **L14 – Text Summary**: Generates human-readable insights  
- **L15 – Visualization**: Plots charts and analysis  
- **L16 – Multi-Timeframe**: Aggregates across timeframes  
- **L17 – Projection**: Generates price targets  
- **L18 – Monte Carlo**: Simulates probabilistic price paths  
- **L19 – Heatmap**: Visualizes liquidity density  
- **L20 – Smart Money**: Detects institutional activity  
- **L21 – Liquidity Gravity**: Models price attraction toward liquidity  

## ⚙️ Configuration

Change the coin by updating the symbol in config/settings.py:

```python
SYMBOL = "BTC/USDT"

import json
import pandas as pd
import matplotlib.pyplot as plt

# -------------------------
# 1. LOAD trade_prices.json
# -------------------------
with open("data/trade_prices.json", "r") as f:
    trade_data = json.load(f)

trade_rows = []
for ts, v in trade_data.items():
    trade_rows.append({
        "timestamp": int(ts),
        "price": v["price"]
    })

df_trade = pd.DataFrame(trade_rows)


# -------------------------
# 2. LOAD oracle_prices.json
# -------------------------
with open("data/oracle_prices.json", "r") as f:
    oracle_data = json.load(f)

oracle_rows = []
for k, v in oracle_data.items():
    oracle_rows.append({
        "timestamp": int(v["timestamp"]),
        "price": v["price"] / 1e8  # convert from 8 decimals
    })

df_oracle = pd.DataFrame(oracle_rows)


# -------------------------
# 3. LOAD trades.csv
# -------------------------
df_csv = pd.read_csv("data/ETHUSD-trades-2026-04-28.csv", header=None)

df_csv = df_csv.rename(columns={
    1: "price",
    4: "timestamp"
})

df_csv = df_csv[["timestamp", "price"]]


# -------------------------
# 4. LOAD calculated_prices.json
# -------------------------
with open("data/calculated_prices.json", "r") as f:
    calculated_data = json.load(f)

calculated_rows = []
for k, v in calculated_data.items():
    calculated_rows.append({
        "timestamp": int(k),
        "price": v
    })

df_calculated = pd.DataFrame(calculated_rows)


# -------------------------
# 4. CLEAN + NORMALIZE TIME
# -------------------------
# convert timestamps (assume oracle + trade are seconds, csv is microseconds)
df_csv["timestamp"] = df_csv["timestamp"] / 1e6


# -------------------------
# 5. AGGREGATE (important)
# -------------------------
df_trade = df_trade.groupby("timestamp").mean().reset_index()
df_oracle = df_oracle.groupby("timestamp").mean().reset_index()
df_csv = df_csv.groupby("timestamp").mean().reset_index()
df_calculated = df_calculated.groupby("timestamp").mean().reset_index()


# -------------------------
# 6. PLOT ALL 4
# -------------------------
plt.figure(figsize=(14, 6))

plt.plot(df_trade["timestamp"], df_trade["price"], label="AMM Trade Price", alpha=0.8)
plt.plot(df_oracle["timestamp"], df_oracle["price"], label="Oracle Price", alpha=0.8)
plt.plot(df_csv["timestamp"], df_csv["price"], label="Binance Price", alpha=0.8)
plt.plot(df_calculated["timestamp"], df_calculated["price"], label="Calculated AMM Price", alpha=0.8)

plt.title("Price Comparison: Calculated vs AMM vs Oracle vs Market")
plt.xlabel("Timestamp")
plt.ylabel("Price")
plt.legend()
plt.grid(True)

plt.show()
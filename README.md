### 1. Fallback oracle source
https://basescan.org/address/0x2A375567f5E13F6bd74fDa7627Df3b1Af6BfA5a6
- **Return types:**
```
// 128 + 64 + 64 = 256 bits (slot size)
    struct TokenInfo {
        uint128 price; // as chainlink oracle (e.g. decimal = 8)                zip: 32 bits = (27, 5)
        uint64 coeff; // k: decimal = 18.    18.4 * 1e18                        zip: 16 bits = (11, 5), 2^11 = 2048
        uint64 spread; // s: decimal = 18.   spread <= 2e18   18.4 * 1e18       zip: 16 bits = (11, 5)
    }
```



### 2. Flow of funds in swap
```
Entrypoint:
User
  │
  │ calls swap function on below vault
  ▼
0x83817A0F7985D055684f01769427bF024373cF5a (vault)
```

- `swap(tuple[] payloads,address outputToken,uint256 amountOutMin,uint256 feePct)` called with output token as `WETH`
and input token as `USDC`

- The vault in this case already been approved by user for spending `USDC` (`37.214018 USDC`). `0.010466 USDC` go to [Fee account](https://basescan.org/address/0xa2fe8E38A14CF7BeECE22aE71E951F78CE233643),
after which, `37.203552 USDC` are left to swap with `WETH`

- The vault approves this amount for [JAMBalanceManager](https://basescan.org/address/0xc5a350853e4e36b73eb0c24aaa4b8816c9a3579a) to spend,
[JAMSettlement](https://basescan.org/address/0xbeb0b0623f66be8ce162ebdfa2ec543a522f4ea6) transfers this amount to a [proxy contract](https://basescan.org/address/0x5cf91ea0b4d5b2aef1607c58683b21aa23e84779)

- This proxy contract transfers the funds to [ElfomoFi Contract](https://basescan.org/address/0xf0f0F0F0FB0d738452EfD03A28e8be14C76d5f73)
  and triggers the `swapWithContractBalance` function.
  
- ElfomoFi's contract gets `amountOut` from its [pricing contract](https://basescan.org/address/0x344E39498b5e47a8A628ffA8c325019b3988583c), and deposits
  the USDC to a [GnosisSafe](https://basescan.org/address/0xBb1b19F138dB3925883a96FF7a304277460E0C99), which is probably a vault.

- This vault transfers WETH corresponding to `amountOut` all the way back to the user's vault


### 3. Pricing contract
- **Contract address that stores the pricing logic:** https://basescan.org/address/0x344E39498b5e47a8A628ffA8c325019b3988583c
- **Slot being updated per block:** slot `0x0000000000000000000000000000000000000000000000000000000000000001` is being updated regularly on contract `0x344E39498b5e47a8A628ffA8c325019b3988583c`

#### Breakdown of what the slot contains:
```
example raw value this slot contains: 0x000000000000000000000000000000002b0d02ae3629000069e74fb601634d08

| Field     |   Bits   | Hex        | Decimal       | 
|-----------|----------|------------|---------------|
| price     | 0..31    | 0x01634d08 | 23,285,000    |     <---- ETH price (decimals=4) at below timestamp
| timestamp | 32..63   | 0x69e74fb6 | 1,776,766,902 |     <---- This shows Tuesday, April 21, 2026 at 10:21:42 AM UTC
| spread    | 80..95   | 0x3629     | 13,865        |     <---- Likely denotes spread
| coeff     | 96..111  | 0x02ae     | 686           |     <---- Likely denotes coeff (rarely updated)
| counter   | 112..127 | 0x2b0d     | 11021         |     <---- No. of times this slot has been updated
```



## Pricing logic

- This algorithm implements a simplified hybrid AMM pricing model.
- It converts a USDC input (dx) into an ETH output (dy) using:
  - an oracle mid-price (p_mid)
  - a bid/ask spread (spread)
  - a liquidity-dependent slippage coefficient (k)

- All on-chain values are stored in fixed-point format and normalized before computation:

USDC uses 6 decimals
price uses 8 decimals
spread and k use 1e18

The final execution price is derived from the ask price adjusted for spread, and then further adjusted for nonlinear slippage proportional to trade size.

### Price Components:

#### 1. Mid Price (Oracle Price):
```math
p_{mid} = \frac{p_{oracle}}{10^8}
```
where $`p_{oracle}`$ is market price (anchor for value)

#### 2. Spread Adjustment:

```math
p_{ask} = p_{mid} \cdot \left(1 + \frac{s}{2}\right)
```
where s is spread

#### 3. Liquidity Slippage:

```math
\text{slippage factor} = (1 + k \cdot dx)
```

where:

- $`k = \frac{k_{raw}}{10^{18}}`$
- $`dx`$ is USDC input (normalized)

This introduces nonlinear price impact based on trade size.


#### 4. Final Execution Formula

```math
dy = \frac{dx}{p_{ask} \cdot (1 + k \cdot dx)}
```



## Plots

We overlay four price series to evaluate the performance of the pricing model against real market execution and external benchmarks.

## 📦 Data Sources

Reference dataset:  
https://github.com/Created-for-a-purpose/prop-amm/tree/main/data


### 1. On-chain trade execution prices
- Source: `ElfomoTrade` event logs
- Block range: `45272776 → 45272776`
- Represents realized swap execution prices for ETH/USDC trades on-chain
- Used as the empirical ground truth for actual trade execution


### 2. Oracle mid prices
- Source: WooFi fallback oracle
- Same block range as trade data
- Represents the **fair market mid-price (p₀)** used as the pricing anchor for the model


### 3. Centralized exchange benchmark (Binance)
- Source: Binance historical ETH/USDC market data
- Used as an external reference for global price consistency
- Helps validate oracle alignment with off-chain market conditions


### 4. Model-derived prices
- Computed using our pricing function
- Inputs:
  - `inAmount` (trade size from above trade dataset)
  - `price` (oracle mid-price from above oracle dataset)
  - `spread`
  - `coeff (k)`


<img width="1512" height="909" alt="image" src="https://github.com/user-attachments/assets/f3928d80-4769-4abb-bf9c-9d627c6a1972" />


## How to run?

```
# Index trade data
# Update block range manually
python indexers/index-events.py

# Index oracle data
# Update block range manually
python indexers/index-oracle.py

# Binance data
# Manually add .csv to data/ for corresponding time range

# Data from our pricing algorithm
python pricing.py

# Plot data
python plot.py
```

# This script calculates the price of WETH in USDC for each trade using the quote function

def quote_usdc_to_eth(dx, p_mid, spread, k):
    USDC_DECIMALS = 1e6
    PRICE_DECIMALS = 1e8
    DECIMAL_SCALE_18 = 1e18

    # normalize
    dx_f = dx / USDC_DECIMALS
    p0 = p_mid / PRICE_DECIMALS
    s = spread / DECIMAL_SCALE_18
    k_f = k  / DECIMAL_SCALE_18

    # ask price
    p_ask = p0 * (1 + s / 2)

    # output
    dy = dx_f / (p_ask * (1 + k_f * dx_f))
    return dy


if __name__ == "__main__":
    import json
    trades = json.load(open('data/trade_prices.json', 'r'))
    reserve_balances = json.load(open('data/reserve_balances.json', 'r'))
    oracle_prices = json.load(open('data/oracle_prices.json', 'r'))

    results = {}

    for ts in trades.keys():
        trade = trades[ts]
        block_number = trade['blockNumber']
        usdc_in = trade['usdcAmount']
        tx_hash = trade['transactionHash']
        weth_balance = reserve_balances[tx_hash]['reserve_weth']
        usdc_balance = reserve_balances[tx_hash]['reserve_usdc']
        oracle_price = None
        coeff = None
        spread = None

        for radius in range(0, 100):
            price_data = oracle_prices.get(str(block_number - radius))
            if price_data:
                oracle_price = price_data['price']
                coeff = price_data['coeff']
                spread = price_data['spread']
                break
        
        if oracle_price is None:
            print(f"No oracle price found for block {block_number} or nearby blocks.")
            continue

        dy = quote_usdc_to_eth(usdc_in, oracle_price, spread, coeff)
        price = (usdc_in / dy) / 1e6
        # print(f"Calculated WETH: {dy}, calculated price: {price}")
        results[ts] = price
        
    with open('data/calculated_prices.json', 'w') as f:
        json.dump(results, f, indent=4)
    print(f"Calculated {len(results)} / {len(trades)} prices and saved to data/calculated_prices.json")
    
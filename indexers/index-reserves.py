import os
from web3 import Web3
import json
import time

# --- CONFIG ---
RPC_URL = f"https://base-mainnet.g.alchemy.com/v2/{os.environ.get('ALCHEMY_API_KEY')}"

# -- FILTER
WETH = "0x4200000000000000000000000000000000000006"
USDC = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
INPUT_BALANCE_OF = "0x70a08231000000000000000000000000bb1b19f138db3925883a96ff7a304277460e0c99"

# --- INIT ---
w3 = Web3(Web3.HTTPProvider(RPC_URL))


# --- FETCH RESERVE BALANCES ---
def fetch_reserve_balance(tx_hash):
    try:
        trace = w3.provider.make_request("debug_traceTransaction", [tx_hash, {"tracer": "callTracer"}])
        calls = trace["result"]["calls"]

        # find balanceOf calls for WETH and USDC
        reserve_weth = None
        reserve_usdc = None

        def recurse_calls(node_list):
            nonlocal reserve_weth, reserve_usdc

            for call in node_list:
                input_data = call.get("input", "")
                if input_data == INPUT_BALANCE_OF:
                    to_address = call.get("to", "")
                    output = call.get("output")
                    if to_address == WETH:
                        reserve_weth = int(output, 16)
                    elif to_address == USDC:
                        reserve_usdc = int(output, 16)

                # if found both, signal to stop recursion
                if reserve_weth is not None and reserve_usdc is not None:
                    return True

                # recurse into nested calls
                if call.get("calls"):
                    if recurse_calls(call["calls"]):
                        return True

            return False

        recurse_calls(calls)

        return {
            "tx_hash": tx_hash,
            "reserve_weth": reserve_weth,
            "reserve_usdc": reserve_usdc,
        }

    except Exception as e:
        print(f"Error at tx_hash {tx_hash}: {e}")
        return None


# --- MAIN LOOP ---
if __name__ == "__main__":
    results = {}

    trades = json.load(open("data/trade_prices.json", "r"))
    tx_hashes = [trade["transactionHash"] for trade in trades.values()]
    print(f"Fetching reserve balances for {len(tx_hashes)} transactions...")

    for tx_hash in tx_hashes:
        r = fetch_reserve_balance(tx_hash)
        if r:
            results[r["tx_hash"]] = {
                "reserve_weth": r["reserve_weth"],
                "reserve_usdc": r["reserve_usdc"],
            }
        if len(results) % 10 == 0:
            print(f"% Progress: {len(results) / len(tx_hashes) * 100:.2f}%")
        
        time.sleep(0.1)  # small delay to avoid rate limits

    print(f"Fetched {len(results)} / {len(tx_hashes)} reserve balances")

    # save results to file
    with open("data/reserve_balances_2.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved {len(results)} reserve balances to data/reserve_balances.json")

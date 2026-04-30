import os
from concurrent.futures import ThreadPoolExecutor
from web3 import Web3

# --- CONFIG ---
RPC_URL = f"https://base-mainnet.g.alchemy.com/v2/{os.environ.get('ALCHEMY_API_KEY')}"
CONTRACT_ADDRESS = "0x2A375567f5E13F6bd74fDa7627Df3b1Af6BfA5a6"
CONTRACT_ABI = [{
    "inputs":[{"internalType":"address","name":"","type":"address"}],
    "name":"infos",
    "outputs":[
        {"internalType":"uint128","name":"price","type":"uint128"},
        {"internalType":"uint64","name":"coeff","type":"uint64"},
        {"internalType":"uint64","name":"spread","type":"uint64"}
    ],
    "stateMutability":"view",
    "type":"function"
}]

# -- BLOCK RANGE
FROM_BLOCK =   45272776  # Apr-28-2026 12:08:19 AM +UTC
TO_BLOCK   =   45315127  # Apr-28-2026 11:40:01 PM +UTC
START_TIMESTAMP = 1777334899 # Timestamp of FROM_BLOCK

# -- FILTER
WETH = "0x4200000000000000000000000000000000000006"

# --- INIT ---
w3 = Web3(Web3.HTTPProvider(RPC_URL))
contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=CONTRACT_ABI)


# --- FETCH SINGLE BLOCK ---
def fetch_price(block):
    try:
        price, coeff, spread = contract.functions.infos(
            Web3.to_checksum_address(WETH)
        ).call(block_identifier=block)

        ts = (block - FROM_BLOCK) * 2 + START_TIMESTAMP  # Assuming 2 seconds per block

        return {
            "block": block,
            "timestamp": ts,
            "price": price,
            "coeff": coeff,
            "spread": spread
        }

    except Exception as e:
        print(f"Error at block {block}: {e}")
        return None


# --- BATCH WORKER ---
async def process_batch(blocks):
    tasks = [fetch_price(b) for b in blocks]
    return await asyncio.gather(*tasks)


# --- MAIN LOOP ---
if __name__ == "__main__":
    results = {}

    blocks = list(range(FROM_BLOCK, TO_BLOCK + 1))

    with ThreadPoolExecutor(max_workers=20) as executor:
        for r in executor.map(fetch_price, blocks):
            if r:
                block = r["block"]
                results[block] = r
                if block % 100 == 0:
                    print(f"Progress: {block} / {TO_BLOCK}")

    print(f"Fetched {len(results)} / {len(blocks)} price points")

    # save
    import json
    with open("data/oracle_prices.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved {len(results)} price points to data/oracle_prices.json")

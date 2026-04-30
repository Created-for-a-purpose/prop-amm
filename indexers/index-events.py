import os
from web3 import Web3

# --- CONFIG ---
RPC_URL = f"https://base-mainnet.g.alchemy.com/v2/{os.environ.get('ALCHEMY_API_KEY')}"
CONTRACT_ADDRESS = "0xf0f0F0F0FB0d738452EfD03A28e8be14C76d5f73"
CONTRACT_ABI = [{
    "anonymous": False,
    "inputs":[
        {"indexed":True, "internalType":"uint256", "name":"quoteId", "type":"uint256"},
        {"indexed":True, "internalType":"uint256", "name":"partnerId", "type":"uint256"},
        {"indexed":False, "internalType":"address", "name":"executor", "type":"address"},
        {"indexed":False, "internalType":"address", "name":"receiver", "type":"address"},
        {"indexed":False, "internalType":"address", "name":"fromToken", "type":"address"},
        {"indexed":False, "internalType":"address", "name":"toToken", "type":"address"},
        {"indexed":False, "internalType":"uint256", "name":"fromAmount", "type":"uint256"},
        {"indexed":False, "internalType":"uint256", "name":"toAmount", "type":"uint256"}
    ],
    "name":"ElfomoTrade",
    "type":"event"
}]
TOPIC_HASH = "0xbe65a3f1f381da16732df786f571604a72b7c122cff3ae2b355566ddf01e2528"

# -- BLOCK RANGE
FROM_BLOCK =   45272776  # Apr-28-2026 12:08:19 AM +UTC
TO_BLOCK   =   45315127  # Apr-28-2026 11:40:01 PM +UTC
START_TIMESTAMP = 1777334899 # Timestamp of FROM_BLOCK

# -- FILTER
FROM_TOKEN = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913" # USDC
TO_TOKEN = "0x4200000000000000000000000000000000000006" # WETH

# --- INIT ---
w3 = Web3(Web3.HTTPProvider(RPC_URL))
contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=CONTRACT_ABI)


# --- FETCH EVENTS ---
def fetch_events(event_name, from_block, to_block, step=5000):
    logs = w3.eth.get_logs({
        "fromBlock": from_block,
        "toBlock": to_block,
        "address": Web3.to_checksum_address(CONTRACT_ADDRESS),
        "topics": [TOPIC_HASH]
    })
    events = []
    for log in logs:
        event = contract.events.ElfomoTrade().process_log(log)
        events.append({
            "fromToken": event.args.fromToken,
            "toToken": event.args.toToken,
            "fromAmount": event.args.fromAmount,
            "toAmount": event.args.toAmount,
            "blockNumber": log.blockNumber,
            "transactionHash": log.transactionHash.hex()
        })
    return events


# --- USAGE ---
if __name__ == "__main__":
    events = fetch_events("ElfomoTrade", FROM_BLOCK, TO_BLOCK)
    
    prices = {}
    total = 0

    for event in events:
        if event["fromToken"].lower() == FROM_TOKEN.lower() and event["toToken"].lower() == TO_TOKEN.lower():
            blockNumber = event["blockNumber"]
            timestamp = ( blockNumber - FROM_BLOCK ) * 2 + START_TIMESTAMP # Assuming 2 seconds per block
            price = ( event["fromAmount"] / event["toAmount"] ) * 10 ** 12 # Adjust for USDC decimals

            prices[timestamp] = {
                "blockNumber": blockNumber,
                "price": price,
                "usdcAmount": event["fromAmount"],
                "wethAmount": event["toAmount"],
                "transactionHash": event["transactionHash"]
            }

            total += 1
    print(f"Fetched {total} trades")

    # Dump prices to data/trade_prices.json
    import json
    with open("data/trade_prices.json", "w") as f:
        json.dump(prices, f, indent=4)
    print(f"Saved {len(prices)} price points to data/trade_prices.json")
    
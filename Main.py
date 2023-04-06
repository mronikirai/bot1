import requests
import time

OPENSEA_API_BASE = "https://api.opensea.io/api/v1"
OPENSEA_API_KEY = "your_opensea_api_key"
YOUR_ETHEREUM_ADDRESS = "your_ethereum_address"

TIME_WINDOW_DAYS = 7
PRICE_THRESHOLD = 0.8

def get_top_collections():
    url = f"{OPENSEA_API_BASE}/collections"
    params = {
        "offset": 0,
        "limit": 10,
        "sort_by": "total_volume",
    }
    response = requests.get(url, params=params)
    return response.json()["collections"]

def get_assets_from_collection(collection_slug):
    url = f"{OPENSEA_API_BASE}/assets"
    params = {
        "order_direction": "desc",
        "offset": 0,
        "limit": 50,
        "collection": collection_slug,
    }
    response = requests.get(url, params=params)
    return response.json()["assets"]

def get_historical_average_price(token_id):
    url = f"{OPENSEA_API_BASE}/events"
    params = {
        "asset_contract_address": token_id,
        "event_type": "successful",
        "only_opensea": "false",
        "offset": "0",
        "limit": "50",
        "occurred_after": int(time.time() - TIME_WINDOW_DAYS * 24 * 60 * 60),
    }
    response = requests.get(url, params=params)
    events = response.json()["asset_events"]

    total_price = 0
    num_sales = len(events)
    for event in events:
        total_price += float(event["total_price"]) / (10 ** 18)

    return total_price / num_sales if num_sales > 0 else None

def analyze_assets(assets):
    analyzed_assets = []
    for asset in assets:
        if asset["sell_orders"] and asset["sell_orders"][0]["current_price"]:
            price_in_eth = float(asset["sell_orders"][0]["current_price"]) / (10 ** 18)
            historical_average_price = get_historical_average_price(asset["token_id"])

            if historical_average_price:
                analyzed_assets.append({
                    "token_id": asset["token_id"],
                    "price_in_eth": price_in_eth,
                    "historical_average_price": historical_average_price,
                })

    return analyzed_assets

def should_trade(asset):
    return asset["price_in_eth"] <= asset["historical_average_price"] * PRICE_THRESHOLD

def execute_trade(asset):
    print(f"Trade executed for token_id: {asset['token_id']}, price: {asset['price_in_eth']} ETH")

def main():
    while True:
        top_collections = get_top_collections()
        for collection in top_collections:
            assets = get_assets_from_collection(collection["slug"])
            analyzed_assets = analyze_assets(assets)
            for asset in analyzed_assets:
                if should_trade(asset):
                    execute_trade(asset)
        time.sleep(60 * 5)

if __name__ == "__main__":
    main()

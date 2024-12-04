import asyncio
from project.scripts.websocket_logic import fetch_market_data

def run():
    print("Running websocket task")

    async def scheduled_fetch():
        while True:
            try:
                # List of crypto pairs to fetch
                pairs = ["ETH/USD", "XRP/USD", "SOL/USD", "BNB/USD", "DOT/USD"]

                for pair in pairs:
                    print(f"Fetching data for {pair}...")
                    await fetch_market_data(pair)

                # Wait for 10 minutes before the next execution
                print("Waiting for 10 minutes...")
                await asyncio.sleep(10 * 60)  # 10 minutes
            except Exception as e:
                print(f"Error during fetch: {e}")
                await asyncio.sleep(10 * 60)  # Wait before retrying

    # Use asyncio to run the asynchronous function
    asyncio.run(scheduled_fetch())

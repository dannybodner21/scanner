import json
import time
import urllib.request
import os
import requests
import asyncio
import websockets
from django.http import HttpResponseRedirect
from django.shortcuts import render
from .models import Recipe, Cryptocurrency
from .forms import AddRecipe
from datetime import datetime, timedelta
from django.http import JsonResponse



def fetch_market_data_two():

    # set up API call to CoinMarketCap
    api_key = '7dd5dd98-35d0-475d-9338-407631033cd9'
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
    url_historical = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/ohlcv/historical"
    url_historical = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/historical'



    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': api_key,
    }

    parameters = {
        'start': '1',
        'limit': '100',
        'convert': 'USD'
    }

    try:
        response = requests.get(url, headers=headers, params=parameters)
        response.raise_for_status()
        data = response.json()['data']

        # get the top 10 coins and display all the data
        top_10_cryptos = []

        for crypto in data:

            name = crypto['name']
            symbol = crypto['symbol']
            last_price = round(float(crypto['quote']['USD']['price']), 4)
            volume_24hr = round(float(crypto['quote']['USD']['volume_24h']), 4)
            circulating_supply = round(float(crypto.get('circulating_supply', 0)), 4)
            relative_volume = 0.0
            price_change_24hr = float(crypto['quote']['USD']['percent_change_24h'])

            # gap percentage - calculate price 24 hours ago
            price_24h_ago = last_price / (1 + (price_change_24hr / 100))
            gap_percentage = 0
            if price_24h_ago > 0.00:
                gap_percentage = round(float(((last_price - price_24h_ago) / price_24h_ago) * 100))

            volume_30min = float(crypto['quote']['USD']['volume_24h']) / 48
            price_change_5min = 0.0
            price_change_10min = 0.0
            price_change_1hr = 0.0


            ####### COME BACK TO THIS ###########
            # criteria for green background
            #criteria_met = (
            #    volume_30min > 10000 and
            #    supply < 20000000 and
            #    relative_volume > 5 and
            #    price_change_5min > 0 and
            #    price_change_10min > 0
            #)
            #####################################
            criteria_met = False

            top_10_cryptos.append({
                'name': name,
                'symbol': symbol,
                'last_price': last_price,
                'volume_24hr': volume_24hr,
                'circulating_supply': circulating_supply,
                'relative_volume': relative_volume,
                'gap_percentage': gap_percentage,
                'price_change_5min': price_change_5min,
                'price_change_10min': price_change_10min,
                'price_change_1hr': price_change_1hr,
                'price_change_24hr': price_change_24hr,

                'row_class': 'green' if criteria_met else 'white',
            })


        headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': api_key,
        }

        for crypto in top_10_cryptos:

            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)
            interval = '5m'
            limit = 120

            params = {
                'symbol': crypto['symbol'],
                'time_start': start_time.isoformat(),
                'time_end': end_time.isoformat(),
                'interval': interval,
                'count': limit,
            }

            response = requests.get(url_historical, headers=headers, params=params)
            data = response.json()

            time.sleep(2)

            quotes = data['data']['quotes']

            price_now = quotes[-1]['quote']['USD']['price']
            price_5min_ago = quotes[-2]['quote']['USD']['price']
            price_10min_ago = quotes[-3]['quote']['USD']['price']
            price_1hr_ago = quotes[-11]['quote']['USD']['price']
            price_change_5min = ((price_now - price_5min_ago) / price_5min_ago) * 100
            price_change_10min = ((price_now - price_10min_ago) / price_10min_ago) * 100
            price_change_1hr = ((price_now - price_1hr_ago) / price_1hr_ago) * 100


            params = {
                'symbol': crypto['symbol'],
                'interval': '1d',
                'count': 30,
            }

            response = requests.get(url_historical, headers=headers, params=params)
            data = response.json()

            time.sleep(2)

            print(crypto['symbol'])

            volumes = [quote['quote']['USD']['volume_24h'] for quote in data['data']['quotes']]
            average_daily_volume = sum(volumes) / len(volumes)
            relative_volume = volumes[-1] / average_daily_volume

            crypto['relative_volume'] = relative_volume
            crypto['price_change_5min'] = price_change_5min
            crypto['price_change_10min'] = price_change_10min
            crypto['price_change_1hr'] = price_change_1hr

        return top_10_cryptos


    # API call failed
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from CoinMarketCap: {e}")
        return render(request, 'market_scanner.html', {'error': str(e)})


# Helper function for Kraken WebSocket connection
async def fetch_realtime_data(pairs):
    """Fetch real-time ticker data using Kraken WebSocket."""
    uri = "wss://ws.kraken.com"
    subscription_message = {
        "event": "subscribe",
        "pair": pairs,
        "subscription": {"name": "ticker"}
    }
    results = {}

    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps(subscription_message))
        while len(results) < len(pairs):  # Ensure we get data for all pairs
            response = await websocket.recv()
            data = json.loads(response)
            if isinstance(data, list):  # Real-time data response
                pair = data[-1]  # Pair name
                ticker_data = data[1]  # Ticker data
                last_price = float(ticker_data["c"][0])
                volume_24hr = float(ticker_data["v"][1])
                low_price_24hr = float(ticker_data["l"][1])
                open_price_24hr = float(ticker_data["o"][1])
                gap_percentage = (
                    ((last_price - open_price_24hr) / open_price_24hr) * 100
                    if open_price_24hr > 0 else 0
                )
                results[pair] = {
                    "last_price": last_price,
                    "volume_24hr": volume_24hr,
                    "low_price_24hr": low_price_24hr,
                    "gap_percentage": gap_percentage,
                }
        return results


def fetch_historical_prices(pair, interval=5):
    """Fetch historical OHLC data using Kraken REST API."""
    url = "https://api.kraken.com/0/public/OHLC"
    params = {
        "pair": pair,
        "interval": interval,
    }
    response = requests.get(url, params=params)
    data = response.json()

    if "error" in data and data["error"]:
        raise Exception(f"Kraken API error: {data['error']}")

    ohlc_data = data["result"][list(data["result"].keys())[0]]
    return ohlc_data


def calculate_relative_volume(pair):
    """Calculate relative volume using historical data."""
    historical_volumes = fetch_historical_prices(pair, interval=1440)
    daily_volumes = [float(row[6]) for row in historical_volumes[-30:]]  # Last 30 days
    average_volume = sum(daily_volumes) / len(daily_volumes)

    # Get current 24-hour volume
    current_data = fetch_historical_prices(pair, interval=5)[-1]
    current_volume = float(current_data[6])  # Current volume from OHLC

    return current_volume / average_volume


def fetch_price_changes(pair):
    """Calculate price changes for 5 min, 10 min, 1 hr, and 24 hr."""
    ohlc_data_5min = fetch_historical_prices(pair, interval=5)
    ohlc_data_1hr = fetch_historical_prices(pair, interval=60)
    ohlc_data_24hr = fetch_historical_prices(pair, interval=1440)

    current_price = float(ohlc_data_5min[-1][4])
    price_5min_ago = float(ohlc_data_5min[-2][4])
    price_10min_ago = float(ohlc_data_5min[-3][4])
    price_1hr_ago = float(ohlc_data_1hr[-2][4])
    price_24hr_ago = float(ohlc_data_24hr[-2][4])

    return {
        "price_change_5min": ((current_price - price_5min_ago) / price_5min_ago) * 100,
        "price_change_10min": ((current_price - price_10min_ago) / price_10min_ago) * 100,
        "price_change_1hr": ((current_price - price_1hr_ago) / price_1hr_ago) * 100,
        "price_change_24hr": ((current_price - price_24hr_ago) / price_24hr_ago) * 100,
    }


async def scheduled_fetch():
    """Fetch data every 10 minutes."""

    pairs = ["ETH/USD", "XRP/USD", "SOL/USD", "ADA/USD","TRX/USD","AVAX/USD",
    "SHIB/USD", "TON/USD", "XLM/USD", "LINK/USD", "DOT/USD","SUI/USD","LTC/USD",
    "NEAR/USD","UNI/USD","PEPE/USD","APT/USD","ICP/USD","POL/USD","FET/USD",
    "RENDER/USD","ALGO/USD","TAO/USD","FIL/USD","ARB/USD","KAS/USD","ATOM/USD",
    "STX/USD","XMR/USD","DAI/USD","AAVE/USD","FTM/USD","TIA/USD","IMX/USD",
    "WIF/USD","INJ/USD","BONK/USD","OP/USD","MNT/USD","GRT/USD","SEI/USD",
    "ONDO/USD","ENA/USD","RUNE/USD","FLOKI/USD","GALA/USD","QNT/USD",
    "MKR/USD","JASMY/USD","SAND/USD","PYTH/USD","FLR/USD","LDO/USD",
    "XTZ/USD","EOS/USD","FLOW/USD","JUP/USD","STRK/USD","BEAM/USD",
    "HNT/USD","RAY/USD","EGLD/USD","ENS/USD","AXS/USD","POPCAT/USD",
    "APE/USD","MANA/USD","DYDX/USD","MSOL/USD","RSR/USD","ZEC/USD",
    "CRV/USD","CHZ/USD","MINA/USD","PENDLE/USD","AKT/USD","W/USD",
    "SNX/USD","MOG/USD","LUNA/USD","MEW/USD","ZK/USD","BLUR/USD","COMP/USD",
    "SUPER/USD","ARKM/USD","EIGEN/USD","KAVA/USD","GNO/USD","KSM/USD",
    "PRIME/USD","DASH/USD","SAFE/USD","ZRO/USD","1INCH/USD","ASTR/USD",
    "WOO/USD","ENJ/USD","GMT/USD","LPT/USD","ETHFI/USD","MEME/USD",
    "WTC/USD","XMC/USD","FORM/USD","TOKAU/USD","RELAY/USD","X/USD"]



    while True:

        print('============== going through ===============')

        try:

            real_time_data = await fetch_realtime_data(pairs)

            top_cryptos = []
            for pair, data in real_time_data.items():
                try:
                    relative_volume = calculate_relative_volume(pair)
                    price_changes = fetch_price_changes(pair)

                    '''
                    top_cryptos.append({
                        "relative_volume": relative_volume,
                        "gap_percentage": data["gap_percentage"],
                        **price_changes,
                    })
                    '''
                    top_cryptos.append({
                        "name": pair.split("/")[0],
                        "symbol": pair,
                        "last_price": data["last_price"],
                        "volume_24hr": data["volume_24hr"],
                        "relative_volume": relative_volume,
                        "gap_percentage": data["gap_percentage"],
                        "price_change_5min": price_changes['price_change_5min'],
                        "price_change_10min": price_changes['price_change_10min'],
                        "price_change_1hr": price_changes['price_change_1hr'],
                        "price_change_24hr": price_changes['price_change_24hr'],
                    })


                except Exception as e:
                    print(f"Error processing {pair}: {e}")

            send_text(top_cryptos)
            await asyncio.sleep(10 * 60)


        except Exception as e:
            print(f"Error during scheduled fetch: {e}")
            await asyncio.sleep(10 * 60)



def serveHTML(cryptos):
    return render("market_scanner.html", {
        "top_cryptos": cryptos,
    })


def send_text(top_cryptos):

    # telegram bot information
    chat_id = '1077594551'
    chat_id_ricki = '1054741134,'
    chat_ids = [chat_id, chat_id_ricki]
    #chat_ids = [chat_id]
    bot_token = '7672687080:AAFWvkwzp-LQE92XdO9vcVa5yWJDUxO17yE'
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"


    # if any of the cryptos meets trigger criteria, send telegram message

    # send message to myself and Ricki
    for chat_id in chat_ids:

        for crypto in top_cryptos:

            trigger_one_hit = False
            trigger_two_hit = False
            trigger_three_hit = False
            message_one = ''
            message_two = ''
            message_three = ''

            # if gap percentage is greater than to 2
            # if relative volume is greater than to 2
            # if 1 hr price change is greater than 5

            if crypto['gap_percentage'] > 20:
                message_one = 'gap percentage is greater than 20%: ' + str(crypto['gap_percentage'])
                trigger_one_hit = True
            if crypto['relative_volume'] > 5:
                message_two = 'relative volume is greater than 5%: ' + str(crypto['relative_volume'])
                trigger_two_hit = True
            if crypto['price_change_1hr'] > 5:
               message_three = 'price change over 1 hr is greater than 5%: ' + str(crypto['price_change_1hr'])
               trigger_three_hit = True
            # send telegram message

            if trigger_one_hit == True and trigger_two_hit == True and trigger_three_hit == True:
                message = crypto['name'] + ' : \n' + message_one + '\n' + message_two + '\n' + message_three

                payload = {
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "Markdown",
                }
                response = requests.post(url, data=payload)
                if response.status_code == 200:
                    print("Message sent successfully.")
                else:
                    print(f"Failed to send message: {response.content}")

    return



def fetch_market_data(request):
    """Trigger the scheduled WebSocket fetch."""
    try:
        top_cryptos = asyncio.run(scheduled_fetch())

    except Exception as e:
        return JsonResponse({"error": str(e)})


async def main_function(request):
    while True:
        fetch_market_data(request)
        await asyncio.sleep(5 * 60)










'''


async def fetch_kraken_data(pairs, subscription_type):
    """Fetch data from Kraken WebSocket API"""
    kraken_url = "wss://ws.kraken.com"
    try:
        async with websockets.connect(kraken_url) as websocket:
            # Subscribe to the WebSocket
            subscription_message = {
                "event": "subscribe",
                "pair": pairs,
                "subscription": {"name": subscription_type},
            }
            await websocket.send(json.dumps(subscription_message))

            # Collect initial responses
            data = []
            for _ in range(10):  # Collect 10 messages for example
                response = await websocket.recv()
                parsed_data = json.loads(response)
                if isinstance(parsed_data, list):
                    data.append(parsed_data)

            return data
    except Exception as e:
        print(f"Error fetching data from Kraken WebSocket: {e}")
        return None


async def fetch_realtime_data(pairs):
    uri = "wss://ws.kraken.com"
    subscription_message = {
        "event": "subscribe",
        "pair": pairs,
        "subscription": {"name": "ticker"}
    }
    results = {}

    async with websockets.connect(uri) as websocket:
        print('------------ HERE 0 ------------------------')
        await websocket.send(json.dumps(subscription_message))
        while len(results) < len(pairs):  # Wait until we receive data for all pairs
            response = await websocket.recv()
            data = json.loads(response)
            print('------------ HERE 1 ------------------------')
            print(data)
            #print('list-------')
            #print(list)
            if isinstance(data, list):  # Data updates
                #print('data -1-----------------------')
                #print(data[-1])
                print('------------ HERE 2 ------------------------')
                pair = data[-1]  # Pair name
                print('------------ HERE 3 ------------------------')
                ticker_data = data[1]  # Ticker information
                print('------------ HERE 4 ------------------------')
                last_price = float(ticker_data["c"][0])  # Close price
                print('------------ HERE 5 ------------------------')
                volume_24hr = float(ticker_data["v"][1])  # 24-hour volume
                print('------------ HERE 6 ------------------------')
                low_price_24hr = float(ticker_data["l"][1])  # 24-hour low
                print('------------ HERE 7 ------------------------')
                open_price_24hr = float(ticker_data["o"][1])  # 24-hour open
                print('------------ HERE 8 ------------------------')
                gap_percentage = (
                    ((last_price - open_price_24hr) / open_price_24hr) * 100
                    if open_price_24hr > 0
                    else 0
                )
                print('------------ HERE 9 ------------------------')
                results[pair] = {
                    "last_price": last_price,
                    "volume_24hr": volume_24hr,
                    "low_price_24hr": low_price_24hr,
                    "gap_percentage": gap_percentage,
                }
                print(results)
            #print('results-------')
            #print(results)

            print('------------ HERE 3 ------------------------')

            print('LENGTH OF RESULTS')
            print(len(results))
        return results


def fetch_historical_data(pair, interval=5):
    url = "https://api.kraken.com/0/public/OHLC"
    since = int((datetime.utcnow() - timedelta(minutes=interval * 2)).timestamp())  # Fetch enough data
    params = {"pair": pair, "interval": interval, "since": since}
    response = requests.get(url, params=params)
    data = response.json()

    if "result" in data:
        pair_data = data["result"].get(pair.replace("/", ""))
        if pair_data:
            return pair_data[-1]  # Most recent interval
    return None


def fetch_historical_volume(pair, days=30):
    url = "https://api.kraken.com/0/public/OHLC"
    interval = 1440  # Daily interval
    params = {
        "pair": pair,
        "interval": interval,
    }

    # Fetch OHLC data
    response = requests.get(url, params=params)
    data = response.json()

    # Extract volumes
    if "error" in data and data["error"]:
        raise Exception(f"Kraken API error: {data['error']}")

    ohlc_data = data["result"][list(data["result"].keys())[0]]
    daily_volumes = [float(row[6]) for row in ohlc_data[-days:]]  # Last 30 days
    return daily_volumes


def calculate_relative_volume(pair):
    # Get historical volume
    historical_volumes = fetch_historical_volume(pair)
    average_volume = sum(historical_volumes) / len(historical_volumes)

    # Get current 24-hour volume from ticker
    url = "https://api.kraken.com/0/public/Ticker"
    params = {"pair": pair}
    response = requests.get(url, params=params)
    data = response.json()

    if "error" in data and data["error"]:
        raise Exception(f"Kraken API error: {data['error']}")

    ticker_data = data["result"][list(data["result"].keys())[0]]
    current_volume_24hr = float(ticker_data["v"][1])  # 24-hour volume

    # Calculate relative volume
    relative_volume = current_volume_24hr / average_volume
    return relative_volume


def fetch_historical_prices(pair, interval=5):
    url = "https://api.kraken.com/0/public/OHLC"
    params = {
        "pair": pair,
        "interval": interval,  # 5-minute interval
    }
    response = requests.get(url, params=params)
    data = response.json()

    if "error" in data and data["error"]:
        raise Exception(f"Kraken API error: {data['error']}")

    # Get OHLC data for the pair
    ohlc_data = data["result"][list(data["result"].keys())[0]]
    return ohlc_data


async def fetch_gap(pair):
    # Fetch current price using WebSocket
    async with websockets.connect("wss://ws.kraken.com/") as websocket:
        subscribe_message = {
            "event": "subscribe",
            "pair": [pair],
            "subscription": {"name": "ticker"},
        }
        await websocket.send(json.dumps(subscribe_message))

        while True:
            message = await websocket.recv()
            data = json.loads(message)

            # Check if the message contains price data
            if isinstance(data, list) and len(data) > 1:
                ticker_data = data[1]
                current_price = float(ticker_data["c"][0])
                break

    # Fetch historical price using REST API
    url = "https://api.kraken.com/0/public/OHLC"
    params = {
        "pair": pair,
        "interval": 1440,  # Daily intervals
    }
    response = requests.get(url, params=params)
    data = response.json()

    if "error" in data and data["error"]:
        raise Exception(f"Kraken API error: {data['error']}")

    ohlc_data = data["result"][list(data["result"].keys())[0]]
    price_24h_ago = float(ohlc_data[-2][4])  # Close price from the previous day

    # Calculate gap percentage
    gap_percentage = ((current_price - price_24h_ago) / price_24h_ago) * 100
    return gap_percentage


async def fetch_price_changes(pair):
    # Fetch current price using WebSocket
    async with websockets.connect("wss://ws.kraken.com/") as websocket:
        subscribe_message = {
            "event": "subscribe",
            "pair": [pair],
            "subscription": {"name": "ticker"},
        }
        await websocket.send(json.dumps(subscribe_message))

        current_price = None
        while True:
            message = await websocket.recv()
            data = json.loads(message)

            # Check if the message contains price data
            if isinstance(data, list) and len(data) > 1:
                ticker_data = data[1]
                current_price = float(ticker_data["c"][0])  # Last trade close price
                break

    # Fetch historical prices using REST API
    def fetch_historical_prices(pair, interval=5):
        url = "https://api.kraken.com/0/public/OHLC"
        params = {
            "pair": pair,
            "interval": interval,  # 5-minute interval
        }
        response = requests.get(url, params=params)
        data = response.json()

        if "error" in data and data["error"]:
            raise Exception(f"Kraken API error: {data['error']}")

        # Get OHLC data for the pair
        ohlc_data = data["result"][list(data["result"].keys())[0]]
        return ohlc_data

    ohlc_data = fetch_historical_prices(pair, interval=5)
    ohlc_data_1hr = fetch_historical_prices(pair, interval=60)
    ohlc_data_24hr = fetch_historical_prices(pair, interval=1440)

    # Get the closing prices
    price_5min_ago = float(ohlc_data[-2][4])  # Close price 5 minutes ago
    price_10min_ago = float(ohlc_data[-3][4])  # Close price 10 minutes ago
    price_1hr_ago = float(ohlc_data_1hr[-2][4])  # Close price 1 hour ago
    price_24hr_ago = float(ohlc_data_24hr[-2][4])  # Close price 24 hours ago

    # Calculate percentage changes
    price_change_5min = ((current_price - price_5min_ago) / price_5min_ago) * 100
    price_change_10min = ((current_price - price_10min_ago) / price_10min_ago) * 100
    price_change_1hr = ((current_price - price_1hr_ago) / price_1hr_ago) * 100
    price_change_24hr = ((current_price - price_24hr_ago) / price_24hr_ago) * 100

    return {
        "price_change_5min": price_change_5min,
        "price_change_10min": price_change_10min,
        "price_change_1hr": price_change_1hr,
        "price_change_24hr": price_change_24hr,
    }


def fetch_market_data(pair):
    #pairs = ["ADA/USD", "DOT/USD", "XRP/USD"]
    try:
        # Fetch real-time data
        real_time_data = asyncio.run(fetch_realtime_data(pairs))

        relative_volume = 0.0
        gap_percentage = 0.0

        # Example: Combine with historical or calculated metrics (placeholder for further logic)
        top_cryptos = []
        for pair, data in real_time_data.items():

            try:
                relative_volume = calculate_relative_volume(pair)
                print(f"Relative Volume for {pair}: {relative_volume}")

                gap_percentage = asyncio.run(fetch_gap(pair))
                print(f"Gap Percentage for {pair}: {gap_percentage:.2f}%")

                changes = asyncio.run(fetch_price_changes(pair))

            except Exception as e:
                print(f"Error: {e}")

            top_cryptos.append({
                "name": pair.split("/")[0],
                "symbol": pair,
                "last_price": data["last_price"],
                "volume_24hr": data["volume_24hr"],
                "relative_volume": relative_volume,
                "gap_percentage": gap_percentage,
                "price_change_5min": changes['price_change_5min'],
                "price_change_10min": changes['price_change_10min'],
                "price_change_1hr": changes['price_change_1hr'],
                "price_change_24hr": changes['price_change_24hr'],
            })

        #test_data = fetch_market_data_two()

        return render(request, "market_scanner.html", {
            "top_cryptos": top_cryptos,
            "test_data": test_data,
        })
    except Exception as e:
        return render(request, "market_scanner.html", {"error": str(e)})


if __name__ == "__main__":
    try:
        asyncio.run(scheduled_fetch())
    except KeyboardInterrupt:
        print("Stopped by user.")


'''

def addRecipe(request, id=''):
    if request.method == "POST":
        form = AddRecipe(request.POST)

        if form.is_valid():
            newRecipe = Recipe(title = form.cleaned_data['title'],
                               ingredients = form.cleaned_data['ingredients'],
                               instructions = form.cleaned_data['instructions'],
                               prepMinutes = form.cleaned_data['prepMinutes'],
                               cookMinutes = form.cleaned_data['cookMinutes'],
                               servings = form.cleaned_data['servings']
                               )
            newRecipe.save()

            return HttpResponseRedirect(f"/viewRecipe/{newRecipe.id}")
        else:
            pass # TODO - Show error

    else:
        form = AddRecipe()

        form.fields['ingredients'].initial = "Separate by line breaks.\nOn each line: Quantity, Unit, Ingredient"
        form.fields['instructions'].initial = "Separate by line breaks."

        return render(request, "addRecipe.html", {
            "form": form,
        })

def viewRecipe(request, id):
    recipe = Recipe.objects.get(pk=id)
    formattedIngredients = recipe.getIngredients()
    formattedInstructions = recipe.getInstructions()
    prepTime = recipe.convert_mins_to_hhmm(recipe.prepMinutes)
    cookTime = recipe.convert_mins_to_hhmm(recipe.cookMinutes)
    combinedTime = recipe.combine_times()

    return render(request, "viewRecipe.html", {
        "recipe": recipe,
        "formattedIngredients": formattedIngredients,
        "formattedInstructions": formattedInstructions,
        "prepTime": prepTime,
        "cookTime" : cookTime,
        "combinedTime" : combinedTime
    })

def browseRecipe(request, tags=None):
    recipes = Recipe.objects.all() # TODO add filtering

    return render(request, "browseRecipes.html", {
        "recipes": recipes
    })

def deleteRecipe(request, id):
    Recipe.objects.filter(pk=id).delete()
    # SomeModel.objects.filter(id=id).delete()
    recipes = Recipe.objects.all()
    return render(request, "browseRecipes.html", {
        "recipes": recipes
    })

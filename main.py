from binance.spot import Spot
import os
import time
import dotenv

dotenv.load_dotenv('.env')
api_key = os.environ.get("API_KEY")
secret_key = os.environ.get("SECRET_KEY")


client = Spot(key=api_key, secret=secret_key,
              base_url="https://api.binance.com", timeout=3)
print(client.time())

# Get account information
print(client.account())

"""
base_url="https://testnet.binance.vision"
# Post a new order
params = {
    'symbol': 'BTCUSDT',
    'side': 'SELL',
    'type': 'LIMIT',
    'timeInForce': 'GTC',
    'quantity': 0.002,
    'price': 9500
}

response = client.new_order(**params)
print(response)
"""

import os, time, pyotp
from dotenv import load_dotenv
from SmartApi import SmartConnect
from SmartApi.smartWebSocketV2 import SmartWebSocketV2

load_dotenv()
api_key = os.environ["ANGEL_API_KEY"]
client_id = os.environ["ANGEL_CLIENT_ID"]

o = SmartConnect(api_key=api_key)
data = o.generateSession(client_id, os.environ["ANGEL_PASSWORD"],
                          pyotp.TOTP(os.environ["ANGEL_TOTP"]).now())
auth_token = data["data"]["jwtToken"]
feed_token = o.getfeedToken()

sws = SmartWebSocketV2(auth_token, api_key, client_id, feed_token, max_retry_attempt=3)

def on_data(wsapp, message):
    print("TICK:", message)

def on_open(wsapp):
    print("WebSocket opened -- subscribing to NIFTY 50 (token 99926000)...")
    sws.subscribe("check_ws", 1, [{"exchangeType": 1, "tokens": ["99926000"]}])

def on_error(wsapp, error):
    print("ERROR:", error)

def on_close(wsapp):
    print("Closed")

sws.on_open = on_open
sws.on_data = on_data
sws.on_error = on_error
sws.on_close = on_close

import threading
threading.Thread(target=sws.connect, daemon=True).start()

print("Waiting 20 seconds for ticks (market must be open for any to arrive)...")
time.sleep(20)
print("Done.")

import os, pyotp
from dotenv import load_dotenv
from SmartApi import SmartConnect

load_dotenv()
o = SmartConnect(api_key=os.environ["ANGEL_API_KEY"])
o.generateSession(os.environ["ANGEL_CLIENT_ID"], os.environ["ANGEL_PASSWORD"],
                   pyotp.TOTP(os.environ["ANGEL_TOTP"]).now())
r = o.getCandleData(dict(exchange="NSE", symboltoken="99926000", interval="FIVE_MINUTE",
                          fromdate="2026-09-16 09:15", todate="2026-09-16 10:00"))
print(r)

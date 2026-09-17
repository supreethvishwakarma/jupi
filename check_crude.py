import os, pyotp, datetime as dt
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from SmartApi import SmartConnect

load_dotenv()
o = SmartConnect(api_key=os.environ["ANGEL_API_KEY"])
o.generateSession(os.environ["ANGEL_CLIENT_ID"], os.environ["ANGEL_PASSWORD"],
                   pyotp.TOTP(os.environ["ANGEL_TOTP"]).now())

# 569900 = CRUDEOIL Oct26, 565899 = CRUDEOIL Sep26 -- change to match what you picked in the sidebar
TOKEN = "569900"

now = dt.datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)
r = o.getCandleData(dict(exchange="MCX", symboltoken=TOKEN, interval="FIVE_MINUTE",
                          fromdate=(now - dt.timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"),
                          todate=now.strftime("%Y-%m-%d %H:%M")))
print(r)

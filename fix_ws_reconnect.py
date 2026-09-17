PATH = "app.py"

old1 = '''        def __init__(self):
            self.latest = {}
            self.subscribed = set()
            self.lock = threading.Lock()
            self.ready = False
            self.sws = None
            self._connect()

        def _connect(self):
            api_key = os.environ["ANGEL_API_KEY"]'''

new1 = '''        def __init__(self):
            self.latest = {}
            self.subscribed = set()
            self.lock = threading.Lock()
            self.ready = False
            self.sws = None
            self.last_reconnect_attempt = 0
            self._connect()

        def _connect(self):
            self.subscribed = set()
            self.ready = False
            api_key = os.environ["ANGEL_API_KEY"]'''

old2 = '''            self.sws.on_data = on_data
            self.sws.on_open = on_open
            self.sws.on_error = on_error
            self.sws.on_close = on_close
            threading.Thread(target=self.sws.connect, daemon=True).start()

        def ensure_subscribed(self, exch, token):'''

new2 = '''            self.sws.on_data = on_data
            self.sws.on_open = on_open
            self.sws.on_error = on_error
            self.sws.on_close = on_close
            threading.Thread(target=self.sws.connect, daemon=True).start()

        def ensure_connected(self):
            """If the WebSocket has died (exhausted its own retry budget, or
            never came up), proactively reconnect instead of staying dead for
            the rest of the process. 60s cooldown between attempts so a truly
            down connection doesn't hammer the login endpoint."""
            if self.ready:
                return
            now_ts = _time.time()
            if now_ts - self.last_reconnect_attempt < 60:
                return
            self.last_reconnect_attempt = now_ts
            try:
                self._connect()
            except Exception:
                pass

        def ensure_subscribed(self, exch, token):'''

old3 = '''        pp = load_paper()
        now = dt.datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)
        ts = tick_service()

        blocked_total ='''

new3 = '''        pp = load_paper()
        now = dt.datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)
        ts = tick_service()
        ts.ensure_connected()

        blocked_total ='''

with open(PATH) as f:
    content = f.read()

results = []
for i, (old, new) in enumerate([(old1, new1), (old2, new2), (old3, new3)], 1):
    n = content.count(old)
    results.append(n)
    if n != 1:
        print(f"WARNING patch {i}: expected 1 match, found {n}. Aborting.")
        raise SystemExit(1)
    content = content.replace(old, new)

import shutil
shutil.copy(PATH, PATH + ".bak_wsreconnect")

with open(PATH, "w") as f:
    f.write(content)

print("Patched -- WebSocket now auto-reconnects if it dies, instead of staying dead forever.")

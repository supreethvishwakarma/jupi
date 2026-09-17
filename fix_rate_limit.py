PATH = "app.py"

pairs = [
    (
'''            df = fetch((now - dt.timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M"),
                       now.strftime("%Y-%m-%d %H:%M"), "ONE_MINUTE", TOKEN, EXCH)''',
'''            try:
                df = fetch((now - dt.timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M"),
                           now.strftime("%Y-%m-%d %H:%M"), "ONE_MINUTE", TOKEN, EXCH)
            except Exception as e:
                status.error(f"Broker call failed: {e}")
                df = pd.DataFrame()'''
    ),
    (
'''            df = fetch((now - dt.timedelta(days=10)).strftime("%Y-%m-%d %H:%M"),
                       now.strftime("%Y-%m-%d %H:%M"), INTERVAL, TOKEN, EXCH)''',
'''            try:
                df = fetch((now - dt.timedelta(days=10)).strftime("%Y-%m-%d %H:%M"),
                           now.strftime("%Y-%m-%d %H:%M"), INTERVAL, TOKEN, EXCH)
            except Exception as e:
                status.error(f"Broker call failed: {e}")
                df = pd.DataFrame()'''
    ),
]

with open(PATH) as f:
    content = f.read()

ok = True
for old, new in pairs:
    n = content.count(old)
    if n != 1:
        print(f"WARNING: expected 1 match, found {n} for a block. Aborting.")
        ok = False
        break
    content = content.replace(old, new)

if ok:
    with open(PATH, "w") as f:
        f.write(content)
    print("Patched -- broker call failures now show a message instead of crashing the app.")

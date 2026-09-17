PATH = "app.py"

with open(PATH) as f:
    content = f.read()

old = "Hilega Milega (RSI x WMA)"
new = "Vanguard (RSI x WMA)"

n = content.count(old)
if n == 0:
    print("No occurrences found -- nothing to rename (or already renamed).")
else:
    content = content.replace(old, new)
    import shutil
    shutil.copy(PATH, PATH + ".bak_rename")
    with open(PATH, "w") as f:
        f.write(content)
    print(f"Patched -- renamed {n} occurrence(s) of 'Hilega Milega (RSI x WMA)' to 'Vanguard (RSI x WMA)'.")

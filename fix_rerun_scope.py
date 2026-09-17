PATH = "app.py"
old = 'st.rerun(scope="fragment")'
new = 'st.rerun()'

with open(PATH) as f:
    content = f.read()

n = content.count(old)
if n == 0:
    print("No match found -- the line may already be fixed, or wording differs. Run: grep -n 'rerun' app.py")
else:
    content = content.replace(old, new)
    with open(PATH, "w") as f:
        f.write(content)
    print(f"Patched {n} occurrence(s).")

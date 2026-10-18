import os, json, shutil, hashlib
SRC, OUT = "kahaniyan", "data"
shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT + "/s")
idx, tot = [], 0
for f in sorted(os.listdir(SRC)):
    if not f.endswith(".txt"):
        continue
    t = open(f"{SRC}/{f}", encoding="utf-8").read().strip()
    sid = hashlib.md5(f.encode()).hexdigest()[:8]
    open(f"{OUT}/s/{sid}.txt", "w", encoding="utf-8").write(t)
    tot += len(t.encode())
    idx.append({"id": sid, "t": f[:-4], "p": t[:120].replace("\n", " ")})
json.dump(idx, open(OUT + "/index.json", "w", encoding="utf-8"),
          ensure_ascii=False, separators=(",", ":"))
print(len(idx), "कहानियाँ |", round(tot / 1e6, 1), "MB (सीमा 1000 MB)")

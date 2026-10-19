import os, json, shutil, hashlib, base64

SRC, OUT = "kahaniyan", "data"
shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT + "/s")
idx, tot = [], 0

for f in sorted(os.listdir(SRC)):
    if not f.endswith(".txt"):
        continue
    
    # असली कहानी पढ़ें
    t = open(f"{SRC}/{f}", encoding="utf-8").read().strip()
    sid = hashlib.md5(f.encode()).hexdigest()[:8]
    
    # कहानी को Base64 में एनकोड करें (सुरक्षा के लिए)
    t_encoded = base64.b64encode(t.encode('utf-8')).decode('utf-8')
    
    # एनकोडेड कहानी को सेव करें
    open(f"{OUT}/s/{sid}.txt", "w", encoding="utf-8").write(t_encoded)
    
    tot += len(t.encode())
    # index.json में सिर्फ टाइटल और प्रीव्यू रखेंगे (सर्च के लिए)
    idx.append({"id": sid, "t": f[:-4], "p": t[:120].replace("\n", " ")})

json.dump(idx, open(OUT + "/index.json", "w", encoding="utf-8"),
          ensure_ascii=False, separators=(",", ":"))
print(len(idx), "कहानियाँ |", round(tot / 1e6, 1), "MB (सीमा 1000 MB)")

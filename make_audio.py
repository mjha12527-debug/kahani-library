import asyncio, os, re, sys, json, hashlib
import edge_tts

HOME = os.path.expanduser("~")
CANDS = [os.environ.get("SRC", ""), "kahaniyan", HOME + "/kahaniyan",
         HOME + "/storage/shared/kahaniyan", HOME + "/kahani-library/kahaniyan"]
SRC = next((c for c in CANDS if c and os.path.isdir(c)), None)
OUT = os.environ.get("OUT", HOME + "/kahani-library/audio")
VOICE = os.environ.get("VOICE", "hi-IN-SwaraNeural")   # पुरुष आवाज़: hi-IN-MadhurNeural
RATE = os.environ.get("RATE", "+0%")                  # धीमी: -10%   तेज़: +10%
EMO = os.environ.get("EMO", "1") != "0"               # भाव बंद करने के लिए EMO=0
try:
    BASE = int(RATE.replace("%", "").replace("+", ""))
except Exception:
    BASE = 0
CHUNK = 1500      # एक टुकड़े में अधिकतम अक्षर
PART = 18000      # एक MP3 भाग में करीब इतने अक्षर (लगभग 20 मिनट)

SADR = re.compile(r"(^|\s)(?:आँसू|आंसू|दुख|दुःख|दर्द|अकेल|मौत|बिछड़|तड़प|सिसक|उदास|रो(?:ना|ने|ता|ती|ते|या|ई|यी))")
ANGR = re.compile(r"(^|\s)(?:गुस्स|क्रोध|चीख|चिल्ला|दहाड़|धिक्कार|खबरदार|ख़बरदार|बर्दाश्त|गद्दार|ग़द्दार)")
HAPR = re.compile(r"(^|\s)(?:खुश|ख़ुश|हँस|हंस|मुस्कु|खिलखिला|मज़ा|मजा|जश्न|बधाई|शाबाश)")
# भाव: (गति में बदलाव %, सुर में बदलाव Hz)
EMOS = {"N": (0, 0), "E": (6, 3), "S": (-10, -3), "A": (8, 2), "H": (4, 4)}

def clean(t):
    t = re.sub(r"https?://\S+", " ", t)
    t = t.replace("॥", "।")
    t = re.sub(r"(\.{2,}|…)", ". ", t)
    t = re.sub(r"[^\w\s।.!?\u200c\u200d\u0900-\u097F]", " ", t)
    t = t.replace("_", " ")
    return t

def cls(s):
    if not EMO:
        return "N"
    if SADR.search(s):
        return "S"
    if ANGR.search(s):
        return "A"
    if HAPR.search(s):
        return "H"
    if s.rstrip().endswith("!"):
        return "E"
    return "N"

def split(t):
    t = clean(t)
    sents = [x.strip() for x in re.split(r"(?<=[।.!?])\s+|\n+", t) if x.strip()]
    out, cur, ck = [], "", "N"
    def flush():
        nonlocal cur
        if cur.strip():
            out.append("<<" + ck + ">>" + cur.strip())
        cur = ""
    for s in sents:
        k = cls(s)
        if cur and (k != ck or len(cur) + len(s) > CHUNK):
            flush()
        while len(s) > CHUNK:
            j = s.rfind(" ", 0, CHUNK)
            j = j if j > 0 else CHUNK
            ck = k
            cur = s[:j]
            flush()
            s = s[j:].strip()
        if s:
            ck = k
            cur = (cur + " " + s).strip()
    flush()
    return out

def group(chunks):
    parts, cur, n = [], [], 0
    for c in chunks:
        if cur and n + len(c) > PART:
            parts.append(cur); cur, n = [], 0
        cur.append(c); n += len(c)
    if cur:
        parts.append(cur)
    return parts

async def speak(text, path):
    m = re.match(r"<<(\w)>>", text)
    k = m.group(1) if m else "N"
    if m:
        text = text[m.end():]
    dr, dp = EMOS.get(k, (0, 0))
    rate = "%+d%%" % (BASE + dr)
    pitch = "%+dHz" % dp
    for i in range(4):
        try:
            await edge_tts.Communicate(text, VOICE, rate=rate, pitch=pitch).save(path)
            if os.path.getsize(path) > 1000:
                return True
        except Exception as e:
            print("   फिर कोशिश", i + 1, str(e)[:60])
            await asyncio.sleep(3 * (i + 1))
    return False

async def main():
    if not SRC:
        print("❌ 'kahaniyan' फ़ोल्डर नहीं मिला। चलाइए: SRC=/पूरा/रास्ता python make_audio.py")
        return
    only = sys.argv[1] if len(sys.argv) > 1 else ""
    os.makedirs(OUT, exist_ok=True)
    ip = OUT + "/index.json"
    idx = json.load(open(ip, encoding="utf-8")) if os.path.exists(ip) else {}
    files = [f for f in sorted(os.listdir(SRC)) if f.endswith(".txt") and only in f]
    if not files:
        print("कोई कहानी नहीं मिली:", only); return
    for f in files:
        name = f[:-4]
        sid = hashlib.md5(f.encode()).hexdigest()[:8]
        if idx.get(sid, {}).get("done"):
            print("⏭️ पहले से बनी:", name); continue
        t = open(f"{SRC}/{f}", encoding="utf-8").read().strip()
        parts = group(split(t))
        d = f"{OUT}/{sid}"
        os.makedirs(d, exist_ok=True)
        print(f"🎙️ {name} — {len(t)} अक्षर, {len(parts)} भाग" + (" · 🎭 भाव चालू" if EMO else ""))
        ok = True
        for pi, chs in enumerate(parts, 1):
            pf = f"{d}/{pi:02d}.mp3"
            if os.path.exists(pf) and os.path.getsize(pf) > 1000:
                continue
            buf = b""
            for ci, c in enumerate(chs, 1):
                tmp = f"{d}/tmp.mp3"
                if not await speak(c, tmp):
                    ok = False; break
                buf += open(tmp, "rb").read()
                print(f"   भाग {pi}/{len(parts)} · टुकड़ा {ci}/{len(chs)}", end="\r")
            if not ok:
                break
            open(pf + ".part", "wb").write(buf)
            os.replace(pf + ".part", pf)
            print(f"   ✅ भाग {pi}/{len(parts)} तैयार ({len(buf)//1024} KB)      ")
        if os.path.exists(f"{d}/tmp.mp3"):
            os.remove(f"{d}/tmp.mp3")
        if ok:
            idx[sid] = {"n": len(parts), "t": name, "done": True}
            json.dump(idx, open(ip, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        else:
            print("⚠️ अधूरी रही (दोबारा चलाने पर वहीं से आगे बढ़ेगी):", name)
    tot = sum(os.path.getsize(os.path.join(r, x)) for r, _, fs in os.walk(OUT) for x in fs)
    print("\n📦 audio फ़ोल्डर का कुल आकार:", round(tot / 1e6, 1), "MB  (GitHub के लिए 1000 MB के अंदर रखें)")

asyncio.run(main())
